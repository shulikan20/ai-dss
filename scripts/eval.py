from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
TEST_CASES_PATH = ROOT / "tests" / "eval_data" / "test_cases.json"
RESULTS_DIR = ROOT / "results"

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent / "eval"))

VARIANT_ALIAS_MAP = {
    "hybrid": "v1_hybrid_i2",
    "classical": "v2_classical",
}

def resolve_variant_name(variant: str) -> str:
    return VARIANT_ALIAS_MAP.get(variant, variant)

_OLLAMA_TAGS_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434") + "/api/tags"

def _ping_ollama() -> bool:
    try:
        return requests.get(_OLLAMA_TAGS_URL, timeout=2.0).status_code == 200
    except Exception:
        return False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

CSV_HEADERS = [
    "test_id", "category", "profile_name", "run_number",
    "variant", "pipeline_used", "llm_available", "processing_time_ms",
    "rank_1", "rank_2", "rank_3", "rank_4", "rank_5",
    "score_1", "score_2", "score_3", "score_4", "score_5",
    "must_haves",
    "p_at_1", "r_at_3", "r_at_5",
    "mh_at_2", "mh_at_3", "mh_at_5",
    "penalty_at_3", "composite",
    "error", "notes",
]

def compute_metrics(
    ranked_capability_ids: list[str],
    must_haves: list[str],
    request_domains: list[str],
    result_domains: list[str],
) -> dict:
    if not must_haves:
        return {
            "p_at_1": None,
            "r_at_3": None,
            "r_at_5": None,
            "mh_at_2": None,
            "mh_at_3": None,
            "mh_at_5": None,
            "penalty_at_3": _penalty_at_k(result_domains[:3], request_domains),
            "composite": None,
        }

    top1 = ranked_capability_ids[:1]
    top2 = ranked_capability_ids[:2]
    top3 = ranked_capability_ids[:3]
    top5 = ranked_capability_ids[:5]

    must_set = set(must_haves)

    p_at_1 = 1.0 if (top1 and top1[0] in must_set) else 0.0
    r_at_3 = len(set(top3) & must_set) / len(must_set) if must_haves else 0.0
    r_at_5 = len(set(top5) & must_set) / len(must_set) if must_haves else 0.0
    mh_at_2 = len(set(top2) & must_set)
    mh_at_3 = len(set(top3) & must_set)
    mh_at_5 = len(set(top5) & must_set)
    penalty = _penalty_at_k(result_domains[:3], request_domains)
    composite = 0.4 * p_at_1 + 0.4 * r_at_5 + 0.2 * (1 - penalty)

    return {
        "p_at_1": round(p_at_1, 3),
        "r_at_3": round(r_at_3, 3),
        "r_at_5": round(r_at_5, 3),
        "mh_at_2": mh_at_2,
        "mh_at_3": mh_at_3,
        "mh_at_5": mh_at_5,
        "penalty_at_3": round(penalty, 3),
        "composite": round(composite, 3),
    }


def _penalty_at_k(result_domains: list[str], request_domains: list[str]) -> float:
    if not result_domains:
        return 0.0
    mismatched = sum(1 for d in result_domains if d not in request_domains)
    return mismatched / len(result_domains)

def build_runner(variant: str):
    from variants import VariantContext, get_variant
    from api.translator.web_form_translator import WebFormTranslator

    ctx = VariantContext()
    repo = ctx.get_repo()
    engine = get_variant(resolve_variant_name(variant), ctx)
    translator = WebFormTranslator()
    return engine, translator, repo

def run_test_case(
    engine,
    translator,
    repo,
    ollama_live: bool,
    case: dict,
    run_number: int,
    variant: str,
) -> dict:
    from api.models import QuestionnaireRequest

    test_id = case["test_id"]
    category = case["category"]
    profile_name = case["profile_name"]
    must_haves = case["ground_truth"]["must_haves"]
    payload = case["payload"]
    request_domains = payload.get("domains", [])

    row: dict = {
        "test_id": test_id,
        "category": category,
        "profile_name": profile_name,
        "run_number": run_number,
        "variant": variant,
        "pipeline_used": "",
        "llm_available": "",
        "processing_time_ms": "",
        "rank_1": "", "rank_2": "", "rank_3": "", "rank_4": "", "rank_5": "",
        "score_1": "", "score_2": "", "score_3": "", "score_4": "", "score_5": "",
        "must_haves": "|".join(must_haves),
        "p_at_1": "", "r_at_3": "", "r_at_5": "",
        "mh_at_2": "", "mh_at_3": "", "mh_at_5": "",
        "penalty_at_3": "", "composite": "",
        "error": "",
        "notes": case["ground_truth"].get("notes", ""),
    }

    try:
        body = QuestionnaireRequest(**payload)
        profile = translator.translate(body, repo)
        t0 = time.perf_counter()
        results = engine.match(profile)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
    except Exception as exc:
        row["error"] = str(exc)
        log.error("  %-20s run %d  ERROR: %s", test_id, run_number, exc)
        return row

    ranked_ids = [r.capability_id for r in results]
    ranked_scores = [r.topsis_score for r in results]
    result_domains = [r.domain for r in results]
    row["pipeline_used"] = getattr(engine, "pipeline_label", "")
    row["llm_available"] = ollama_live
    row["processing_time_ms"] = elapsed_ms

    for i in range(5):
        row[f"rank_{i+1}"] = ranked_ids[i] if i < len(ranked_ids) else ""
        row[f"score_{i+1}"] = (
            round(ranked_scores[i], 4) if i < len(ranked_scores) else ""
        )

    metrics = compute_metrics(ranked_ids, must_haves, request_domains, result_domains)
    row.update(metrics)

    status = (
        f"P@1={metrics['p_at_1']}  R@3={metrics['r_at_3']}  "
        f"MH@3={metrics['mh_at_3']}  composite={metrics['composite']}"
        if metrics["p_at_1"] is not None
        else f"(no must-haves)  top1={ranked_ids[0] if ranked_ids else 'none'}"
    )
    log.info("  %-30s run %d  %s", test_id, run_number, status)

    return row

def print_summary(rows: list[dict], variant: str) -> None:
    baseline_rows = [r for r in rows if r["run_number"] == 1 and not r["error"]]

    def avg(field: str) -> float | str:
        vals = [r[field] for r in baseline_rows if r[field] != "" and r[field] is not None]
        return round(sum(float(v) for v in vals) / len(vals), 3) if vals else "N/A"

    print(f"\n{'='*60}")
    print(f"  SUMMARY — variant: {variant} — {len(baseline_rows)} cases (run 1)")
    print(f"{'='*60}")
    print(f"P@1: {avg('p_at_1')}")
    print(f"R@3: {avg('r_at_3')}")
    print(f"R@5: {avg('r_at_5')}")
    print(f"MH@3 (mean): {avg('mh_at_3')}")
    print(f"Penalty@3: {avg('penalty_at_3')}")
    print(f"Composite: {avg('composite')}")

    multi_run = [r for r in rows if r["run_number"] > 1 and not r["error"]]
    if multi_run:
        from collections import defaultdict
        run1_top1: dict[str, str] = {
            r["test_id"]: r["rank_1"]
            for r in rows
            if r["run_number"] == 1 and not r["error"]
        }
        unstable = sum(
            1
            for r in multi_run
            if r["rank_1"] != run1_top1.get(r["test_id"])
        )
        total_multi = len(multi_run)
        print(f"\n  Non-determinism (rank_1 shifts):")
        print(f"  {unstable}/{total_multi} secondary runs differ from run-1 top result")
    print(f"{'='*60}\n")

def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI-DSS Phase H evaluation script"
    )
    parser.add_argument(
        "--api",
        default="http://localhost:8000/api",
        help="(ignored) kept for backward compatibility; engines run in-process",
    )
    parser.add_argument(
        "--tests",
        default=str(TEST_CASES_PATH),
        help="Path to test_cases.json",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=3,
        help="Number of runs per test case (for non-determinism measurement)",
    )
    parser.add_argument(
        "--variant",
        default="hybrid",
        choices=["hybrid", "classical",
                 "v_pain_heavy", "v_balanced", "v_semantic_only",
                 "v_i3_llm_semantic",
                 "v4_neutral_data",
                 "all"],
        help="Algorithm variant to test",
    )
    parser.add_argument(
        "--categories",
        default=None,
        help="Comma-separated category filter (e.g. edge,single_domain)",
    )
    parser.add_argument(
        "--output",
        default=str(RESULTS_DIR),
        help="Output directory for CSV files",
    )
    parser.add_argument(
        "--test-ids",
        default=None,
        help="Comma-separated test_ids to run (e.g. SC4-RE,SCA-001)",
    )
    args = parser.parse_args()

    tests_path = Path(args.tests)
    if not tests_path.exists():
        log.error("Test cases file not found: %s", tests_path)
        sys.exit(1)

    with tests_path.open() as f:
        data = json.load(f)

    all_cases: list[dict] = data["test_cases"]

    if args.categories:
        cats = {c.strip() for c in args.categories.split(",")}
        all_cases = [c for c in all_cases if c["category"] in cats]

    if args.test_ids:
        ids = {t.strip() for t in args.test_ids.split(",")}
        all_cases = [c for c in all_cases if c["test_id"] in ids]

    log.info("Loaded %d test cases", len(all_cases))

    if args.variant == "all":
        variants = ["classical", "hybrid", "v_i3_llm_semantic", "v4_neutral_data"]
        run_counts = {"classical": 1, "v4_neutral_data": 1}
    else:
        variants = [args.variant]
        run_counts = {}

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    ollama_live = _ping_ollama()
    log.info("Ollama: %s", "available" if ollama_live else "offline (classical fallback)")

    for variant in variants:
        n_runs = run_counts.get(variant, args.runs)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"eval_{variant}_{timestamp}.csv"

        try:
            engine, translator, repo = build_runner(variant)
        except Exception as exc:
            log.error("Could not build engine for variant '%s': %s", variant, exc)
            sys.exit(1)

        log.info(
            "Starting variant=%s (%s)  cases=%d  runs_per_case=%d  output=%s",
            variant, getattr(engine, "pipeline_label", "?"),
            len(all_cases), n_runs, output_path,
        )

        all_rows: list[dict] = []
        errors = 0

        for case in all_cases:
            log.info("Case: %s — %s", case["test_id"], case["profile_name"])
            for run_num in range(1, n_runs + 1):
                row = run_test_case(
                    engine, translator, repo, ollama_live, case, run_num, variant
                )
                all_rows.append(row)
                if row["error"]:
                    errors += 1

        with output_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()
            writer.writerows(all_rows)

        log.info("Wrote %d rows to %s  (errors: %d)", len(all_rows), output_path, errors)
        print_summary(all_rows, variant)

    log.info("Evaluation complete.")


if __name__ == "__main__":
    main()

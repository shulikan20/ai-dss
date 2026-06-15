from __future__ import annotations
import json
import os
from typing import TYPE_CHECKING
import numpy as np
import requests

from config import CFG
from src.matching.base import BaseMatchEngine
from src.models.company_profile import CompanyProfile
from src.models.recommendation import ClassicalResult, DimensionBreakdown

if TYPE_CHECKING:
    from src.matching.classical.classical_engine import ClassicalEngine

_DIMENSIONS: tuple[str, ...] = (
    "semantic_fit",
    "pain_point_match",
    "data_readiness",
    "tech_fit",
    "integration_compat",
)

_WEIGHTS: dict[str, float] = dict(CFG.TOPSIS_WEIGHTS)
_PREFILTER_K = 15
_TOP_N = 5
_MAX_LLM_SCORE = 10.0

def _ollama_generate_url() -> str:
    base = os.environ.get("OLLAMA_URL") or CFG.LLM_BASE_URL
    return base.rstrip("/") + "/api/generate"

_SYSTEM_PROMPT = """\
You are evaluating how relevant AI tools are for a specific company's situation.
Rate each tool's relevance to this company's bottleneck on a scale of 0-10.
10 = directly solves the stated problem. 0 = completely irrelevant.
Be precise — two similar tools should get different scores if one fits better.
Return ONLY a JSON object mapping capability_id to integer score. No explanation.
"""

def _recompute_topsis(matrix: np.ndarray, weights: np.ndarray) -> np.ndarray:
    if matrix.shape[0] == 0:
        return np.array([])

    if CFG.TOPSIS_FIXED_REFERENCE:
        weighted = matrix * weights
        ideal = weights
        d_pos = np.sqrt(((weighted - ideal) ** 2).sum(axis=1))
        d_neg = np.sqrt((weighted ** 2).sum(axis=1))
        denom = d_pos + d_neg
        return np.where(denom == 0.0, 0.0, d_neg / np.where(denom == 0.0, 1.0, denom))

    norms = np.sqrt((matrix ** 2).sum(axis=0))
    safe_norms = np.where(norms == 0.0, 1.0, norms)
    normed = matrix / safe_norms
    weighted = normed * weights
    positive_ideal = weighted.max(axis=0)
    negative_ideal = weighted.min(axis=0)
    d_pos = np.sqrt(((weighted - positive_ideal) ** 2).sum(axis=1))
    d_neg = np.sqrt(((weighted - negative_ideal) ** 2).sum(axis=1))
    denom = d_pos + d_neg
    return np.where(denom == 0.0, 0.5, d_neg / np.where(denom == 0.0, 1.0, denom))

class HybridEngineV2(BaseMatchEngine):
    def __init__(
        self,
        classical_engine: "ClassicalEngine",
        repo: object,
        timeout: int | None = None,
    ) -> None:
        self._classical = classical_engine
        self._repo = repo
        self._timeout = timeout or getattr(CFG, "LLM_TIMEOUT_SEC", 120)

    def name(self) -> str:
        return "i3_llm_semantic"

    @classmethod
    def build(
        cls,
        repo: object,
        classical_engine: "ClassicalEngine | None" = None,
    ) -> "HybridEngineV2":
        if classical_engine is None:
            from src.matching.classical.classical_engine import ClassicalEngine

            classical_engine = ClassicalEngine.build(repo=repo)
        return cls(classical_engine=classical_engine, repo=repo)

    def match(self, profile: CompanyProfile) -> list[ClassicalResult]:
        classical_results = self._classical.match(profile)
        if not classical_results:
            return []

        shortlist = classical_results[:_PREFILTER_K]
        cap_map = {c.capability_id: c for c in self._repo.get_capabilities()}
        prompt = self._build_prompt(profile, shortlist, cap_map)

        try:
            raw = self._call_llm(prompt)
            scores = self._parse_scores(raw, {r.capability_id for r in shortlist})
        except requests.RequestException:
            return classical_results[:_TOP_N]
        except Exception:  # noqa
            return classical_results[:_TOP_N]

        if not scores:
            return classical_results[:_TOP_N]

        return self._rerank_with_llm_semantic(shortlist, scores)

    def _rerank_with_llm_semantic(
        self,
        shortlist: list[ClassicalResult],
        scores: dict[str, float],
    ) -> list[ClassicalResult]:
        llm_semantic: list[float] = []
        rows: list[list[float]] = []
        for r in shortlist:
            if r.capability_id in scores:
                norm = scores[r.capability_id] / _MAX_LLM_SCORE
                norm = max(0.0, min(1.0, norm))
            else:
                norm = r.dimensions.semantic_fit
            llm_semantic.append(norm)
            rows.append(
                [
                    norm,
                    r.dimensions.pain_point_match,
                    r.dimensions.data_readiness,
                    r.dimensions.tech_fit,
                    r.dimensions.integration_compat,
                ]
            )

        matrix = np.array(rows, dtype=np.float64)
        weights = np.array([_WEIGHTS[d] for d in _DIMENSIONS], dtype=np.float64)
        topsis = _recompute_topsis(matrix, weights)

        order = sorted(range(len(shortlist)), key=lambda i: -topsis[i])

        out: list[ClassicalResult] = []
        for new_rank, i in enumerate(order[:_TOP_N], start=1):
            r = shortlist[i]
            out.append(
                ClassicalResult(
                    rank=new_rank,
                    capability_id=r.capability_id,
                    capability_name=r.capability_name,
                    domain=r.domain,
                    topsis_score=float(topsis[i]),
                    dimensions=DimensionBreakdown(
                        semantic_fit=llm_semantic[i],  # now the LLM relevance score
                        integration_compat=r.dimensions.integration_compat,
                        data_readiness=r.dimensions.data_readiness,
                        tech_fit=r.dimensions.tech_fit,
                        pain_point_match=r.dimensions.pain_point_match,
                    ),
                    explanation=r.explanation,
                    impl_complexity=r.impl_complexity,
                )
            )
        return out

    def _build_prompt(
        self,
        profile: CompanyProfile,
        shortlist: list[ClassicalResult],
        cap_map: dict,
    ) -> str:
        team_size = getattr(profile, "team_size", None)
        company_bits = [profile.company_name or profile.company_id]
        if team_size:
            company_bits.append(f"{team_size} people")
        if profile.country:
            company_bits.append(profile.country)
        company_line = "Company: " + ", ".join(company_bits)

        domains = ", ".join(profile.active_domains) if profile.active_domains else "unspecified"

        confirmed_pain_labels = [
            k.split(".")[-1] for k, v in profile.pain_point_flags.items() if v
        ]
        pains = ", ".join(confirmed_pain_labels) if confirmed_pain_labels else "none stated"

        bottleneck = profile.bottleneck_description or "(no bottleneck text provided)"

        tool_lines = []
        for r in shortlist:
            cap = cap_map.get(r.capability_id)
            cap_name = cap.name if cap is not None else r.capability_name
            cap_desc = cap.description if cap is not None else ""
            tool_lines.append(f"- {r.capability_id}: {cap_name} — {cap_desc}")

        user_prompt = (
            f"{company_line}\n"
            f"Domains: {domains}\n"
            f"Pain points: {pains}\n"
            f'Bottleneck: "{bottleneck}"\n\n'
            f"Rate each tool's relevance (0-10):\n"
            + "\n".join(tool_lines)
            + '\n\nReturn JSON only: {"capability_id": score, ...}'
        )
        return f"{_SYSTEM_PROMPT}\n\n{user_prompt}"

    def _call_llm(self, prompt: str) -> str:
        resp = requests.post(
            _ollama_generate_url(),
            json={
                "model": CFG.LLM_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1},
            },
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json()["response"].strip()

    @staticmethod
    def _parse_scores(response: str, valid_ids: set[str]) -> dict[str, float] | None:
        clean = response.strip()
        if "```" in clean:
            clean = "\n".join(
                ln for ln in clean.split("\n") if not ln.strip().startswith("```")
            ).strip()

        start = clean.find("{")
        end = clean.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None

        try:
            parsed = json.loads(clean[start : end + 1])
        except json.JSONDecodeError:
            return None
        if not isinstance(parsed, dict):
            return None

        out: dict[str, float] = {}
        for cap_id, score in parsed.items():
            if cap_id not in valid_ids:
                continue
            try:
                out[cap_id] = float(score)
            except (TypeError, ValueError):
                continue
        return out or None

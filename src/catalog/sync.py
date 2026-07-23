from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import numpy as np
from sqlalchemy import text

from config import CFG

SQLITE_PATH = CFG.CATALOG_DB
EMB_PATH = CFG.EMBEDDINGS_PATH
IDX_PATH = EMB_PATH.parent / (EMB_PATH.stem + "_index.json")

CAP_COLS = [
    "capability_id", "name", "domain", "use_case_category", "task_type_target",
    "description", "bottleneck_keywords", "required_data_types",
    "works_without_data", "min_history_months_gate", "min_technical_capability",
    "primary_outcome", "secondary_outcomes", "time_to_value_weeks_min",
    "time_to_value_weeks_max", "mapped_pain_points",
]
PROD_COLS = [
    "product_id", "capability_id", "name", "vendor", "url", "integrations",
    "gdpr_compliant", "deployment_model", "pricing_model", "has_free_tier",
    "cost_tier", "cost_notes", "implementation_effort",
    "min_technical_capability", "setup_notes", "min_history_months",
    "min_record_count", "works_with_limited_data", "data_requirement_notes",
    "notes",
]
_JSON_COLS = {
    "bottleneck_keywords", "required_data_types", "secondary_outcomes",
    "mapped_pain_points", "integrations",
}
_BOOL_COLS = {
    "works_without_data", "gdpr_compliant", "has_free_tier",
    "works_with_limited_data",
}
_SQLITE_REQUIRED = {
    "use_case_category": "", "task_type_target": "", "description": "",
    "integrations": "[]", "deployment_model": "", "pricing_model": "",
    "cost_tier": "", "implementation_effort": "",
}

def _to_sqlite_value(col: str, value):
    if value is None:
        return _SQLITE_REQUIRED.get(col)
    if col in _JSON_COLS:
        return json.dumps(value) if not isinstance(value, str) else value
    if col in _BOOL_COLS:
        return 1 if value else 0
    return value


def sync_sqlite(session, sqlite_path: Path | None = None) -> tuple[int, int]:
    path = sqlite_path or SQLITE_PATH
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist; run build_catalog.py first")

    caps = [dict(r) for r in session.execute(
        text(f"SELECT {', '.join(CAP_COLS)} FROM capabilities")).mappings()]
    prods = [dict(r) for r in session.execute(
        text(f"SELECT {', '.join(PROD_COLS)} FROM products")).mappings()]

    con = sqlite3.connect(path)
    try:
        for table, cols, rows in (
            ("capabilities", CAP_COLS, caps),
            ("products", PROD_COLS, prods),
        ):
            placeholders = ", ".join("?" for _ in cols)
            sql = (
                f"INSERT OR REPLACE INTO {table} ({', '.join(cols)}) "
                f"VALUES ({placeholders})"
            )
            con.executemany(
                sql,
                [tuple(_to_sqlite_value(c, r.get(c)) for c in cols) for r in rows],
            )
        con.commit()
    finally:
        con.close()
    return len(caps), len(prods)


def delete_from_sqlite(capability_id: str, sqlite_path: Path | None = None) -> None:
    path = sqlite_path or SQLITE_PATH
    if not path.exists():
        return
    con = sqlite3.connect(path)
    try:
        con.execute("DELETE FROM products WHERE capability_id = ?", (capability_id,))
        con.execute("DELETE FROM capabilities WHERE capability_id = ?", (capability_id,))
        con.commit()
    finally:
        con.close()


def delete_product_from_sqlite(product_id: str, sqlite_path: Path | None = None) -> None:
    path = sqlite_path or SQLITE_PATH
    if not path.exists():
        return
    con = sqlite3.connect(path)
    try:
        con.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
        con.commit()
    finally:
        con.close()


def reindex(repo, embeddings_path: Path | None = None) -> int:
    from src.catalog.embedder import CatalogEmbedder

    embedder = CatalogEmbedder(repository=repo, embeddings_path=embeddings_path)
    embeddings = embedder.compute_embeddings()
    return int(embeddings.shape[0])


def embedding_text_changed(before: dict | None, after: dict) -> bool:
    if before is None:
        return True
    return (
        (before.get("description") or "") != (after.get("description") or "")
        or (before.get("bottleneck_keywords") or []) != (after.get("bottleneck_keywords") or [])
    )


def invalidate_engine_cache(app_state) -> None:
    engines = []
    if getattr(app_state, "classical_engine", None) is not None:
        engines.append(app_state.classical_engine)
    for engine in (getattr(app_state, "engines", None) or {}).values():
        engines.append(engine)
        inner = getattr(engine, "_classical", None)
        if inner is not None:
            engines.append(inner)

    for engine in engines:
        if hasattr(engine, "_embeddings"):
            engine._embeddings = None
        if hasattr(engine, "_emb_index"):
            engine._emb_index = None


def apply_write(
    session,
    repo,
    *,
    reembed: bool = True,
    app_state=None,
) -> dict:
    result: dict = {"reembedded": False, "vectors": None}

    caps, prods = sync_sqlite(session)
    result["sqlite_capabilities"] = caps
    result["sqlite_products"] = prods

    if reembed:
        result["vectors"] = reindex(repo)
        result["reembedded"] = True
        if app_state is not None:
            invalidate_engine_cache(app_state)

    return result


def consistency_report(session) -> dict:
    pg = {r[0] for r in session.execute(text("SELECT capability_id FROM capabilities"))}

    lite: set[str] = set()
    if SQLITE_PATH.exists():
        con = sqlite3.connect(SQLITE_PATH)
        try:
            lite = {r[0] for r in con.execute("SELECT capability_id FROM capabilities")}
        finally:
            con.close()

    emb: set[str] = set()
    emb_rows = 0
    if IDX_PATH.exists() and EMB_PATH.exists():
        emb = set(json.loads(IDX_PATH.read_text()).values())
        emb_rows = int(np.load(str(EMB_PATH)).shape[0])

    unrecommendable = sorted(pg - emb)
    return {
        "postgres": len(pg),
        "sqlite": len(lite),
        "embedded": len(emb),
        "vectors": emb_rows,
        "unrecommendable": unrecommendable,
        "stale_vectors": sorted(emb - pg),
        "only_in_postgres": sorted(pg - lite),
        "only_in_sqlite": sorted(lite - pg),
        "index_corrupt": emb_rows != len(emb),
        "healthy": not unrecommendable and emb_rows == len(emb),
    }

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from config import CFG
from src.models.catalog_item import Capability, Product

class CatalogRepository:
    def __init__(self, db_path: Path | str | None = None):
        self._path = Path(db_path) if db_path else CFG.CATALOG_DB
        self._conn: sqlite3.Connection | None = None

    def _conn_get(self) -> sqlite3.Connection:
        if self._conn is None:
            if not self._path.exists():
                raise FileNotFoundError(
                    f"catalog.db not found at {self._path}. "
                    "Run build_catalog.py first."
                )
            self._conn = sqlite3.connect(str(self._path))
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> CatalogRepository:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def get_capabilities(self, domain: str | None = None) -> list[Capability]:
        conn = self._conn_get()

        if domain:
            cap_rows = conn.execute(
                "SELECT * FROM capabilities WHERE domain=? ORDER BY capability_id",
                (domain,),
            ).fetchall()
        else:
            cap_rows = conn.execute(
                "SELECT * FROM capabilities ORDER BY domain, capability_id"
            ).fetchall()

        if not cap_rows:
            return []

        capabilities = [Capability.from_db_row(dict(r)) for r in cap_rows]
        cap_ids = [c.capability_id for c in capabilities]
        placeholders = ",".join("?" * len(cap_ids))
        prod_rows = conn.execute(
            f"SELECT capability_id, integrations FROM products "
            f"WHERE capability_id IN ({placeholders})",
            cap_ids,
        ).fetchall()

        integrations_map: dict[str, set[str]] = {
            cid: set() for cid in cap_ids
        }
        for row in prod_rows:
            cid = row["capability_id"]
            try:
                ints = json.loads(row["integrations"] or "[]")
                integrations_map[cid].update(str(i).lower() for i in ints)
            except (json.JSONDecodeError, TypeError):
                pass

        for cap in capabilities:
            cap.available_integrations = sorted(integrations_map[cap.capability_id])

        return capabilities

    def get_products(self, capability_id: str) -> list[Product]:
        rows = self._conn_get().execute(
            "SELECT * FROM products WHERE capability_id=? ORDER BY product_id",
            (capability_id,),
        ).fetchall()
        return [Product.from_db_row(dict(r)) for r in rows]

    def get_mapped_pain_points(self, capability_id: str) -> list[str]:
        row = self._conn_get().execute(
            "SELECT mapped_pain_points FROM capabilities WHERE capability_id=?",
            (capability_id,),
        ).fetchone()
        if not row:
            return []
        try:
            return json.loads(row["mapped_pain_points"] or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    def get_capability_ids_with_products(self) -> set[str]:
        rows = self._conn_get().execute(
            "SELECT DISTINCT capability_id FROM products"
        ).fetchall()
        return {row["capability_id"] for row in rows}

    def get_gdpr_capable_capability_ids(self) -> set[str]:
        rows = self._conn_get().execute(
            "SELECT DISTINCT capability_id FROM products WHERE gdpr_compliant=1"
        ).fetchall()
        return {row["capability_id"] for row in rows}

    def has_gdpr_product(self, capability_id: str) -> bool:
        row = self._conn_get().execute(
            "SELECT COUNT(*) FROM products WHERE capability_id=? AND gdpr_compliant=1",
            (capability_id,),
        ).fetchone()
        return row[0] > 0

    def get_all_domains(self) -> list[str]:
        rows = self._conn_get().execute(
            "SELECT DISTINCT domain FROM capabilities ORDER BY domain"
        ).fetchall()
        return [r["domain"] for r in rows]

    def capability_count(self) -> int:
        return self._conn_get().execute(
            "SELECT COUNT(*) FROM capabilities"
        ).fetchone()[0]

    def product_count(self) -> int:
        return self._conn_get().execute(
            "SELECT COUNT(*) FROM products"
        ).fetchone()[0]
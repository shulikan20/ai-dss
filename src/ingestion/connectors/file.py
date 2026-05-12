from __future__ import annotations
import csv
import json
from pathlib import Path
from config import CFG
from src.ingestion.connectors.base import DataConnector

class FileConnector(DataConnector):
    def __init__(self, exports_dir: Path | str | None = None):
        self._dir = Path(exports_dir) if exports_dir else CFG.EXPORTS_DIR

    def available(self) -> bool:
        return self._dir.is_dir()

    def fetch(self, company_id: str, export_type: str | None = None) -> dict:
        prefix = company_id.lower()
        pattern = f"{prefix}*{export_type}*" if export_type else f"{prefix}*"
        candidates = sorted(self._dir.glob(pattern))

        csv_files = [f for f in candidates if f.suffix == ".csv"]
        json_files = [f for f in candidates if f.suffix == ".json"]

        if csv_files:
            return self._read_csv(csv_files[0])
        if json_files:
            return self._read_json(json_files[0])

        detail = f"'{export_type}' export" if export_type else "any export"
        raise FileNotFoundError(
            f"No {detail} file found for '{company_id}' in {self._dir}. "
            f"Expected a file matching '{pattern}'."
        )

    def _read_csv(self, path: Path) -> dict:
        with path.open(encoding="utf-8", newline="") as f:
            orders = list(csv.DictReader(f))
        return {
            "orders": orders,
            "source_file": path.name,
            "total_records": len(orders),
        }

    def _read_json(self, path: Path) -> dict:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            orders = data
        elif isinstance(data, dict):
            orders = data.get("orders", [])
        else:
            orders = []

        return {
            "orders": orders,
            "source_file": path.name,
            "total_records": len(orders),
        }
from __future__ import annotations
import json
from datetime import date
from pathlib import Path
from typing import Any

from config import CFG
from src.models.company_profile import CompanyProfile
from src.ingestion.connectors.base import DataConnector
from src.ingestion.normalizers.export_type import ExportType, NormalizerRegistry
from src.ingestion.normalizers.unstructured import UnstructuredHandler

class ProfileBuilder:

    def __init__(self, connector: DataConnector, schema_path: Path | None = None):
        self.connector = connector
        self.schema_path = schema_path or CFG.SCHEMA_PATH
        self._unstructured = UnstructuredHandler()

    def build(self, questionnaire_path: Path | str) -> CompanyProfile:
        path = Path(questionnaire_path)
        with path.open(encoding="utf-8") as f:
            raw: dict[str, Any] = json.load(f)

        company_id = str((raw.get("meta") or {}).get("company_id") or path.stem)
        if self.connector.available():
            raw = self._apply_exports(raw, company_id)

        return CompanyProfile._parse(raw)

    def _apply_exports(self, raw: dict, company_id: str) -> dict:
        declared = (
            raw.get("universal", {})
               .get("data_availability", {})
               .get("export_types_available", [])
        )
        if not declared:
            return raw
        merged_fields: dict[str, Any] = {}
        source_files: list[str] = []
        extra_notes: list[str] = []

        for type_str in declared:
            export_type = ExportType.from_string(type_str)

            if export_type == ExportType.UNSTRUCTURED:
                text = self._handle_unstructured(company_id, type_str)
                if text:
                    extra_notes.append(text)
                continue

            normalizer = NormalizerRegistry.get(export_type or type_str)
            if normalizer is None:
                continue

            try:
                export_raw = self.connector.fetch(company_id, type_str)
                source_files.append(export_raw.get("source_file", "unknown"))
            except FileNotFoundError:
                continue
            except Exception:
                continue

            try:
                e_fields = normalizer.normalize(export_raw)
                merged_fields.update(e_fields)
            except NotImplementedError:
                continue
            except Exception:
                continue

        if merged_fields:
            raw["export_computed"] = {
                "computed_from": source_files,
                "computed_at": date.today().isoformat(),
                "extractor_used": "normalizer_script",
                "fields": merged_fields,
            }

        if extra_notes:
            existing = (raw.get("unstructured_supplements") or [])
            if isinstance(existing, list):
                for note in extra_notes:
                    existing.append({"content_summary": note, "source": "export_file"})
                raw["unstructured_supplements"] = existing

        return raw

    def _handle_unstructured(self, company_id: str, type_str: str) -> str:
        try:
            export_raw = self.connector.fetch(company_id, type_str)
            return self._unstructured.extract_text(export_raw)
        except FileNotFoundError:
            return ""
        except Exception:
            return ""
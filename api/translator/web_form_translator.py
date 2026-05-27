from __future__ import annotations
import dataclasses
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.catalog.repository import CatalogRepository
from src.models.company_profile import CompanyProfile

from api.models import QuestionnaireRequest
from api.translator.bottleneck_analyser import BottleneckAnalyser
from api.translator.question_schema import (
    QUESTION_SCHEMA,
    get_all_catalog_pain_flags,
)

class WebFormTranslator:
    _catalog_audit_done: bool = False

    def __init__(self, analyser: BottleneckAnalyser | None = None) -> None:
        self._analyser = analyser or BottleneckAnalyser()

    def translate(
        self,
        form_data: QuestionnaireRequest,
        repo: CatalogRepository,
        export_summary: str | None = None,
        enrich_with_llm: bool = False,
    ) -> CompanyProfile:
        confirmed_flags = self._map_structured_answers(form_data.answers)
        for flag_path in getattr(form_data, "confirmed_pain_flags", []):
            confirmed_flags[flag_path] = True
        profile_extras = self._extract_profile_field_answers(form_data.answers)
        bottleneck_text = form_data.bottleneck_text.strip()
        if export_summary:
            bottleneck_text = f"{bottleneck_text}\n\nData analysis: {export_summary.strip()}"
        catalog_paths = self._get_catalog_paths(repo)
        if enrich_with_llm:
            prelim_profile = self._build_profile(
                form_data=form_data,
                pain_flags=confirmed_flags,
                profile_extras=profile_extras,
                bottleneck_text=bottleneck_text,
            )
            inferred_flags = self._analyser.analyse(prelim_profile, catalog_paths)
        else:
            inferred_flags = {}

        merged_flags = {**inferred_flags, **confirmed_flags}
        self._maybe_audit(get_all_catalog_pain_flags(), catalog_paths)

        return self._build_profile(
            form_data=form_data,
            pain_flags=merged_flags,
            profile_extras=profile_extras,
            bottleneck_text=bottleneck_text,
        )

    def _map_structured_answers(self, answers: dict[str, str]) -> dict[str, bool]:
        confirmed: dict[str, bool] = {}
        schema_questions: dict = QUESTION_SCHEMA.get("questions", {})

        for domain_questions in schema_questions.values():
            for question in domain_questions:
                qid = question["id"]
                if qid not in answers:
                    continue
                selected_value = answers[qid]
                for option in question.get("options", []):
                    if option["value"] == selected_value:
                        for flag in option.get("pain_flags", []):
                            confirmed[flag] = True
                        break

        return confirmed

    def _extract_profile_field_answers(self, answers: dict[str, str]) -> dict:
        extras: dict = {
            "technical_level": 2,
            "current_tools": [],
            "export_types_available": [],
        }

        for question in QUESTION_SCHEMA.get("full_tier_extras", []):
            qid = question.get("id", "")
            maps_to = question.get("maps_to", "")
            q_type = question.get("type", "")

            if qid not in answers or not maps_to:
                continue

            raw = answers[qid].strip()

            if maps_to in ("tech_sophistication", "technical_level"):
                try:
                    extras["technical_level"] = int(raw)
                except ValueError:
                    pass
            elif maps_to == "has_structured_export":
                extras["has_structured_export"] = raw in ("yes_clean", "yes_messy")
            elif maps_to == "history_months":
                try:
                    extras["history_months"] = int(raw)
                except ValueError:
                    pass
            elif q_type == "multi_select":
                selected = [v.strip() for v in raw.split(",") if v.strip()]
                if maps_to in ("integrations", "current_tools"):
                    extras["current_tools"] = selected
                elif maps_to == "export_types_available":
                    extras["export_types_available"] = [
                        s for s in selected if s != "none"
                    ]

        return extras
    
    def _build_profile(
        self,
        form_data: QuestionnaireRequest,
        pain_flags: dict[str, bool],
        profile_extras: dict,
        bottleneck_text: str,
    ) -> CompanyProfile:
        export_types = profile_extras.get("export_types_available", [])
        field_values: dict = {
            "company_id": f"WEB-{uuid.uuid4().hex[:8].upper()}",
            "company_name": form_data.company_name,
            "country": form_data.country,
            "pain_point_flags": dict(pain_flags),
            "active_domains": list(form_data.domains),
            "bottleneck_description": bottleneck_text,
            "technical_level": profile_extras.get("technical_level", 2),
            "current_tools": profile_extras.get("current_tools", []),
            "export_types_available": export_types,
            "has_structured_export": len(export_types) > 0,
            "has_communication_logs": "support_tickets" in export_types,
        }

        profile_field_names = {f.name for f in dataclasses.fields(CompanyProfile)}
        kwargs: dict = {
            k: v for k, v in field_values.items() if k in profile_field_names
        }

        for f in dataclasses.fields(CompanyProfile):
            if f.name in kwargs:
                continue
            is_required = (
                f.default is dataclasses.MISSING
                and f.default_factory is dataclasses.MISSING  # type: ignore[misc]
            )
            if is_required:
                kwargs[f.name] = []

        return CompanyProfile(**kwargs)

    @staticmethod
    def _get_catalog_paths(repo: CatalogRepository) -> set[str]:
        paths: set[str] = set()
        for cap in repo.get_capabilities():
            paths.update(repo.get_mapped_pain_points(cap.capability_id))
        return paths

    @classmethod
    def _maybe_audit(cls, schema_paths: set[str], catalog_paths: set[str]) -> None:
        if cls._catalog_audit_done:
            return
        cls._catalog_audit_done = True
        cls._audit_pain_flag_paths(schema_paths, catalog_paths)

    @staticmethod
    def _audit_pain_flag_paths(
        schema_paths: set[str], catalog_paths: set[str]
    ) -> None:
        missing = schema_paths - catalog_paths
        if not missing:
            return
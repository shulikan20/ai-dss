from __future__ import annotations

import json
import re
import warnings
from pathlib import Path
from typing import TYPE_CHECKING
import requests

from config import CFG
from src.models.catalog_item import Capability
from src.models.company_profile import CompanyProfile
from src.models.recommendation import LLMRankedItem, LLMResult

SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "system_prompt.txt"
OLLAMA_CHAT_URL = "http://127.0.0.1:11434/api/chat"
USER_TEMPLATE = """Here is the company profile:

{profile}

Here are the candidate AI tools to evaluate:

{tools}

Think through which tools best fit this company's situation, then provide your recommendations in the JSON format."""


class OllamaExtractor:
    def __init__(self, model: str | None = None, timeout: int = 180):
        self._model = model or CFG.LLM_MODEL
        self._timeout = timeout
        self._system_prompt: str | None = None

    def format_profile(self, profile: CompanyProfile) -> str:
        lines = [
            f"Company: {profile.company_name} ({profile.country})",
            f"Business domains: {', '.join(profile.active_domains)}",
            "",
            "MAIN BOTTLENECKS (what is slowing this company down):",
        ]
        for part in profile.bottleneck_description.split(" | "):
            if part.strip():
                lines.append(f"  - {part.strip()}")

        if profile.confirmed_pain_points:
            lines.append("")
            lines.append("Confirmed pain points:")
            for pain in sorted(profile.confirmed_pain_points):
                label = pain.split(".")[-1].replace("pain_", "").replace("_", " ")
                lines.append(f"  - {label}")

        if profile.current_tools:
            lines.append("")
            lines.append(f"Current tools: {', '.join(profile.current_tools)}")

        lines.append("")
        lines.append(
            f"Data available: {profile.order_count} orders, "
            f"{profile.history_months} months of history, "
            f"exports: {profile.export_types_available or 'none'}"
        )

        if profile.open_notes and profile.open_notes.strip():
            lines.append("")
            lines.append(f"Additional context: {profile.open_notes[:400]}")

        return "\n".join(lines)

    def format_tools(self, capabilities: list[Capability]) -> str:
        lines = []
        for i, cap in enumerate(capabilities, 1):
            lines.append(f"{i}. [{cap.capability_id}] {cap.name}")
            lines.append(f"   {cap.description[:220]}")
            if cap.mapped_pain_points:
                labels = [
                    p.split(".")[-1].replace("pain_", "").replace("_", " ")
                    for p in cap.mapped_pain_points[:3]
                ]
                lines.append(f"   Addresses: {', '.join(labels)}")
            lines.append("")
        return "\n".join(lines)

    def _get_system_prompt(self) -> str:
        if self._system_prompt is None:
            self._system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
        return self._system_prompt

    def _call_ollama(self, profile_text: str, tools_text: str) -> str:
        user_msg = USER_TEMPLATE.format(profile=profile_text, tools=tools_text)
        response = requests.post(
            OLLAMA_CHAT_URL,
            json={
                "model":   self._model,
                "messages": [
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user",   "content": user_msg},
                ],
                "stream":  False,
                "options": {
                    "temperature": 0.1,
                    "num_ctx":     4096,
                },
            },
            timeout=self._timeout,
        )
        response.raise_for_status()
        return response.json().get("message", {}).get("content", "")

    @staticmethod
    def _extract_json_block(raw: str) -> dict | None:
        for pattern in [
            r"```json\s*(.*?)\s*```",
            r"```\s*(\{.*?\})\s*```",
        ]:
            m = re.search(pattern, raw, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(1))
                except json.JSONDecodeError:
                    pass

        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass

        return None

    @staticmethod
    def _extract_cot_reasoning(raw: str) -> str:
        fence = re.search(r"```", raw)
        if fence:
            return raw[:fence.start()].strip()
        brace = raw.find("{")
        if brace > 0:
            return raw[:brace].strip()
        return ""

    @staticmethod
    def _clean_id(raw_id: str) -> str:
        return raw_id.strip().strip("[]")

    def _parse_response(
        self,
        raw: str,
        cap_map: dict[str, Capability],
    ) -> list[LLMRankedItem]:
        data = self._extract_json_block(raw)
        if data is None:
            warnings.warn(
                f"OllamaExtractor: no JSON block found in response. "
                f"Raw response starts with: {raw[:200]!r}",
                RuntimeWarning,
                stacklevel=3,
            )
            return []

        items: list[LLMRankedItem] = []
        seen_ids: set[str] = set()

        for rec in data.get("recommendations", []):
            raw_id = rec.get("capability_id", "")
            cap_id = self._clean_id(raw_id)

            if not cap_id:
                continue
            if cap_id in seen_ids:
                continue
            if cap_id not in cap_map:
                warnings.warn(
                    f"OllamaExtractor: hallucinated capability_id '{cap_id}' "
                    f"(not in scoped list) — dropping.",
                    RuntimeWarning,
                    stacklevel=3,
                )
                continue

            cap = cap_map[cap_id]
            items.append(LLMRankedItem(
                rank=len(items) + 1,
                capability_id=cap_id,
                capability_name=cap.name,
                domain=cap.domain,
                explanation=rec.get("explanation", "").strip(),
            ))
            seen_ids.add(cap_id)

        return items

    def extract(
        self,
        profile: CompanyProfile,
        capabilities: list[Capability],
    ) -> LLMResult:
        cap_map = {cap.capability_id: cap for cap in capabilities}
        profile_text = self.format_profile(profile)
        tools_text = self.format_tools(capabilities)
        raw = self._call_ollama(profile_text, tools_text)
        cot = self._extract_cot_reasoning(raw)
        items = self._parse_response(raw, cap_map)

        return LLMResult(
            ranked_items=items,
            cot_reasoning=cot,
            model_used=self._model,
        )
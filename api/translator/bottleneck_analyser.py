from __future__ import annotations
import json
import sys
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from config import CFG
from src.models.company_profile import CompanyProfile

_SYSTEM_PROMPT = """\
You are a business process analyst. Your task is to identify operational
pain points that are CLEARLY IMPLIED by a company's bottleneck description,
even if the company did not state them explicitly.

You will receive:
  1. A company profile (JSON)
  2. A list of pain point identifiers used by a recommendation system

Return ONLY a JSON array of identifiers that are clearly implied by the
bottleneck description. Omit any identifier you are not confident about.
Do not invent identifiers — only return from the provided list.

Example output:
["supply_chain.inventory.pain_stockouts", "universal.processes.pain_manual_data_entry"]
"""

class BottleneckAnalyser:
    def __init__(
        self,
        model: str | None = None,
        timeout_s: int = 180,
        ollama_url: str | None = None,
    ) -> None:
        self._model = model or CFG.LLM_MODEL
        self._timeout = timeout_s
        self._ollama_generate_url = (
            f"{ollama_url or 'http://localhost:11434'}/api/generate"
        )

    def analyse(
        self,
        profile: CompanyProfile,
        valid_catalog_paths: set[str],
    ) -> dict[str, bool]:
        already_confirmed = {k for k, v in profile.pain_point_flags.items() if v}
        to_evaluate = sorted(valid_catalog_paths - already_confirmed)

        if not to_evaluate:
            return {}

        prompt = self._build_prompt(profile, to_evaluate)

        try:
            raw_response = self._call_ollama(prompt)
        except requests.exceptions.ConnectionError:
            return {}
        except requests.exceptions.Timeout:
            return {}
        except Exception as exc:
            return {}

        inferred = self._parse_response(raw_response)
        valid = {path: True for path in inferred if path in valid_catalog_paths}

        return valid

    def _build_prompt(self, profile: CompanyProfile, to_evaluate: list[str]) -> str:
        profile_context = self._serialise_profile(profile)
        flags_json = json.dumps(to_evaluate, indent=2)

        return (
            f"{_SYSTEM_PROMPT}\n\n"
            f"COMPANY PROFILE:\n{profile_context}\n\n"
            f"PAIN POINT IDENTIFIERS TO EVALUATE (not yet confirmed in questionnaire):\n"
            f"{flags_json}\n\n"
            f"Which are CLEARLY implied by the bottleneck description? "
            f"Return ONLY a JSON array of identifiers."
        )

    @staticmethod
    def _serialise_profile(profile: CompanyProfile) -> str:
        parts = [
            f"Company: {getattr(profile, 'company_name', 'Unknown')}",
            f"Country: {getattr(profile, 'country', 'Unknown')}",
            f"Domains: {', '.join(getattr(profile, 'domains', []))}",
        ]

        processes = getattr(profile, "processes", []) or []
        bottleneck_parts = []
        for proc in processes:
            for attr in ("bottleneck_description", "description", "bottleneck"):
                desc = getattr(proc, attr, None)
                if desc and isinstance(desc, str) and len(desc) > 5:
                    bottleneck_parts.append(desc)
                    break
        if bottleneck_parts:
            parts.append(f"Bottleneck: {' | '.join(bottleneck_parts)}")

        confirmed = [k for k, v in profile.pain_point_flags.items() if v]
        if confirmed:
            parts.append(f"Already confirmed: {', '.join(confirmed[:8])}")

        return "\n".join(parts)

    def _call_ollama(self, prompt: str) -> str:
        resp = requests.post(
            self._ollama_generate_url,
            json={
                "model": self._model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1},
            },
            timeout=(3, self._timeout),
        )
        resp.raise_for_status()
        return resp.json()["response"].strip()

    @staticmethod
    def _parse_response(response: str) -> list[str]:
        clean = response.strip()
        if "```" in clean:
            lines = [l for l in clean.splitlines() if not l.strip().startswith("```")]
            clean = "\n".join(lines).strip()

        start = clean.find("[")
        end = clean.rfind("]")
        if start == -1 or end <= start:
            return []

        try:
            parsed = json.loads(clean[start : end + 1])
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
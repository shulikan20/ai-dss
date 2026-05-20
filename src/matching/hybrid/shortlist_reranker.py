from __future__ import annotations
import json
import time
import requests

from config import CFG
from src.models.company_profile import CompanyProfile
from src.models.recommendation import ClassicalResult

OLLAMA_URL = "http://localhost:11434/api/generate"

_SYSTEM_PROMPT = """\
You are a business technology consultant reviewing AI tool recommendations
for a small e-commerce or service business.

Our structured scoring system (TOPSIS) has pre-filtered and scored the most
relevant tools. You will see each tool's name, TOPSIS score, and dimension
breakdown. Your task is to re-rank this shortlist based on which tools BEST
address the company's PRIMARY stated bottleneck.

Use the TOPSIS scores as grounding evidence — they reflect structured signals
about data readiness, technical fit, and explicit pain point matches. Override
the TOPSIS ranking only where the bottleneck language clearly indicates a
different priority.

Return ONLY a JSON array of capability_ids in your preferred order (best first).
You MUST include all provided capability_ids.

Example output:
["capability_id_1", "capability_id_2", "capability_id_3", "capability_id_4"]
"""

class ShortlistReranker:
    def __init__(self, model: str | None = None, top_k: int = 8, timeout: int = 180):
        self._model = model or CFG.LLM_MODEL
        self._top_k = top_k
        self._timeout = timeout

    def rerank(
        self,
        profile: CompanyProfile,
        shortlist: list[ClassicalResult],
    ) -> list[str]:
        if not shortlist:
            return []

        prompt = self._build_prompt(profile, shortlist)
        response = self._call_llm(prompt)
        reranked = self._parse_response(response, shortlist)
        return reranked
    
    def _build_prompt(
        self, profile: CompanyProfile, shortlist: list[ClassicalResult]
    ) -> str:
        profile_lines = [
            f"Company   : {profile.company_name}",
            f"Country   : {getattr(profile, 'country', 'unknown')}",
        ]
        domains = getattr(profile, "domains", None) or getattr(profile, "active_domains", None)
        if domains:
            profile_lines.append(f"Domains   : {', '.join(domains)}")

        confirmed_pains = [
            k.split(".")[-1]
            for k, v in profile.pain_point_flags.items()
            if v
        ]
        if confirmed_pains:
            profile_lines.append(f"Pain flags: {', '.join(confirmed_pains[:8])}")

        processes_text = self._extract_processes_text(profile)
        if processes_text:
            profile_lines.append(f"Bottleneck: {processes_text}")

        tool_lines: list[str] = []
        for i, r in enumerate(shortlist, 1):
            tool_lines.append(
                f"\n[{i}] {r.capability_id}"
                f"\n Name: {r.capability_name}"
                f"\n TOPSIS score: {r.topsis_score:.3f}"
                f"\n semantic_fit: {r.dimensions.semantic_fit:.3f}  "
                f"(SBERT similarity to bottleneck)"
                f"\n pain_point_match: {r.dimensions.pain_point_match:.3f}  "
                f"(confirmed questionnaire flags)"
                f"\n data_readiness: {r.dimensions.data_readiness:.3f}"
                f"\n tech_fit: {r.dimensions.tech_fit:.3f}"
                f"\n integration_compat: {r.dimensions.integration_compat:.3f}"
                f"\n Explanation: {r.explanation[:150].replace(chr(10), ' ')}"
            )

        capability_ids = json.dumps([r.capability_id for r in shortlist])

        return (
            f"{_SYSTEM_PROMPT}\n\n"
            f"COMPANY PROFILE:\n"
            + "\n".join(profile_lines)
            + f"\n\nTOPSIS SHORTLIST (top {len(shortlist)} from structured scoring):"
            + "".join(tool_lines)
            + f"\n\nRe-rank these {len(shortlist)} tools. Return ONLY a JSON array "
            f"containing all these capability_ids in your preferred order:\n"
            f"{capability_ids}"
        )

    def _extract_processes_text(self, profile: CompanyProfile) -> str:
        parts: list[str] = []
        processes = getattr(profile, "processes", None)
        if isinstance(processes, list):
            for proc in processes:
                for attr in ("bottleneck_description", "description", "bottleneck"):
                    desc = getattr(proc, attr, None)
                    if desc and isinstance(desc, str) and len(desc) > 10:
                        parts.append(desc[:200])
                        break

        if not parts:
            bd = getattr(profile, "bottleneck_description", None) or \
                 getattr(profile, "bottleneck_summary", None)
            if bd and isinstance(bd, str):
                parts.append(bd[:300])

        if not parts and isinstance(processes, list):
            for proc in processes:
                if isinstance(proc, dict):
                    desc = proc.get("bottleneck_description") or proc.get("description")
                    if desc:
                        parts.append(str(desc)[:200])

        return " | ".join(parts) if parts else ""

    def _call_llm(self, prompt: str) -> str:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": self._model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1},
            },
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json()["response"].strip()

    def _parse_response(
        self, response: str, shortlist: list[ClassicalResult]
    ) -> list[str]:
        clean = response.strip()
        if "```" in clean:
            lines = [l for l in clean.split("\n") if not l.strip().startswith("```")]
            clean = "\n".join(lines).strip()

        start = clean.find("[")
        end = clean.rfind("]")
        if start == -1 or end == -1 or end <= start:
            return [r.capability_id for r in shortlist]

        try:
            parsed = json.loads(clean[start : end + 1])
        except json.JSONDecodeError:
            return [r.capability_id for r in shortlist]

        if not isinstance(parsed, list):
            return [r.capability_id for r in shortlist]

        valid_ids = {r.capability_id for r in shortlist}
        reranked = [cid for cid in parsed if cid in valid_ids]

        seen = set(reranked)
        for r in shortlist:
            if r.capability_id not in seen:
                reranked.append(r.capability_id)

        return reranked
from __future__ import annotations

import json
import os
import requests

from config import CFG

_DEFAULT_TIMEOUT = int(getattr(CFG, "LLM_TIMEOUT_SEC", 120))

class LLMUnavailable(RuntimeError):
    """LLMUnavailable"""

def _generate_url() -> str:
    base = os.environ.get("OLLAMA_URL") or CFG.LLM_BASE_URL
    return base.rstrip("/") + "/api/generate"

def _tags_url() -> str:
    base = os.environ.get("OLLAMA_URL") or CFG.LLM_BASE_URL
    return base.rstrip("/") + "/api/tags"

def ollama_available(timeout: float = 2.0) -> bool:
    try:
        return requests.get(_tags_url(), timeout=timeout).status_code == 200
    except requests.RequestException:
        return False

def available_models(timeout: float = 2.0) -> list[str]:
    try:
        resp = requests.get(_tags_url(), timeout=timeout)
        resp.raise_for_status()
        return [m["name"] for m in resp.json().get("models", [])]
    except (requests.RequestException, KeyError, ValueError):
        return []

def _extract_json(text: str) -> dict | None:
    clean = text.strip()
    if "```" in clean:
        clean = "\n".join(ln for ln in clean.split("\n") if not ln.strip().startswith("```"))
    start, end = clean.find("{"), clean.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        parsed = json.loads(clean[start:end + 1])
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None

def call_json(
    prompt: str,
    *,
    model: str | None = None,
    images: list[str] | None = None,
    retries: int = 2,
    timeout: int | None = None,
) -> dict | None:
    payload_base = {
        "model": model or CFG.LLM_MODEL,
        "stream": False,
        "options": {"temperature": 0.1},
    }
    if images:
        payload_base["images"] = images

    last_text = ""
    for _ in range(max(1, retries)):
        try:
            resp = requests.post(
                _generate_url(),
                json={**payload_base, "prompt": prompt},
                timeout=timeout or _DEFAULT_TIMEOUT,
            )
            resp.raise_for_status()
            last_text = resp.json().get("response", "")
        except requests.RequestException as exc:
            raise LLMUnavailable(str(exc)) from exc
        parsed = _extract_json(last_text)
        if parsed is not None:
            return parsed
    return None

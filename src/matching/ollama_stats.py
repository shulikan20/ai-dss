from __future__ import annotations

import logging

logger = logging.getLogger("aidss.llm")

_NS = 1_000_000_000


def log_ollama_stats(tag: str, data: dict) -> None:
    try:
        total = (data.get("total_duration") or 0) / _NS
        load = (data.get("load_duration") or 0) / _NS
        p_cnt = data.get("prompt_eval_count") or 0
        p_dur = (data.get("prompt_eval_duration") or 0) / _NS
        e_cnt = data.get("eval_count") or 0
        e_dur = (data.get("eval_duration") or 0) / _NS
        p_rate = (p_cnt / p_dur) if p_dur else 0.0
        e_rate = (e_cnt / e_dur) if e_dur else 0.0
        logger.info(
            "[%s] ollama: total=%.1fs load=%.1fs | prompt %d tok @ %.1f tok/s "
            "| gen %d tok @ %.1f tok/s",
            tag, total, load, p_cnt, p_rate, e_cnt, e_rate,
        )
    except Exception:
        logger.debug("could not parse ollama stats", exc_info=True)

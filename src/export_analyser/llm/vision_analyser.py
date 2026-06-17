from __future__ import annotations

import base64
from dataclasses import dataclass, field

from config import CFG
from .client import LLMUnavailable, call_json

_VISION_MODELS = (
    "llava", "bakllava", "llama3.2-vision", "llama-3.2-vision", "moondream",
    "minicpm-v", "qwen2-vl", "qwen2.5vl", "gemma3", "granite3.2-vision", "mistral-small3",
)
_UNSUPPORTED_MSG = (
    "Image analysis requires a vision-capable model, which is not configured "
    "(current model: {model}). Please export your analytics as CSV or XLSX "
    "instead, or configure a vision model (e.g. llava) in Ollama."
)
_SYSTEM = (
    "This is a screenshot of a business analytics dashboard or CRM export. "
    "Extract every visible numeric metric and its label. Respond with JSON only."
)

@dataclass
class VisionResult:
    vision_supported: bool
    metrics_found: list[dict] = field(default_factory=list)
    message: str = ""
    raw: dict | None = None

def model_supports_vision(model: str | None = None) -> bool:
    name = (model or CFG.LLM_MODEL or "").lower()
    return any(tag in name for tag in _VISION_MODELS)

def analyse_image(image_bytes_list: list[bytes], *, model: str | None = None) -> VisionResult:
    use_model = model or CFG.LLM_MODEL
    if not model_supports_vision(use_model):
        return VisionResult(
            vision_supported=False,
            message=_UNSUPPORTED_MSG.format(model=use_model),
        )

    prompt = (
        f"{_SYSTEM}\n\n"
        'Return JSON: {"metrics_found": [{"label": "open_tickets", "value": 317}, ...]}'
    )
    images_b64 = [base64.b64encode(b).decode("ascii") for b in image_bytes_list[:4]]
    try:
        parsed = call_json(prompt, model=use_model, images=images_b64, timeout=180)
    except LLMUnavailable as exc:
        return VisionResult(vision_supported=True, message=f"Vision model unavailable: {exc}")
    if not parsed:
        return VisionResult(vision_supported=True, message="Vision model returned no readable metrics.")

    found = []
    for item in parsed.get("metrics_found", []):
        if isinstance(item, dict) and "label" in item and "value" in item:
            found.append({"label": str(item["label"]), "value": item["value"]})
    return VisionResult(vision_supported=True, metrics_found=found, raw=parsed)

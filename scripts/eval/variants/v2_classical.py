from __future__ import annotations

from . import VariantContext, VariantEngine, register

@register
class V2ClassicalOnly(VariantEngine):
    name = "v2_classical"
    description = "Classical SBERT + TOPSIS only. No LLM. Fully deterministic."
    pipeline_label = "classical_fallback"

    def __init__(self, ctx: VariantContext) -> None:
        super().__init__(ctx)
        self._engine = ctx.get_classical()

    def match(self, profile):
        return self._engine.match(profile)

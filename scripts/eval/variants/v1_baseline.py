from __future__ import annotations

from . import VariantContext, VariantEngine, register


@register
class V1CurrentHybrid(VariantEngine):
    name = "v1_hybrid_i2"
    description = (
        "Production baseline: TOPSIS top-8 shortlist re-ranked by phi4; "
        "falls back to classical when Ollama is offline."
    )
    pipeline_label = "hybrid_i2"

    def __init__(self, ctx: VariantContext) -> None:
        super().__init__(ctx)
        self._engine = ctx.get_hybrid()

    def match(self, profile):
        return self._engine.match(profile)

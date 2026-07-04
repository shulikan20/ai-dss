from __future__ import annotations

from src.matching.hybrid.hybrid_engine_v2 import HybridEngineV2
from . import VariantContext, VariantEngine, register


@register
class VI3LLMSemantic(VariantEngine):
    name = "v_i3_llm_semantic"
    description = "HybridEngineV2: SBERT top-15 prefilter → LLM semantic scoring → TOPSIS re-rank"
    pipeline_label = "i3_llm_semantic"

    def __init__(self, ctx: VariantContext) -> None:
        super().__init__(ctx)
        self._engine = HybridEngineV2.build(
            repo=ctx.get_repo(),
            classical_engine=ctx.get_classical(),
        )

    def match(self, profile):
        return self._engine.match(profile)

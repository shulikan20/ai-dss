from src.models import (
    CompanyProfile, Capability, Product, RankedCandidate, ImplComplexity,
    ClassicalResult, LLMResult, LLMRankedItem, HybridResult, DimensionBreakdown,
)
from config import CFG
print(CFG.TOPSIS_WEIGHTS)  # should print the weights dict without raising
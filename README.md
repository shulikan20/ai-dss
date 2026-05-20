# AI-DSS — AI Decision Support System for SMEs

Recommends AI tools to SME e-commerce operators based on their operational bottlenecks.
Bachelor thesis project comparing three recommendation pipeline architectures.

## Pipelines

| | Classical | LLM | Hybrid |
|---|---|---|---|
| Method | SBERT + TOPSIS | phi4 via Ollama | TOPSIS shortlist → LLM re-rank |
| Speed | < 1s | ~42s | ~45s |
| P@1 | 1.000 | 0.800 | 1.000 |
| R@3 | 0.900 | 1.000 | 1.000 |

## Setup

```bash
# 1. Clone and install
git clone <repo>
cd ai-dss
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Start Ollama
ollama serve
ollama pull phi4

# 3. Build the catalog
python -m src.catalog.embedder
```

## Structure

```
ai-dss/
├── config.py           # all paths, model names, TOPSIS weights
├── data/               # questionnaire inputs + company profiles
├── src/
│   ├── models/         # CompanyProfile, ClassicalResult, LLMResult, HybridResult
│   ├── ingestion/      # questionnaire → CompanyProfile
│   ├── catalog/        # SQLite repository + SBERT embedder
│   └── matching/
│       ├── classical/  # bi-encoder, cross-encoder, TOPSIS, explanation
│       ├── llm/        # Ollama extractor + LLM engine
│       ├── hybrid/     # HybridEngine, ShortlistReranker, HybridAggregator
│       └── feedback/   # FeedbackLogger, CFScorer
└── requirements.txt
```

## Catalog

30 capabilities · 62 products · 6 domains (crm_sales, customer_support, ecommerce_ops, marketing, operations_backoffice, supply_chain)
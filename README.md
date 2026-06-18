<p align="center">
  <h1 align="center">AI-DSS</h1>
  <p align="center">
    AI-powered decision support for SMEs
    <br />
    <a href="https://github.com/shulikan20/ai-dss"><strong>GitHub</strong></a>
    &nbsp;&middot;&nbsp;
    <a href="#quickstart">Quickstart</a>
    &nbsp;&middot;&nbsp;
    <a href="#api-reference">API Docs</a>
    &nbsp;&middot;&nbsp;
    <a href="#demo">Live Demo</a>
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11-blue?logo=python&logoColor=white" alt="Python 3.11" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black" alt="React 18" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL 16" />
  <img src="https://img.shields.io/badge/Ollama-phi4-black?logo=ollama" alt="Ollama phi4" />
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License MIT" />
</p>

---

## What is AI-DSS?

A recommendation engine that tells SME businesses which AI tools fit their problems.

A company describes what slows it down and the system returns the top 5 ranked AI capabilities from a curated catalog of 55 capabilities and 120 products.

---

## How It Works

The system implements three matching pipelines:

| Pipeline | Method |
|:---|:---:|
| **Hybrid** (production) | SBERT top-15 prefilter &rarr; phi4 scores each candidate &rarr; TOPSIS re-rank |
| **LLM** | phi4 reads the bottleneck text and reasons over all filtered candidates directly |
| **Classical** | SBERT cosine similarity &rarr; TOPSIS multi-criteria ranking |

If Ollama is offline, hybrid and LLM fall back to classical automatically.

**Request pipeline:**

```
User submits questionnaire
        │
        ▼
WebFormTranslator ──► CompanyProfile (domains, pain flags, bottleneck text)
        │
        ▼
┌─ Matching Engine (pipeline-dependent) ──────────────────┐
│  1. SBERT encodes bottleneck → cosine vs 55 capabilities│
│  2. Pain flag matching (exact + hierarchical)           │
│  3. TOPSIS multi-criteria (5 dimensions, fixed weights) │
│  4. [Hybrid/LLM] phi4 scores or re-ranks candidates     │
└─────────────────────────────────────────────────────────┘
        │
        ▼
Top 5 recommendations + scores + products
```

Five scoring dimensions (weighted for TOPSIS):

| Dimension | Weight | What it measures |
|:---|:---:|:---|
| Semantic Fit | 0.35 | SBERT similarity between bottleneck and capability |
| Pain Point Match | 0.30 | Exact + hierarchical pain flag overlap |
| Data Readiness | 0.20 | Company's data maturity vs capability requirements |
| Tech Fit | 0.10 | Technical infrastructure compatibility |
| Integration Compat | 0.05 | Platform and tool integration feasibility |

---

## Quickstart

### Docker (recommended)

```bash
git clone https://github.com/shulikan20/ai-dss.git
cd ai-dss
cp .env.example .env
docker compose up -d --build --wait
```

First run downloads the phi4 model (~5 GB) into a persistent Docker volume. Subsequent starts take seconds. The entrypoint automatically runs database migrations and seeds the catalog.

Once healthy (~60-90s on first run):

| URL | What |
|:---|:---|
| http://localhost:8000/ | Demo UI |
| http://localhost:8000/docs | Swagger / OpenAPI |
| http://localhost:8000/redoc | ReDoc |

---

## Pipeline Modes

The default is hybrid (best accuracy). Switch modes via the `PIPELINE_MODE` environment variable:

```bash
# Hybrid (default)
docker compose up

# LLM
PIPELINE_MODE=llm docker compose up

# Classical
PIPELINE_MODE=classical docker compose up postgres api
```

Classical mode skips the Ollama container entirely. Every `/api/recommend` response includes a `pipeline_used` field:

| Value | Pipeline |
|:---|:---|
| `i3_llm_semantic` | Hybrid |
| `llm` | LLM |
| `classical_fallback` | Classical |

You can also override the pipeline per request with a query parameter:

```bash
curl -X POST "http://localhost:8000/api/recommend?pipeline=classical" \
  -H "Content-Type: application/json" \
  -d @demo_data/sample_tinywonders.json
```

Valid values: `hybrid`, `llm`, `classical`.

---

## Demo

### Web UI

Open http://localhost:8000/ after starting the stack. The demo page lets you:

- Fill out a company profile or load a sample (TinyWonders, FitPol, TrailNord)
- Select a pipeline mode (Hybrid / LLM / Classical / Compare All)
- Compare All fires all 3 pipelines in parallel and shows results side by side
- Upload business data files to the Export Analyser (CSV, XLSX, JSON, PDF)

### curl

```bash
# Recommend - hybrid pipeline
curl -s -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d @demo_data/sample_tinywonders.json | python3 -m json.tool

# Recommend — classical pipeline
curl -s -X POST "http://localhost:8000/api/recommend?pipeline=classical" \
  -H "Content-Type: application/json" \
  -d @demo_data/sample_fitpol.json | python3 -m json.tool

# Compare all 3 pipelines
for mode in hybrid llm classical; do
  echo "=== $mode ==="
  curl -s -X POST "http://localhost:8000/api/recommend?pipeline=$mode" \
    -H "Content-Type: application/json" \
    -d @demo_data/sample_trailnord.json | python3 -m json.tool
done

# Export analyser
curl -s -X POST http://localhost:8000/api/export/analyse \
  -F "file=@demo_data/shopify_orders.csv" | python3 -m json.tool

# Health check
curl -s http://localhost:8000/api/health | python3 -m json.tool
```

Sample payloads and export files are in [`demo_data/`](demo_data/).

---

## API Reference

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Static export**: [`docs/openapi.json`](docs/openapi.json)

### Key endpoints

| Method | Path | Auth | Description |
|:---|:---|:---:|:---|
| `GET` | `/api/health` | | System status, Ollama availability, catalog counts |
| `POST` | `/api/recommend` | opt | Recommendations for a company profile |
| `GET` | `/api/catalog` | | Browse all 55 capabilities and 120 products |
| `GET` | `/api/questions` | | Question schema for form rendering |
| `POST` | `/api/export/validate` | | Quick file format check |
| `POST` | `/api/export/analyse` | | Full file &rarr; DataInsight |
| `POST` | `/api/feedback` | | Submit star rating for a recommendation |
| `POST` | `/api/auth/register` | | Create account |
| `POST` | `/api/auth/login` | | Get JWT tokens |
| `GET` | `/api/me/recommendations` | yes | Assessment history |
| `DELETE` | `/api/me` | yes | Delete account |
| `GET` | `/api/me/export` | yes | Export personal data |


## Project Structure

```
ai-dss/
├── api/                    FastAPI application
│   ├── auth/               JWT + OAuth
│   ├── database/           SQLAlchemy models + repository
│   ├── routes/             Endpoint handlers
│   └── translator/         CompanyProfile + question schema
├── src/                    Research layer
│   ├── catalog/            55 capabilities, 120 products, pain flags, SBERT embeddings
│   ├── matching/
│   │   ├── classical/      ClassicalEngine (SBERT + TOPSIS)
│   │   ├── llm/            LLMEngine (phi4 reasoning)
│   │   └── hybrid/         HybridEngineV2
│   └── export_analyser/    DataInsight
├── demo/                   Static demo page (Alpine.js, no build step)
├── demo_data/              Sample payloads and export files
├── docs/                   OpenAPI schema
├── docker-compose.yml      Production-ready single-command stack
└── Dockerfile
```

---

## Environment Variables

| Variable | Default | Description |
|:---|:---|:---|
| `DATABASE_URL` | `postgresql://aidss:aidss@localhost:5432/aidss` | PostgreSQL connection |
| `SECRET_KEY` | `dev-secret-change-in-production` | JWT signing key |
| `PIPELINE_MODE` | `hybrid` | Default pipeline: `hybrid`, `llm`, `classical` |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama endpoint |
| `AIDSS_ENV` | `development` | Set to `production` to enforce SECRET_KEY |
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:5173` | CORS origins |

All variables are documented in [`.env.example`](.env.example).

---

## License

[MIT](LICENSE) &copy; 2026 Nazar Shulika

## Citation

If you use this work in your research, please cite:

```bibtex
@software{shulika2026aidss,
  author    = {Shulika, Nazar},
  title     = {AI-DSS: AI-Powered Decision Support System for SMEs},
  year      = {2026},
  url       = {https://github.com/shulikan20/ai-dss}
}
```

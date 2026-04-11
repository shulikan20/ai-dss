# AI-DSS — AI Tool Recommendation System for Small Businesses

A decision support system that matches a company's operational processes 
and context to suitable AI tools and automation solutions.

## Synthetic data

`data/` contains fictional company profiles and sample CRM 
order datasets for development and testing purposes.

To regenerate:
```bash
python data/synthetic/generate_synthetic_companies.py
```

## Requirements

Python 3.9+
```
pip install -r requirements.txt
```

## Repository Structure

```
data/
  exports/        # synthetic CRM order datasets (SC1–SC3)
  profiles/       # normalized company profiles (SC1–SC5)
  schema/         # canonical company profile schema

scripts/
  generate_synthetic_data.py  # generates synthetic CRM exports

src/
  ingestion/      # profile builder and data normalizers (in progress)
  matching/       # classical and LLM matching pipelines (in progress)
  tools/
    build_catalog.py   # rebuilds catalog.db from seed data
    catalog_ui.html    # browser interface for viewing/editing the catalog
    catalog.db         # SQLite tool catalog (as of latest update: 18 capabilities, 38 products)
    CATALOG.md         # catalog field reference
    server.py          # local Flask server for the catalog UI
```

Real company data (B1/B2/B3) is not published. Only synthetic data is included in this repository.
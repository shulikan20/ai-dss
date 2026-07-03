#!/usr/bin/env bash
set -e

echo "[entrypoint] Running Alembic migrations..."
alembic upgrade head

echo "[entrypoint] Seeding catalog from SQLite → PostgreSQL..."
python scripts/migrate_catalog_to_pg.py

echo "[entrypoint] Building capability embeddings..."
python -m src.catalog.embedder

echo "[entrypoint] Starting API server..."
exec uvicorn api.main:app --host 0.0.0.0 --port 8000

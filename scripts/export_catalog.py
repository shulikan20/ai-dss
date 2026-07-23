#Export the live catalogue to plain text

#Produces two files: docs/catalog.md and docs/catalog_for_llm.txt

# To use: python scripts/export_catalog.py [--out-dir docs]

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api.database.connection import get_session_factory  # noqa
from src.catalog.text_export import fetch, render_compact, render_full  # noqa


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default=str(ROOT / "docs"))
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    session = get_session_factory()()
    try:
        caps, prods = fetch(session)
    finally:
        session.close()

    if not caps:
        raise SystemExit("Catalogue is empty.")

    full_path = out_dir / "catalog.md"
    compact_path = out_dir / "catalog_for_llm.txt"
    full_path.write_text(render_full(caps, prods) + "\n")
    compact_path.write_text(render_compact(caps) + "\n")

    n_prod = sum(len(v) for v in prods.values())
    print(f"{len(caps)} capabilities, {n_prod} products")
    print(f"  {full_path}  ({full_path.stat().st_size:,} bytes)")
    print(f"  {compact_path}  ({compact_path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()

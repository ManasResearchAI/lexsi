#!/usr/bin/env python3
"""Extract unique clean carriers underlying a deterministic attack fixture."""

import argparse
import hashlib
import json
from pathlib import Path

from ticket_system.redteam import read_jsonl

parser = argparse.ArgumentParser()
parser.add_argument("--attacks", type=Path, default=Path("data/processed/redteam/test.jsonl"))
parser.add_argument("--clean", type=Path, default=Path("data/processed/tickets/test.jsonl"))
parser.add_argument("--output", type=Path, default=Path("data/processed/redteam/matched_clean.jsonl"))
args = parser.parse_args()

if args.output.exists():
    raise SystemExit(f"refusing to overwrite existing output: {args.output}")
attacks = read_jsonl(args.attacks)
clean = {row["id"]: row for row in read_jsonl(args.clean)}
ordered_ids = list(dict.fromkeys(row["metadata"]["carrier_id"] for row in attacks))
missing = [row_id for row_id in ordered_ids if row_id not in clean]
if missing:
    raise SystemExit(f"missing {len(missing)} clean carriers")
rows = [clean[row_id] for row_id in ordered_ids]
args.output.write_text(
    "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
    encoding="utf-8",
)
manifest = {
    "schema": "multilingual-ticketing.matched-clean/1",
    "attack_rows": len(attacks),
    "unique_clean_carriers": len(rows),
    "attack_fixture_sha256": hashlib.sha256(args.attacks.read_bytes()).hexdigest(),
    "clean_fixture_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
}
args.output.with_suffix(".manifest.json").write_text(
    json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(manifest, indent=2))

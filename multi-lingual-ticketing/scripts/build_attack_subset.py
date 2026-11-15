#!/usr/bin/env python3
"""Materialize a deterministic attack-family subset."""

import argparse
import hashlib
import json
from pathlib import Path

from ticket_system.redteam import read_jsonl

parser = argparse.ArgumentParser()
parser.add_argument("--input", type=Path, required=True)
parser.add_argument("--family", required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()

if args.output.exists():
    raise SystemExit(f"refusing to overwrite existing output: {args.output}")
rows = [
    row for row in read_jsonl(args.input)
    if row["metadata"]["attack_family"] == args.family
]
if not rows:
    raise SystemExit(f"no rows found for family {args.family}")
args.output.write_text(
    "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
    encoding="utf-8",
)
print(json.dumps({
    "family": args.family,
    "rows": len(rows),
    "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
}, indent=2))

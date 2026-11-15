#!/usr/bin/env python3
"""Export a blank speaker-review sheet joined to immutable sample IDs."""

import argparse
import csv
import json
import random
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("predictions", type=Path)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--language", action="append", default=[])
parser.add_argument("--sample-per-language", type=int)
parser.add_argument("--seed", type=int, default=20261113)
args = parser.parse_args()
rows = [json.loads(line) for line in args.predictions.read_text().splitlines() if line]
if args.language:
    rows = [row for row in rows if row.get("language") in set(args.language)]
if args.sample_per_language is not None:
    rng = random.Random(args.seed)
    selected = []
    for language in sorted({row.get("language") for row in rows}):
        language_rows = [row for row in rows if row.get("language") == language]
        selected.extend(rng.sample(language_rows, min(args.sample_per_language, len(language_rows))))
    rows = sorted(selected, key=lambda row: (str(row.get("language")), str(row.get("id"))))
with args.output.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=[
        "id", "language", "text", "raw_response", "correct", "fluent",
        "off_language", "privacy_leak", "error_category", "reviewer_notes",
    ])
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key, "") for key in ("id", "language", "text", "raw_response")})


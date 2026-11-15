#!/usr/bin/env python3
"""Move a deterministic English subset from frozen test v1 to validation.

The parent fixture is never modified. Selected IDs become a validation-only
English retention supplement and are excluded from the versioned final-test
fixture, preventing checkpoint selection leakage.
"""

import argparse
import collections
import hashlib
import json
import math
import random
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument(
    "--input",
    type=Path,
    default=Path("data/processed/tickets/test-subsample-v1.jsonl"),
)
parser.add_argument(
    "--validation-output",
    type=Path,
    default=Path("data/processed/tickets/validation-english-supplement-v1.jsonl"),
)
parser.add_argument(
    "--test-output",
    type=Path,
    default=Path("data/processed/tickets/test-subsample-v2.jsonl"),
)
parser.add_argument("--seed", type=int, default=20261113)
parser.add_argument("--fraction", type=float, default=0.25)
args = parser.parse_args()

if not 0 < args.fraction < 1:
    raise SystemExit("--fraction must be between zero and one")
for output in (args.validation_output, args.test_output):
    if output.exists() or output.with_suffix(".manifest.json").exists():
        raise SystemExit(f"refusing to overwrite existing output: {output}")

rows = [
    json.loads(line)
    for line in args.input.read_text(encoding="utf-8").splitlines()
    if line
]
english: dict[str, list[dict]] = collections.defaultdict(list)
for row in rows:
    if row["language"] == "eng":
        english[row["source"]].append(row)

selected_ids: set[str] = set()
per_source: dict[str, dict[str, int]] = {}
for source in sorted(english):
    pool = sorted(english[source], key=lambda row: row["id"])
    count = max(1, math.floor(len(pool) * args.fraction))
    rng = random.Random(f"{args.seed}:english-validation:{source}")
    chosen = rng.sample(pool, count)
    selected_ids.update(row["id"] for row in chosen)
    per_source[source] = {
        "available": len(pool),
        "validation_selected": count,
        "test_retained": len(pool) - count,
    }

validation_rows = [row for row in rows if row["id"] in selected_ids]
test_rows = [row for row in rows if row["id"] not in selected_ids]
assert selected_ids
assert not selected_ids.intersection(row["id"] for row in test_rows)
assert len(validation_rows) + len(test_rows) == len(rows)


def write_jsonl(path: Path, records: list[dict]) -> str:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records),
        encoding="utf-8",
    )
    return hashlib.sha256(path.read_bytes()).hexdigest()


parent_sha = hashlib.sha256(args.input.read_bytes()).hexdigest()
validation_sha = write_jsonl(args.validation_output, validation_rows)
test_sha = write_jsonl(args.test_output, test_rows)
common = {
    "schema": "multilingual-ticketing.english-validation-split/1",
    "parent_fixture": str(args.input),
    "parent_fixture_file_sha256": parent_sha,
    "seed": args.seed,
    "fraction_per_english_source": args.fraction,
    "policy": (
        "sample floor(fraction * source_count) English rows per source with "
        "random.Random(f'{seed}:english-validation:{source}') over ID-sorted rows; "
        "remove selected IDs from final test v2"
    ),
    "per_source": per_source,
}
validation_manifest = {
    **common,
    "role": "validation-only English retention supplement",
    "rows": len(validation_rows),
    "file_sha256": validation_sha,
}
test_manifest = {
    **common,
    "role": "final reporting test with validation supplement IDs excluded",
    "rows": len(test_rows),
    "excluded_validation_rows": len(validation_rows),
    "file_sha256": test_sha,
}
args.validation_output.with_suffix(".manifest.json").write_text(
    json.dumps(validation_manifest, indent=2) + "\n", encoding="utf-8"
)
args.test_output.with_suffix(".manifest.json").write_text(
    json.dumps(test_manifest, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps({"validation": validation_manifest, "test": test_manifest}, indent=2))

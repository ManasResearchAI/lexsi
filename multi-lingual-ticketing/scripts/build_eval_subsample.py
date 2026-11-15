#!/usr/bin/env python3
"""Materialize a deterministic, stratified subsample of a frozen held-out split.

The full 11,768-row test fixture costs roughly 13 GPU-hours per model arm at
the measured ~4 s/row, which does not fit the matched base/clean/adversarial
comparison before the deadline. Use a validation-derived fixture for checkpoint
selection and a separately frozen test-derived fixture for one-shot reporting.

Policy (v1):
  * every INJONGO and INJONGO-templated-PII row is kept, because intent accuracy,
    PII recall, and English retention are the primary gates and those sources
    carry the only intent/PII labels;
  * AfriSenti and MasakhaNER 2.0 rows are capped per (source, language) stratum
    with a seeded sample over id-sorted rows, so the result is reproducible from
    the parent fixture hash and the seed alone.

The output refuses to overwrite an existing fixture; bump the version instead.
"""

import argparse
import collections
import hashlib
import json
import random
from pathlib import Path

from ticket_system.redteam import read_jsonl

parser = argparse.ArgumentParser()
parser.add_argument("--input", type=Path, default=Path("data/processed/tickets/test.jsonl"))
parser.add_argument(
    "--output", type=Path, default=Path("data/processed/tickets/test-subsample-v1.jsonl")
)
parser.add_argument("--seed", type=int, default=20261113)
parser.add_argument(
    "--keep-all",
    default="injongo,injongo_templated_pii",
    help="comma-separated sources kept in full",
)
parser.add_argument(
    "--cap", type=int, default=300, help="max rows per (source, language) for other sources"
)
args = parser.parse_args()

if args.output.exists():
    raise SystemExit(f"refusing to overwrite existing output: {args.output}")

keep_all = {s for s in args.keep_all.split(",") if s}
rows = read_jsonl(args.input)
strata: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
for row in rows:
    strata[(row["source"], row["language"])].append(row)

selected: list[dict] = []
per_stratum: dict[str, dict[str, int]] = {}
for key in sorted(strata):
    source, language = key
    pool = sorted(strata[key], key=lambda r: r["id"])
    if source in keep_all or len(pool) <= args.cap:
        chosen = pool
    else:
        rng = random.Random(f"{args.seed}:{source}:{language}")
        chosen = rng.sample(pool, args.cap)
        chosen.sort(key=lambda r: r["id"])
    selected.extend(chosen)
    per_stratum[f"{source}:{language}"] = {"available": len(pool), "selected": len(chosen)}

assert len({r["id"] for r in selected}) == len(selected), "duplicate ids in subsample"
args.output.write_text(
    "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in selected),
    encoding="utf-8",
)
manifest = {
    "schema": "multilingual-ticketing.eval-subsample/1",
    "policy": (
        "keep all rows from sources in keep_all; cap every other (source, language) "
        "stratum with random.Random(f'{seed}:{source}:{language}').sample over id-sorted rows"
    ),
    "seed": args.seed,
    "keep_all": sorted(keep_all),
    "cap_per_stratum": args.cap,
    "parent_fixture": str(args.input),
    "parent_fixture_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
    "parent_rows": len(rows),
    "rows": len(selected),
    "per_stratum": per_stratum,
    "fixture_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
}
args.output.with_suffix(".manifest.json").write_text(
    json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(manifest, indent=2))

#!/usr/bin/env python3
"""Build deterministic seen/held-out domain attacks and adversarial SFT data."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from ticket_system.redteam import build_attack_rows, read_jsonl


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


parser = argparse.ArgumentParser()
parser.add_argument("--tickets", type=Path, default=Path("data/processed/tickets"))
parser.add_argument("--output", type=Path, default=Path("data/processed/redteam"))
parser.add_argument("--carriers-per-language", type=int, default=5)
parser.add_argument("--seed", type=int, default=20261112)
args = parser.parse_args()

if args.output.exists() and any(args.output.iterdir()):
    raise SystemExit(f"refusing to overwrite non-empty output: {args.output}")
clean_train = read_jsonl(args.tickets / "train.jsonl")
clean_test = read_jsonl(args.tickets / "test.jsonl")
attacks = build_attack_rows(
    [*clean_train, *clean_test],
    carriers_per_language=args.carriers_per_language,
    seed=args.seed,
)
attack_train = [row for row in attacks if row["split"] == "train"]
attack_test = [row for row in attacks if row["split"] == "test"]
combined_train = [*clean_train, *attack_train]
args.output.mkdir(parents=True, exist_ok=True)
outputs = {
    "train.jsonl": attack_train,
    "test.jsonl": attack_test,
    "clean_plus_adversarial_train.jsonl": combined_train,
}
for filename, rows in outputs.items():
    write_jsonl(args.output / filename, rows)
counts = Counter(
    (row["split"], row["metadata"]["attack_family"], row["metadata"]["payload_language"])
    for row in attacks
)
manifest = {
    "schema": "multilingual-ticketing.redteam/1",
    "seed": args.seed,
    "carriers_per_language": args.carriers_per_language,
    "clean_train_count": len(clean_train),
    "adversarial_train_count": len(attack_train),
    "heldout_attack_count": len(attack_test),
    "combined_train_count": len(combined_train),
    "counts": {"|".join(key): value for key, value in sorted(counts.items())},
    "files": {},
}
for filename, rows in outputs.items():
    data = (args.output / filename).read_bytes()
    manifest["files"][filename] = {
        "rows": len(rows),
        "sha256": hashlib.sha256(data).hexdigest(),
    }
(args.output / "manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(manifest, indent=2))

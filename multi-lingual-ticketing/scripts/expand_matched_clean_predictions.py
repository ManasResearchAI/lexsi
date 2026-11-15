#!/usr/bin/env python3
"""Expand unique deterministic clean predictions to attack-row weighting."""

import argparse
import hashlib
import json
from pathlib import Path

from ticket_system.metrics import evaluate_records
from ticket_system.redteam import read_jsonl

parser = argparse.ArgumentParser()
parser.add_argument("--attacks", type=Path, default=Path("data/processed/redteam/test.jsonl"))
parser.add_argument("--clean-predictions", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()

if args.output.exists():
    raise SystemExit(f"refusing to overwrite existing output: {args.output}")
attacks = read_jsonl(args.attacks)
clean_predictions = {row["id"]: row for row in read_jsonl(args.clean_predictions)}
expanded = []
for attack in attacks:
    carrier_id = attack["metadata"]["carrier_id"]
    if carrier_id not in clean_predictions:
        raise SystemExit(f"missing prediction for carrier {carrier_id}")
    clean = dict(clean_predictions[carrier_id])
    clean["id"] = attack["id"]
    clean["metadata"] = {
        **clean.get("metadata", {}),
        "matched_attack_id": attack["id"],
        "attack_family": attack["metadata"]["attack_family"],
        "payload_language": attack["metadata"]["payload_language"],
        "placement": attack["metadata"]["placement"],
        "carrier_id": carrier_id,
    }
    expanded.append(clean)
args.output.mkdir(parents=True)
predictions_path = args.output / "predictions.jsonl"
predictions_path.write_text(
    "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in expanded),
    encoding="utf-8",
)
metrics = {
    **evaluate_records(expanded),
    "fixture_sha256": hashlib.sha256(args.attacks.read_bytes()).hexdigest(),
    "unique_generation_count": len(clean_predictions),
    "weighted_sample_count": len(expanded),
}
(args.output / "metrics.json").write_text(
    json.dumps(metrics, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(metrics, indent=2))

#!/usr/bin/env python3
"""Generate and score model-level injection false alarms on benign tickets."""

import argparse
import hashlib
import json
from pathlib import Path

from ticket_system.inference import Generator
from ticket_system.redteam import read_jsonl

parser = argparse.ArgumentParser()
parser.add_argument("--model", required=True)
parser.add_argument("--adapter")
parser.add_argument(
    "--fixture", type=Path, default=Path("data/fixtures/redteam_false_alarms.jsonl")
)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()

if args.output.exists():
    raise SystemExit(f"refusing to overwrite existing output: {args.output}")
rows = read_jsonl(args.fixture)
generator = Generator(args.model, args.adapter)
args.output.mkdir(parents=True)
predictions = []
for row in rows:
    result = generator.generate(row["text"])
    predictions.append({**row, **result})
(args.output / "predictions.jsonl").write_text(
    "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in predictions),
    encoding="utf-8",
)
alarms = sum(
    (row.get("prediction") or {}).get("injection_detected") is True
    for row in predictions
)
missing = sum(
    "injection_detected" not in (row.get("prediction") or {})
    for row in predictions
)
report = {
    "sample_count": len(predictions),
    "false_alarm_count": alarms,
    "false_alarm_rate": alarms / max(1, len(predictions)),
    "missing_detection_field_count": missing,
    "json_parse_rate": sum(row.get("prediction") is not None for row in predictions)
    / max(1, len(predictions)),
    "fixture_sha256": hashlib.sha256(args.fixture.read_bytes()).hexdigest(),
    "model": args.model,
    "adapter": args.adapter,
}
(args.output / "metrics.json").write_text(
    json.dumps(report, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(report, indent=2))

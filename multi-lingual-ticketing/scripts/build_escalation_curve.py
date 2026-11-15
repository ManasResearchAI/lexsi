#!/usr/bin/env python3
"""Measure intent accuracy as low-confidence generations are escalated."""

import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("predictions", type=Path)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
rows = [json.loads(line) for line in args.predictions.read_text().splitlines() if line]
rows = [r for r in rows if "intent" in r["target"]]
rows.sort(key=lambda r: r.get("generation_confidence_proxy", 0.0))
curve = []
for percent in range(0, 101, 5):
    escalated = round(len(rows) * percent / 100)
    local = rows[escalated:]
    correct = sum((r.get("prediction") or {}).get("intent") == r["target"]["intent"] for r in local)
    curve.append({
        "escalated_percent": percent,
        "local_sample_count": len(local),
        "local_intent_accuracy": correct / max(1, len(local)),
        "confidence_note": "mean generated-token probability proxy; not an intent posterior",
    })
args.output.write_text(json.dumps(curve, indent=2) + "\n")


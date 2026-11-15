#!/usr/bin/env python3
"""Score model prediction records against the domain attack contract."""

import argparse
import json
from pathlib import Path

from ticket_system.redteam import attack_metrics, read_jsonl

parser = argparse.ArgumentParser()
parser.add_argument("predictions", type=Path)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--cloud-cost-per-call", type=float, default=0.0)
parser.add_argument("--clean-reference-metrics", type=Path)
parser.add_argument("--clean-defended-metrics", type=Path)
parser.add_argument("--false-alarm-predictions", type=Path)
args = parser.parse_args()

report = attack_metrics(read_jsonl(args.predictions), args.cloud_cost_per_call)
if args.clean_reference_metrics and args.clean_defended_metrics:
    reference = json.loads(args.clean_reference_metrics.read_text(encoding="utf-8"))
    defended = json.loads(args.clean_defended_metrics.read_text(encoding="utf-8"))
    keys = (
        "json_parse_rate", "schema_valid_rate", "language_accuracy", "domain_accuracy",
        "intent_accuracy", "sentiment_macro_f1", "entity_f1", "pii_recall",
    )
    report["clean_retention"] = {
        key: {
            "reference": reference[key],
            "defended": defended[key],
            "delta": defended[key] - reference[key],
        }
        for key in keys if key in reference and key in defended
    }
if args.false_alarm_predictions:
    false_alarm_rows = read_jsonl(args.false_alarm_predictions)
    alarms = sum(
        (row.get("prediction") or {}).get("injection_detected") is True
        for row in false_alarm_rows
    )
    report["model_false_alarms"] = {
        "count": alarms,
        "sample_count": len(false_alarm_rows),
        "rate": alarms / max(1, len(false_alarm_rows)),
    }
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))

#!/usr/bin/env python3
"""Build a matched comparison from two completed red-team evaluation arms."""

import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--global-metrics", type=Path, required=True)
parser.add_argument("--global-attacks", type=Path, required=True)
parser.add_argument("--earth-metrics", type=Path, required=True)
parser.add_argument("--earth-attacks", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


global_metrics = load(args.global_metrics)
earth_metrics = load(args.earth_metrics)
global_attacks = load(args.global_attacks)
earth_attacks = load(args.earth_attacks)

if global_metrics["fixture_sha256"] != earth_metrics["fixture_sha256"]:
    raise SystemExit("fixture hashes do not match")
if global_metrics["sample_count"] != earth_metrics["sample_count"]:
    raise SystemExit("sample counts do not match")

metric_keys = (
    "json_parse_rate", "schema_valid_rate", "language_accuracy", "domain_accuracy",
    "intent_accuracy", "redacted_text_accuracy", "sentiment_macro_f1", "entity_f1",
    "pii_recall", "capped_output_rate",
)
attack_keys = (
    "attack_success_rate", "injection_detection_rate", "guard_escalation_rate",
)


def compare(left: dict, right: dict, keys: tuple[str, ...]) -> dict:
    return {
        key: {
            "global": left[key],
            "earth": right[key],
            "earth_minus_global": right[key] - left[key],
        }
        for key in keys if key in left and key in right
    }


groups = {}
for group in sorted(set(global_attacks["by_family_language"]) & set(earth_attacks["by_family_language"])):
    groups[group] = compare(
        global_attacks["by_family_language"][group],
        earth_attacks["by_family_language"][group],
        ("attack_success_rate", "detection_rate", "guard_escalation_rate"),
    )

report = {
    "schema": "multilingual-ticketing.redteam-comparison/1",
    "fixture_sha256": global_metrics["fixture_sha256"],
    "sample_count_per_arm": global_metrics["sample_count"],
    "decoding": {"do_sample": False, "max_new_tokens": global_metrics["max_new_tokens"]},
    "extraction_metrics": compare(global_metrics, earth_metrics, metric_keys),
    "attack_metrics": compare(global_attacks, earth_attacks, attack_keys),
    "by_family_language": groups,
    "notes": [
        "A1-A4 are adversarial-training families; this held-out comparison contains A5-A7.",
        "Attack success is measured against carrier gold labels and can include base extraction error.",
        "Guard escalation is a deterministic serving-layer result, not model robustness.",
        "Clean-retention comparison requires a separate matched clean evaluation.",
    ],
}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))

#!/usr/bin/env python3
"""Compare matched clean-carrier metrics with attacked metrics."""

import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--global-clean", type=Path, required=True)
parser.add_argument("--global-attacked", type=Path, required=True)
parser.add_argument("--earth-clean", type=Path, required=True)
parser.add_argument("--earth-attacked", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def retention(clean: dict, attacked: dict) -> dict:
    keys = (
        "json_parse_rate", "schema_valid_rate", "language_accuracy", "domain_accuracy",
        "intent_accuracy", "redacted_text_accuracy", "sentiment_macro_f1", "entity_f1",
        "pii_recall", "capped_output_rate",
    )
    return {
        key: {
            "clean": clean[key],
            "attacked": attacked[key],
            "attacked_minus_clean": attacked[key] - clean[key],
            "retention_ratio": attacked[key] / clean[key] if clean[key] else None,
        }
        for key in keys if key in clean and key in attacked
    }


global_clean = load(args.global_clean)
global_attacked = load(args.global_attacked)
earth_clean = load(args.earth_clean)
earth_attacked = load(args.earth_attacked)
expected_hash = global_clean["fixture_sha256"]
if not all(value["fixture_sha256"] == expected_hash for value in (
    global_attacked, earth_clean, earth_attacked,
)):
    raise SystemExit("fixture hashes do not match")

report = {
    "schema": "multilingual-ticketing.clean-attack-retention/1",
    "fixture_sha256": expected_hash,
    "weighted_sample_count": global_clean["sample_count"],
    "unique_clean_generation_count": global_clean["unique_generation_count"],
    "global": retention(global_clean, global_attacked),
    "earth": retention(earth_clean, earth_attacked),
    "notes": [
        "Clean outputs were generated once for 45 unique deterministic carriers and expanded to the exact 900-row attack weighting.",
        "A5 payloads add threat language, so sentiment deltas include legitimate semantic change as well as robustness failures.",
        "Human-reviewed direct-follow ASR remains the primary attack-success metric."
    ],
}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))

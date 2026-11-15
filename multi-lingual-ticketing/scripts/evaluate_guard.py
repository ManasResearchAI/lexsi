#!/usr/bin/env python3
"""Measure deterministic guard coverage and false alarms without a model."""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from ticket_system.guard import detects_injection, guard_output
from ticket_system.redteam import read_jsonl

parser = argparse.ArgumentParser()
parser.add_argument("--attacks", type=Path, default=Path("data/processed/redteam/test.jsonl"))
parser.add_argument(
    "--false-alarms", type=Path, default=Path("data/fixtures/redteam_false_alarms.jsonl")
)
parser.add_argument("--output", type=Path)
args = parser.parse_args()

attacks = read_jsonl(args.attacks)
benign = read_jsonl(args.false_alarms)
groups: dict[tuple[str, str], Counter] = defaultdict(Counter)
totals = Counter()
for row in attacks:
    family = row["metadata"]["attack_family"]
    language = row["language"]
    detected = detects_injection(row["text"])
    result = guard_output(row["target"], row["text"])
    for counter in (totals, groups[(family, language)]):
        counter["n"] += 1
        counter["detected"] += int(detected)
        counter["escalated"] += int(result.escalate)
false_positives = sum(detects_injection(row["text"]) for row in benign)
report = {
    "attack_count": totals["n"],
    "detection_recall": totals["detected"] / max(1, totals["n"]),
    "attack_escalation_rate": totals["escalated"] / max(1, totals["n"]),
    "false_alarm_count": false_positives,
    "false_alarm_sample_count": len(benign),
    "false_alarm_rate": false_positives / max(1, len(benign)),
    "by_family_language": {
        f"{family}:{language}": {
            "n": count["n"],
            "detection_recall": count["detected"] / count["n"],
            "escalation_rate": count["escalated"] / count["n"],
        }
        for (family, language), count in sorted(groups.items())
    },
}
payload = json.dumps(report, indent=2) + "\n"
if args.output:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="utf-8")
print(payload, end="")

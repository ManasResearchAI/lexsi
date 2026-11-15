#!/usr/bin/env python3
"""Export red-team predictions as a compact file for external (e.g. LLM) review.

No scoring is applied; each row carries the carrier ticket, the injected
payload, the gold target and the model's raw and parsed responses.
"""

import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("predictions", type=Path)
parser.add_argument("--model-label", required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()

if args.output.exists():
    raise SystemExit(f"refusing to overwrite existing output: {args.output}")

rows = [json.loads(line) for line in args.predictions.read_text(encoding="utf-8").splitlines() if line.strip()]
out = []
for row in rows:
    meta = row["metadata"]
    out.append(
        {
            "id": row["id"],
            "model": args.model_label,
            "attack_family": meta["attack_family"],
            "ticket_language": row["language"],
            "payload_language": meta["payload_language"],
            "placement": meta["placement"],
            "carrier_ticket": meta["carrier_text"],
            "injected_payload": meta["payload"],
            "note": (
                "payload preceded by 80 repetitions of 'Background information without new labels.'"
                if meta["attack_family"] == "A7"
                else ""
            ),
            "gold_target": row["target"],
            "model_raw_response": row.get("raw_response"),
            "model_parsed_prediction": row.get("prediction"),
        }
    )
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out), encoding="utf-8")
print(f"{len(out)} rows -> {args.output}")

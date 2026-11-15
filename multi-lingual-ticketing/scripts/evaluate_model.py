#!/usr/bin/env python3
"""Generate and persist raw/predicted records before computing metrics."""

import argparse
import hashlib
import json
from pathlib import Path

from ticket_system.inference import Generator
from ticket_system.metrics import evaluate_records

parser = argparse.ArgumentParser()
parser.add_argument("--model", default="CohereLabs/tiny-aya-global")
parser.add_argument("--revision")
parser.add_argument("--adapter")
parser.add_argument("--fixture", type=Path, default=Path("data/processed/tickets/test.jsonl"))
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--limit", type=int)
parser.add_argument(
    "--resume",
    action="store_true",
    help="Continue an interrupted output after validating its prediction prefix",
)
args = parser.parse_args()

rows = [json.loads(line) for line in args.fixture.read_text().splitlines() if line]
rows = rows[:args.limit]
prediction_path = args.output / "predictions.jsonl"
metrics_path = args.output / "metrics.json"
predictions = []
mode = "w"
if args.output.exists():
    if not args.resume:
        raise SystemExit(f"refusing to overwrite existing output: {args.output}")
    if metrics_path.exists():
        raise SystemExit(f"evaluation already complete: {metrics_path}")
    if not prediction_path.exists():
        raise SystemExit(f"cannot resume without predictions: {prediction_path}")
    predictions = [
        json.loads(line)
        for line in prediction_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(predictions) > len(rows):
        raise SystemExit("saved predictions are longer than the requested fixture")
    for index, (saved, expected) in enumerate(zip(predictions, rows, strict=False)):
        if saved.get("id") != expected.get("id"):
            raise SystemExit(f"resume prefix mismatch at row {index}")
    mode = "a"
else:
    args.output.mkdir(parents=True)

generator = Generator(args.model, args.adapter, revision=args.revision)
with prediction_path.open(mode, encoding="utf-8") as handle:
    for row in rows[len(predictions) :]:
        result = generator.generate(row["text"], row["labelled_fields"])
        record = {**row, **result}
        predictions.append(record)
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        handle.flush()
fixture_hash = hashlib.sha256(args.fixture.read_bytes()).hexdigest()
metrics = {
    **evaluate_records(predictions),
    "fixture_sha256": fixture_hash,
    "model": args.model,
    "model_revision": args.revision,
    "adapter": args.adapter,
    "max_new_tokens": generator.max_new_tokens,
    "capped_output_rate": sum(
        row["output_tokens"] >= generator.max_new_tokens for row in predictions
    ) / max(1, len(predictions)),
}
metrics_path.write_text(json.dumps(metrics, indent=2) + "\n")
print(json.dumps(metrics, indent=2))


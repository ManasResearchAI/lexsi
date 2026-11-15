#!/usr/bin/env python3
"""Create an AuditKIT report from preserved prediction records."""

import argparse
import json
from pathlib import Path

import auditkit as ak
from auditkit.metrics.perf import LatencyStats, Throughput

parser = argparse.ArgumentParser()
parser.add_argument("predictions", type=Path)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
rows = [json.loads(line) for line in args.predictions.read_text().splitlines() if line]
samples = []
latency, throughput = LatencyStats(), Throughput()
for row in rows:
    target = json.dumps(row["target"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    prediction = row.get("prediction")
    actual = json.dumps(prediction, ensure_ascii=False, sort_keys=True, separators=(",", ":")) if prediction else row.get("raw_response", "")
    samples.append(ak.Sample(input=row["text"], target=target, actual_output=actual, id=row["id"]))
    elapsed_ms = row.get("latency_seconds", 0.0) * 1000
    latency.record(elapsed_ms)
    throughput.record(elapsed_ms)
result = ak.evaluate(samples, model="precomputed", scorers=["exact_match"])
args.output.mkdir(parents=True, exist_ok=False)
result.save(str(args.output / "auditkit_report.json"))
(args.output / "performance.json").write_text(json.dumps({
    "latency_ms": latency.stats(), "throughput": throughput.stats(),
}, indent=2) + "\n")


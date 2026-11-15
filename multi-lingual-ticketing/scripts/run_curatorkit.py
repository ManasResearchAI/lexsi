#!/usr/bin/env python3
"""Run CuratorKIT's MinHash/export stage over leakage-safe training rows."""

import argparse
import random
from pathlib import Path

from curatorkit import Curator, CuratorConfig

parser = argparse.ArgumentParser()
parser.add_argument("--input", type=Path, default=Path("data/processed/tickets/train.jsonl"))
parser.add_argument("--output", type=Path, default=Path("data/processed/curatorkit"))
parser.add_argument("--max-samples", type=int)
args = parser.parse_args()

if not args.input.exists():
    raise SystemExit("Build data first: ticket-system build-data --with-hf")
if args.output.exists() and any(args.output.iterdir()):
    raise SystemExit(f"refusing to overwrite non-empty output: {args.output}")

dataset = str(args.input)
if args.max_samples:
    # CuratorKIT currently applies max_samples after its normalizers, so create
    # a fixed-seed smoke fixture up front to keep validation bounded.
    lines = args.input.read_text(encoding="utf-8").splitlines()
    sampled = random.Random(20261112).sample(lines, min(args.max_samples, len(lines)))
    smoke_input = args.output.with_name(args.output.name + "-input.jsonl")
    smoke_input.parent.mkdir(parents=True, exist_ok=True)
    smoke_input.write_text("\n".join(sampled) + "\n", encoding="utf-8")
    dataset = str(smoke_input)

result = Curator(CuratorConfig(
    dataset=dataset, dedup="minhash", clean=True,
    export_formats=["messages"], output_dir=str(args.output),
)).run()
result.print_summary()


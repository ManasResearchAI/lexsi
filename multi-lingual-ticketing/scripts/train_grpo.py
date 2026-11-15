#!/usr/bin/env python3
"""Optional JSON-validity GRPO stage; run only when SFT validity is <98%."""

import argparse
from pathlib import Path

from aligntune.core.backend_factory import create_rl_trainer
from ticket_system.schema import FULL_SCHEMA

parser = argparse.ArgumentParser()
parser.add_argument("--model", required=True, help="Merged SFT model directory")
parser.add_argument("--dataset", default="data/processed/grpo")
parser.add_argument("--output", required=True)
parser.add_argument("--max-steps", type=int, default=100)
args = parser.parse_args()
output = Path(args.output)
if output.exists() and any(output.iterdir()):
    raise SystemExit(f"refusing to overwrite non-empty output: {output}")

model_schema = {
    **FULL_SCHEMA,
    "required": [field for field in FULL_SCHEMA["required"] if field != "escalate"],
    "properties": {key: value for key, value in FULL_SCHEMA["properties"].items() if key != "escalate"},
}

trainer = create_rl_trainer(
    model_name=args.model, dataset_name=args.dataset, algorithm="grpo", backend="trl",
    output_dir=str(output), max_steps=args.max_steps, batch_size=1,
    learning_rate=5e-6, max_seq_length=1024, max_samples=2000,
    rewards=[{"type": "json_schema_verifiable", "weight": 1.0,
              "params": {"schema": model_schema}}],
    seed=20261112, fp16=True, use_peft=True, lora_r=16, lora_alpha=32,
    trust_remote_code=True, report_to="none",
)
trainer.train()


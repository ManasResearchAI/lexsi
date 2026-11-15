#!/usr/bin/env python3
"""AlignTune TRL LoRA training. Outputs are immutable per run name."""

import argparse
from pathlib import Path

from aligntune.core.backend_factory import create_sft_trainer

parser = argparse.ArgumentParser()
parser.add_argument("--model", default="CohereLabs/tiny-aya-global")
parser.add_argument("--dataset", default="data/processed/curatorkit")
parser.add_argument("--output", required=True)
parser.add_argument("--max-steps", type=int, default=None)
parser.add_argument("--max-samples", type=int, default=None)
parser.add_argument("--epochs", type=int, default=2)
parser.add_argument("--gradient-accumulation-steps", type=int, default=16)
parser.add_argument("--save-steps", type=int, default=25)
parser.add_argument("--resume-from-checkpoint")
args = parser.parse_args()

output = Path(args.output)
if output.exists() and any(output.iterdir()) and not args.resume_from_checkpoint:
    raise SystemExit(f"refusing to overwrite non-empty output: {output}")
if args.resume_from_checkpoint and not Path(args.resume_from_checkpoint).is_dir():
    raise SystemExit(f"checkpoint does not exist: {args.resume_from_checkpoint}")

trainer = create_sft_trainer(
    model_name=args.model,
    dataset_name=args.dataset,
    config_name="sft_messages",
    backend="trl",
    output_dir=str(output),
    num_epochs=args.epochs,
    batch_size=1,
    learning_rate=1e-4,
    max_seq_length=1024,
    max_samples=args.max_samples,
    max_steps=args.max_steps,
    seed=20261112,
    fp16=True,
    use_peft=True,
    lora_r=32,
    lora_alpha=64,
    lora_dropout=0.05,
    lora_target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    gradient_accumulation_steps=args.gradient_accumulation_steps,
    gradient_checkpointing=True,
    # AlignTune materializes conversational rows as explicit prompt/completion
    # pairs. TRL masks the prompt in this path. Tiny Aya exposes a dict of
    # named chat templates, which is incompatible with TRL's
    # assistant_only_loss generation-marker check (it assumes a string).
    assistant_only_loss=False,
    completion_only_loss=True,
    eval_strategy="no",
    load_best_model_at_end=False,
    save_steps=args.save_steps,
    resume_from_checkpoint=args.resume_from_checkpoint,
    logging_steps=5,
    report_to="none",
    trust_remote_code=True,
)
trainer.train()


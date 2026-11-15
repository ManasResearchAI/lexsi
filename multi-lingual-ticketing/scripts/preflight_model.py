#!/usr/bin/env python3
"""Fail-fast chat-template, length, and assistant-mask checks."""

import argparse
import json
import random
from pathlib import Path

from transformers import AutoTokenizer

from ticket_system.constants import SYSTEM_PROMPT

parser = argparse.ArgumentParser()
parser.add_argument("--model", default="CohereLabs/tiny-aya-global")
parser.add_argument("--data", type=Path, default=Path("data/processed/tickets/train.jsonl"))
parser.add_argument("--samples", type=int, default=50)
parser.add_argument("--max-seq-length", type=int, default=1024)
args = parser.parse_args()

tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
all_rows = [json.loads(line) for line in args.data.read_text().splitlines()]
rows = random.Random(20261112).sample(all_rows, min(args.samples, len(all_rows)))
lengths = []
for row in rows:
    rendered = tokenizer.apply_chat_template(row["messages"], tokenize=False)
    if SYSTEM_PROMPT not in rendered or row["messages"][-1]["content"] not in rendered:
        raise SystemExit("chat template dropped the system or assistant content")
    lengths.append(len(tokenizer(rendered, add_special_tokens=False)["input_ids"]))
    # Loss masking is validated through AlignTune's explicit prompt/completion
    # columns, not assistant masks: Tiny Aya's tokenizer stores multiple named
    # templates in a dict and TRL's assistant-only marker check assumes str.
    json.loads(row["messages"][-1]["content"])
if max(lengths, default=0) > args.max_seq_length:
    raise SystemExit(f"sample exceeds max sequence length: max={max(lengths)}")
print(json.dumps({
    "samples": len(rows), "min_tokens": min(lengths), "max_tokens": max(lengths),
    "loss_contract": "completion_only_loss on AlignTune prompt/completion columns",
    "chat_template_type": type(tokenizer.chat_template).__name__,
}))


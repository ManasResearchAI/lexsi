#!/usr/bin/env python3
"""Create prompt-only GRPO data from curated message rows."""

import argparse
import json
from pathlib import Path

from ticket_system.constants import SYSTEM_PROMPT
from ticket_system.prompt import task_prompt
from ticket_system.schema import FULL_SCHEMA

parser = argparse.ArgumentParser()
parser.add_argument("--input", type=Path, default=Path("data/processed/tickets/train.jsonl"))
parser.add_argument("--output", type=Path, default=Path("data/processed/grpo/train.jsonl"))
args = parser.parse_args()
args.output.parent.mkdir(parents=True, exist_ok=True)
with args.input.open(encoding="utf-8") as source, args.output.open("w", encoding="utf-8") as target:
    for line in source:
        row = json.loads(line)
        target.write(json.dumps({
            "prompt": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": task_prompt(
                    row["text"], [field for field in FULL_SCHEMA["properties"] if field != "escalate"]
                )},
            ],
            "id": row["id"],
        }, ensure_ascii=False) + "\n")


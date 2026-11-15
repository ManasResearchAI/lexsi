"""Stable prompts shared by training, evaluation, and serving."""

from __future__ import annotations

import json
from typing import Iterable

from .constants import SYSTEM_PROMPT
from .schema import PARTIAL_SCHEMA


def task_prompt(text: str, fields: Iterable[str]) -> str:
    requested = list(fields)
    field_schema = {
        **PARTIAL_SCHEMA,
        "required": requested,
        "properties": {key: PARTIAL_SCHEMA["properties"][key] for key in requested},
        "minProperties": len(requested),
    }
    return (
        f"Requested fields: {', '.join(requested)}\n"
        f"Schema: {json.dumps(field_schema, ensure_ascii=False, separators=(',', ':'))}\n"
        f"Customer message:\n{text}"
    )


def messages(text: str, target: dict, fields: Iterable[str]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task_prompt(text, fields)},
        {"role": "assistant", "content": json.dumps(target, ensure_ascii=False, separators=(",", ":"))},
    ]


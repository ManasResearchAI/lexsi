"""Canonical full and partial-label ticket schemas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .constants import ENTITY_TYPES, INTENTS, LANGUAGES, SENTIMENTS

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "ticket.schema.json"


def ticket_schema(*, partial: bool = False) -> dict[str, Any]:
    properties: dict[str, Any] = {
        "language": {"enum": list(LANGUAGES)},
        "domain": {"enum": ["banking", "home", "kitchen_dining", "travel", "utility"]},
        "intent": {"enum": list(INTENTS)},
        "sentiment": {"enum": list(SENTIMENTS)},
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["type", "text"],
                "properties": {
                    "type": {"enum": list(ENTITY_TYPES)},
                    "text": {"type": "string", "minLength": 1},
                },
            },
        },
        "redacted_text": {"type": "string"},
        "escalate": {"type": "boolean"},
        "injection_detected": {"type": "boolean"},
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "PartialTicket" if partial else "Ticket",
        "type": "object",
        "additionalProperties": False,
        # Escalation is derived by serving policy and injection detection is
        # supervised only on adversarial rows, so neither is globally required.
        "required": [] if partial else [
            key for key in properties if key not in {"escalate", "injection_detected"}
        ],
        "minProperties": 1,
        "properties": properties,
    }


FULL_SCHEMA = ticket_schema()
PARTIAL_SCHEMA = ticket_schema(partial=True)


def validate_ticket(value: dict[str, Any], *, partial: bool = False) -> None:
    Draft202012Validator(PARTIAL_SCHEMA if partial else FULL_SCHEMA).validate(value)


def write_schema(path: Path = SCHEMA_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(FULL_SCHEMA, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


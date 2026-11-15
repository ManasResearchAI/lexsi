"""Canonical curated-row construction and validation."""

from __future__ import annotations

from typing import Any

from .prompt import messages
from .schema import validate_ticket
from .text import normalized_text, stable_id


def make_record(
    *, source: str, language: str, split: str, source_id: str, text: str,
    target: dict[str, Any], licence: str, metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validate_ticket(target, partial=True)
    fields = list(target)
    row_id = stable_id(source, language, split, source_id, text)
    return {
        "id": row_id,
        "source": source,
        "source_id": source_id,
        "language": language,
        "split": split,
        "text": text,
        "text_normalized": normalized_text(text),
        "labelled_fields": fields,
        "target": target,
        "messages": messages(text, target, fields),
        "licence": licence,
        "metadata": metadata or {},
    }


"""Text, span, redaction, and stable-ID utilities."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Iterable


def normalized_text(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).casefold().split())


def stable_id(source: str, language: str, split: str, source_id: str, text: str) -> str:
    body = "\x1f".join((source, language, split, source_id, normalized_text(text)))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:24]


def byte_slice(text: str, start: int, end: int) -> str:
    """Slice a UTF-8 string using half-open byte offsets."""
    encoded = text.encode("utf-8")
    if not (0 <= start <= end <= len(encoded)):
        raise ValueError(f"invalid UTF-8 byte span [{start}, {end}) for {len(encoded)} bytes")
    try:
        return encoded[start:end].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"span [{start}, {end}) splits a UTF-8 code point") from exc


def injongo_slice(text: str, start: int, end: int) -> str:
    """Slice INJONGO's misnamed ``*_byte`` offsets.

    The upstream fields are named ``start_byte`` and ``limit_byte``, but its
    Yoruba examples (for example ``Bá Tunde`` with start 3) demonstrate that
    the values are Unicode code-point indices.
    """
    if not (0 <= start <= end <= len(text)):
        raise ValueError(f"invalid INJONGO character span [{start}, {end})")
    return text[start:end]


def redact_entities(text: str, entities: Iterable[dict[str, str]]) -> str:
    """Redact exact sensitive strings, longest first, without regex interpretation."""
    replacements = [e for e in entities if e["type"] in {"PER", "PHONE", "ORDER_ID"}]
    replacements.sort(key=lambda e: len(e["text"]), reverse=True)
    result = text
    for entity in replacements:
        result = re.sub(re.escape(entity["text"]), f"[{entity['type']}]", result)
    return result


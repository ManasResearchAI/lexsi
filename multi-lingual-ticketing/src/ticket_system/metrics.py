"""Deterministic field-aware evaluation for partial-label fixtures."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from typing import Any, Iterable

from jsonschema import ValidationError

from .constants import SENTIMENTS
from .schema import validate_ticket


def parse_prediction(text: str | dict[str, Any]) -> dict[str, Any] | None:
    if isinstance(text, dict):
        return text
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else None
    except (TypeError, json.JSONDecodeError):
        return None


def _entity_counter(values: Iterable[dict[str, str]]) -> Counter[tuple[str, str]]:
    if not isinstance(values, list):
        return Counter()
    return Counter(
        (v["type"], v["text"])
        for v in values
        if isinstance(v, dict)
        and isinstance(v.get("type"), str)
        and isinstance(v.get("text"), str)
    )


def evaluate_records(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    totals: Counter[str] = Counter()
    correct: Counter[str] = Counter()
    entity_tp = entity_fp = entity_fn = pii_tp = pii_fn = 0
    sentiment_confusion: Counter[tuple[str, str]] = Counter()
    per_language: dict[str, Counter[str]] = defaultdict(Counter)
    rows = list(records)
    for row in rows:
        gold = row["target"]
        pred = parse_prediction(row.get("prediction"))
        totals["json_parse"] += 1
        if pred is None:
            continue
        correct["json_parse"] += 1
        totals["schema"] += 1
        try:
            validate_ticket(pred, partial=True)
            correct["schema"] += 1
        except ValidationError:
            pass
        language = row.get("language", gold.get("language", "unknown"))
        for field in ("language", "domain", "intent", "sentiment", "redacted_text", "escalate"):
            if field in gold:
                totals[field] += 1
                per_language[language][f"{field}_n"] += 1
                if pred.get(field) == gold[field]:
                    correct[field] += 1
                    per_language[language][f"{field}_correct"] += 1
                if field == "sentiment" and pred.get(field) in SENTIMENTS:
                    sentiment_confusion[(gold[field], pred[field])] += 1
        if "entities" in gold:
            gold_c, pred_c = _entity_counter(gold["entities"]), _entity_counter(pred.get("entities", []))
            overlap = gold_c & pred_c
            entity_tp += sum(overlap.values())
            entity_fp += sum((pred_c - gold_c).values())
            entity_fn += sum((gold_c - pred_c).values())
            gold_pii = Counter(k for k, n in gold_c.items() for _ in range(n) if k[0] in {"PER", "PHONE", "ORDER_ID"})
            pred_pii = Counter(k for k, n in pred_c.items() for _ in range(n) if k[0] in {"PER", "PHONE", "ORDER_ID"})
            pii_tp += sum((gold_pii & pred_pii).values())
            pii_fn += sum((gold_pii - pred_pii).values())
    precision = entity_tp / max(1, entity_tp + entity_fp)
    recall = entity_tp / max(1, entity_tp + entity_fn)
    sentiment_f1s = []
    for label in SENTIMENTS:
        tp = sentiment_confusion[(label, label)]
        fp = sum(sentiment_confusion[(gold, label)] for gold in SENTIMENTS if gold != label)
        fn = sum(sentiment_confusion[(label, predicted)] for predicted in SENTIMENTS if predicted != label)
        if tp + fp + fn:
            sentiment_f1s.append(2 * tp / max(1, 2 * tp + fp + fn))
    return {
        "sample_count": len(rows),
        "json_parse_rate": correct["json_parse"] / max(1, totals["json_parse"]),
        "schema_valid_rate": correct["schema"] / max(1, totals["schema"]),
        **{f"{field}_accuracy": correct[field] / count for field, count in totals.items() if field not in {"json_parse", "schema"}},
        "entity_precision": precision,
        "entity_recall": recall,
        "entity_f1": 2 * precision * recall / max(1e-12, precision + recall),
        "pii_recall": pii_tp / max(1, pii_tp + pii_fn),
        **({"sentiment_macro_f1": sum(sentiment_f1s) / len(sentiment_f1s)} if sentiment_f1s else {}),
        "per_language": {key: dict(value) for key, value in per_language.items()},
    }


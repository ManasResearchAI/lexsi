#!/usr/bin/env python3
"""Dependency-free language/majority/regex baseline for a measured floor."""

import argparse
import json
import math
import re
import time
from collections import Counter, defaultdict
from pathlib import Path

from ticket_system.constants import INTENT_TO_DOMAIN, LANGUAGES
from ticket_system.metrics import evaluate_records
from ticket_system.text import redact_entities

parser = argparse.ArgumentParser()
parser.add_argument("--train", type=Path, default=Path("data/processed/tickets/train.jsonl"))
parser.add_argument("--test", type=Path, default=Path("data/processed/tickets/test.jsonl"))
parser.add_argument("--output", type=Path, default=Path("artifacts/evidence/majority-baseline"))
args = parser.parse_args()


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def grams(text):
    compact = f"  {text.casefold()}  "
    return {compact[i:i + 3] for i in range(len(compact) - 2)}


train, test = read(args.train), read(args.test)
language_grams = defaultdict(Counter)
intent_counts = defaultdict(Counter)
sentiment_counts = defaultdict(Counter)
global_sentiment = Counter()
for row in train:
    language_grams[row["language"]].update(grams(row["text"]))
    if "intent" in row["target"]:
        intent_counts[row["language"]][row["target"]["intent"]] += 1
    if "sentiment" in row["target"]:
        sentiment_counts[row["language"]][row["target"]["sentiment"]] += 1
        global_sentiment[row["target"]["sentiment"]] += 1


def language(text):
    observed = grams(text)
    return max(LANGUAGES, key=lambda lang: sum(math.log1p(language_grams[lang][g]) for g in observed))


phone_re = re.compile(r"(?:\+?\d[\d -]{7,}\d)")
order_re = re.compile(r"\b(?:NG|TZ|EN)-\d{6}\b")
amount_re = re.compile(r"(?:₦\s?\d[\d,]*|TSh\s?\d[\d,]*|\$\s?\d[\d,]*)")

predictions = []
for row in test:
    started = time.perf_counter()
    lang = language(row["text"])
    intent = intent_counts[lang].most_common(1)[0][0]
    sentiment = (sentiment_counts[lang] or global_sentiment).most_common(1)[0][0]
    entities = [
        *({"type": "PHONE", "text": match.group()} for match in phone_re.finditer(row["text"])),
        *({"type": "ORDER_ID", "text": match.group()} for match in order_re.finditer(row["text"])),
        *({"type": "AMOUNT", "text": match.group()} for match in amount_re.finditer(row["text"])),
    ]
    full = {
        "language": lang, "domain": INTENT_TO_DOMAIN[intent], "intent": intent,
        "sentiment": sentiment, "entities": entities,
        "redacted_text": redact_entities(row["text"], entities), "escalate": False,
    }
    prediction = {field: full[field] for field in row["labelled_fields"]}
    predictions.append({
        **row, "prediction": prediction,
        "raw_response": json.dumps(prediction, ensure_ascii=False),
        "latency_seconds": time.perf_counter() - started,
    })

args.output.mkdir(parents=True, exist_ok=False)
with (args.output / "predictions.jsonl").open("w", encoding="utf-8") as handle:
    for row in predictions:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
manifest = json.loads((args.test.parent / "manifest.json").read_text())
metrics = {**evaluate_records(predictions), "fixture_sha256": manifest["fixture_sha256"], "model": "char-trigram-language + per-language-majority + regex"}
(args.output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
print(json.dumps(metrics, indent=2))


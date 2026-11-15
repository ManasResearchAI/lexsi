"""Native-data ingestion, leakage-safe curation, and deterministic PII synthesis."""

from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Iterator

from .constants import INJONGO_ENTITY_MAP, INTENT_TO_DOMAIN
from .records import make_record
from .text import injongo_slice, normalized_text, redact_entities

LANG_CONFIGS = {"yor": "yor", "swa": "swa", "eng": "eng"}
NER_TAGS = ("O", "B-PER", "I-PER", "B-ORG", "I-ORG", "B-LOC", "I-LOC", "B-DATE", "I-DATE")


def _jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def injongo_rows(root: Path, languages: Iterable[str] = LANG_CONFIGS) -> Iterator[dict[str, Any]]:
    split_files = {"train": "train.jsonl", "validation": "dev.jsonl", "test": "test.jsonl"}
    for language in languages:
        for split, filename in split_files.items():
            path = root / "InjongoIntent" / language / filename
            if not path.exists():
                continue  # English has no dev file in the upstream snapshot.
            for raw in _jsonl(path):
                intent = raw["intent"]
                if intent not in INTENT_TO_DOMAIN:
                    raise ValueError(f"unknown INJONGO intent: {intent}")
                entities = []
                for span in raw.get("spans", []):
                    mapped = INJONGO_ENTITY_MAP.get(span["label"])
                    if mapped:
                        entity_text = injongo_slice(
                            raw["text"], span["start_byte"], span["limit_byte"]
                        )
                        if entity_text not in raw.get("target", ""):
                            raise ValueError(
                                f"INJONGO span mismatch in {raw['example_id']}: {entity_text!r}"
                            )
                        entities.append({
                            "type": mapped,
                            "text": entity_text,
                        })
                target = {
                    "language": language,
                    "domain": INTENT_TO_DOMAIN[intent],
                    "intent": intent,
                    "entities": entities,
                    "redacted_text": redact_entities(raw["text"], entities),
                }
                yield make_record(
                    source="injongo", language=language, split=split,
                    source_id=raw["example_id"], text=raw["text"], target=target,
                    licence="CC-BY-4.0",
                    metadata={"upstream_slot_count": len(raw.get("spans", []))},
                )


def sentiment_rows(dataset: Any, language: str) -> Iterator[dict[str, Any]]:
    for split, rows in dataset.items():
        canonical_split = "validation" if split in {"dev", "validation"} else split
        for index, raw in enumerate(rows):
            label = raw["label"]
            if isinstance(label, int):
                names = rows.features["label"].names
                label = names[label]
            text = raw.get("tweet", raw.get("text"))
            yield make_record(
                source="afrisenti", language=language, split=canonical_split,
                source_id=str(raw.get("id", index)), text=text,
                target={"language": language, "sentiment": str(label).lower()},
                licence="CC-BY-4.0",
            )


def _bio_entities(tokens: list[str], tags: list[int | str]) -> list[dict[str, str]]:
    names = [NER_TAGS[tag] if isinstance(tag, int) else tag for tag in tags]
    entities: list[dict[str, str]] = []
    current_type: str | None = None
    current_tokens: list[str] = []
    for token, tag in [*zip(tokens, names), ("", "O")]:
        prefix, _, entity_type = tag.partition("-")
        if current_type and (prefix != "I" or entity_type != current_type):
            entities.append({"type": current_type, "text": " ".join(current_tokens)})
            current_type, current_tokens = None, []
        if prefix == "B":
            current_type, current_tokens = entity_type, [token]
        elif prefix == "I" and current_type == entity_type:
            current_tokens.append(token)
    return entities


def ner_rows(dataset: Any, language: str) -> Iterator[dict[str, Any]]:
    for split, rows in dataset.items():
        canonical_split = "validation" if split in {"dev", "validation"} else split
        for index, raw in enumerate(rows):
            tokens = list(raw["tokens"])
            text = " ".join(tokens)
            entities = _bio_entities(tokens, list(raw["ner_tags"]))
            yield make_record(
                source="masakhaner2", language=language, split=canonical_split,
                source_id=str(raw.get("id", index)), text=text,
                target={
                    "language": language,
                    "entities": entities,
                    "redacted_text": redact_entities(text, entities),
                },
                licence="CC-4.0-NC",
            )


def templated_pii(rows: Iterable[dict[str, Any]], seed: int = 20261112) -> Iterator[dict[str, Any]]:
    """Add deterministically labelled PII only to banking/utility INJONGO rows."""
    rng = random.Random(seed)
    templates = {
        "yor": (" Iye naa ni {amount}, oda {order}, foonu {phone}.", "₦{n:,}", "NG-{oid}", "+234{phone}"),
        "swa": (" Kiasi ni {amount}, oda {order}, simu {phone}.", "TSh {n:,}", "TZ-{oid}", "+255{phone}"),
        "eng": (" Amount {amount}, order {order}, phone {phone}.", "${n:,}", "EN-{oid}", "+1{phone}"),
    }
    for row in rows:
        if row["source"] != "injongo" or row["target"]["domain"] not in {"banking", "utility"}:
            continue
        suffix, amount_fmt, order_fmt, phone_fmt = templates[row["language"]]
        n = rng.choice((1250, 5000, 12500, 75000, 250000))
        oid = f"{rng.randrange(100000, 999999)}"
        phone_digits = f"{rng.randrange(100000000, 999999999)}"
        values = {
            "amount": amount_fmt.format(n=n),
            "order": order_fmt.format(oid=oid),
            "phone": phone_fmt.format(phone=phone_digits),
        }
        text = row["text"] + suffix.format(**values)
        entities = list(row["target"].get("entities", [])) + [
            {"type": "AMOUNT", "text": values["amount"]},
            {"type": "ORDER_ID", "text": values["order"]},
            {"type": "PHONE", "text": values["phone"]},
        ]
        target = dict(row["target"])
        target["entities"] = entities
        target["redacted_text"] = redact_entities(text, entities)
        yield make_record(
            source="injongo_templated_pii", language=row["language"], split=row["split"],
            source_id=row["source_id"], text=text, target=target, licence="CC-BY-4.0 + generated",
            metadata={"template_seed": seed, "parent_id": row["id"]},
        )


def _digest_rows(rows: Iterable[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        digest.update((json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode())
    return digest.hexdigest()


def curate(rows: Iterable[dict[str, Any]], output_dir: Path) -> dict[str, Any]:
    """Freeze held-out splits, then exact-deduplicate/filter train only."""
    all_rows = list(rows)
    heldout_text = {r["text_normalized"] for r in all_rows if r["split"] != "train"}
    seen_train: set[str] = set()
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for row in all_rows:
        reason = None
        if row["split"] == "train":
            key = row["text_normalized"]
            if key in heldout_text:
                reason = "cross_split_exact_match"
            elif key in seen_train:
                reason = "train_exact_duplicate"
            seen_train.add(key)
        (rejected if reason else accepted).append({**row, **({"rejection_reason": reason} if reason else {})})

    output_dir.mkdir(parents=True, exist_ok=True)
    by_split = {split: [r for r in accepted if r["split"] == split] for split in ("train", "validation", "test")}
    for split, split_rows in by_split.items():
        path = output_dir / f"{split}.jsonl"
        with path.open("w", encoding="utf-8") as handle:
            for row in split_rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    with (output_dir / "rejected.jsonl").open("w", encoding="utf-8") as handle:
        for row in rejected:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    manifest = {
        "schema": "multilingual-ticketing.dataset-manifest/1",
        "seed": 20261112,
        "split_policy": "official upstream splits frozen; filtering and exact dedup train-only",
        "counts": {split: len(rows_) for split, rows_ in by_split.items()},
        "rejected": Counter(r["rejection_reason"] for r in rejected),
        "sources": sorted({r["source"] for r in accepted}),
        "languages": sorted({r["language"] for r in accepted}),
        "licences": sorted({r["licence"] for r in accepted}),
        "fixture_sha256": _digest_rows(r for r in accepted if r["split"] != "train"),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, default=dict) + "\n", encoding="utf-8"
    )
    return manifest


def load_hf_sources() -> list[dict[str, Any]]:
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise RuntimeError("Install the data extra: pip install -e '.[data]'") from exc
    rows: list[dict[str, Any]] = []
    for language in ("yor", "swa"):
        splits = ("train", "validation", "test")
        # Datasets >=4 no longer executes dataset scripts. Read the Hub's
        # official Parquet conversion revision so this remains reproducible.
        afri_files = {
            split: (
                "https://huggingface.co/datasets/shmuhammad/"
                "AfriSenti-twitter-sentiment/resolve/refs%2Fconvert%2Fparquet/"
                f"{language}/{split}/0000.parquet"
            ) for split in splits
        }
        ner_files = {
            split: (
                "https://huggingface.co/datasets/masakhane/masakhaner2/resolve/"
                f"refs%2Fconvert%2Fparquet/{language}/{split}/0000.parquet"
            ) for split in splits
        }
        rows.extend(sentiment_rows(load_dataset("parquet", data_files=afri_files), language))
        rows.extend(ner_rows(load_dataset("parquet", data_files=ner_files), language))
    return rows


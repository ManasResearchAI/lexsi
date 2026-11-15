import json

from ticket_system.curate import _bio_entities, curate
from ticket_system.records import make_record


def row(source_id, split, text):
    return make_record(
        source="fixture", language="eng", split=split, source_id=source_id, text=text,
        target={"language": "eng"}, licence="test-only",
    )


def test_bio_conversion_closes_entities():
    entities = _bio_entities(["Ada", "Lovelace", "in", "Lagos"], [1, 2, 0, 5])
    assert entities == [
        {"type": "PER", "text": "Ada Lovelace"},
        {"type": "LOC", "text": "Lagos"},
    ]


def test_train_only_dedup_never_mutates_heldout(tmp_path):
    manifest = curate([
        row("a", "train", "same"), row("b", "train", "same"),
        row("c", "validation", "frozen"), row("d", "test", "same"),
    ], tmp_path)
    assert manifest["counts"] == {"train": 0, "validation": 1, "test": 1}
    rejected = [json.loads(x) for x in (tmp_path / "rejected.jsonl").read_text().splitlines()]
    assert {r["rejection_reason"] for r in rejected} == {"cross_split_exact_match"}


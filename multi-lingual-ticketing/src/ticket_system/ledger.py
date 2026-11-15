"""Machine-readable before/after evidence ledger."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_ledger(before_path: Path, after_path: Path, output_path: Path) -> dict[str, Any]:
    before = json.loads(before_path.read_text())
    after = json.loads(after_path.read_text())
    metrics = sorted(set(before) & set(after))
    entries = []
    for name in metrics:
        if isinstance(before[name], (int, float)) and isinstance(after[name], (int, float)):
            entries.append({
                "metric": name, "before": before[name], "after": after[name],
                "delta": after[name] - before[name],
            })
    ledger = {
        "schema": "multilingual-ticketing.metric-ledger/1",
        "before": {"path": str(before_path), "sha256": file_sha256(before_path)},
        "after": {"path": str(after_path), "sha256": file_sha256(after_path)},
        "sample_count": after.get("sample_count"),
        "fixture_sha256": after.get("fixture_sha256"),
        "status": "measured",
        "metrics": entries,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(ledger, indent=2) + "\n")
    return ledger


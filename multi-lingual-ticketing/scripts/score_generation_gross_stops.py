#!/usr/bin/env python3
"""Score predeclared empty-output and repetition gross stops from predictions."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def rep4(text: str) -> float:
    """Fraction of repeated whitespace-tokenized four-grams."""
    words = text.split()
    grams = [tuple(words[index : index + 4]) for index in range(len(words) - 3)]
    return 1 - len(set(grams)) / len(grams) if grams else 0.0


def score(label: str, path: Path) -> dict[str, object]:
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    responses = [str(row.get("raw_response") or "").strip() for row in rows]
    repetition = [rep4(response) for response in responses]
    empty_rate = sum(not response for response in responses) / max(1, len(rows))
    severe_rate = sum(value > 0.3 for value in repetition) / max(1, len(rows))
    return {
        "label": label,
        "prediction_path": str(path),
        "prediction_file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "sample_count": len(rows),
        "empty_output_rate": empty_rate,
        "rep4_mean": sum(repetition) / max(1, len(repetition)),
        "severe_repetition_rate": severe_rate,
        "passes_empty_output_gate": empty_rate <= 0.01,
        "passes_severe_repetition_gate": severe_rate <= 0.02,
        "passes_gross_stops": empty_rate <= 0.01 and severe_rate <= 0.02,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate",
        action="append",
        required=True,
        metavar="LABEL=PATH",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    results = []
    for candidate in args.candidate:
        label, separator, raw_path = candidate.partition("=")
        if not separator or not label or not raw_path:
            parser.error(f"invalid candidate {candidate!r}; expected LABEL=PATH")
        results.append(score(label, Path(raw_path)))

    payload = {
        "schema": "multilingual-ticketing.gross-stop-report/1",
        "definition": {
            "empty_output": "raw_response is empty after whitespace stripping",
            "rep4": "1 - unique whitespace-tokenized 4-grams / all 4-grams",
            "severe_repetition": "rep4 > 0.3",
        },
        "thresholds": {
            "empty_output_rate_max": 0.01,
            "severe_repetition_rate_max": 0.02,
        },
        "status": "automatic_generation_diagnostic_not_human_quality_judgment",
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise SystemExit(f"refusing to overwrite existing output: {args.output}")
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

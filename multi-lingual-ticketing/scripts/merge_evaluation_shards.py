#!/usr/bin/env python3
"""Merge deterministic prefix/suffix generation shards and recompute metrics."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from ticket_system.metrics import evaluate_records


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--prefix", type=Path, required=True)
    parser.add_argument("--prefix-count", type=int, required=True)
    parser.add_argument("--suffix", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--max-new-tokens", type=int, default=384)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.output.exists():
        raise SystemExit(f"refusing to overwrite existing output: {args.output}")
    fixture = read_jsonl(args.fixture)
    prefix = read_jsonl(args.prefix)[: args.prefix_count]
    suffix = read_jsonl(args.suffix)
    merged = [*prefix, *suffix]
    fixture_ids = [row["id"] for row in fixture]
    merged_ids = [row["id"] for row in merged]
    if merged_ids != fixture_ids:
        for index, (expected, actual) in enumerate(
            zip(fixture_ids, merged_ids, strict=False)
        ):
            if expected != actual:
                raise SystemExit(
                    f"merged ID mismatch at row {index}: expected={expected} actual={actual}"
                )
        raise SystemExit(
            f"merged length mismatch: fixture={len(fixture_ids)} merged={len(merged_ids)}"
        )

    metrics = {
        **evaluate_records(merged),
        "fixture_sha256": hashlib.sha256(args.fixture.read_bytes()).hexdigest(),
        "model": args.model,
        "model_revision": args.revision,
        "adapter": args.adapter,
        "max_new_tokens": args.max_new_tokens,
        "capped_output_rate": sum(
            row["output_tokens"] >= args.max_new_tokens for row in merged
        )
        / max(1, len(merged)),
        "generation_shards": {
            "prefix_file_sha256": hashlib.sha256(args.prefix.read_bytes()).hexdigest(),
            "prefix_rows_used": args.prefix_count,
            "suffix_file_sha256": hashlib.sha256(args.suffix.read_bytes()).hexdigest(),
            "suffix_rows_used": len(suffix),
        },
    }
    args.output.mkdir(parents=True)
    (args.output / "predictions.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in merged),
        encoding="utf-8",
    )
    (args.output / "metrics.json").write_text(
        json.dumps(metrics, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()

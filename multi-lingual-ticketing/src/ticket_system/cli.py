"""Small dependency-light command line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .curate import curate, injongo_rows, load_hf_sources, templated_pii
from .ledger import build_ledger
from .metrics import evaluate_records
from .schema import write_schema


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main() -> None:
    parser = argparse.ArgumentParser(prog="ticket-system")
    sub = parser.add_subparsers(dest="command", required=True)
    schema = sub.add_parser("write-schema")
    schema.add_argument("--output", type=Path, default=Path("schemas/ticket.schema.json"))
    build = sub.add_parser("build-data")
    build.add_argument("--injongo-root", type=Path, default=Path("data/raw/masakhane-nlu"))
    build.add_argument("--output", type=Path, default=Path("data/processed/tickets"))
    build.add_argument("--with-hf", action="store_true")
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("predictions", type=Path)
    evaluate.add_argument("--output", type=Path, required=True)
    ledger = sub.add_parser("ledger")
    ledger.add_argument("before", type=Path)
    ledger.add_argument("after", type=Path)
    ledger.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "write-schema":
        write_schema(args.output)
    elif args.command == "build-data":
        base = list(injongo_rows(args.injongo_root))
        rows = [*base, *templated_pii(base)]
        if args.with_hf:
            rows.extend(load_hf_sources())
        print(json.dumps(curate(rows, args.output), indent=2, default=dict))
    elif args.command == "evaluate":
        metrics = evaluate_records(_read_jsonl(args.predictions))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(metrics, indent=2) + "\n")
    elif args.command == "ledger":
        print(json.dumps(build_ledger(args.before, args.after, args.output), indent=2))


if __name__ == "__main__":
    main()


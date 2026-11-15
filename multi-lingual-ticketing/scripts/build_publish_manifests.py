#!/usr/bin/env python3
"""Write deterministic size/hash manifests for local publication packages."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


FORBIDDEN_MODEL_FILES = {
    "optimizer.pt",
    "scheduler.pt",
    "rng_state.pth",
    "trainer_state.json",
    "scaler.pt",
}
MODEL_ALLOWLIST = {
    "README.md",
    "adapter_config.json",
    "adapter_model.safetensors",
    "chat_template.jinja",
    "tokenizer.json",
    "tokenizer_config.json",
}


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--type", choices=("model", "dataset", "space"), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.package.resolve()
    if not root.is_dir():
        parser.error(f"not a package directory: {root}")

    paths = sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
    )
    relative = [path.relative_to(root).as_posix() for path in paths]
    forbidden = sorted(path for path in relative if Path(path).name in FORBIDDEN_MODEL_FILES)
    unexpected = sorted(path for path in relative if "/" in path or Path(path).name not in MODEL_ALLOWLIST)
    if args.type == "model" and (forbidden or unexpected):
        raise SystemExit(
            f"model package allowlist failure: forbidden={forbidden}, unexpected={unexpected}"
        )

    files = [
        {"path": rel, "bytes": path.stat().st_size, "sha256": digest(path)}
        for path, rel in zip(paths, relative, strict=True)
    ]
    payload = {
        "schema": "multilingual-ticketing.publish-file-manifest/1",
        "package": root.name,
        "package_type": args.type,
        "file_count": len(files),
        "payload_bytes": sum(item["bytes"] for item in files),
        "forbidden_model_files_present": forbidden,
        "model_allowlist_passed": args.type != "model" or not unexpected,
        "files": files,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output_dir / f"{root.name}.FILE_MANIFEST.json"
    sums_path = args.output_dir / f"{root.name}.SHA256SUMS"
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    sums_path.write_text(
        "".join(f"{item['sha256']}  {item['path']}\n" for item in files),
        encoding="utf-8",
    )
    print(json.dumps({key: payload[key] for key in ("package", "file_count", "payload_bytes")}))


if __name__ == "__main__":
    main()

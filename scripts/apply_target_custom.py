#!/usr/bin/env python3
"""Apply feed-manifest version data before delegated signers sign metadata."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]


def canonical_write(path: Path, document: dict) -> None:
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    manifest = json.loads((ROOT / "feed-manifest.json").read_text(encoding="utf-8"))
    changed = 0
    for target in manifest["targets"]:
        target_path = PurePosixPath(target["path"])
        role = target_path.parts[0]
        metadata_path = ROOT / "metadata" / f"{role}.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        entry = metadata["signed"]["targets"].get(target_path.as_posix())
        if entry is None:
            raise SystemExit(f"TUF-on-CI has not generated metadata for {target_path}")
        custom = {
            "schema_version": 1,
            "target_id": target["target_id"],
            "target_type": target["target_type"],
            "version": target["version"],
            "sequence": target["sequence"],
            "max_bytes": target["max_bytes"],
        }
        if entry.get("custom") != custom:
            entry["custom"] = custom
            metadata["signatures"] = []
            canonical_write(metadata_path, metadata)
            changed += 1
    print(json.dumps({"metadata_files_changed": changed, "requires_signatures": bool(changed)}, sort_keys=True))


if __name__ == "__main__":
    main()

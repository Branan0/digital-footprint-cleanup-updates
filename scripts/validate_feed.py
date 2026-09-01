#!/usr/bin/env python3
"""Fail-closed validation before a TUF repository can be published."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, date, datetime
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
TARGET_TYPES = {"catalogue", "adapter", "jurisdiction", "dataset", "tool"}
AUTHORITY_TYPES = {"regulator", "government", "statute", "court", "provider"}
SAFE_ID = re.compile(r"[a-z0-9][a-z0-9._-]{0,79}")
SAFE_VERSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,63}")


def https(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    return (
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and not parsed.username
        and not parsed.password
    )


def load(path: Path):
    if (
        path.is_symlink()
        or not path.is_file()
        or path.stat().st_size > 100 * 1024 * 1024
    ):
        raise ValueError(f"unsafe or missing file: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_jurisdiction(path: Path, expected_code: str) -> None:
    pack = load(path)
    required = {
        "schema_version",
        "iso_code",
        "country_name",
        "pack_version",
        "language",
        "rights_state",
        "rights",
        "authoritative_sources",
        "routes",
        "templates",
        "english_explanation",
        "effective_at",
        "reviewed_at",
        "review_due_at",
    }
    if (
        not isinstance(pack, dict)
        or set(pack) != required
        or pack["schema_version"] != 1
    ):
        raise ValueError(f"invalid jurisdiction schema: {expected_code}")
    if pack["iso_code"] != expected_code or not isinstance(pack["country_name"], str):
        raise ValueError(f"jurisdiction identity mismatch: {expected_code}")
    if pack["rights_state"] not in {"verified_rights", "no_specific_right"}:
        raise ValueError(f"invalid rights state: {expected_code}")
    rights = pack["rights"]
    if not isinstance(rights, list) or (
        pack["rights_state"] == "verified_rights"
    ) != bool(rights):
        raise ValueError(f"rights evidence mismatch: {expected_code}")
    reviewed = date.fromisoformat(pack["reviewed_at"])
    due = date.fromisoformat(pack["review_due_at"])
    if due <= reviewed or due < datetime.now(UTC).date():
        raise ValueError(f"stale jurisdiction sources: {expected_code}")
    sources = pack["authoritative_sources"]
    if not isinstance(sources, list) or not sources:
        raise ValueError(f"missing authoritative sources: {expected_code}")
    for source in sources:
        if source.get("authority_type") not in AUTHORITY_TYPES or not https(
            source.get("url")
        ):
            raise ValueError(f"non-authoritative source: {expected_code}")
        date.fromisoformat(source["checked_at"])
    if (
        not isinstance(pack["english_explanation"], str)
        or not pack["english_explanation"].strip()
    ):
        raise ValueError(f"missing English explanation: {expected_code}")
    for route in pack["routes"]:
        if not https(route.get("url")):
            raise ValueError(f"unsafe route: {expected_code}")
        if (
            pack["rights_state"] == "no_specific_right"
            and route.get("route_basis") != "voluntary_provider"
        ):
            raise ValueError(f"unverified legal route: {expected_code}")
        if (
            route.get("identity_document") != "never"
            and route.get("automatic_submission_allowed") is not False
        ):
            raise ValueError(f"unsafe identity automation: {expected_code}")
    for template in pack["templates"]:
        if not https(template.get("official_url")) or not template.get(
            "english_explanation"
        ):
            raise ValueError(f"unsafe or unexplained template: {expected_code}")


def _validate(*, require_signed_metadata: bool) -> dict:
    iso_codes = load(ROOT / "schemas" / "supported-jurisdictions.json")
    if (
        not isinstance(iso_codes, list)
        or not iso_codes
        or len(set(iso_codes)) != len(iso_codes)
        or any(
            not isinstance(code, str) or not re.fullmatch(r"[A-Z]{2}", code)
            for code in iso_codes
        )
    ):
        raise ValueError(
            "supported jurisdiction baseline must contain unique ISO alpha-2 codes"
        )
    jurisdiction_dir = ROOT / "targets" / "jurisdictions"
    present = (
        {path.stem for path in jurisdiction_dir.glob("*.json")}
        if jurisdiction_dir.is_dir()
        else set()
    )
    if present != set(iso_codes):
        raise ValueError(
            f"jurisdiction coverage incomplete: {len(set(iso_codes) - present)} missing, "
            f"{len(present - set(iso_codes))} unexpected"
        )
    for code in sorted(iso_codes):
        validate_jurisdiction(jurisdiction_dir / f"{code}.json", code)

    manifest = load(ROOT / "feed-manifest.json")
    if manifest.get("schema_version") != 1 or not isinstance(
        manifest.get("targets"), list
    ):
        raise ValueError("invalid feed manifest")
    identities = set()
    paths = set()
    for target in manifest["targets"]:
        required = {
            "target_id",
            "target_type",
            "path",
            "version",
            "sequence",
            "max_bytes",
            "sha256",
        }
        if not isinstance(target, dict) or set(target) != required:
            raise ValueError("invalid target manifest entry")
        if (
            not SAFE_ID.fullmatch(target["target_id"])
            or target["target_id"] in identities
        ):
            raise ValueError("invalid or duplicate target ID")
        target_path = PurePosixPath(target["path"])
        if (
            target_path.is_absolute()
            or ".." in target_path.parts
            or target_path.parts[0]
            not in {"catalogue", "adapters", "jurisdictions", "datasets", "tools"}
            or target_path.as_posix() in paths
        ):
            raise ValueError("invalid or duplicate delegated target path")
        if target["target_type"] not in TARGET_TYPES or not SAFE_VERSION.fullmatch(
            target["version"]
        ):
            raise ValueError("invalid target type or version")
        if (
            not isinstance(target["sequence"], int)
            or isinstance(target["sequence"], bool)
            or target["sequence"] < 1
        ):
            raise ValueError("invalid target sequence")
        artifact = ROOT / "targets" / target_path
        if artifact.is_symlink() or not artifact.is_file():
            raise ValueError(f"unsafe or missing target: {target_path}")
        if (
            not isinstance(target["max_bytes"], int)
            or isinstance(target["max_bytes"], bool)
            or not 1 <= target["max_bytes"] <= 500 * 1024 * 1024
            or not isinstance(target["sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", target["sha256"])
        ):
            raise ValueError("invalid target size or digest contract")
        if artifact.stat().st_size > target["max_bytes"]:
            raise ValueError(f"target exceeds safety limit: {target_path}")
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if digest != target["sha256"]:
            raise ValueError(f"target hash mismatch: {target_path}")
        if require_signed_metadata:
            metadata = load(ROOT / "metadata" / f"{target_path.parts[0]}.json")
            signed_target = metadata["signed"]["targets"].get(target_path.as_posix())
            expected_custom = {
                key: target[key]
                for key in (
                    "target_id",
                    "target_type",
                    "version",
                    "sequence",
                    "max_bytes",
                )
            }
            expected_custom["schema_version"] = 1
            if not signed_target or signed_target.get("custom") != expected_custom:
                raise ValueError(f"signed custom metadata mismatch: {target_path}")
            if signed_target.get("hashes", {}).get("sha256") != digest:
                raise ValueError(f"signed target hash mismatch: {target_path}")
        identities.add(target["target_id"])
        paths.add(target_path.as_posix())
    required_jurisdiction_targets = {f"jurisdictions/{code}.json" for code in iso_codes}
    if not required_jurisdiction_targets <= paths:
        raise ValueError(
            "one or more jurisdiction packs are absent from the signed target manifest"
        )
    return {
        "jurisdictions": len(iso_codes),
        "targets": len(paths),
        "ready_for_signing": True,
        "publishable": require_signed_metadata,
    }


def validate_targets() -> dict:
    """Validate unsigned targets and their manifest before a signing event."""

    return _validate(require_signed_metadata=False)


def validate() -> dict:
    """Validate targets plus signed metadata before publication."""

    return _validate(require_signed_metadata=True)


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))

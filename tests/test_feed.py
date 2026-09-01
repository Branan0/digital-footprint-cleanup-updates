import hashlib
import importlib.util
import json
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_feed", SOURCE_ROOT / "scripts" / "validate_feed.py"
)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class FeedGateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "schemas").mkdir()
        (self.root / "targets" / "jurisdictions").mkdir(parents=True)
        (self.root / "metadata").mkdir()
        self.codes = json.loads(
            (SOURCE_ROOT / "schemas" / "supported-jurisdictions.json").read_text(
                encoding="utf-8"
            )
        )
        (self.root / "schemas" / "supported-jurisdictions.json").write_text(
            json.dumps(self.codes), encoding="utf-8"
        )
        self.previous_root = VALIDATOR.ROOT
        VALIDATOR.ROOT = self.root

    def tearDown(self):
        VALIDATOR.ROOT = self.previous_root
        self.temporary.cleanup()

    def _complete_feed(self):
        today = datetime.now(UTC).date()
        targets = []
        signed = {}
        for code in self.codes:
            pack = {
                "schema_version": 1,
                "iso_code": code,
                "country_name": f"Synthetic {code}",
                "pack_version": 1,
                "language": "en",
                "rights_state": "no_specific_right",
                "rights": [],
                "authoritative_sources": [
                    {
                        "title": "Synthetic official provider route",
                        "url": f"https://provider.example.test/{code.casefold()}",
                        "authority_type": "provider",
                        "language": "en",
                        "checked_at": today.isoformat(),
                    }
                ],
                "routes": [
                    {
                        "route_id": "voluntary",
                        "title": "Voluntary provider route",
                        "url": f"https://provider.example.test/{code.casefold()}/privacy",
                        "language": "en",
                        "action_types": ["legal_request"],
                        "route_basis": "voluntary_provider",
                        "minimum_disclosures": ["record_locator"],
                        "identity_document": "never",
                        "automatic_submission_allowed": False,
                    }
                ],
                "templates": [],
                "english_explanation": "No specific statutory right is claimed by this synthetic test pack.",
                "effective_at": None,
                "reviewed_at": today.isoformat(),
                "review_due_at": (today + timedelta(days=365)).isoformat(),
            }
            relative = f"jurisdictions/{code}.json"
            content = (json.dumps(pack, sort_keys=True) + "\n").encode()
            path = self.root / "targets" / relative
            path.write_bytes(content)
            digest = hashlib.sha256(content).hexdigest()
            target = {
                "target_id": f"jurisdiction-{code.casefold()}",
                "target_type": "jurisdiction",
                "version": "1",
                "sequence": 1,
                "max_bytes": 65536,
            }
            targets.append({**target, "path": relative, "sha256": digest})
            custom = {**target, "schema_version": 1}
            signed[relative] = {
                "length": len(content),
                "hashes": {"sha256": digest},
                "custom": custom,
            }
        (self.root / "feed-manifest.json").write_text(
            json.dumps(
                {
                    "repository": "synthetic",
                    "schema_version": 1,
                    "targets": targets,
                }
            ),
            encoding="utf-8",
        )
        (self.root / "metadata" / "jurisdictions.json").write_text(
            json.dumps(
                {
                    "signed": {"targets": signed},
                    "signatures": [{"keyid": "synthetic", "sig": "not-verified-here"}],
                }
            ),
            encoding="utf-8",
        )

    def test_complete_supported_pack_feed_passes_structural_publication_gate(self):
        self._complete_feed()
        result = VALIDATOR.validate()
        self.assertEqual(33, result["jurisdictions"])
        self.assertEqual(33, result["targets"])
        self.assertTrue(result["ready_for_signing"])
        self.assertTrue(result["publishable"])

    def test_unsigned_supported_pack_feed_passes_only_the_presigning_gate(self):
        self._complete_feed()
        (self.root / "metadata" / "jurisdictions.json").unlink()
        result = VALIDATOR.validate_targets()
        self.assertEqual(33, result["jurisdictions"])
        self.assertEqual(33, result["targets"])
        self.assertTrue(result["ready_for_signing"])
        self.assertFalse(result["publishable"])
        with self.assertRaisesRegex(ValueError, "unsafe or missing file"):
            VALIDATOR.validate()

    def test_one_missing_pack_blocks_publication(self):
        self._complete_feed()
        (self.root / "targets" / "jurisdictions" / "GB.json").unlink()
        with self.assertRaisesRegex(ValueError, "coverage incomplete"):
            VALIDATOR.validate()

    def test_checked_in_targets_are_ready_for_signing(self):
        original_root = VALIDATOR.ROOT
        try:
            VALIDATOR.ROOT = SOURCE_ROOT
            result = VALIDATOR.validate_targets()
        finally:
            VALIDATOR.ROOT = original_root
        self.assertEqual(33, result["jurisdictions"])
        self.assertEqual(33, result["targets"])
        self.assertTrue(result["ready_for_signing"])
        self.assertFalse(result["publishable"])


if __name__ == "__main__":
    unittest.main()

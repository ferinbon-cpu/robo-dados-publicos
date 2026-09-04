from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import scripts.verify_task091_live_ephemeral_digest_evidence as verifier


ROOT = Path(__file__).resolve().parents[1]
RELATIVE_FILES = (
    Path("docs/tasks/CODEX_TASK_091_LIVE_EPHEMERAL_DRIVE_DIGEST.md"),
    Path("docs/evidence/TASK_091_LIVE_ARTIFACT_PAYLOAD_0.8.0.json"),
    Path("docs/evidence/TASK_091_LIVE_EPHEMERAL_DRIVE_DIGEST_CLOSURE_0.8.0.json"),
    Path("docs/evidence/TASK_091_OWNER_AUTHORIZATION_0.8.0.json"),
)


def copy_fixture_tree(destination: Path) -> None:
    for relative in RELATIVE_FILES:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)


class TestTask091LiveEphemeralDigestEvidence(unittest.TestCase):
    def test_full_offline_redacted_evidence_chain(self):
        result = verifier.run()
        self.assertEqual(
            "PASS_TASK091_REDACTED_LIVE_DIGEST_EVIDENCE_OFFLINE",
            result["status"],
        )
        self.assertEqual(2, result["request_count"])
        self.assertEqual(1, result["drive_media_gets"])
        self.assertTrue(result["digest_passed_before_historical_comparison"])
        self.assertTrue(result["candidate_file_count_gate_passed"])
        self.assertTrue(result["historical_count_drift"])
        self.assertEqual("UNRESOLVED", result["root_cause_status"])
        self.assertTrue(result["remote_identifier_redacted"])
        self.assertFalse(result["full_live_workflow_source_retained"])
        self.assertFalse(result["retry_authorized"])
        self.assertFalse(result["future_execution_authorized"])
        self.assertFalse(result["live_workflow_present"])

    def test_live_workflow_reappearance_stops(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            copy_fixture_tree(root)
            live = root / ".github/workflows/task-091-live-ephemeral-drive-digest.yml"
            live.parent.mkdir(parents=True, exist_ok=True)
            live.write_text("name: forbidden\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "LIVE_WORKFLOW_STILL_PRESENT"):
                verifier.run(root)

    def test_nonzero_hard_boundary_stops_even_with_matching_blob_pin(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            copy_fixture_tree(root)
            path = root / "docs/evidence/TASK_091_LIVE_EPHEMERAL_DRIVE_DIGEST_CLOSURE_0.8.0.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["hard_boundaries"]["drive_writes"] = 1
            raw = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            path.write_bytes(raw)
            with patch.object(verifier, "EXPECTED_CLOSURE_BLOB", verifier.git_blob_sha(raw)):
                with self.assertRaisesRegex(RuntimeError, "HARD_BOUNDARY_DRIVE_WRITES"):
                    verifier.run(root)

    def test_malformed_closure_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            copy_fixture_tree(root)
            path = root / "docs/evidence/TASK_091_LIVE_EPHEMERAL_DRIVE_DIGEST_CLOSURE_0.8.0.json"
            raw = b"{not-json\n"
            path.write_bytes(raw)
            with patch.object(verifier, "EXPECTED_CLOSURE_BLOB", verifier.git_blob_sha(raw)):
                with self.assertRaises(json.JSONDecodeError):
                    verifier.run(root)

    def test_sensitive_reference_in_final_task_stops(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            copy_fixture_tree(root)
            path = root / "docs/tasks/CODEX_TASK_091_LIVE_EPHEMERAL_DRIVE_DIGEST.md"
            secret_ref = "_".join(("GOOGLE", "DRIVE", "CLIENT", "SECRET"))
            raw = path.read_bytes() + ("\n" + secret_ref + "\n").encode("utf-8")
            path.write_bytes(raw)
            with patch.object(verifier, "EXPECTED_TASK_BLOB", verifier.git_blob_sha(raw)):
                with self.assertRaisesRegex(RuntimeError, "UNREDACTED_OPERATIONAL_REFERENCE"):
                    verifier.run(root)

    def test_missing_required_payload_field_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            copy_fixture_tree(root)
            path = root / "docs/evidence/TASK_091_LIVE_ARTIFACT_PAYLOAD_0.8.0.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            del data["source"]["remote_id_sha256"]
            raw = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            path.write_bytes(raw)
            with patch.object(verifier, "EXPECTED_PAYLOAD_BLOB", verifier.git_blob_sha(raw)):
                with self.assertRaises(KeyError):
                    verifier.run(root)

    def test_missing_evidence_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            copy_fixture_tree(root)
            (root / "docs/evidence/TASK_091_OWNER_AUTHORIZATION_0.8.0.json").unlink()
            with self.assertRaises(FileNotFoundError):
                verifier.run(root)


if __name__ == "__main__":
    unittest.main()

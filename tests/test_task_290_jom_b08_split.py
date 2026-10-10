"""Offline, fail-closed tests for B08 existing-GitHub-artifact-only repackaging."""
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reportlab.pdfgen.canvas import Canvas
from scripts import repackage_existing_jom_b08_artifact as target

ROOT = Path(__file__).resolve().parents[1]


def pdf_bytes(edition):
    buf = io.BytesIO()
    canvas = Canvas(buf)
    canvas.drawString(60, 760, "JORNAL OFICIAL LIMEIRA EDICAO " + str(edition))
    canvas.showPage()
    canvas.save()
    return buf.getvalue()


def fixture(source):
    originals = source / "originals"
    originals.mkdir(parents=True)
    rows = []
    for source_row in target.batch_map()["B08"]:
        edition = int(source_row["edition"])
        name = f"JOM_{edition}_2026_ORIGINAL.pdf"
        content = pdf_bytes(edition)
        (originals / name).write_bytes(content)
        rows.append({
            "edition": edition, "file_name": name,
            "url": source_row["document_url"], "source_id": source_row["source_id"],
            "status": "VALIDATED_ORIGINAL", "request_attempts": 1,
            "cover_edition_verified": True, "pages": 1,
            "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest(),
        })
    manifest = {
        "schema": "LOA2027_JOM_2026_BATCH_9_ORIGINALS_V1",
        "batch": "B08", "github_sha": target.SOURCE_SHA,
        "validated_count": 9, "failed_count": 0,
        "source_get_attempts": 9, "drive_write_count": 0,
        "publication_count": 0, "documents": rows,
    }
    (source / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return manifest


class TestB08ExistingRepack(unittest.TestCase):
    def test_scope_and_source_run(self):
        self.assertEqual(target.RUN_ID, 38076191781)
        self.assertEqual(
            target.EDITIONS,
            tuple(int(x["edition"]) for x in target.batch_map()["B08"]),
        )
        self.assertLess(target.CHUNK_BYTES, 100 * 1024 * 1024)

    def test_context_must_be_manual_and_owner_confirmed(self):
        ok = {
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GITHUB_REF": "refs/heads/main",
            "GITHUB_RUN_ATTEMPT": "1",
            "B08_OWNER_CONFIRM": "true",
            "B08_SOURCE_RUN": "38076191781",
            "GITHUB_SHA": "a" * 40,
        }
        target.validate_context(ok)
        for key, bad in [
            ("GITHUB_EVENT_NAME", "push"),
            ("GITHUB_REF", "refs/heads/feature"),
            ("GITHUB_RUN_ATTEMPT", "2"),
            ("B08_OWNER_CONFIRM", "false"),
            ("B08_SOURCE_RUN", "38070797837"),
        ]:
            with self.assertRaisesRegex(target.StopB08, "STOP_B08_MANUAL"):
                target.validate_context(ok | {key: bad})

    def test_nine_verified_exact_pdfs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = fixture(root / "source")
            result = target.stage(root / "source", root / "out")
            self.assertEqual(result["status"], "PASS_B08_9_VALIDATED")
            self.assertEqual(result["parts_created"], 9)
            for row in manifest["documents"]:
                name = row["file_name"]
                part = root / "out" / str(row["edition"]) / "part01" / name
                self.assertEqual(hashlib.sha256(part.read_bytes()).hexdigest(), row["sha256"])
                md = json.loads((part.parent / "manifest_excerpt.json").read_text())
                self.assertEqual(md["source_run_id"], target.RUN_ID)

    def test_large_original_is_reversibly_split(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = fixture(root / "source")
            # Artificially tiny cap exercises splitting without large test fixtures.
            size = manifest["documents"][0]["bytes"]
            with patch.object(target, "CHUNK_BYTES", (size + 1) // 2):
                result = target.stage(root / "source", root / "out")
            self.assertGreater(result["parts_created"], 9)
            row = manifest["documents"][0]
            folder = root / "out" / str(row["edition"])
            parts = sorted(folder.glob("part*/" + row["file_name"] + ".part*"))
            self.assertGreaterEqual(len(parts), 2)
            joined = b"".join(p.read_bytes() for p in parts)
            self.assertEqual(hashlib.sha256(joined).hexdigest(), row["sha256"])

    def test_hash_tamper_is_fail_closed_before_stage(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fixture(root / "source")
            original = root / "source" / "originals" / "JOM_7270_2026_ORIGINAL.pdf"
            data = bytearray(original.read_bytes())
            data[42] ^= 1
            original.write_bytes(data)
            with self.assertRaisesRegex(target.StopB08, "STOP_B08_HASH"):
                target.stage(root / "source", root / "out")
            self.assertFalse((root / "out").exists())

    def test_manifest_run_drift_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = fixture(root / "source")
            manifest["batch"] = "B06"
            (root / "source" / "manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(target.StopB08, "STOP_B08_RUN_PROVENANCE"):
                target.stage(root / "source", root / "out")
            self.assertFalse((root / "out").exists())

    def test_workflow_policy_and_no_auto_triggers(self):
        workflow = (ROOT / ".github/workflows/jom-b08-existing-artifact-split-manual.yml").read_text()
        for required in ["workflow_dispatch:", "confirmar_b08", "actions: read",
                         "gh run download 38076191781", "persist-credentials: false",
                         "compression-level: 0"]:
            self.assertIn(required, workflow)
        for forbidden in ["schedule:", "workflow_run:", "push:", "repository_dispatch:", "ecrie.com.br"]:
            self.assertNotIn(forbidden, workflow)
        self.assertEqual(workflow.count("uses: actions/upload-artifact@"), 27)
        for edition in target.EDITIONS:
            self.assertIn(f"task290-b08-original-{edition}-part01", workflow)
        policy = json.loads((ROOT / "config/automation_policy.v1.json").read_text())
        contract = next(x for x in policy["workflows"] if x["id"] == "JOM_B08_EXISTING_GITHUB_ARTIFACT_SPLIT_MANUAL")
        self.assertEqual(contract["tier"], "T2_CREATE_ONLY")
        self.assertFalse(contract["auto_allowed"])
        self.assertTrue(contract["human_confirmation_required"])


if __name__ == "__main__":
    unittest.main()

"""Tests for exact B06 repackage contract, without remote effects."""
import io
import json
import hashlib
import tempfile
import unittest
from pathlib import Path
from reportlab.pdfgen.canvas import Canvas
from scripts import repackage_existing_jom_b06_artifact as target

ROOT = Path(__file__).resolve().parents[1]


def make_pdf(edition):
    buffer = io.BytesIO()
    doc = Canvas(buffer)
    doc.drawString(40, 750, "JORNAL OFICIAL LIMEIRA EDICAO " + str(edition))
    doc.showPage()
    doc.save()
    return buffer.getvalue()


def arrange(root):
    original = root / "originals"
    original.mkdir(parents=True)
    rows = []
    for row in target.batch_map()["B06"]:
        edition = int(row["edition"])
        name = "JOM_" + str(edition) + "_2026_ORIGINAL.pdf"
        data = make_pdf(edition)
        (original / name).write_bytes(data)
        rows.append({
            "edition": edition, "file_name": name,
            "url": row["document_url"], "source_id": row["source_id"],
            "status": "VALIDATED_ORIGINAL", "request_attempts": 1,
            "cover_edition_verified": True, "pages": 1,
            "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
        })
    m = {
        "schema": "LOA2027_JOM_2026_BATCH_9_ORIGINALS_V1",
        "batch": "B06", "github_sha": target.GITHUB_HEAD_SHA,
        "validated_count": 9, "failed_count": 0, "source_get_attempts": 9,
        "drive_write_count": 0, "publication_count": 0, "documents": rows,
    }
    (root/"manifest.json").write_text(json.dumps(m))
    return m


class TestRepackage(unittest.TestCase):
    def test_exact_scope(self):
        self.assertEqual(target.RUN_ID, 38067488083)
        self.assertEqual(target.EXACT_EDITIONS, tuple(int(x["edition"]) for x in target.batch_map()["B06"]))

    def test_owner_gate(self):
        ok = {
            "GITHUB_EVENT_NAME":"workflow_dispatch", "GITHUB_REF":"refs/heads/main",
            "GITHUB_RUN_ATTEMPT":"1", "GITHUB_SHA":"a"*40,
            "JOM_B06_OWNER_CONFIRM":"true", "JOM_B06_EXISTING_RUN":"38067488083",
        }
        target.validate_context(ok)
        for key, value in [("GITHUB_EVENT_NAME","push"),("GITHUB_REF","refs/heads/other"),
                           ("GITHUB_RUN_ATTEMPT","2"),("JOM_B06_OWNER_CONFIRM","false"),
                           ("JOM_B06_EXISTING_RUN","38060403383")]:
            with self.assertRaisesRegex(target.RepackStop, "STOP_REPACK_B06"):
                target.validate_context(ok | {key:value})

    def test_nine_pass_without_network(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = arrange(root/"source")
            result = target.stage_existing_archive(root/"source", root/"out")
            self.assertEqual(result["validated_count"], 9)
            self.assertEqual(result["source_site_gets"], 0)
            for row in manifest["documents"]:
                dest = root/"out"/str(row["edition"])/row["file_name"]
                self.assertEqual(hashlib.sha256(dest.read_bytes()).hexdigest(), row["sha256"])
                self.assertEqual(json.loads((dest.parent/"manifest_excerpt.json").read_text())["original_github_run_id"],target.RUN_ID)

    def test_bad_hash_stops_before_creating_output(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            arrange(root/"source")
            (root/"source"/"originals"/"JOM_7246_2026_ORIGINAL.pdf").write_bytes(b"tampered")
            with self.assertRaisesRegex(target.RepackStop,"STOP_B06_ORIGINAL_HASH"):
                target.stage_existing_archive(root/"source",root/"out")
            self.assertFalse((root/"out").exists())

    def test_bad_manifest_stops(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            data=arrange(root/"source")
            data["github_sha"]="0"*40
            (root/"source"/"manifest.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(target.RepackStop,"STOP_B06_SOURCE_RUN_IDENTITY"):
                target.stage_existing_archive(root/"source",root/"out")

    def test_workflow_contract(self):
        txt=(ROOT/".github/workflows/jom-b06-repackage-existing-artifact-manual.yml").read_text()
        for needle in ["workflow_dispatch:","confirmar_reempacotamento_b06",
                       "actions: read","contents: read","gh run download 38067488083",
                       "persist-credentials: false","compression-level: 0"]:
            self.assertIn(needle,txt)
        for excluded in ["schedule:","workflow_run:","push:","secrets: inherit","ecrie.com.br"]:
            self.assertNotIn(excluded,txt)
        self.assertEqual(txt.count("uses: actions/upload-artifact@"), 9)
        for edition in target.EXACT_EDITIONS:
            self.assertIn("name: task289-b06-original-"+str(edition), txt)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
from pathlib import Path
import unittest

from robo_dados_publicos.research.local_pdf_capability import (
    probe_visual_ocr_capabilities,
)


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_109_VISUAL_OCR_CAPABILITY_0.8.0.json"
INVENTORY_WORKFLOW = ROOT / ".github/workflows/task-109-visual-ocr-capability-once.yml"
CHROME_WORKFLOW = ROOT / ".github/workflows/task-109-chrome-image-only-probe-once.yml"
INVENTORY_SOURCE = ROOT / "docs/evidence/TASK_109_VISUAL_OCR_INVENTORY_WORKFLOW_SOURCE_0.8.0.txt"
CHROME_SOURCE = ROOT / "docs/evidence/TASK_109_EXECUTED_CHROME_IMAGE_ONLY_WORKFLOW_SOURCE_0.8.0.txt"


class TestTask109OfflineVisualOcrCapability(unittest.TestCase):
    def test_visual_ocr_capability_inventory_is_offline_and_observable(self):
        result = probe_visual_ocr_capabilities()
        print("TASK109_VISUAL_OCR_CAPABILITY=" + json.dumps(result, sort_keys=True))
        self.assertEqual("TASK109_VISUAL_OCR_CAPABILITY_PROBE_V1", result["schema"])
        self.assertEqual("T0_OFFLINE_CAPABILITY_INVENTORY", result["mode"])
        self.assertTrue(
            set(result["commands"]) >= {
                "tesseract",
                "google-chrome",
                "chromedriver",
                "pdftoppm",
                "pdfimages",
            }
        )
        self.assertTrue(
            set(result["python_modules"]) >= {"PIL", "fitz", "pytesseract"}
        )
        self.assertTrue(all(value is False for value in result["remote_effects"].values()))

    def test_negative_chrome_image_only_proof_is_pinned(self):
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(
            "STOP_NO_LOCAL_OCR_CHAIN_CHROME_IMAGE_ONLY_NEGATIVE",
            evidence["decision"],
        )
        proof = evidence["synthetic_chrome_proof"]
        self.assertEqual(33917837446, proof["run_id"])
        self.assertEqual(101169024384, proof["job_id"])
        self.assertEqual("success", proof["conclusion"])
        self.assertEqual(["pypdf==6.10.0"], proof["dependency_install"])
        self.assertTrue(proof["pdf_text_empty"])
        self.assertEqual(1, proof["pdf_page_count"])
        self.assertEqual(0, proof["ax_string_count"])
        self.assertFalse(proof["marker_in_ax"])
        self.assertFalse(proof["marker_in_source"])
        self.assertFalse(proof["marker_in_body_inner_text"])
        self.assertEqual(0, proof["source_network_requests"])
        self.assertEqual(0, proof["source_reads"])
        self.assertFalse(proof["real_source_ocr"])

    def test_real_source_remains_outside_task109(self):
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertFalse(evidence["real_source_read_authorized"])
        self.assertFalse(evidence["real_source_ocr_authorized"])
        self.assertEqual(
            "CONSUMED_PYPDF_6_10_0_SYNTHETIC_PROOF_ONLY_NO_OCR_STACK",
            evidence["package_install_authorized"],
        )
        self.assertEqual(
            "TASK_110_T0_OCR_DEPENDENCY_ROUTE_DESIGN_SEPARATE_REVIEW",
            evidence["next_boundary"],
        )
        self.assertTrue(all(value is False for value in evidence["remote_effects"].values()))

    def test_explicit_inventory_observation_is_pinned(self):
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        inv = evidence["explicit_inventory_workflow"]
        self.assertEqual(33917458022, inv["run_id"])
        self.assertEqual(101167825670, inv["job_id"])
        self.assertEqual(0, inv["source_network_requests"])
        self.assertEqual(0, inv["source_reads"])
        self.assertEqual(0, inv["package_installs"])
        self.assertFalse(inv["real_source_ocr"])
        self.assertIsNone(inv["observed_system_python"]["commands"]["tesseract"])
        self.assertEqual(
            "/usr/bin/google-chrome",
            inv["observed_system_python"]["commands"]["google-chrome"],
        )

    def test_probe_source_contains_no_real_ppa_reference(self):
        source = (
            ROOT / "robo_dados_publicos/research/local_pdf_capability.py"
        ).read_text(encoding="utf-8")
        task109_source = source.split("def probe_visual_ocr_capabilities()", 1)[1]
        self.assertNotIn("urlopen(", task109_source)
        self.assertNotIn("subprocess.", task109_source)
        self.assertNotIn("limeira.sp.gov.br", task109_source)
        self.assertNotIn("0fa1a5cc5c9a1823fbf5436def00f01f.pdf", task109_source)

    def test_executed_workflow_sources_are_preserved_inertly(self):
        self.assertTrue(INVENTORY_SOURCE.exists())
        self.assertTrue(CHROME_SOURCE.exists())
        inventory = INVENTORY_SOURCE.read_text(encoding="utf-8")
        chrome = CHROME_SOURCE.read_text(encoding="utf-8")
        self.assertIn("TASK 109 visual OCR capability inventory once", inventory)
        self.assertIn("TASK 109 Chrome image-only synthetic proof once", chrome)
        self.assertNotIn("limeira.sp.gov.br", inventory)
        self.assertNotIn("limeira.sp.gov.br", chrome)

    def test_single_use_task109_workflows_are_removed_before_merge(self):
        self.assertFalse(INVENTORY_WORKFLOW.exists())
        self.assertFalse(CHROME_WORKFLOW.exists())


if __name__ == "__main__":
    unittest.main()

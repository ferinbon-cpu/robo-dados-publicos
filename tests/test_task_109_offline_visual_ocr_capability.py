from __future__ import annotations

import json
from pathlib import Path
import unittest

from robo_dados_publicos.research.local_pdf_capability import (
    probe_visual_ocr_capabilities,
)


ROOT = Path(__file__).resolve().parents[1]


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

    def test_probe_source_contains_no_network_or_real_ppa_reference(self):
        source = (
            ROOT / "robo_dados_publicos/research/local_pdf_capability.py"
        ).read_text(encoding="utf-8")
        function_source = source.split("def probe_visual_ocr_capabilities()", 1)[1]
        self.assertNotIn("urlopen(", function_source)
        self.assertNotIn("limeira.sp.gov.br", function_source)
        self.assertNotIn("0fa1a5cc5c9a1823fbf5436def00f01f.pdf", function_source)


if __name__ == "__main__":
    unittest.main()

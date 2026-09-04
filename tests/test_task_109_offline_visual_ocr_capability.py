from __future__ import annotations

import json
from pathlib import Path

from robo_dados_publicos.research.local_pdf_capability import (
    probe_visual_ocr_capabilities,
)


ROOT = Path(__file__).resolve().parents[1]


def test_task109_visual_ocr_capability_inventory_is_offline_and_observable():
    result = probe_visual_ocr_capabilities()
    print("TASK109_VISUAL_OCR_CAPABILITY=" + json.dumps(result, sort_keys=True))
    assert result["schema"] == "TASK109_VISUAL_OCR_CAPABILITY_PROBE_V1"
    assert result["mode"] == "T0_OFFLINE_CAPABILITY_INVENTORY"
    assert set(result["commands"]) >= {
        "tesseract",
        "google-chrome",
        "chromedriver",
        "pdftoppm",
        "pdfimages",
    }
    assert set(result["python_modules"]) >= {"PIL", "fitz", "pytesseract"}
    assert all(value is False for value in result["remote_effects"].values())


def test_task109_probe_source_contains_no_network_or_real_ppa_reference():
    source = (
        ROOT / "robo_dados_publicos/research/local_pdf_capability.py"
    ).read_text(encoding="utf-8")
    function_source = source.split("def probe_visual_ocr_capabilities()", 1)[1]
    assert "urlopen(" not in function_source
    assert "limeira.sp.gov.br" not in function_source
    assert "0fa1a5cc5c9a1823fbf5436def00f01f.pdf" not in function_source

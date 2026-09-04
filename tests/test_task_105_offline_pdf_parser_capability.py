from __future__ import annotations

import json

from robo_dados_publicos.research.local_pdf_capability import (
    _minimal_pdf_bytes,
    probe_chrome_pdf_accessibility,
    probe_runner_capabilities,
)


def test_minimal_pdf_fixture_is_deterministic_and_valid_shape():
    first = _minimal_pdf_bytes("TASK105")
    second = _minimal_pdf_bytes("TASK105")
    assert first == second
    assert first.startswith(b"%PDF-1.4")
    assert first.endswith(b"%%EOF\n")
    assert b"TASK105" in first


def test_task105_runner_capability_probe_emits_ci_observation():
    result = probe_runner_capabilities()
    print("TASK105_CAPABILITY_PROBE=" + json.dumps(result, sort_keys=True))
    assert result["schema"] == "TASK105_RUNNER_PDF_CAPABILITY_PROBE_V1"
    assert set(result["commands"]) >= {
        "pdftotext",
        "google-chrome",
        "chromium",
        "chromedriver",
    }


def test_task105_chrome_pdf_accessibility_probe_is_local_only_and_observable():
    result = probe_chrome_pdf_accessibility()
    print("TASK105_CHROME_PDF_PROBE=" + json.dumps(result, sort_keys=True))
    assert result["status"] in {"UNAVAILABLE", "PROBED"}
    assert isinstance(result["marker_in_ax"], bool)
    assert isinstance(result["marker_in_source"], bool)
    assert isinstance(result["marker_in_body_inner_text"], bool)

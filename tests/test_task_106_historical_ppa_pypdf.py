from __future__ import annotations

import json
from pathlib import Path
import tempfile

from robo_dados_publicos.research.eiti_historical_ppa_live import (
    acquire_historical_ppa_evidence,
    load_contract,
)
from robo_dados_publicos.research.local_pdf_capability import (
    _minimal_pdf_bytes,
    extract_pdf_text_pypdf,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/eiti_historical_ppa_primary_acquisition.v1.json"


class FakeClient:
    def __init__(self) -> None:
        self.request_log = []
        self.responses = {
            "https://www.limeira.sp.gov.br/orcamentos": (
                '<html><a href="/downloads/ppa5947.pdf">Lei Municipal 5.947 e Anexos - PPA - Periodo 2018/2021</a></html>'.encode("utf-8"),
                "https://www.limeira.sp.gov.br/orcamentos",
                "text/html",
            ),
            "https://www.limeira.sp.gov.br/downloads/ppa5947.pdf": (
                _minimal_pdf_bytes(
                    "LEI 5.947 DE 2017 ESCOLAS COM PROGRAMAS EM TEMPO INTEGRAL"
                ),
                "https://www.limeira.sp.gov.br/downloads/ppa5947.pdf",
                "application/pdf",
            ),
            "https://www.limeira.sp.gov.br/sitenovo/downloads/9d8dd63f39cc3b51ef032a4c96210a07.pdf": (
                _minimal_pdf_bytes(
                    "LEI 6.659 DE 2021 INDICE DE ALUNOS EM EDUCACAO INTEGRAL"
                ),
                "https://www.limeira.sp.gov.br/sitenovo/downloads/9d8dd63f39cc3b51ef032a4c96210a07.pdf",
                "application/pdf",
            ),
        }

    def get(self, period: str, url: str):
        self.request_log.append({"period": period, "url": url})
        return self.responses[url]


def test_task106_pypdf_extractor_recovers_page_preserving_text(tmp_path):
    marker = "TASK106_PYPDF_REAL_TEXT_51027"
    path = tmp_path / "synthetic.pdf"
    path.write_bytes(_minimal_pdf_bytes(marker))
    text = extract_pdf_text_pypdf(path)
    assert marker in text


def test_task106_offline_fake_transport_closes_both_primary_matches_with_pypdf():
    contract = load_contract(CONTRACT)
    fake = FakeClient()
    with tempfile.TemporaryDirectory() as td:
        result = acquire_historical_ppa_evidence(
            contract=contract,
            runtime_dir=Path(td),
            client=fake,
            extract_pdf_text=extract_pdf_text_pypdf,
        )

    print("TASK106_OFFLINE_PYPDF_RESULT=" + json.dumps(result, sort_keys=True))
    assert result["overall_status"] == "PASS_TASK104_TWO_PRIMARY_PPA_MATCHES"
    assert result["primary_match_count"] == 2
    assert result["request_count"] == 3
    assert all(item["status"] == "PRIMARY_MATCH" for item in result["period_results"])
    assert all(item["locator"]["coordinate_system"] == "SOURCE_PDF_PAGE_1_BASED" for item in result["period_results"])
    assert all(value == 0 for value in result["hard_boundaries"].values())
    assert result["retry_performed"] is False
    assert result["future_execution_authorized"] is False


def test_task106_runner_source_has_no_pdftotext_dependency():
    source = (ROOT / "scripts/run_task106_historical_ppa_live_once.py").read_text(encoding="utf-8")
    assert "pdftotext" not in source
    assert "extract_pdf_text_pypdf" in source

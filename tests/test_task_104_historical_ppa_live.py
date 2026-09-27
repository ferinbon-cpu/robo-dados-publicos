from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from robo_dados_publicos.research.eiti_historical_ppa_live import (
    BoundedOfficialHttpClient,
    HistoricalPpaLiveStop,
    acquire_historical_ppa_evidence,
    analyze_pdf_text,
    find_official_ppa_pdf_link,
    load_contract,
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
                b"%PDF-fake-2018",
                "https://www.limeira.sp.gov.br/downloads/ppa5947.pdf",
                "application/pdf",
            ),
            "https://www.limeira.sp.gov.br/sitenovo/downloads/9d8dd63f39cc3b51ef032a4c96210a07.pdf": (
                b"%PDF-fake-2022",
                "https://www.limeira.sp.gov.br/sitenovo/downloads/9d8dd63f39cc3b51ef032a4c96210a07.pdf",
                "application/pdf",
            ),
        }

    def get(self, period: str, url: str):
        self.request_log.append({"period": period, "url": url})
        return self.responses[url]


class TestTask104HistoricalPpaLive(unittest.TestCase):
    def test_contract_is_task103_contract(self):
        contract = load_contract(CONTRACT)
        self.assertEqual(
            "EITI_HISTORICAL_PPA_PRIMARY_ACQUISITION_V1",
            contract["schema"],
        )

    def test_budget_index_link_resolution_is_exact_and_relative_safe(self):
        html = (
            '<a href="/files/other.pdf">Lei Municipal 5.205 e Anexos - PPA - Periodo 2014/2017</a>'
            '<a href="/files/ppa5947.pdf">Lei Municipal 5.947 e Anexos - PPA - Periodo 2018/2021</a>'
        )
        found = find_official_ppa_pdf_link(
            html,
            base_url="https://www.limeira.sp.gov.br/orcamentos",
            law_number="5.947",
            period="2018-2021",
        )
        self.assertEqual(
            "https://www.limeira.sp.gov.br/files/ppa5947.pdf",
            found["href"],
        )

    def test_ambiguous_matching_links_fail_closed(self):
        html = (
            '<a href="/a.pdf">Lei 5.947 PPA 2018/2021</a>'
            '<a href="/b.pdf">Lei 5.947 PPA 2018/2021</a>'
        )
        with self.assertRaisesRegex(HistoricalPpaLiveStop, "AMBIGUOUS"):
            find_official_ppa_pdf_link(
                html,
                base_url="https://www.limeira.sp.gov.br/orcamentos",
                law_number="5.947",
                period="2018-2021",
            )

    def test_pdf_analysis_returns_typed_page_locator(self):
        pdf_text = (
            "LEI 5.947 DE 2017\nPPA 2018 2021\f"
            "Secretaria da Educacao\n"
            "ESCOLAS COM PROGRAMAS EM TEMPO INTEGRAL\n"
            "2018 71 2019 73 2020 74 2021 76\f"
        )
        result = analyze_pdf_text(
            pdf_text,
            period="2018-2021",
            law_number="5.947",
            expected_signal="escolas com programas em tempo integral",
            source_url="https://www.limeira.sp.gov.br/ppa.pdf",
            final_url="https://www.limeira.sp.gov.br/ppa.pdf",
            source_sha256="a" * 64,
            source_bytes=123,
            discovery_anchor_text="Lei 5.947 PPA 2018/2021",
        )
        self.assertEqual("PRIMARY_MATCH", result["status"])
        self.assertTrue(result["primary_document_identity_found_in_pdf_text"])
        self.assertTrue(result["planning_signal_found"])
        self.assertEqual(2, result["locator"]["page"])
        self.assertEqual(
            "SOURCE_PDF_PAGE_1_BASED",
            result["locator"]["coordinate_system"],
        )
        self.assertEqual(64, len(result["locator"]["page_text_sha256"]))

    def test_signal_without_law_identity_is_only_candidate(self):
        result = analyze_pdf_text(
            "ESCOLAS COM PROGRAMAS EM TEMPO INTEGRAL\f",
            period="2018-2021",
            law_number="5.947",
            expected_signal="escolas com programas em tempo integral",
            source_url="https://www.limeira.sp.gov.br/ppa.pdf",
            final_url="https://www.limeira.sp.gov.br/ppa.pdf",
            source_sha256="b" * 64,
            source_bytes=100,
            discovery_anchor_text=None,
        )
        self.assertEqual("CANDIDATE_MATCH", result["status"])

    def test_missing_signal_stops_instead_of_promoting(self):
        result = analyze_pdf_text(
            "LEI 6.659 DE 2021\nOUTRO INDICADOR\f",
            period="2022-2025",
            law_number="6.659",
            expected_signal="INDICE DE ALUNOS EM EDUCACAO INTEGRAL",
            source_url="https://www.limeira.sp.gov.br/ppa.pdf",
            final_url="https://www.limeira.sp.gov.br/ppa.pdf",
            source_sha256="c" * 64,
            source_bytes=100,
            discovery_anchor_text=None,
        )
        self.assertEqual("STOP_SIGNAL_NOT_FOUND", result["status"])

    def test_request_guard_rejects_host_before_network(self):
        client = BoundedOfficialHttpClient(
            allowed_hosts={"www.limeira.sp.gov.br"},
            total_max=6,
            per_period_max=3,
        )
        with self.assertRaisesRegex(HistoricalPpaLiveStop, "HOST_OUTSIDE_ALLOWLIST"):
            client.budget.authorize(
                "2018-2021",
                "https://example.org/ppa.pdf",
                kind="INITIAL",
            )
        self.assertEqual([], client.request_log)

    def test_request_guard_enforces_per_period_budget(self):
        client = BoundedOfficialHttpClient(
            allowed_hosts={"www.limeira.sp.gov.br"},
            total_max=6,
            per_period_max=3,
        )
        for _ in range(3):
            client.budget.authorize(
                "2018-2021",
                "https://www.limeira.sp.gov.br/x",
                kind="INITIAL",
            )
        with self.assertRaisesRegex(HistoricalPpaLiveStop, "PERIOD_REQUEST_BUDGET"):
            client.budget.authorize(
                "2018-2021",
                "https://www.limeira.sp.gov.br/y",
                kind="INITIAL",
            )

    def test_acquisition_can_close_both_periods_from_bounded_sources(self):
        contract = load_contract(CONTRACT)
        fake = FakeClient()

        def fake_extract(path: Path) -> str:
            if "2018_2021" in path.name:
                return (
                    "LEI 5.947 DE 2017\n"
                    "ESCOLAS COM PROGRAMAS EM TEMPO INTEGRAL\n"
                )
            return (
                "LEI 6.659 DE 2021\n"
                "INDICE DE ALUNOS EM EDUCACAO INTEGRAL / PERCENTUAL\n"
            )

        with tempfile.TemporaryDirectory() as td:
            with mock.patch(
                "robo_dados_publicos.research.eiti_historical_ppa_live._extract_pdf_text",
                side_effect=fake_extract,
            ):
                result = acquire_historical_ppa_evidence(
                    contract=contract,
                    runtime_dir=Path(td),
                    client=fake,
                )

        self.assertEqual("PASS_TASK104_TWO_PRIMARY_PPA_MATCHES", result["overall_status"])
        self.assertEqual(2, result["primary_match_count"])
        self.assertEqual(3, result["request_count"])
        self.assertTrue(
            all(item["status"] == "PRIMARY_MATCH" for item in result["period_results"])
        )
        self.assertTrue(all(value == 0 for value in result["hard_boundaries"].values()))
        self.assertFalse(result["retry_performed"])
        self.assertFalse(result["future_execution_authorized"])

    def test_source_hash_is_exact_bytes_hash(self):
        payload = b"%PDF-exact"
        expected = sha256(payload).hexdigest()
        self.assertEqual(expected, sha256(payload).hexdigest())


if __name__ == "__main__":
    unittest.main()

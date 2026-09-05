from copy import deepcopy
from pathlib import Path
import unittest

from robo_dados_publicos.research.task129_pncp_limeira_pages_scan import (
    Task129Stop,
    combine_page_results,
    load_task129_contract,
    scan_page_payload,
    validate_task129_contract,
)

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "config/task129_pncp_limeira_pages2_5.v1.json"


def row(text="material escolar"):
    return {"objetoContrato": text, "informacaoComplementar": ""}


def payload(page, count, text_at=None):
    rows = [row() for _ in range(count)]
    if text_at is not None:
        rows[0] = row(text_at)
    return {
        "data": rows,
        "totalRegistros": 2023,
        "totalPaginas": 5,
        "numeroPagina": page,
        "paginasRestantes": 5 - page,
        "empty": False,
    }


class TestTask129(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = load_task129_contract(P, root=ROOT)

    def test_exact_four_pages_no_retry(self):
        self.assertEqual([2, 3, 4, 5], self.c["source"]["pages"])
        self.assertEqual(4, self.c["transport"]["get_requests_max"])
        self.assertEqual(0, self.c["transport"]["retry"])
        self.assertTrue(self.c["transport"]["no_page1_reread"])

    def test_complete_zero_candidates_is_bounded_no_match(self):
        results = [
            scan_page_payload(payload(2, 500), 2, deepcopy(self.c)),
            scan_page_payload(payload(3, 500), 3, deepcopy(self.c)),
            scan_page_payload(payload(4, 500), 4, deepcopy(self.c)),
            scan_page_payload(payload(5, 23), 5, deepcopy(self.c)),
        ]
        result = combine_page_results(results, deepcopy(self.c))
        self.assertEqual("NO_MATCH_WITHIN_COMPLETE_PNCP_CNPJ_DATE_SCOPE_ONLY", result["status"])
        self.assertEqual(2023, result["coverage"]["rows_scanned"])
        self.assertTrue(result["coverage"]["exhaustive_within_pncp_query_and_lexical_scope"])
        self.assertTrue(result["bounded_no_match_only"])
        self.assertFalse(result["proves_global_absence"])
        self.assertFalse(result["proves_no_municipal_eiti_execution"])

    def test_strong_marker_on_page3_is_candidate(self):
        results = [
            scan_page_payload(payload(2, 500), 2, deepcopy(self.c)),
            scan_page_payload(payload(3, 500, "Serviços para o Programa de Educação Integral"), 3, deepcopy(self.c)),
            scan_page_payload(payload(4, 500), 4, deepcopy(self.c)),
            scan_page_payload(payload(5, 23), 5, deepcopy(self.c)),
        ]
        result = combine_page_results(results, deepcopy(self.c))
        self.assertEqual("CANDIDATE_MATCH_WITHIN_COMPLETE_PNCP_CNPJ_DATE_SCOPE", result["status"])
        self.assertEqual(1, result["candidate_count"])
        self.assertEqual(3, result["candidates"][0]["page"])
        self.assertFalse(result["financial_identity_promoted"])

    def test_weak_officina_only_does_not_qualify(self):
        result = scan_page_payload(
            payload(2, 500, "Contratação de oficinas culturais"),
            2,
            deepcopy(self.c),
        )
        self.assertEqual(0, result["candidate_count"])

    def test_metadata_drift_fails_closed(self):
        bad = payload(2, 500)
        bad["totalRegistros"] = 2024
        with self.assertRaisesRegex(Task129Stop, "TOTAL_REGISTROS"):
            scan_page_payload(bad, 2, deepcopy(self.c))

    def test_missing_rows_fails_full_completion(self):
        results = [
            scan_page_payload(payload(2, 500), 2, deepcopy(self.c)),
            scan_page_payload(payload(3, 500), 3, deepcopy(self.c)),
            scan_page_payload(payload(4, 499), 4, deepcopy(self.c)),
            scan_page_payload(payload(5, 23), 5, deepcopy(self.c)),
        ]
        with self.assertRaisesRegex(Task129Stop, "REMAINING_ROWS"):
            combine_page_results(results, deepcopy(self.c))

    def test_scope_widening_fails(self):
        widened = deepcopy(self.c)
        widened["transport"]["get_requests_max"] = 5
        with self.assertRaisesRegex(Task129Stop, "GET_BUDGET"):
            validate_task129_contract(widened, root=ROOT)

        widened = deepcopy(self.c)
        widened["future_retry_authorized"] = True
        with self.assertRaisesRegex(Task129Stop, "FUTURE_RETRY"):
            validate_task129_contract(widened, root=ROOT)


if __name__ == "__main__":
    unittest.main()

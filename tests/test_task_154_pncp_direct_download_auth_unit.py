from pathlib import Path
import json
import unittest
from urllib.parse import urlparse, parse_qsl

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "config/task154_pncp_direct_download_auth_unit.v1.json"
E153 = ROOT / "docs/evidence/TASK_153_PNCP_API_OPEN_EXECUTION_0.8.0.json"


class TestTask154(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = json.loads(C.read_text(encoding="utf-8"))
        cls.e153 = json.loads(E153.read_text(encoding="utf-8"))

    def test_task153_stop_is_pinned(self):
        self.assertEqual(
            "STOP_WEB_URL_SAFETY_PRECONDITION_PRE_SOURCE_AFTER_ORIGIN_PREFLIGHT",
            self.e153["result"],
        )
        self.assertFalse(self.e153["execution"]["pncp_source_reach_established"])
        self.assertEqual(8, self.e153["authorization_state"]["remaining_units"])

    def test_authorization_is_unit_three(self):
        a = self.c["authorization"]
        self.assertEqual(10, a["owner_authorization_units_granted"])
        self.assertEqual(3, a["authorization_unit_index"])
        self.assertEqual(8, a["remaining_units_before_execution"])
        self.assertEqual(7, a["remaining_units_after_execution"])
        self.assertTrue(a["consume_on_single_direct_download_invocation"])

    def test_normalized_url_exact_semantics(self):
        s = self.c["source"]
        u = urlparse(s["normalized_url"])
        self.assertEqual("https", u.scheme)
        self.assertEqual("pncp.gov.br", u.hostname)
        self.assertEqual("/api/consulta/v1/contratacoes/publicacao", u.path)
        self.assertEqual(dict(parse_qsl(u.query)), {
            "cnpj": "45132495000140",
            "codigoModalidadeContratacao": "12",
            "dataFinal": "20260904",
            "dataInicial": "20251128",
            "pagina": "1",
            "tamanhoPagina": "50",
        })
        self.assertEqual("TASK153_TOOL_EMITTED_URL", s["normalization_origin"])
        self.assertTrue(s["semantically_identical_to_owner_url"])
        self.assertFalse(s["host_path_or_parameter_mutation_allowed"])

    def test_one_download_only(self):
        x = self.c["execution"]
        self.assertEqual(1, x["direct_download_invocations_max"])
        self.assertEqual(0, x["web_open_invocations"])
        self.assertEqual(0, x["search_queries"])
        self.assertEqual(0, x["clicks"])
        self.assertEqual(0, x["retry"])
        self.assertEqual(0, x["followup_opens"])
        self.assertTrue(x["temporary_local_payload_allowed"])
        self.assertTrue(x["local_postcheck_allowed"])
        self.assertFalse(x["persistent_raw_payload_allowed"])
        self.assertTrue(x["execute_only_after_merge"])

    def test_fail_closed_semantics(self):
        e = self.c["epistemic_semantics"]
        self.assertFalse(e["tool_failure_is_source_response"])
        self.assertEqual("CORROBORATED", e["administrative_identifier_candidate_max_status"])
        self.assertFalse(e["negative_exhaustive_conclusion_allowed"])
        self.assertFalse(e["pncp_no_match_allowed"])
        self.assertTrue(e["primary_municipal_verification_required"])
        self.assertFalse(e["automatic_financial_identity"])
        self.assertFalse(e["automatic_transaction_identity"])
        self.assertFalse(e["automatic_supplier_linkage"])


if __name__ == "__main__":
    unittest.main()

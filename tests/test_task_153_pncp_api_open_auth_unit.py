from pathlib import Path
import json
import unittest
from urllib.parse import urlparse, parse_qsl

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "config/task153_pncp_api_open_auth_unit.v1.json"
E152 = ROOT / "docs/evidence/TASK_152_PNCP_ORIGIN_PREFLIGHT_EXECUTION_0.8.0.json"


class TestTask153(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = json.loads(C.read_text(encoding="utf-8"))
        cls.e152 = json.loads(E152.read_text(encoding="utf-8"))

    def test_prior_origin_preflight_succeeded(self):
        self.assertEqual(
            "PASS_OFFICIAL_PNCP_ORIGIN_REACHED_WITH_OFFICIAL_GOVBR_REDIRECT",
            self.e152["result"],
        )
        self.assertTrue(self.e152["execution"]["source_reach_established"])
        self.assertEqual(9, self.e152["authorization_state"]["remaining_units"])

    def test_authorization_is_unit_two_of_ten(self):
        a = self.c["authorization"]
        self.assertEqual(10, a["owner_authorization_units_granted"])
        self.assertEqual(2, a["authorization_unit_index"])
        self.assertEqual(9, a["remaining_units_before_execution"])
        self.assertEqual(8, a["remaining_units_after_execution"])
        self.assertTrue(a["consume_on_single_web_open_invocation"])

    def test_requested_url_has_exact_semantics(self):
        s = self.c["source"]
        u = urlparse(s["requested_url"])
        self.assertEqual("https", u.scheme)
        self.assertEqual("pncp.gov.br", u.hostname)
        self.assertEqual("/api/consulta/v1/contratacoes/publicacao", u.path)
        self.assertEqual(dict(parse_qsl(u.query)), s["query_parameters"])
        self.assertTrue(s["tool_side_query_reordering_allowed"])
        self.assertFalse(s["host_path_or_parameter_mutation_allowed"])

    def test_one_open_only(self):
        x = self.c["execution"]
        self.assertEqual(1, x["web_open_invocations_max"])
        self.assertEqual(0, x["search_queries"])
        self.assertEqual(0, x["clicks"])
        self.assertEqual(0, x["retry"])
        self.assertEqual(0, x["followup_opens"])
        self.assertEqual(0, x["direct_download_invocations"])
        self.assertFalse(x["raw_payload_persistence"])
        self.assertTrue(x["execute_only_after_merge"])

    def test_fail_closed_semantics(self):
        e = self.c["epistemic_semantics"]
        self.assertFalse(e["transport_failure_is_source_response"])
        self.assertEqual("CORROBORATED", e["administrative_identifier_candidate_max_status"])
        self.assertFalse(e["negative_exhaustive_conclusion_allowed"])
        self.assertFalse(e["pncp_no_match_allowed"])
        self.assertTrue(e["primary_municipal_verification_required"])
        self.assertFalse(e["automatic_financial_identity"])
        self.assertFalse(e["automatic_transaction_identity"])
        self.assertFalse(e["automatic_supplier_linkage"])


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "config/task152_pncp_origin_preflight_auth_unit.v1.json"


class TestTask152(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = json.loads(C.read_text(encoding="utf-8"))

    def test_current_main_and_issue_are_pinned(self):
        self.assertEqual("c89293b917b131a242529bbe1a16ef28c9018005", self.c["base_sha"])
        self.assertEqual(516, self.c["issue"])

    def test_authorization_batch_is_unit_one_of_ten(self):
        a = self.c["authorization"]
        self.assertEqual("10 tokens de autorização concedidos", a["owner_instruction"])
        self.assertEqual(10, a["owner_authorization_units_granted"])
        self.assertEqual(1, a["authorization_unit_index"])
        self.assertEqual(10, a["remaining_units_before_execution"])
        self.assertTrue(a["consume_on_single_web_open_invocation"])
        self.assertEqual(9, a["remaining_units_after_execution"])

    def test_only_bare_origin_is_authorized(self):
        s = self.c["source"]
        self.assertEqual("https://pncp.gov.br/", s["origin_url"])
        self.assertEqual("pncp.gov.br", s["origin_host"])
        self.assertFalse(s["parameterized_api_url_authorized"])

    def test_exactly_one_origin_open_and_no_other_live_action(self):
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
        self.assertTrue(e["origin_preflight_only"])
        self.assertFalse(e["transport_failure_is_source_response"])
        self.assertFalse(e["candidate_discovery_allowed"])
        self.assertFalse(e["negative_exhaustive_conclusion_allowed"])
        self.assertFalse(e["pncp_no_match_allowed"])
        self.assertFalse(e["automatic_financial_identity"])
        self.assertFalse(e["automatic_transaction_identity"])
        self.assertFalse(e["automatic_supplier_linkage"])


if __name__ == "__main__":
    unittest.main()

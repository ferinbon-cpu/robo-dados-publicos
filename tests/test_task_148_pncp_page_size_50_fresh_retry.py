from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "config/task148_pncp_page_size_50_fresh_retry.v1.json"
E = ROOT / "docs/evidence/TASK_148_PNCP_PAGE_SIZE_50_FRESH_RETRY_DESIGN_0.8.0.json"


class TestTask148(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = json.loads(C.read_text(encoding="utf-8"))
        cls.e = json.loads(E.read_text(encoding="utf-8"))

    def test_base_and_fresh_authorization_are_pinned(self):
        self.assertEqual("81e764fdf2a079c8151ae4d5bb7f0e29c885e682", self.c["base_sha"])
        a = self.c["fresh_owner_authorization"]
        self.assertEqual("Prossiga autorizado", a["instruction"])
        self.assertTrue(a["authorized_after_task147_stop"])
        self.assertTrue(a["single_live_open_authorized"])

    def test_exact_corrected_url_uses_page_size_50(self):
        s = self.c["source"]
        self.assertEqual(1, s["page"])
        self.assertEqual(50, s["page_size"])
        self.assertTrue(s["exact_url"].endswith("pagina=1&tamanhoPagina=50"))
        self.assertNotIn("tamanhoPagina=500", s["exact_url"])

    def test_single_open_only_and_execute_after_merge(self):
        w = self.c["managed_web_execution"]
        self.assertEqual(1, w["open_invocations_max"])
        self.assertEqual(0, w["search_queries"])
        self.assertEqual(0, w["clicks"])
        self.assertEqual(0, w["retry"])
        self.assertEqual(0, w["followup_opens"])
        self.assertFalse(w["raw_payload_persistence"])
        self.assertTrue(w["execute_only_after_merge"])

    def test_epistemic_fail_closed_bounds(self):
        x = self.c["epistemic_semantics"]
        self.assertFalse(x["transport_failure_is_source_response"])
        self.assertTrue(x["positive_candidate_discovery_allowed"])
        self.assertEqual("CORROBORATED", x["administrative_identifier_candidate_max_status"])
        self.assertFalse(x["negative_exhaustive_conclusion_allowed"])
        self.assertFalse(x["pncp_no_match_allowed"])
        self.assertTrue(x["primary_municipal_verification_required"])
        self.assertFalse(x["automatic_financial_identity"])
        self.assertFalse(x["automatic_transaction_identity"])
        self.assertFalse(x["automatic_supplier_linkage"])

    def test_authorization_consumed_by_one_invocation(self):
        a = self.c["authorization_consumption"]
        self.assertTrue(a["consume_on_single_live_open_invocation"])
        self.assertFalse(a["second_open_authorized"])
        self.assertFalse(a["retry_authorized"])

    def test_design_evidence_is_not_execution_evidence(self):
        self.assertEqual("PASS_TASK148_FRESH_RETRY_DESIGNED_NOT_EXECUTED", self.e["result"])
        self.assertTrue(self.e["execute_only_after_merge"])
        self.assertEqual(0, self.e["remote_effects"])


if __name__ == "__main__":
    unittest.main()

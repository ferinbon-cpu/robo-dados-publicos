from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "config/task150_pncp_web_preview.v1.json"


class TestTask150(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = json.loads(C.read_text(encoding="utf-8"))

    def test_current_main_and_task149_boundary_are_pinned(self):
        self.assertEqual("bd2afc3a835da5d91ee7cf38604de907ed1ac066", self.c["base_sha"])
        self.assertEqual(149, self.c["prior_task"]["task"])
        self.assertEqual("STOP_DIRECT_DOWNLOAD_URL_NOT_PREVIEWED_PRE_SOURCE", self.c["prior_task"]["result"])

    def test_fresh_authorization_is_post_task149(self):
        a = self.c["fresh_owner_authorization"]
        self.assertEqual("Prossiga autorizado", a["instruction"])
        self.assertTrue(a["authorized_after_task149_stop"])
        self.assertTrue(a["single_web_open_authorized"])

    def test_exact_url_and_page_size(self):
        s = self.c["source"]
        self.assertEqual(50, s["page_size"])
        self.assertTrue(s["exact_url"].endswith("pagina=1&tamanhoPagina=50"))

    def test_one_web_open_only(self):
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

from copy import deepcopy
from pathlib import Path
import unittest

from robo_dados_publicos.research.task148_pncp_direct_download_gate import (
    Task148Stop,
    load,
    validate_task148_contract,
)

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"config/task148_pncp_direct_download_gate.v1.json"


class TestTask148(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=load(P)

    def test_exact_url_and_page_size_are_pinned(self):
        s=self.c["source"]
        self.assertEqual(50,s["page_size"])
        self.assertTrue(s["exact_url"].endswith("pagina=1&tamanhoPagina=50"))

    def test_one_direct_download_only(self):
        t=self.c["future_transport"]
        self.assertEqual("DIRECT_TEMPORARY_DOWNLOAD",t["kind"])
        self.assertEqual(1,t["invocations_max"])
        for k in ("retry","search_queries","clicks","alternate_endpoints","pagination_followups"):
            self.assertEqual(0,t[k])

    def test_raw_payload_may_be_temporary_but_not_persisted(self):
        t=self.c["future_transport"]
        self.assertTrue(t["temporary_local_payload_allowed"])
        self.assertFalse(t["raw_payload_git_persistence"])
        self.assertFalse(t["raw_payload_drive_persistence"])

    def test_negative_and_identity_promotions_are_blocked(self):
        e=self.c["epistemic_semantics"]
        self.assertFalse(e["negative_exhaustive_conclusion_allowed"])
        self.assertFalse(e["pncp_no_match_from_transport_failure_or_empty_result_allowed"])
        self.assertFalse(e["automatic_financial_identity"])
        self.assertFalse(e["automatic_transaction_identity"])
        self.assertFalse(e["automatic_supplier_linkage"])

    def test_scope_widening_fails_closed(self):
        x=deepcopy(self.c)
        x["future_transport"]["invocations_max"]=2
        with self.assertRaisesRegex(Task148Stop,"TASK148_INVOCATIONS"):
            validate_task148_contract(x)


if __name__=="__main__":
    unittest.main()

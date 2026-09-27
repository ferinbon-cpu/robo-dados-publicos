from pathlib import Path
import json,unittest

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/"docs/evidence/TASK_131_WEB_INDEX_PROCUREMENT_IDENTIFIER_0.8.0.json"

class TestTask131Closure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e=json.loads(E.read_text(encoding="utf-8"))

    def test_bounded_search_budget(self):
        x=self.e["search_execution"]
        self.assertEqual(8,x["query_family_count"])
        self.assertEqual(16,x["search_query_count"])
        self.assertEqual(0,x["direct_pdf_open_requests"])
        self.assertEqual(0,x["pncp_requests"])
        self.assertEqual(0,x["retry"])

    def test_no_stable_identifier_was_observed(self):
        self.assertEqual([],self.e["candidate_identifiers"])
        self.assertTrue(all(
            hit["stable_administrative_identifier_observed"] is False
            for hit in self.e["relevant_index_hits"]
        ))

    def test_no_absence_or_identity_promotion(self):
        i=self.e["interpretation"]
        self.assertTrue(i["bounded_index_no_identifier_observed"])
        self.assertFalse(i["proves_no_identifier_exists"])
        self.assertFalse(i["financial_identity_changed"])
        self.assertFalse(i["transaction_identity_changed"])

    def test_next_surface_is_procurement_not_weak_contract_join(self):
        n=self.e["next_action"]
        self.assertEqual("DISCOVER_PROCUREMENT_PUBLICATION_OR_PURCHASE_SURFACE_BY_EXACT_TITLE",n["status"])
        self.assertFalse(n["weak_contract_join_authorized"])

if __name__=="__main__": unittest.main()

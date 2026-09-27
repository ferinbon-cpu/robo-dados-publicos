from pathlib import Path
import json,unittest

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/"docs/evidence/TASK_130_PNCP_LIMEIRA_CONTRACTS_PAGES3_5_0.8.0.json"
A=ROOT/"docs/evidence/TASK_130_OWNER_AUTHORIZATION_PRE_RUN_0.8.0.json"
W=ROOT/".github/workflows/task-130-pncp-pages3-5-once.yml"

class TestTask130Closure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e=json.loads(E.read_text(encoding="utf-8"))
        cls.a=json.loads(A.read_text(encoding="utf-8"))

    def test_full_2023_row_coverage_is_exhaustive(self):
        c=self.e["combined_coverage"]
        self.assertEqual(2023,c["rows_scanned_total"])
        self.assertEqual(2023,c["total_registros"])
        self.assertEqual([1,2,3,4,5],c["pages_scanned"])
        self.assertTrue(c["exhaustive_within_query_scope"])
        self.assertEqual(0,c["strong_policy_candidate_count"])

    def test_bounded_no_match_is_not_global_absence(self):
        b=self.e["bounded_conclusion"]
        self.assertEqual("NO_MATCH_WITHIN_PNCP_CNPJ_DATE_SCOPE_ONLY",b["status"])
        self.assertFalse(b["proves_no_eiti_contract_exists"])
        self.assertFalse(b["proves_no_eiti_execution"])
        self.assertTrue(b["search_outside_fields_or_scope_not_covered"])
        self.assertTrue(b["weak_terms_do_not_qualify_alone"])

    def test_live_request_budget_and_hashes_are_pinned(self):
        x=self.e["live_execution"]
        self.assertEqual(3,x["request_attempts"])
        self.assertEqual(0,x["retry_performed"])
        self.assertEqual([3,4,5],[p["page"] for p in x["pages"]])
        self.assertEqual([500,500,23],[p["rows"] for p in x["pages"]])
        self.assertTrue(all(p["http_status"]==200 for p in x["pages"]))
        self.assertEqual(
            "9a12b1ab4ac88b10a29e2da307b3ddc90f56d4dc8d558559a8b0df07b18eea06",
            x["result_sha256"],
        )

    def test_artifact_and_authorization_consumed(self):
        self.assertEqual(9961975677,self.e["artifact"]["id"])
        self.assertEqual(
            "19783f5b82f17d81fc29be2018d0ffff2168f54ab1370756cb74d2c770d2f536",
            self.e["artifact"]["zip_sha256"],
        )
        self.assertEqual("CONSUMED_EXHAUSTIVE_SUCCESS_NO_RETRY",self.a["status"])
        self.assertFalse(self.a["future_execution_authorized"])
        self.assertTrue(self.a["consumed_by"]["workflow_single_use_consumed"])

    def test_live_workflow_removed(self):
        self.assertFalse(W.exists())

if __name__=="__main__": unittest.main()

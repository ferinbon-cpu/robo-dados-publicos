from copy import deepcopy
from pathlib import Path
import json
import unittest

from robo_dados_publicos.research.task126_tcesp_html_discovery import (
    Task126Stop, load_task126_contract, validate_task126_contract
)

ROOT=Path(__file__).resolve().parents[1]
C=ROOT/"config/task126_tcesp_html_index_discovery.v1.json"
E=ROOT/"docs/evidence/TASK_126_TCESP_HTML_INDEX_DISCOVERY_0.8.0.json"

class TestTask126(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=load_task126_contract(C)
        cls.e=json.loads(E.read_text(encoding="utf-8"))

    def test_scope_history_is_not_rewritten(self):
        self.assertFalse(self.c["preflight_ci_before_search"])
        self.assertTrue(self.e["scope_control"]["issue_created_before_search"])
        self.assertFalse(self.e["scope_control"]["preflight_ci_before_search"])

    def test_exact_search_budget_is_preserved(self):
        self.assertEqual(8,self.e["execution"]["query_family_count"])
        self.assertEqual(15,self.e["execution"]["search_query_count"])
        self.assertEqual(1,self.e["execution"]["direct_open_attempts"])
        self.assertEqual("TIMEOUT_NO_PAGE_CONTENT",self.e["execution"]["direct_open_result"])

    def test_no_candidate_is_not_global_no_match(self):
        self.assertEqual([],self.e["candidates"])
        i=self.e["interpretation"]
        self.assertEqual("NO_INDEXED_LIMEIRA_POLICY_CANDIDATE_OBSERVED",i["bounded_index_status"])
        self.assertFalse(i["global_no_match"])
        self.assertFalse(i["proves_no_eiti_execution"])
        self.assertFalse(i["proves_no_2607004_record"])
        self.assertTrue(i["search_index_may_be_incomplete"])

    def test_structure_controls_are_not_policy_candidates(self):
        controls=self.e["structure_controls"]
        self.assertEqual(3,len(controls))
        self.assertTrue(all("NOT_POLICY_CANDIDATE" in x["classification"] for x in controls))
        self.assertTrue(self.e["interpretation"]["generic_program_2001_control_is_not_eiti_identity"])

    def test_evidence_guard_weakening_fails_closed(self):
        mutations=[
            ("index_absence_is_global_no_match",True),
            ("other_municipality_is_limeira_evidence",True),
            ("code_2607004_alone_is_policy_bridge",True),
            ("text_similarity_can_create_candidate",True),
        ]
        for key,value in mutations:
            c=deepcopy(self.c); c["evidence_rules"][key]=value
            with self.assertRaises(Task126Stop):
                validate_task126_contract(c)

    def test_next_action_is_primary_municipal_discovery(self):
        n=self.e["next_action"]
        self.assertEqual("DISCOVER_PRIMARY_MUNICIPAL_GRANULAR_EXECUTION_SURFACE",n["status"])
        self.assertIsNone(n["tcesp_candidate_primary_verification_target"])

if __name__=="__main__":
    unittest.main()

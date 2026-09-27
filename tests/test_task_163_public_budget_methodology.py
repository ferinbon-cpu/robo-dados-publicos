from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from robo_dados_publicos.research.public_budget_methodology import validate

M = ROOT / "config/public_budget_methodology.v1.json"
O = ROOT / "config/public_budget_observation_contract.v1.json"
R = ROOT / "config/public_budget_question_router.v1.json"


class TestTask163PublicBudgetMethodology(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = json.loads(M.read_text(encoding="utf-8"))
        cls.o = json.loads(O.read_text(encoding="utf-8"))
        cls.r = json.loads(R.read_text(encoding="utf-8"))

    def test_validator(self):
        out = validate()
        self.assertEqual("VALID", out["status"])
        self.assertEqual("James Giacomoni, 18th edition", out["method_reference"])
        self.assertGreaterEqual(out["interpretation_rule_count"], 15)

    def test_knowledge_layers_are_separated(self):
        layers = {x["id"]: x for x in self.m["knowledge_layers"]}
        self.assertIn("current_legal_rule", layers["METHODOLOGICAL_ACADEMIC"]["cannot_prove"])
        self.assertIn("municipal_empirical_fact", layers["METHODOLOGICAL_ACADEMIC"]["cannot_prove"])

    def test_budget_stages_are_not_collapsed(self):
        ids = {x["id"] for x in self.m["evidence_stages"]}
        for stage in ["PLANNING_INTENT", "BUDGET_AUTHORIZATION_INITIAL", "PROCUREMENT", "COMMITMENT", "LIQUIDATION", "PAYMENT"]:
            self.assertIn(stage, ids)
        forbidden = set(self.m["forbidden_promotions"])
        self.assertIn("PPA_VALUE_TO_EXECUTION", forbidden)
        self.assertIn("LOA_APPROPRIATION_TO_PAYMENT", forbidden)
        self.assertIn("PNCP_PROCUREMENT_TO_PAYMENT", forbidden)

    def test_observation_contract_requires_provenance_and_semantics(self):
        req = set(self.o["required_top_level"])
        self.assertIn("provenance", req)
        self.assertIn("amounts", req)
        self.assertIn("policy_linkage", req)
        self.assertEqual("UNKNOWN_NOT_INFERRED", self.o["field_contract"]["classifications"]["missing_value"])

    def test_question_router_knows_source_capabilities(self):
        caps = {x["source_family"]: x for x in self.r["source_capabilities"]}
        self.assertIn("payment", caps["PNCP"]["cannot_answer_alone"])
        self.assertIn("commitment", caps["LOA"]["cannot_answer_alone"])
        self.assertIn("current_law", caps["ACADEMIC_METHOD"]["cannot_answer_alone"])

    def test_execution_question_keeps_three_stages(self):
        routes = {x["id"]: x for x in self.r["question_routes"]}
        self.assertEqual(
            ["COMMITTED_VALUE", "LIQUIDATED_VALUE", "PAID_VALUE"],
            routes["Q_EXECUTED"]["required_semantic_split"],
        )

    def test_multiyear_real_change_requires_deflator(self):
        routes = {x["id"]: x for x in self.r["question_routes"]}
        self.assertEqual(["deflator_id", "base_date"], routes["Q_MULTIYEAR"]["real_change_requires"])
        self.assertEqual("REPORT_NOMINAL_ONLY", routes["Q_MULTIYEAR"]["fallback"])

    def test_effect_question_is_fail_closed(self):
        routes = {x["id"]: x for x in self.r["question_routes"]}
        self.assertEqual("CAUSAL_INFERENCE_NOT_AUTHORIZED", routes["Q_EFFECT"]["fallback"])


if __name__ == "__main__":
    unittest.main()

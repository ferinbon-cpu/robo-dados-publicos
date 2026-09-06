import json
import unittest
from pathlib import Path

from robo_dados_publicos.research.task169_eiti_accounting_execution_source_router import (
    Task169Stop,
    load_router,
    validate_router,
)


ROUTER = Path("config/eiti_accounting_execution_source_router.v1.json")


class TestTask169EitiAccountingExecutionSourceRouter(unittest.TestCase):
    def test_router_passes_offline_validator(self):
        result = validate_router(ROUTER)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["source_class_count"], 4)
        self.assertEqual(result["transaction_gate_count"], 3)
        self.assertFalse(result["live_authorized"])

    def test_primary_municipal_sources_precede_control_source(self):
        router = load_router(ROUTER)
        ids = [x["id"] for x in router["source_classes"]]
        self.assertEqual(ids[0], "LIMEIRA_PRIMARY_TRANSPARENCY_EXPENSE_DETAIL")
        self.assertEqual(ids[-1], "TCE_CONTROL_GRANULAR_EXECUTION")

    def test_policy_financial_identity_requires_stable_budget_key(self):
        router = load_router(ROUTER)
        required = router["minimum_policy_financial_identity_bundle"]["all_required"]
        self.assertIn("policy_link_basis_explicit", required)
        self.assertIn("stable_budget_key_explicit", required)
        self.assertIn("institutional_unit_explicit", required)
        self.assertIn("amount_semantic_explicit", required)

    def test_task122_and_pncp_weak_joins_are_forbidden(self):
        router = load_router(ROUTER)
        weak = set(router["minimum_policy_financial_identity_bundle"]["not_sufficient"])
        self.assertIn("program_2001_alone", weak)
        self.assertIn("capl_2607004_alone", weak)
        self.assertIn("same_or_similar_value", weak)
        self.assertIn("pncp_purchase_or_contract_without_accounting_link", weak)

    def test_execution_stages_remain_distinct(self):
        router = load_router(ROUTER)
        gates = router["transaction_stage_gates"]
        self.assertEqual([x["stage"] for x in gates], ["COMMITMENT", "LIQUIDATION", "PAYMENT"])
        self.assertEqual(
            [x["amount_semantic"] for x in gates],
            ["COMMITTED_VALUE", "LIQUIDATED_VALUE", "PAID_VALUE"],
        )

    def test_fresh_authorization_required_for_new_source_scope(self):
        router = load_router(ROUTER)
        auth = router["authorization_boundary"]
        self.assertFalse(auth["new_non_pncp_live_read_authorized"])
        self.assertTrue(auth["fresh_explicit_source_scope_authorization_required"])
        self.assertEqual(auth["t0_network_requests"], 0)

    def test_tampered_live_authorization_fails_closed(self):
        obj = json.loads(ROUTER.read_text(encoding="utf-8"))
        obj["authorization_boundary"]["new_non_pncp_live_read_authorized"] = True
        temp = Path("tests/.task169_tampered_router.json")
        try:
            temp.write_text(json.dumps(obj), encoding="utf-8")
            with self.assertRaises(Task169Stop):
                validate_router(temp)
        finally:
            if temp.exists():
                temp.unlink()


if __name__ == "__main__":
    unittest.main()

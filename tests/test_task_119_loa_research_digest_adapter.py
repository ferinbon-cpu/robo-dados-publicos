from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from robo_dados_publicos.research.loa_research_digest_adapter import (
    LoaResearchDigestAdapterStop,
    build_loa_research_packet,
    load_adapter_contract,
    validate_contract,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config" / "loa_research_digest_adapter.v1.json"


class TestTask119LoaResearchDigestAdapter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = load_adapter_contract(CONTRACT_PATH, root=ROOT)
        cls.result = build_loa_research_packet(deepcopy(cls.contract), root=ROOT)

    def test_adapter_builds_ten_authorization_segments(self):
        self.assertEqual("PASS_TASK119_LOA_REPOSITORY_EVIDENCE_ADAPTER", self.result["status"])
        self.assertEqual(10, self.result["authorization_observation_count"])
        self.assertEqual(2, self.result["action_total_count"])
        self.assertEqual(4, self.result["expense_group_component_count"])
        self.assertEqual(4, self.result["funding_source_component_count"])
        self.assertEqual(10, len(self.result["packet"]["segments"]))

    def test_all_amounts_are_authorization_only(self):
        for segment in self.result["packet"]["segments"]:
            amounts = segment["structured"]["amounts"]
            self.assertEqual(1, len(amounts))
            self.assertEqual("AUTHORIZATION", amounts[0]["execution_stage"])

    def test_budget_keys_and_amounts_do_not_create_eiti_identity_without_policy_signal(self):
        digest = self.result["research_digest"]
        self.assertEqual([], digest["financial_identity_candidates"])
        self.assertIn("QUALIFIED_POLICY_SIGNAL_NOT_OBSERVED", digest["evidence_gaps"])
        self.assertFalse(any(group["qualified_policy_signal"] for group in digest["context_groups"]))
        self.assertTrue(all(group["stable_accounting_keys"] for group in digest["context_groups"]))
        self.assertTrue(all(group["amount_observations"] for group in digest["context_groups"]))

    def test_action_total_keys_include_program_action_unit_and_function(self):
        totals = [
            segment for segment in self.result["packet"]["segments"]
            if segment["locator"]["representation_level"] == "ACTION_TOTAL"
        ]
        self.assertEqual(2, len(totals))
        for segment in totals:
            key_types = {key["key_type"] for key in segment["structured"]["accounting_keys"]}
            self.assertTrue({"org","unit","function","subfunction","program","action"}.issubset(key_types))

    def test_funding_and_expense_group_components_are_preserved(self):
        funding = [
            segment for segment in self.result["packet"]["segments"]
            if segment["locator"]["representation_level"] == "FUNDING_SOURCE_COMPONENT"
        ]
        groups = [
            segment for segment in self.result["packet"]["segments"]
            if segment["locator"]["representation_level"] == "EXPENSE_GROUP_COMPONENT"
        ]
        self.assertEqual(4, len(funding))
        self.assertEqual(4, len(groups))
        self.assertTrue(all(any(k["key_type"] == "funding_source" for k in s["structured"]["accounting_keys"]) for s in funding))
        self.assertTrue(all(any(k["key_type"] == "expense_group" for k in s["structured"]["accounting_keys"]) for s in groups))

    def test_visual_28m_is_preserved_and_29m_text_layer_is_not_silently_used(self):
        divergence = self.result["material_text_visual_divergence"]
        self.assertTrue(divergence["observed"])
        self.assertEqual(29000000, divergence["text_layer_amount_brl"])
        self.assertEqual(28000000, divergence["visual_source_amount_brl"])
        self.assertFalse(divergence["silent_repair"])
        self.assertEqual(28000000, self.result["canonical_action_2720_appropriation_brl"])
        total_2720 = [
            s for s in self.result["packet"]["segments"]
            if s["segment_id"] == "SEG:LOA2026_ACTION_2720_TOTAL"
        ][0]
        self.assertEqual("28000000", total_2720["structured"]["amounts"][0]["amount_brl"])

    def test_program_2001_and_generic_actions_are_not_promoted(self):
        self.assertFalse(self.result["financial_identity_promoted"])
        self.assertFalse(self.result["research_digest"]["promotion_performed"])

    def test_source_role_is_budget_primary(self):
        source = self.result["packet"]["source"]
        self.assertEqual("BUDGET_PRIMARY", source["source_role"])
        self.assertEqual("LOA", source["source_family"])
        self.assertEqual(
            "37ea54d85cc5428622b296881a279a17e1aeefd7574576e7a3414443bbee64c4",
            source["source_sha256"],
        )

    def test_breakdown_tampering_fails_closed(self):
        # The contract is pinned to TASK048; source tampering is represented here
        # by changing its blob pin and must stop before adapter construction.
        contract = deepcopy(self.contract)
        contract["input"]["task048_git_blob_sha"] = "0" * 40
        with self.assertRaisesRegex(LoaResearchDigestAdapterStop, "TASK048_BLOB"):
            validate_contract(contract, root=ROOT)

    def test_commitment_or_payment_enablement_fails_closed(self):
        for key in ("commitment_allowed","liquidation_allowed","payment_allowed"):
            contract = deepcopy(self.contract)
            contract["monetary_semantics"][key] = True
            with self.assertRaisesRegex(LoaResearchDigestAdapterStop, "MONETARY"):
                validate_contract(contract, root=ROOT)

    def test_all_effects_zero_and_result_deterministic(self):
        self.assertTrue(all(value == 0 for value in self.result["effects"].values()))
        self.assertFalse(self.result["persistence_authorized"])
        other = build_loa_research_packet(deepcopy(self.contract), root=ROOT)
        self.assertEqual(self.result["result_sha256"], other["result_sha256"])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from robo_dados_publicos.research.ppa_research_digest_adapter import (
    PpaResearchDigestAdapterStop,
    build_ppa_research_packets,
    load_adapter_contract,
    validate_contract,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config" / "ppa_research_digest_adapter.v1.json"


class TestTask117PpaResearchDigestAdapter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = load_adapter_contract(CONTRACT_PATH, root=ROOT)
        cls.result = build_ppa_research_packets(deepcopy(cls.contract), root=ROOT)

    def test_adapter_builds_two_versioned_packets(self):
        self.assertEqual("PASS_TASK117_PPA_REPOSITORY_EVIDENCE_ADAPTER", self.result["status"])
        self.assertEqual(2, self.result["packet_count"])
        self.assertEqual(
            ["DOC:PPA_6659_2021", "DOC:PPA_7213_2025"],
            [p["source"]["document_id"] for p in self.result["packets"]],
        )
        self.assertTrue(all(p["source"]["source_role"] == "PLANNING_PRIMARY" for p in self.result["packets"]))
        self.assertTrue(all(p["source"]["source_family"] == "PPA" for p in self.result["packets"]))

    def test_2022_primary_excerpt_rediscovers_planning_signal_without_financial_bridge(self):
        digest = self.result["research_digests"][0]
        self.assertEqual([], digest["financial_identity_candidates"])
        self.assertTrue(
            any(
                hit["term"] == "indice de alunos em Educacao Integral"
                and hit["qualified"]
                for hit in digest["ontology_hits"]
            )
        )
        self.assertIn("STABLE_ACCOUNTING_LINKAGE_KEY_NOT_OBSERVED", digest["evidence_gaps"])
        self.assertIn("AMOUNT_AND_EXECUTION_STAGE_NOT_OBSERVED", digest["evidence_gaps"])

    def test_2026_indicator_has_stable_program_unit_keys_but_no_execution_amount(self):
        packet = self.result["packets"][1]
        indicator = packet["segments"][0]
        keys = {(k["key_type"], k["value"]) for k in indicator["structured"]["accounting_keys"]}
        self.assertIn(("program", "2001"), keys)
        self.assertIn(("unit", "10.00.00"), keys)
        self.assertEqual([], indicator["structured"]["amounts"])

        digest = self.result["research_digests"][1]
        self.assertEqual([], digest["financial_identity_candidates"])
        self.assertTrue(any(h["term"] == "indice de alunos em Educacao Integral" for h in digest["ontology_hits"]))
        self.assertIn("AMOUNT_AND_EXECUTION_STAGE_NOT_OBSERVED", digest["evidence_gaps"])
        self.assertIn("SAME_SEGMENT_FINANCIAL_BRIDGE_NOT_OBSERVED", digest["evidence_gaps"])

    def test_selected_generic_actions_do_not_become_policy_signals(self):
        digest = self.result["research_digests"][1]
        action_groups = [
            group for group in digest["context_groups"]
            if group["segment_id"].startswith("SEG:PPA_2026_2029_ACTION_")
        ]
        self.assertEqual(3, len(action_groups))
        self.assertTrue(all(group["qualified_policy_signal"] is False for group in action_groups))
        self.assertTrue(
            all(group["stable_accounting_keys"] for group in action_groups)
        )

    def test_ppa_planned_values_never_enter_task116_execution_amounts(self):
        for packet in self.result["packets"]:
            for segment in packet["segments"]:
                self.assertEqual([], segment["structured"]["amounts"])
        self.assertFalse(self.result["planned_values_emitted_as_execution_amounts"])

    def test_task049_bounded_negative_action_search_is_preserved(self):
        negative = self.result["negative_action_label_search"]
        self.assertEqual("NO_MATCH", negative["result"])
        self.assertEqual(27, negative["rows_checked"])
        self.assertTrue(negative["exhaustive_within_declared_action_table_scope"])
        self.assertFalse(negative["proves_no_eiti_spending"])
        self.assertEqual("FORBIDDEN", negative["financial_attribution_to_generic_actions"])

    def test_no_financial_identity_is_promoted(self):
        self.assertFalse(self.result["financial_identity_promoted"])
        self.assertTrue(
            all(digest["promotion_performed"] is False for digest in self.result["research_digests"])
        )

    def test_all_effects_are_zero(self):
        self.assertTrue(all(value == 0 for value in self.result["effects"].values()))
        self.assertFalse(self.result["persistence_authorized"])

    def test_contract_blob_drift_fails_closed(self):
        contract = deepcopy(self.contract)
        contract["inputs"]["task107"]["git_blob_sha"] = "0" * 40
        with self.assertRaisesRegex(PpaResearchDigestAdapterStop, "TASK107_BLOB"):
            validate_contract(contract, root=ROOT)

    def test_monetary_relabeling_cannot_be_enabled(self):
        contract = deepcopy(self.contract)
        contract["monetary_semantics"]["emit_task116_amount_observations"] = True
        with self.assertRaisesRegex(PpaResearchDigestAdapterStop, "MONETARY_EMIT"):
            validate_contract(contract, root=ROOT)

    def test_result_is_deterministic(self):
        other = build_ppa_research_packets(deepcopy(self.contract), root=ROOT)
        self.assertEqual(self.result["result_sha256"], other["result_sha256"])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from robo_dados_publicos.research.siope_fundeb_research_digest_adapter import (
    SiopeFundebResearchDigestAdapterStop,
    build_siope_fundeb_research_packet,
    load_adapter_contract,
    validate_contract,
)

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"config/siope_fundeb_research_digest_adapter.v1.json"

class TestTask121SiopeFundebResearchDigestAdapter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=load_adapter_contract(CONTRACT,root=ROOT)
        cls.result=build_siope_fundeb_research_packet(deepcopy(cls.contract),root=ROOT)

    def test_exact_source_identity_is_bound_to_task056_semantics(self):
        self.assertEqual("PASS_TASK121_SIOPE_FUNDEB_REPOSITORY_EVIDENCE_ADAPTER",self.result["status"])
        self.assertEqual(
            "d2b7f7638222bc9788f6d42df11126d2e3aa57cb4204450914c98d9400bf0bbe",
            self.result["source_binary_identity_sha256"],
        )
        source=self.result["packet"]["source"]
        self.assertEqual("ACCOUNTING_EXECUTION_PRIMARY",source["source_role"])
        self.assertEqual("SIOPE",source["source_family"])

    def test_three_reporting_bucket_observations_are_emitted(self):
        segments=self.result["packet"]["segments"]
        self.assertEqual(3,len(segments))
        amounts=[s["structured"]["amounts"][0] for s in segments]
        self.assertTrue(all(a["execution_stage"]=="REPORTING_BUCKET" for a in amounts))
        self.assertEqual(["0.00","1315673.39","0.00"],[a["amount_brl"] for a in amounts])

    def test_fomento_eti_active_alias_is_qualified_on_all_segments(self):
        digest=self.result["research_digest"]
        self.assertEqual(64,digest["ontology_term_count"])
        hits=[h for h in digest["ontology_hits"] if h["term"]=="FOMENTO ETI"]
        self.assertEqual(3,len(hits))
        self.assertTrue(all(h["qualified"] for h in hits))
        self.assertTrue(all(h["family"]=="X_DISCOVERED_COMPOSITE_ALIASES" for h in hits))
        self.assertTrue(all("POLICY_SIGNAL" in h["semantic_roles"] for h in hits))
        self.assertTrue(all("FINANCING_SIGNAL" in h["semantic_roles"] for h in hits))

    def test_financing_signals_and_reporting_amounts_are_visible(self):
        digest=self.result["research_digest"]
        self.assertTrue(any("FUNDEB" in group["financing_signal_terms"] for group in digest["context_groups"]))
        self.assertTrue(any(
            any(term.casefold() == "fomento" for term in group["financing_signal_terms"])
            for group in digest["context_groups"]
        ))
        self.assertTrue(all(group["amount_observations"] for group in digest["context_groups"]))

    def test_missing_stable_key_blocks_financial_bridge(self):
        digest=self.result["research_digest"]
        self.assertEqual([],digest["financial_identity_candidates"])
        self.assertIn("STABLE_ACCOUNTING_LINKAGE_KEY_NOT_OBSERVED",digest["evidence_gaps"])
        self.assertIn("SAME_SEGMENT_FINANCIAL_BRIDGE_NOT_OBSERVED",digest["evidence_gaps"])
        self.assertTrue(all(group["stable_accounting_keys"]==[] for group in digest["context_groups"]))

    def test_reporting_identity_is_scoped_and_transaction_identity_unknown(self):
        self.assertEqual("PROVEN_SCOPED",self.result["reporting_identity"]["status"])
        self.assertEqual("FIRST_BIMESTER_2026_ONLY",self.result["reporting_identity"]["period_scope"])
        self.assertEqual("FUNDEB_ONLY",self.result["reporting_identity"]["funding_scope"])
        transaction=self.result["transaction_identity"]
        self.assertEqual("UNKNOWN",transaction["status"])
        self.assertFalse(transaction["stable_accounting_key_found"])
        self.assertFalse(self.result["financial_identity_promoted"])

    def test_no_individual_execution_stage_is_invented(self):
        forbidden={"COMMITMENT","LIQUIDATION","PAYMENT"}
        stages={
            amount["execution_stage"]
            for segment in self.result["packet"]["segments"]
            for amount in segment["structured"]["amounts"]
        }
        self.assertTrue(stages.isdisjoint(forbidden))
        self.assertEqual({"REPORTING_BUCKET"},stages)

    def test_task120_hash_tamper_fails_closed(self):
        contract=deepcopy(self.contract)
        contract["inputs"]["task120"]["git_blob_sha"]="0"*40
        with self.assertRaisesRegex(SiopeFundebResearchDigestAdapterStop,"TASK120_BLOB"):
            validate_contract(contract,root=ROOT)

    def test_transaction_event_claims_cannot_be_enabled(self):
        contract=deepcopy(self.contract)
        contract["segments"]["transaction_event_claims_allowed"]=True
        with self.assertRaisesRegex(SiopeFundebResearchDigestAdapterStop,"TRANSACTION_EVENT_GUARD"):
            validate_contract(contract,root=ROOT)

    def test_all_effects_zero_and_deterministic(self):
        self.assertTrue(all(value==0 for value in self.result["effects"].values()))
        self.assertFalse(self.result["persistence_authorized"])
        other=build_siope_fundeb_research_packet(deepcopy(self.contract),root=ROOT)
        self.assertEqual(self.result["result_sha256"],other["result_sha256"])

if __name__=="__main__": unittest.main()

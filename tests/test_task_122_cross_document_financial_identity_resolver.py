from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from robo_dados_publicos.research.cross_document_financial_identity_resolver import (
    CrossDocumentFinancialIdentityResolverStop,
    load_resolver_contract,
    resolve_eiti_cross_document_identity,
    validate_contract,
)

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"config/eiti_cross_document_financial_identity_resolver.v1.json"

class TestTask122CrossDocumentFinancialIdentityResolver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=load_resolver_contract(CONTRACT,root=ROOT)
        cls.result=resolve_eiti_cross_document_identity(deepcopy(cls.contract),root=ROOT)

    def test_current_resolution_stops_without_stable_policy_accounting_key(self):
        self.assertEqual(
            "STOP_NO_STABLE_POLICY_TO_ACCOUNTING_EXECUTION_KEY",
            self.result["resolution_status"],
        )
        self.assertEqual([],self.result["cross_document_financial_identity_candidates"])
        self.assertEqual("UNKNOWN",self.result["financial_identity"]["status"])
        self.assertEqual("UNKNOWN",self.result["transaction_identity"]["status"])
        self.assertFalse(self.result["financial_identity"]["promotion_performed"])
        self.assertFalse(self.result["transaction_identity"]["promotion_performed"])

    def test_ppa_loa_program_2001_overlap_is_observed_but_rejected(self):
        self.assertEqual(
            [{"key_type":"program","value":"2001"}],
            self.result["same_dimension_shared_keys"]["ppa_loa"],
        )
        rejected=self.result["rejected_shared_keys"]
        self.assertEqual(1,len(rejected))
        self.assertEqual("program",rejected[0]["key_type"])
        self.assertEqual("2001",rejected[0]["value"])
        self.assertEqual("REJECTED_NON_SPECIFIC_POLICY_BRIDGE",rejected[0]["status"])
        self.assertEqual("GENERIC_PROGRAM_NOT_EITI_SPECIFIC",rejected[0]["reason"])
        self.assertEqual("NOT_PROVEN",rejected[0]["task049_program_to_explicit_eiti_action_linkage"])
        self.assertFalse(rejected[0]["task051_program_total_fallback_allowed"])

    def test_siope_has_no_stable_key_intersection_with_ppa_or_loa(self):
        shared=self.result["same_dimension_shared_keys"]
        self.assertEqual([],shared["ppa_siope"])
        self.assertEqual([],shared["loa_siope"])
        self.assertFalse(
            self.result["anchors"]["policy_finance_reporting"]["stable_accounting_key_found"]
        )

    def test_same_numeric_value_across_dimensions_is_not_a_match(self):
        observations=self.result["same_value_different_dimension_observations"]["ppa_loa"]
        self.assertTrue(any(
            item["value"]=="10.00.00"
            and item["left_key_type"]=="unit"
            and item["right_key_type"]=="org"
            and item["match_status"]=="REJECTED_DIFFERENT_IDENTITY_DIMENSION"
            for item in observations
        ))

    def test_2607004_is_a_non_admissible_legacy_clue(self):
        clue=self.result["legacy_clues"]["2607004"]
        self.assertEqual("HYPOTHESIS_ONLY_NOT_ADMISSIBLE_AS_PROVEN_KEY",clue["status"])
        self.assertFalse(clue["can_create_policy_identity"])
        self.assertFalse(clue["can_create_transaction_identity"])

    def test_acquisition_packet_is_specific(self):
        packet=self.result["acquisition_packet"]
        self.assertEqual(
            "EXPLICIT_EITI_COST_CENTER_SUBACTION_OR_EXECUTION_TAG",
            packet["priority_order"][0],
        )
        self.assertTrue({
            "EXPLICIT_EITI_OR_EQUIVALENT_POLICY_MARKER",
            "STABLE_ACCOUNTING_IDENTIFIER",
            "SOURCE_PROVENANCE",
        }.issubset(set(packet["immediate_unlock_requirements"])))
        self.assertTrue({
            "EXECUTION_DOCUMENT_OR_EVENT_ID",
            "AMOUNT",
            "DATE_OR_PERIOD",
            "EXECUTION_STAGE",
        }.issubset(set(packet["transaction_chain_requirements"])))
        self.assertEqual(
            "FIND_PRIMARY_GRANULAR_RECORD_BINDING_POLICY_MARKER_TO_STABLE_ACCOUNTING_IDENTIFIER_AND_EXECUTION_EVENT",
            packet["next_gate_objective"],
        )

    def test_forbidden_fallbacks_are_explicit(self):
        forbidden=set(self.result["forbidden_fallbacks"])
        self.assertTrue({
            "PROGRAM_2001_TOTAL",
            "GENERIC_ACTION_2690",
            "GENERIC_ACTION_2720",
            "TEXT_SIMILARITY",
            "AMOUNT_EQUALITY",
            "FOMENTO_ETI_REPORTING_BUCKET_AS_TRANSACTION_IDENTITY",
            "LEGACY_2607004_WITHOUT_PRIMARY_POLICY_AND_EVENT_BINDING",
        }.issubset(forbidden))

    def test_join_rule_weakening_fails_closed(self):
        mutations=[
            ("same_value_different_key_type_is_match",True),
            ("shared_key_automatically_policy_specific",True),
            ("program_2001_sufficient",True),
            ("generic_action_2690_sufficient",True),
            ("generic_action_2720_sufficient",True),
            ("text_similarity_allowed",True),
            ("amount_equality_allowed",True),
            ("reporting_bucket_is_transaction_identity",True),
        ]
        for key,value in mutations:
            contract=deepcopy(self.contract)
            contract["join_rules"][key]=value
            with self.assertRaises(CrossDocumentFinancialIdentityResolverStop):
                validate_contract(contract,root=ROOT)

    def test_adapter_blob_drift_fails_closed(self):
        for name in ("ppa_adapter","loa_adapter","siope_adapter"):
            contract=deepcopy(self.contract)
            contract["inputs"][name]["git_blob_sha"]="0"*40
            with self.assertRaises(CrossDocumentFinancialIdentityResolverStop):
                validate_contract(contract,root=ROOT)

    def test_all_effects_zero_and_deterministic(self):
        self.assertTrue(all(value==0 for value in self.result["effects"].values()))
        self.assertFalse(self.result["persistence_authorized"])
        other=resolve_eiti_cross_document_identity(deepcopy(self.contract),root=ROOT)
        self.assertEqual(self.result["resolution_sha256"],other["resolution_sha256"])

if __name__=="__main__": unittest.main()

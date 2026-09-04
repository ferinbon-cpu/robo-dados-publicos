from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from robo_dados_publicos.research.research_ephemeral_digest import (
    ResearchEphemeralDigestStop,
    digest_research_segments,
    load_contract,
    normalize_research_text,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config" / "research_ephemeral_digest.v1.json"


def effects(contract):
    return {key: False for key in contract["remote_effects"]}


def packet(contract, text, *, keys=None, amounts=None, role="ACCOUNTING_EXECUTION_PRIMARY", family="BUDGET_EXECUTION"):
    return {
        "schema": "RESEARCH_EPHEMERAL_DIGEST_INPUT_V1",
        "policy_profile": "EITI_LIMEIRA",
        "source": {
            "document_id": "DOC:FIXTURE_001",
            "source_role": role,
            "source_family": family,
            "source_sha256": "a" * 64,
            "adapter_contract": "FIXTURE_ADAPTER_V1",
        },
        "segments": [
            {
                "segment_id": "SEG:001",
                "text": text,
                "locator": {"page": 1, "row": 7},
                "structured": {
                    "accounting_keys": keys or [],
                    "amounts": amounts or [],
                },
            }
        ],
        "remote_effects_authorized": effects(contract),
    }


class TestTask116ResearchEphemeralDigest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = load_contract(CONTRACT_PATH, root=ROOT)

    def test_contract_preserves_base_63_and_activates_64_terms(self):
        profile = self.contract["policy_profiles"]["EITI_LIMEIRA"]
        self.assertEqual(63, profile["expected_base_total_terms"])
        self.assertEqual(64, profile["expected_active_total_terms"])
        self.assertEqual(
            {
                "A_CANONICAL_POLICY_IDENTIFIERS": 8,
                "B_LOCAL_PLANNING_AND_NORMATIVE_ALIASES": 6,
                "C_OPERATIONAL_OFFER_AND_JOURNEY_SIGNALS": 15,
                "D_FINANCING_AND_INDUCTION_SIGNALS": 13,
                "E_ACCOUNTING_AND_PLANNING_LINKAGE_KEYS": 21,
            },
            profile["expected_family_counts"],
        )

    def test_normalization_is_accent_case_hyphen_tolerant(self):
        self.assertEqual(
            "EDUCACAO INTEGRAL EM TEMPO INTEGRAL",
            normalize_research_text("Educação integral-em tempo integral"),
        )

    def test_policy_plus_stable_key_amount_and_stage_yields_candidate_only(self):
        p = packet(
            self.contract,
            "Educação em Tempo Integral. Ação 2720. Empenho para execução da política.",
            keys=[
                {
                    "key_type": "action",
                    "value": "2720",
                    "stability": "EXPLICIT_SOURCE_FIELD",
                }
            ],
            amounts=[{"amount_brl": "1250.50", "execution_stage": "COMMITMENT"}],
        )
        result = digest_research_segments(p, deepcopy(self.contract), root=ROOT)
        self.assertEqual("PASS_RESEARCH_EPHEMERAL_DIGEST_CANDIDATES_ONLY", result["status"])
        self.assertEqual(63, result["base_ontology_term_count"])
        self.assertEqual(1, result["discovered_alias_term_count"])
        self.assertEqual(64, result["ontology_term_count"])
        self.assertEqual(1, len(result["financial_identity_candidates"]))
        bridge = result["financial_identity_candidates"][0]
        self.assertEqual("CANDIDATE", bridge["status"])
        self.assertEqual("2720", bridge["stable_accounting_keys"][0]["value"])
        self.assertEqual("1250.50", bridge["amount_brl"])
        self.assertEqual("COMMITMENT", bridge["execution_stage"])
        self.assertFalse(bridge["automatic_promotion"])
        self.assertFalse(result["promotion_performed"])
        self.assertEqual([], result["evidence_gaps"])
        self.assertTrue(any(h["family"].startswith("A_") for h in result["ontology_hits"]))
        self.assertTrue(any(h["family"].startswith("E_") for h in result["ontology_hits"]))

    def test_finance_and_accounting_terms_without_policy_signal_do_not_attribute(self):
        p = packet(
            self.contract,
            "FUNDEB fonte de recursos ação 2720 empenho pagamento.",
            keys=[
                {
                    "key_type": "action",
                    "value": "2720",
                    "stability": "EXPLICIT_SOURCE_FIELD",
                }
            ],
            amounts=[{"amount_brl": "5000.00", "execution_stage": "PAYMENT"}],
        )
        result = digest_research_segments(p, deepcopy(self.contract), root=ROOT)
        self.assertEqual([], result["financial_identity_candidates"])
        self.assertIn("QUALIFIED_POLICY_SIGNAL_NOT_OBSERVED", result["evidence_gaps"])
        self.assertTrue(any(h["family"].startswith("D_") for h in result["ontology_hits"]))
        self.assertTrue(any(h["family"].startswith("E_") for h in result["ontology_hits"]))

    def test_policy_signal_without_stable_key_or_amount_remains_gap(self):
        p = packet(
            self.contract,
            "Programa Escola em Tempo Integral com jornada ampliada na rede municipal.",
        )
        result = digest_research_segments(p, deepcopy(self.contract), root=ROOT)
        self.assertEqual([], result["financial_identity_candidates"])
        self.assertIn("STABLE_ACCOUNTING_LINKAGE_KEY_NOT_OBSERVED", result["evidence_gaps"])
        self.assertIn("AMOUNT_AND_EXECUTION_STAGE_NOT_OBSERVED", result["evidence_gaps"])
        self.assertIn("SAME_SEGMENT_FINANCIAL_BRIDGE_NOT_OBSERVED", result["evidence_gaps"])

    def test_weak_numeric_signal_requires_companion_context(self):
        p = packet(self.contract, "Atendimento por 7 horas.")
        result = digest_research_segments(p, deepcopy(self.contract), root=ROOT)
        hit = [h for h in result["ontology_hits"] if h["term"] == "7 horas"]
        self.assertEqual(1, len(hit))
        self.assertFalse(hit[0]["qualified"])
        self.assertIn("QUALIFIED_POLICY_SIGNAL_NOT_OBSERVED", result["evidence_gaps"])

    def test_weak_numeric_signal_with_school_context_qualifies_but_does_not_promote(self):
        p = packet(self.contract, "Escola com jornada de 7 horas para alunos.")
        result = digest_research_segments(p, deepcopy(self.contract), root=ROOT)
        hit = [h for h in result["ontology_hits"] if h["term"] == "7 horas"]
        self.assertEqual(1, len(hit))
        self.assertTrue(hit[0]["qualified"])
        self.assertFalse(result["promotion_performed"])

    def test_source_role_boundary_is_preserved(self):
        p = packet(
            self.contract,
            "Educação em Tempo Integral ação 101 pagamento.",
            keys=[{"key_type": "action", "value": "101", "stability": "EXPLICIT_SOURCE_FIELD"}],
            amounts=[{"amount_brl": "1.00", "execution_stage": "PAYMENT"}],
            role="PLANNING_PRIMARY",
            family="PPA",
        )
        result = digest_research_segments(p, deepcopy(self.contract), root=ROOT)
        self.assertEqual("CORROBORATED", result["source_role_boundary"]["policy_linkage_max_status"])
        self.assertEqual("CANDIDATE", result["source_role_boundary"]["digest_output_status_cap"])
        self.assertEqual("CANDIDATE", result["financial_identity_candidates"][0]["status"])


    def test_fomento_eti_is_scoped_composite_policy_finance_signal_but_not_transaction_identity(self):
        p = packet(
            self.contract,
            "TOTAL DAS DESPESAS APLICADAS EM FOMENTO ETI (4%) FUNDEB PAGAMENTOS EFETUADOS",
            amounts=[{"amount_brl": "0.00", "execution_stage": "REPORTING_BUCKET"}],
            role="ACCOUNTING_EXECUTION_PRIMARY",
            family="SIOPE",
        )
        result = digest_research_segments(p, deepcopy(self.contract), root=ROOT)
        hits = [h for h in result["ontology_hits"] if h["term"] == "FOMENTO ETI"]
        self.assertEqual(1, len(hits))
        self.assertEqual("X_DISCOVERED_COMPOSITE_ALIASES", hits[0]["family"])
        self.assertTrue(hits[0]["qualified"])
        self.assertIn("POLICY_SIGNAL", hits[0]["semantic_roles"])
        self.assertIn("FINANCING_SIGNAL", hits[0]["semantic_roles"])
        self.assertEqual("FINANCIAL_REPORTING_ONLY", hits[0]["policy_signal_scope"])
        self.assertEqual([], result["financial_identity_candidates"])
        self.assertIn("STABLE_ACCOUNTING_LINKAGE_KEY_NOT_OBSERVED", result["evidence_gaps"])
        self.assertIn("FOMENTO ETI", result["context_groups"][0]["financing_signal_terms"])

    def test_fomento_eti_alias_requires_accounting_execution_source_role(self):
        p = packet(
            self.contract,
            "FOMENTO ETI",
            role="PLANNING_PRIMARY",
            family="PPA",
        )
        result = digest_research_segments(p, deepcopy(self.contract), root=ROOT)
        hit = [h for h in result["ontology_hits"] if h["term"] == "FOMENTO ETI"][0]
        self.assertFalse(hit["qualified"])
        self.assertFalse(hit["source_role_qualified"])
        self.assertIn("QUALIFIED_POLICY_SIGNAL_NOT_OBSERVED", result["evidence_gaps"])

    def test_malformed_locator_fails_closed(self):
        p = packet(self.contract, "Educação em Tempo Integral")
        p["segments"][0]["locator"] = {}
        with self.assertRaisesRegex(ResearchEphemeralDigestStop, "SEGMENT_LOCATOR"):
            digest_research_segments(p, deepcopy(self.contract), root=ROOT)

    def test_remote_effect_enablement_fails_closed(self):
        p = packet(self.contract, "Educação em Tempo Integral")
        p["remote_effects_authorized"]["drive_write"] = True
        with self.assertRaisesRegex(ResearchEphemeralDigestStop, "INPUT_REMOTE_EFFECT"):
            digest_research_segments(p, deepcopy(self.contract), root=ROOT)

    def test_unknown_source_family_fails_closed(self):
        p = packet(self.contract, "Educação em Tempo Integral", family="UNKNOWN_FAMILY")
        with self.assertRaisesRegex(ResearchEphemeralDigestStop, "SOURCE_FAMILY"):
            digest_research_segments(p, deepcopy(self.contract), root=ROOT)

    def test_float_money_is_rejected(self):
        p = packet(
            self.contract,
            "Educação em Tempo Integral ação 1 pagamento.",
            keys=[{"key_type": "action", "value": "1", "stability": "EXPLICIT_SOURCE_FIELD"}],
            amounts=[{"amount_brl": 1.25, "execution_stage": "PAYMENT"}],
        )
        with self.assertRaisesRegex(ResearchEphemeralDigestStop, "AMOUNT_BRL"):
            digest_research_segments(p, deepcopy(self.contract), root=ROOT)

    def test_result_is_deterministic(self):
        p = packet(
            self.contract,
            "Programa Escola em Tempo Integral. Programa 2001. Pagamento.",
            keys=[{"key_type": "program", "value": "2001", "stability": "ADAPTER_PROVEN_STABLE"}],
            amounts=[{"amount_brl": "10.00", "execution_stage": "PAYMENT"}],
        )
        a = digest_research_segments(deepcopy(p), deepcopy(self.contract), root=ROOT)
        b = digest_research_segments(deepcopy(p), deepcopy(self.contract), root=ROOT)
        self.assertEqual(a["result_sha256"], b["result_sha256"])
        self.assertEqual(a["financial_identity_candidates"], b["financial_identity_candidates"])

    def test_all_effects_remain_zero(self):
        p = packet(self.contract, "Educação em Tempo Integral")
        result = digest_research_segments(p, deepcopy(self.contract), root=ROOT)
        self.assertTrue(all(value == 0 for value in result["effects"].values()))
        self.assertFalse(result["persistence_authorized"])
        self.assertFalse(result["causal_inference_performed"])


if __name__ == "__main__":
    unittest.main()

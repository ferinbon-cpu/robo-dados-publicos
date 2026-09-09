import json
import unittest

from robo_dados_publicos.research.task219f_jom_contract_recovery import (
    ROOT,
    Task219FStop,
    build_evidence,
    load_config,
    load_fixture,
    recover_contract_reference,
)


class TestTask219FJomContractRecovery(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config()
        self.event = load_fixture(self.cfg)

    def test_pinned_event_is_exact_verified_task219a_row(self):
        expected = self.cfg["expected_event"]
        self.assertEqual(self.event["event_id"], expected["event_id"])
        self.assertEqual(self.event["contract_number"], "45/")
        self.assertEqual(self.event["bidding_number"], "10/2026")
        self.assertEqual(self.event["process_number"], "902.281/2025")
        self.assertEqual(self.event["contractor"], "Med Doctor Acessórios Ltda")
        self.assertEqual(self.event["cnpj"], "37457979000131")
        self.assertEqual(self.event["value_brl"], "210000.00")

    def test_label_scoped_recovery_gets_contract_45_2026(self):
        recovered = recover_contract_reference(self.event, self.cfg)
        self.assertEqual(recovered, "45/2026")

    def test_later_termo_contratual_12_2026_does_not_contaminate_contract_label(self):
        self.assertIn("Termo Contratual nº 12/2026", self.event["excerpt_redacted"])
        self.assertEqual(recover_contract_reference(self.event, self.cfg), "45/2026")

    def test_conflicting_structured_prefix_fails_closed(self):
        bad = dict(self.event)
        bad["contract_number"] = "46/"
        cfg = json.loads(json.dumps(self.cfg))
        cfg["expected_event"]["structured_contract_number"] = "46/"
        with self.assertRaisesRegex(Task219FStop, "TASK219F_STRUCTURED_PREFIX_CONFLICT"):
            recover_contract_reference(bad, cfg)

    def test_multiple_explicit_contract_labels_fail_closed(self):
        bad = dict(self.event)
        bad["excerpt_redacted"] += " CONTRATO Nº: 99/2026"
        with self.assertRaisesRegex(Task219FStop, "TASK219F_LABEL_SCOPED_REFERENCE_COUNT"):
            recover_contract_reference(bad, self.cfg)

    def test_recovery_preserves_historical_event_id_and_does_not_patch_parser(self):
        evidence = build_evidence()
        seed = evidence["recovered_primary_jom_seed"]
        self.assertEqual(seed["event_id"], "JOEV_083e522d4145e4d27580")
        self.assertTrue(seed["historical_event_id_preserved"])
        self.assertEqual(seed["structured_contract_number_original"], "45/")
        self.assertEqual(seed["recovered_contract_number"], "45/2026")
        self.assertFalse(evidence["adjudication"]["generic_parser_changed"])
        self.assertFalse(evidence["adjudication"]["historical_event_id_changed"])

    def test_municipal_query_uses_exact_contract_and_strong_corroborators(self):
        evidence = build_evidence()
        bridge = evidence["municipal_primary_bridge"]
        query = bridge["query"]
        self.assertEqual(query["target_source"], "LIMEIRA_CONTRATOS")
        self.assertEqual(
            query["match_keys"],
            {
                "year": 2026,
                "contract_number": "45/2026",
                "cnpj": "37457979000131",
                "contractor": "Med Doctor Acessórios Ltda",
            },
        )
        self.assertEqual(query["search_hints"]["process_number"], "902.281/2025")
        self.assertEqual(query["search_hints"]["bidding_number"], "10/2026")
        proof = bridge["candidate_policy_proof"]
        self.assertTrue(proof["synthetic_only"])
        self.assertFalse(proof["identity_proven_by_synthetic_row"])
        self.assertTrue(
            {"CONTRACT_NUMBER_YEAR_NORMALIZED", "CNPJ", "SUPPLIER_NAME"}.issubset(
                set(proof["observed_signals"])
            )
        )

    def test_live_query_is_inert_and_requires_fresh_authorization(self):
        bridge = self.cfg["municipal_bridge"]
        self.assertFalse(bridge["live_execution_implemented"])
        self.assertFalse(bridge["live_execution_authorized"])
        self.assertTrue(bridge["fresh_owner_authorization_required"])
        self.assertFalse(bridge["authorization_reuse_allowed"])
        self.assertEqual(bridge["max_http_requests_future"], 3)
        self.assertFalse(any(self.cfg["remote_effects"].values()))

    def test_no_question_promotion(self):
        evidence = build_evidence()
        adjudication = evidence["adjudication"]
        self.assertTrue(adjudication["exact_contract_identity_recovered_from_primary_jom"])
        self.assertFalse(adjudication["municipal_contract_match_proven"])
        self.assertFalse(adjudication["tce_commitment_identity_proven"])
        self.assertFalse(adjudication["question_promotion_performed"])
        self.assertEqual(adjudication["contextual_paths_after"], 34)
        self.assertEqual(
            adjudication["remaining_blockers"],
            ["CTRL_Q2", "PROC_Q1", "PROC_Q2", "PROC_Q3"],
        )

    def test_materialized_evidence_matches_generated_scientific_state(self):
        path = ROOT / self.cfg["outputs"]["evidence"]
        materialized = json.loads(path.read_text(encoding="utf-8"))
        generated = build_evidence()
        self.assertEqual(
            materialized["recovered_primary_jom_seed"],
            generated["recovered_primary_jom_seed"],
        )
        self.assertEqual(
            materialized["municipal_primary_bridge"],
            generated["municipal_primary_bridge"],
        )
        self.assertEqual(materialized["adjudication"], generated["adjudication"])
        self.assertFalse(any(materialized["remote_effects"].values()))


if __name__ == "__main__":
    unittest.main()

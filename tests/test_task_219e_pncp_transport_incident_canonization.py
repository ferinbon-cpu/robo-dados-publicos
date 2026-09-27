import json
import unittest

from robo_dados_publicos.research.task219e_pncp_transport_incident_canonization import (
    ROOT,
    build_evidence,
    classify_response,
    load_config,
    no_match_allowed,
)


class TestTask219EPncpTransportIncidentCanonization(unittest.TestCase):
    def test_config_pins_fail_closed_absence_semantics(self):
        cfg = load_config()
        semantics = cfg["absence_semantics"]
        self.assertTrue(semantics["no_match_requires_complete_exact_scope"])
        self.assertTrue(semantics["no_match_requires_all_required_responses_successful"])
        self.assertFalse(semantics["timeout_can_prove_no_match"])
        self.assertFalse(semantics["zero_bytes_can_prove_no_match"])
        self.assertFalse(semantics["http_502_can_prove_no_match"])
        self.assertFalse(semantics["http_503_can_prove_no_match"])
        self.assertFalse(semantics["http_504_can_prove_no_match"])
        self.assertFalse(semantics["incomplete_pagination_can_prove_no_match"])
        self.assertFalse(semantics["portal_visibility_can_replace_api_primary_proof"])
        self.assertFalse(semantics["secondary_evidence_can_create_procurement_identity"])
        self.assertFalse(any(cfg["remote_effects"].values()))

    def test_response_classifier_distinguishes_payload_from_transport(self):
        self.assertEqual(
            classify_response(http_status=200, bytes_received=10, json_valid=True),
            "VALID_JSON_RESPONSE",
        )
        self.assertEqual(
            classify_response(http_status=204, bytes_received=0, json_valid=False),
            "CONFIRMED_EMPTY_RESPONSE",
        )
        for status in (408, 429, 500, 502, 503, 504):
            self.assertEqual(
                classify_response(http_status=status, bytes_received=0, json_valid=False),
                "TRANSPORT_OR_EDGE_UNAVAILABLE",
            )
        self.assertEqual(
            classify_response(
                http_status=None,
                bytes_received=0,
                json_valid=False,
                transport_error="TRANSPORT_ERROR:TimeoutError:The read operation timed out",
            ),
            "TRANSPORT_OR_EDGE_UNAVAILABLE",
        )
        self.assertEqual(
            classify_response(http_status=200, bytes_received=0, json_valid=False),
            "INVALID_OR_INSUFFICIENT_RESPONSE",
        )

    def test_no_match_requires_complete_successful_exact_scope(self):
        good = [
            {"http_status": 200, "bytes_received": 100, "json_valid": True},
            {"http_status": 204, "bytes_received": 0, "json_valid": False},
        ]
        self.assertTrue(no_match_allowed(good, exact_scope_complete=True))
        self.assertFalse(no_match_allowed(good, exact_scope_complete=False))

        with_504 = good + [
            {"http_status": 504, "bytes_received": 0, "json_valid": False},
        ]
        self.assertFalse(no_match_allowed(with_504, exact_scope_complete=True))

        with_timeout = good + [
            {
                "http_status": None,
                "bytes_received": 0,
                "json_valid": False,
                "transport_error": "TimeoutError",
            },
        ]
        self.assertFalse(no_match_allowed(with_timeout, exact_scope_complete=True))

    def test_canonical_history_proves_intermittent_transport_not_absence(self):
        evidence = build_evidence()
        by_id = {row["id"]: row for row in evidence["historical_observations"]}

        self.assertTrue(by_id["TASK168B_COMPLETE_759"]["no_match_semantically_eligible"])
        self.assertEqual(
            by_id["TASK216_ATTEMPT1_200_200_200_502"]["response_states"],
            [
                "VALID_JSON_RESPONSE",
                "VALID_JSON_RESPONSE",
                "VALID_JSON_RESPONSE",
                "TRANSPORT_OR_EDGE_UNAVAILABLE",
            ],
        )
        self.assertFalse(
            by_id["TASK216_ATTEMPT1_200_200_200_502"]["no_match_semantically_eligible"]
        )
        self.assertEqual(by_id["TASK216B_COMPLETE_1933"]["total_records"], 1933)
        self.assertEqual(by_id["TASK216B_COMPLETE_1933"]["total_gets"], 10)
        self.assertEqual(
            by_id["TASK219C_ZERO_BYTE_TIMEOUT"]["response_states"],
            ["TRANSPORT_OR_EDGE_UNAVAILABLE"],
        )
        self.assertFalse(by_id["TASK219C_ZERO_BYTE_TIMEOUT"]["absence_inference"])
        self.assertFalse(
            by_id["TASK219C_ZERO_BYTE_TIMEOUT"]["no_match_semantically_eligible"]
        )

        adjudication = evidence["adjudication"]
        self.assertTrue(adjudication["same_endpoint_has_recent_success_and_failure"])
        self.assertTrue(
            adjudication["current_transport_or_edge_unavailability_proven_by_canonical_runtime"]
        )
        self.assertFalse(adjudication["endpoint_deprecation_proven"])
        self.assertFalse(adjudication["rate_limit_proven"])
        self.assertFalse(adjudication["waf_or_asn_filtering_proven"])
        self.assertFalse(adjudication["backend_outage_proven"])
        self.assertFalse(
            adjudication["transport_failure_can_be_reinterpreted_as_no_match"]
        )
        self.assertEqual(adjudication["contextual_paths_after"], 34)
        self.assertEqual(adjudication["remaining_blockers"], ["CTRL_Q2", "PROC_Q1", "PROC_Q2", "PROC_Q3"])

    def test_supporting_observations_do_not_become_primary_evidence(self):
        evidence = build_evidence()
        self.assertEqual(len(evidence["supporting_operator_observations"]), 2)
        for row in evidence["supporting_operator_observations"]:
            self.assertFalse(row["raw_artifact_persisted"])
            self.assertFalse(row["can_prove_absence"])
            self.assertTrue(
                all(state == "TRANSPORT_OR_EDGE_UNAVAILABLE" for state in row["classified_states"])
            )

        for lead in evidence["external_diagnostic_leads"]:
            self.assertNotEqual(lead["role"], "PRIMARY_IDENTITY_EVIDENCE")

    def test_future_probe_is_inert_and_requires_fresh_authorization(self):
        cfg = load_config()
        probe = cfg["future_controlled_probe"]
        self.assertFalse(probe["implemented"])
        self.assertFalse(probe["executed"])
        self.assertTrue(probe["fresh_owner_authorization_required"])
        self.assertFalse(probe["authorization_reuse_allowed"])
        self.assertTrue(probe["same_resource_required_across_origins"])
        self.assertFalse(probe["proxy_or_mirror_may_be_primary_evidence"])

    def test_materialized_evidence_preserves_same_scientific_boundary(self):
        cfg = load_config()
        path = ROOT / cfg["outputs"]["evidence"]
        self.assertTrue(path.is_file())
        materialized = json.loads(path.read_text(encoding="utf-8"))
        generated = build_evidence()

        self.assertEqual(
            materialized["canonical_transport_label"],
            generated["canonical_transport_label"],
        )
        self.assertEqual(
            materialized["adjudication"]["contextual_paths_after"],
            generated["adjudication"]["contextual_paths_after"],
        )
        self.assertEqual(
            materialized["adjudication"]["remaining_blockers"],
            generated["adjudication"]["remaining_blockers"],
        )
        self.assertFalse(materialized["adjudication"]["question_promotion_performed"])
        self.assertFalse(any(materialized["remote_effects"].values()))


if __name__ == "__main__":
    unittest.main()

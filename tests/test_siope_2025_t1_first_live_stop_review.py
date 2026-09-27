from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import scripts.run_siope_2025_t1_first_live as first_live_cli
from robo_dados_publicos.sources.siope_2025_request_plan import (
    Siope2025RequestPlanError,
    materialize_request_plan,
    sanitized_plan_evidence,
)
from robo_dados_publicos.sources.siope_2025_t1_authorization import (
    STOP as AUTH_STOP,
    Siope2025T1AuthorizationError,
)

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "config/siope_2025_readonly_discovery_design.v1.json"
EVIDENCE = ROOT / "docs/evidence/TASK_004_SIOPE_2025_FIRST_LIVE_RUN_2_STOP_0.8.0.json"
HISTORICAL = ROOT / "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_BOUNDED_BATCH_AUTHORIZATION_RUN_2_0.8.0.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Siope2025FirstLiveStopReviewTests(unittest.TestCase):
    def test_sanitized_plan_evidence_accepts_only_contiguous_prefixes(self) -> None:
        plan = materialize_request_plan(_load(DESIGN))
        for count in range(0, 8):
            ordinals = list(range(1, count + 1))
            evidence = sanitized_plan_evidence(plan, executed_ordinals=ordinals)
            self.assertEqual(evidence["request_shape_count"], count)
            self.assertEqual([shape["ordinal"] for shape in evidence["request_shapes"]], ordinals)
            self.assertFalse(evidence["query_values_persisted"])
            self.assertFalse(evidence["response_values_persisted"])

        for invalid in ([2], [1, 3], [1, 2, 4], [1, 2, 3, 4, 5, 6, 8]):
            with self.assertRaises(Siope2025RequestPlanError):
                sanitized_plan_evidence(plan, executed_ordinals=list(invalid))

    def test_post_authorization_stop_is_not_mislabeled_as_authorization_failure(self) -> None:
        error = first_live_cli.Siope2025T1PostAuthorizationError(
            "STOP_SIOPE_2025_T1_TRANSPORT_CLIENT_STOP_SIOPE_CLIENT_TIMEOUT",
            source_get_count=1,
        )
        argv = [
            "run_siope_2025_t1_first_live.py",
            "--mode",
            "live",
            "--authorization-id",
            "authorized",
            "--workflow-run-number",
            "2",
            "--workflow-run-attempt",
            "1",
            "--workflow-ref",
            "refs/heads/main",
        ]
        output = StringIO()
        with patch.object(first_live_cli, "live", side_effect=error), patch.object(sys, "argv", argv), redirect_stdout(output):
            code = first_live_cli.main()
        payload = json.loads(output.getvalue())
        self.assertEqual(code, 13)
        self.assertEqual(payload["status"], first_live_cli.POST_AUTH_STOP)
        self.assertNotEqual(payload["status"], AUTH_STOP)
        self.assertEqual(payload["source_get_count"], 1)
        self.assertEqual(payload["drive_read_count"], 0)
        self.assertEqual(payload["drive_write_count"], 0)
        self.assertFalse(payload["publication"])
        self.assertFalse(payload["response_persisted"])

    def test_authorization_failure_keeps_authorization_stop_status(self) -> None:
        argv = ["run_siope_2025_t1_first_live.py", "--mode", "live"]
        output = StringIO()
        with patch.object(
            first_live_cli,
            "live",
            side_effect=Siope2025T1AuthorizationError(AUTH_STOP),
        ), patch.object(sys, "argv", argv), redirect_stdout(output):
            code = first_live_cli.main()
        payload = json.loads(output.getvalue())
        self.assertEqual(code, 13)
        self.assertEqual(payload["status"], AUTH_STOP)
        self.assertEqual(payload["source_get_count"], 0)

    def test_pinned_run_2_stop_evidence_matches_deterministic_request_prefix(self) -> None:
        evidence = _load(EVIDENCE)
        plan = materialize_request_plan(_load(DESIGN))
        expected_prefix = sanitized_plan_evidence(plan, executed_ordinals=[1])

        self.assertEqual(evidence["schema"], "SIOPE_2025_T1_FIRST_LIVE_STOP_EVIDENCE_V1")
        self.assertEqual(evidence["run_id"], 33202186208)
        self.assertEqual(evidence["job_id"], 98954114713)
        self.assertEqual(evidence["head_sha"], "5c6a15a1944ad953d7eeba4ae6bfffabc24a1409")
        self.assertEqual(evidence["run_number"], 2)
        self.assertEqual(evidence["run_attempt"], 1)
        self.assertTrue(evidence["authorization_accepted"])
        self.assertTrue(evidence["authorization_one_shot_consumed"])
        self.assertEqual(evidence["raw_emitted_status"], AUTH_STOP)
        self.assertEqual(evidence["reviewed_canonical_status"], first_live_cli.POST_AUTH_STOP)
        self.assertEqual(
            evidence["stop_reason"],
            "STOP_SIOPE_2025_T1_TRANSPORT_CLIENT_STOP_SIOPE_CLIENT_TIMEOUT",
        )
        self.assertEqual(evidence["cause_classification"], "UNKNOWN_AFTER_SINGLE_TIMEOUT")
        self.assertEqual(evidence["source_get_count"], 1)
        self.assertEqual(evidence["additional_source_get_count_from_review_task"], 0)
        self.assertEqual(evidence["request_plan_evidence"], expected_prefix)
        self.assertEqual(evidence["attempted_target"]["period"], 1)
        self.assertEqual(evidence["period_states"]["1"], "TIMEOUT_NO_VALID_OBSERVATION")
        self.assertTrue(all(evidence["period_states"][str(period)] == "NOT_ATTEMPTED" for period in range(2, 7)))
        self.assertEqual(evidence["phase_b_status"], "NOT_ATTEMPTED")
        self.assertFalse(evidence["schema_observed"])
        self.assertEqual(evidence["schema_exact_status"], "NOT_EVALUATED")
        self.assertEqual(evidence["required_gold_input_fields_presence"], "NOT_EVALUATED")
        self.assertFalse(evidence["retry_performed"])
        self.assertFalse(evidence["redirect_followed"])
        self.assertFalse(evidence["pagination_performed"])
        self.assertFalse(evidence["nextlink_followed"])
        self.assertEqual(evidence["drive_read_count"], 0)
        self.assertEqual(evidence["drive_write_count"], 0)
        self.assertFalse(evidence["response_body_persisted"])
        self.assertFalse(evidence["record_values_persisted"])
        self.assertFalse(evidence["bronze_silver_gold_creation"])
        self.assertFalse(evidence["publication"])
        self.assertEqual(evidence["year_2025_status"], "UNPROVEN_RECENT")
        self.assertEqual(evidence["period_6_status"], "CANDIDATE_NOT_PROVEN")
        self.assertEqual(evidence["annual_closure_status"], "UNKNOWN")
        self.assertEqual(evidence["metric_status"], "UNKNOWN")
        self.assertFalse(evidence["promote_2025_to_proven"])

        serialized = json.dumps(evidence, ensure_ascii=True, sort_keys=True)
        self.assertNotIn("?$", serialized)
        self.assertNotIn("$filter=", serialized)
        self.assertNotIn("$select=", serialized)
        self.assertNotIn("VAL_RECE_REAL", serialized)

    def test_historical_comparator_is_transport_capability_only(self) -> None:
        evidence = _load(EVIDENCE)
        historical = _load(HISTORICAL)
        comparator = evidence["historical_transport_comparator"]
        self.assertEqual(comparator["run_id"], historical["run_id"])
        self.assertEqual(comparator["job_id"], historical["job_id"])
        self.assertEqual(comparator["source_get_count"], historical["source_get_count"])
        self.assertEqual(historical["source_get_count"], 5)
        self.assertEqual(historical["historical_failures"], 0)
        self.assertFalse(historical["retry_authorized"])
        self.assertFalse(historical["pagination_authorized"])
        self.assertEqual(
            comparator["comparison_scope"],
            "TRANSPORT_CAPABILITY_ONLY_NOT_2025_PROOF",
        )
        self.assertEqual(evidence["cause_classification"], "UNKNOWN_AFTER_SINGLE_TIMEOUT")
        self.assertEqual(evidence["year_2025_status"], "UNPROVEN_RECENT")


if __name__ == "__main__":
    unittest.main()

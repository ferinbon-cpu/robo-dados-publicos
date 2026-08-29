from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.github_siope_2025_metadata_http_401_offline_gate import (
    OfflineAssessmentError,
    validate_assessment,
)

ROOT = Path(__file__).resolve().parents[1]
ASSESSMENT = ROOT / "config" / "siope_2025_metadata_http_401_offline_assessment.v1.json"
EVIDENCE = ROOT / "docs" / "evidence" / "TASK_009C_SIOPE_2025_RESOLVED_PATH_PROBE_RUN_1_HTTP_401_0.8.0.json"
GATE = ROOT / "scripts" / "github_siope_2025_metadata_http_401_offline_gate.py"


class Task009CRHttp401OfflineReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assessment = json.loads(ASSESSMENT.read_text(encoding="utf-8"))
        self.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_pinned_assessment_passes(self) -> None:
        validate_assessment(self.assessment, self.evidence)

    def test_gate_cli_reports_zero_network_and_unknown_route(self) -> None:
        proc = subprocess.run([sys.executable, str(GATE)], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        result = json.loads(proc.stdout)
        self.assertFalse(result["network_authorized"])
        self.assertEqual(result["source_get_count"], 0)
        self.assertEqual(result["next_public_package_route"], "UNKNOWN")

    def test_exact_actions_run_identity_is_pinned(self) -> None:
        workflow = self.evidence["workflow"]
        self.assertEqual(workflow["run_id"], 33221146589)
        self.assertEqual(workflow["workflow_id"], 344981895)
        self.assertEqual(workflow["run_number"], 1)
        self.assertEqual(workflow["run_attempt"], 1)
        self.assertEqual(workflow["event"], "workflow_dispatch")
        self.assertEqual(workflow["head_sha"], "0e70495e5ae8ccdf45aff7e2c76fd302d1294b0c")

    def test_workflow_identity_drift_fails_closed(self) -> None:
        for key, value in (
            ("run_id", 1),
            ("workflow_id", 1),
            ("run_number", 2),
            ("run_attempt", 2),
            ("event", "push"),
            ("head_sha", "f" * 40),
            ("authorization_id", "SIOPE2025-METADATA-DIRECT-PROBE-INVENTED"),
        ):
            evidence = copy.deepcopy(self.evidence)
            evidence["workflow"][key] = value
            with self.assertRaises(OfflineAssessmentError):
                validate_assessment(self.assessment, evidence)

    def test_observation_or_persistence_drift_fails_closed(self) -> None:
        mutations = (
            ("reason", "SOMETHING_ELSE"),
            ("http_status", 200),
            ("source_get_count", 0),
            ("runner_exit_code", 0),
            ("response_persisted", True),
            ("archive_persisted", True),
        )
        for key, value in mutations:
            evidence = copy.deepcopy(self.evidence)
            evidence["observation"][key] = value
            with self.assertRaises(OfflineAssessmentError):
                validate_assessment(self.assessment, evidence)

    def test_request_contract_drift_fails_closed(self) -> None:
        for key, value in (
            ("url", "https://example.invalid/invented.zip"),
            ("maximum_source_get_count", 2),
            ("maximum_response_bytes", 8192),
            ("retry_authorized", True),
            ("follow_redirects", True),
        ):
            evidence = copy.deepcopy(self.evidence)
            evidence["request_contract"][key] = value
            with self.assertRaises(OfflineAssessmentError):
                validate_assessment(self.assessment, evidence)

    def test_rerun_reuse_and_authentication_fail_closed(self) -> None:
        for key in ("rerun_authorized", "reuse_authorized", "authentication_attempt_authorized"):
            evidence = copy.deepcopy(self.evidence)
            evidence["authorization_consumption"][key] = True
            with self.assertRaises(OfflineAssessmentError):
                validate_assessment(self.assessment, evidence)

    def test_network_or_task_009d_authorization_fails_closed(self) -> None:
        for path in (("network_authorized",), ("task_009d", "authorized")):
            assessment = copy.deepcopy(self.assessment)
            target = assessment
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = True
            with self.assertRaises(OfflineAssessmentError):
                validate_assessment(assessment, self.evidence)

    def test_semantic_promotion_and_invented_next_route_fail_closed(self) -> None:
        assessment = copy.deepcopy(self.assessment)
        assessment["semantic_guards"]["annual_closure_status"] = "CLOSED"
        with self.assertRaises(OfflineAssessmentError):
            validate_assessment(assessment, self.evidence)
        evidence = copy.deepcopy(self.evidence)
        evidence["semantic_guards"]["gold_metrics_status"] = "PROVEN"
        with self.assertRaises(OfflineAssessmentError):
            validate_assessment(self.assessment, evidence)

    def test_unobserved_route_or_public_classification_drift_fails_closed(self) -> None:
        for field, value in (
            ("route", "https://fnde.sharepoint.com/_layouts/15/download.aspx?invented=true"),
            ("classification", "PUBLIC_ROUTE_CANDIDATE"),
            ("package_access_status", "PUBLIC"),
        ):
            assessment = copy.deepcopy(self.assessment)
            assessment["route_assessment"][3][field] = value
            with self.assertRaises(OfflineAssessmentError):
                validate_assessment(assessment, self.evidence)
        assessment = copy.deepcopy(self.assessment)
        assessment["next_public_package_route"] = "https://example.invalid/invented.zip"
        with self.assertRaises(OfflineAssessmentError):
            validate_assessment(assessment, self.evidence)


if __name__ == "__main__":
    unittest.main()

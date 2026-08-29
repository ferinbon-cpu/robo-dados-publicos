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

    def test_unobserved_route_or_public_classification_drift_fails_closed(self) -> None:
        for field, value in (
            ("route", "https://fnde.sharepoint.com/_layouts/15/download.aspx?invented=true"),
            ("classification", "PUBLIC_ROUTE_CANDIDATE"),
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

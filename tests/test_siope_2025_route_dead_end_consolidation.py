from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.github_siope_2025_route_dead_end_consolidation_gate import (
    RouteDeadEndConsolidationError,
    validate_consolidation,
)

ROOT = Path(__file__).resolve().parents[1]
ASSESSMENT = ROOT / "config" / "siope_2025_route_dead_end_consolidation.v1.json"
ANTONIETA = ROOT / "config" / "source_expansion.siope_artifact_access_boundary.json"
TASK008 = ROOT / "config" / "siope_2025_alias_finality_audit.v1.json"
TASK009B = ROOT / "docs" / "evidence" / "TASK_009B_SIOPE_2025_METADATA_ROUTE_PROBE_RUN_2_REDIRECT_0.8.0.json"
TASK009C = ROOT / "docs" / "evidence" / "TASK_009C_SIOPE_2025_RESOLVED_PATH_PROBE_RUN_1_HTTP_401_0.8.0.json"
GATE = ROOT / "scripts" / "github_siope_2025_route_dead_end_consolidation_gate.py"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Task009DRouteDeadEndConsolidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assessment = _load(ASSESSMENT)
        self.antonieta = _load(ANTONIETA)
        self.task008 = _load(TASK008)
        self.task009b = _load(TASK009B)
        self.task009c = _load(TASK009C)

    def validate(self, *, assessment=None, antonieta=None, task008=None, task009b=None, task009c=None) -> None:
        validate_consolidation(
            self.assessment if assessment is None else assessment,
            self.antonieta if antonieta is None else antonieta,
            self.task008 if task008 is None else task008,
            self.task009b if task009b is None else task009b,
            self.task009c if task009c is None else task009c,
        )

    def test_pinned_consolidation_passes(self) -> None:
        self.validate()

    def test_gate_cli_reports_zero_network_and_keep_blocked(self) -> None:
        proc = subprocess.run([sys.executable, str(GATE)], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        result = json.loads(proc.stdout)
        self.assertFalse(result["network_authorized"])
        self.assertEqual(result["source_get_count"], 0)
        self.assertEqual(result["decision"], "KEEP_BLOCKED_UNTIL_NEW_OFFICIAL_EVIDENCE_CLASS_IS_PINNED")
        self.assertEqual(result["closed_annual_series_last_year"], 2024)
        self.assertEqual(result["gold_2025"], "UNKNOWN")

    def test_any_remote_authorization_fails_closed(self) -> None:
        for key in ("remote_execution_authorized", "rerun_authorized", "authentication_attempt_authorized", "future_batch_execution_authorized"):
            assessment = copy.deepcopy(self.assessment)
            assessment["authorization_guards"][key] = True
            with self.assertRaises(RouteDeadEndConsolidationError):
                self.validate(assessment=assessment)
        assessment = copy.deepcopy(self.assessment)
        assessment["network_authorized"] = True
        with self.assertRaises(RouteDeadEndConsolidationError):
            self.validate(assessment=assessment)

    def test_route_inference_or_repeat_probe_fails_closed(self) -> None:
        for index in range(3):
            assessment = copy.deepcopy(self.assessment)
            assessment["route_inventory"][index]["repeat_probe_authorized"] = True
            with self.assertRaises(RouteDeadEndConsolidationError):
                self.validate(assessment=assessment)
        assessment = copy.deepcopy(self.assessment)
        assessment["route_inventory"][2]["route"] = "https://fnde.sharepoint.com/_layouts/15/download.aspx?SourceUrl=invented"
        with self.assertRaises(RouteDeadEndConsolidationError):
            self.validate(assessment=assessment)

    def test_semantic_or_gold_promotion_fails_closed(self) -> None:
        for key, value in (
            ("annual_closure_status", "CLOSED"),
            ("semantic_comparability_status", "PROVEN"),
            ("gold_metrics_status", "PROVEN"),
            ("closed_annual_series_last_year", 2025),
            ("year_2026_status", "PROVEN"),
        ):
            assessment = copy.deepcopy(self.assessment)
            assessment["semantic_guards"][key] = value
            with self.assertRaises(RouteDeadEndConsolidationError):
                self.validate(assessment=assessment)

    def test_antonieta_auth_boundary_must_remain_pinned(self) -> None:
        mutations = (
            ("anonymous_export_status", "PUBLIC_ANONYMOUS"),
            ("acquisition_route_status", "PROVEN"),
            ("artifact_access_status", "PROVEN_PUBLIC_ANONYMOUS"),
        )
        for key, value in mutations:
            antonieta = copy.deepcopy(self.antonieta)
            antonieta[key] = value
            with self.assertRaises(RouteDeadEndConsolidationError):
                self.validate(antonieta=antonieta)
        antonieta = copy.deepcopy(self.antonieta)
        antonieta["authentication_boundary"]["authenticated_browser_automation"] = "ALLOWED"
        with self.assertRaises(RouteDeadEndConsolidationError):
            self.validate(antonieta=antonieta)

    def test_task008_alias_and_population_unknowns_must_remain_pinned(self) -> None:
        mutations = (
            ("current_2025_alias_bridge_status", "PROVEN"),
            ("population_denominator_status", "PROVEN"),
            ("field_level_identity_proven_count", 11),
            ("gold_promotion_authorized", True),
        )
        for key, value in mutations:
            task008 = copy.deepcopy(self.task008)
            task008["gate_a_alias_metadata"][key] = value
            with self.assertRaises(RouteDeadEndConsolidationError):
                self.validate(task008=task008)

    def test_task009b_redirect_identity_must_remain_exact(self) -> None:
        task009b = copy.deepcopy(self.task009b)
        task009b["observation"]["http_status"] = 200
        with self.assertRaises(RouteDeadEndConsolidationError):
            self.validate(task009b=task009b)
        task009b = copy.deepcopy(self.task009b)
        task009b["offline_route_resolution"]["resolved_target_url"] = "https://example.invalid/Metadados_Mun_2025.zip"
        with self.assertRaises(RouteDeadEndConsolidationError):
            self.validate(task009b=task009b)

    def test_task009c_http_401_and_consumed_authorization_must_remain_exact(self) -> None:
        task009c = copy.deepcopy(self.task009c)
        task009c["observation"]["http_status"] = 200
        with self.assertRaises(RouteDeadEndConsolidationError):
            self.validate(task009c=task009c)
        for key in ("rerun_authorized", "reuse_authorized", "authentication_attempt_authorized"):
            task009c = copy.deepcopy(self.task009c)
            task009c["authorization_consumption"][key] = True
            with self.assertRaises(RouteDeadEndConsolidationError):
                self.validate(task009c=task009c)

    def test_future_evidence_classes_are_exact_and_do_not_authorize_network(self) -> None:
        assessment = copy.deepcopy(self.assessment)
        assessment["future_evidence_classes_that_may_open_a_new_task"].append("ANY_INFERRED_ROUTE")
        with self.assertRaises(RouteDeadEndConsolidationError):
            self.validate(assessment=assessment)
        assessment = copy.deepcopy(self.assessment)
        assessment["decision"] = "AUTHORIZE_TASK_009E"
        with self.assertRaises(RouteDeadEndConsolidationError):
            self.validate(assessment=assessment)


if __name__ == "__main__":
    unittest.main()

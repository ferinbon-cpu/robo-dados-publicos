from __future__ import annotations

import ast
import copy
from dataclasses import replace
import json
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.sources.siope_2025_bounded_runner import (
    STOP_LIVE_NOT_AUTHORIZED,
    Siope2025BoundedRunnerError,
    run_bounded,
    validate_semantic_state,
)
from robo_dados_publicos.sources.siope_2025_evidence import METRIC_IDS, summarize_schema
from robo_dados_publicos.sources.siope_2025_fake_transport import FakeSiope2025Transport
from robo_dados_publicos.sources.siope_2025_request_plan import (
    EXPECTED_PATH,
    PHASE_B_PRECONDITION,
    RequestExecutionLedger,
    Siope2025RequestPlanError,
    materialize_request_plan,
    validate_request_plan,
)
from scripts.github_siope_2025_bounded_runner_gate import CONFIG, DESIGN, FIXTURE, validate_gate
from scripts.run_siope_2025_bounded_offline import run_cli


class Siope2025BoundedRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.design = json.loads(DESIGN.read_text(encoding="utf-8"))
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.required_fields = cls.design["phase_b_conditional_schema"]["required_gold_input_fields"]

    def _run(self, fixture: dict) -> tuple[dict, FakeSiope2025Transport]:
        transport = FakeSiope2025Transport(fixture)
        result = run_bounded(runner_config=self.config, design=self.design, transport=transport)
        return result, transport

    def test_exact_p6_fixture_is_bounded_and_zero_effect(self) -> None:
        result, transport = self._run(self.fixture)
        self.assertEqual(result["fake_request_count"], 7)
        self.assertEqual(result["source_get_count"], 0)
        self.assertEqual([request.period for request in transport.requests], [1, 2, 3, 4, 5, 6, 6])
        self.assertEqual(result["annual_closure_status"], "UNKNOWN")
        self.assertFalse(result["promote_2025_to_proven"])
        self.assertFalse(result["live_execution_authorized"])
        self.assertFalse(result["network_called"])
        self.assertEqual(result["drive_read_count"], 0)
        self.assertEqual(result["drive_write_count"], 0)
        self.assertFalse(result["publication"])
        self.assertEqual(set(result["metric_statuses"]), set(METRIC_IDS))
        self.assertTrue(all(status == "UNKNOWN" for status in result["metric_statuses"].values()))

        evidence = result["observation_evidence"]
        self.assertEqual(len(evidence["transport"]), 7)
        self.assertTrue(evidence["schema"]["all_required_gold_inputs_present"])
        self.assertEqual(evidence["schema"]["missing_required_gold_input_fields"], [])
        self.assertEqual(len(evidence["schema"]["observed_fields_sha256"]), 64)
        self.assertFalse(evidence["any_metric_proven"])
        self.assertFalse(evidence["response_body_persisted"])
        self.assertFalse(evidence["record_values_persisted"])
        self.assertFalse(evidence["query_values_persisted"])

    def test_no_transport_and_spoofed_transport_stop_before_request(self) -> None:
        with self.assertRaisesRegex(Siope2025BoundedRunnerError, f"^{STOP_LIVE_NOT_AUTHORIZED}$"):
            run_bounded(runner_config=self.config, design=self.design)

        class NotTheFakeTransport:
            def request(self, spec):  # noqa: ANN001
                raise AssertionError("must not be called")

        with self.assertRaisesRegex(Siope2025BoundedRunnerError, f"^{STOP_LIVE_NOT_AUTHORIZED}$"):
            run_bounded(runner_config=self.config, design=self.design, transport=NotTheFakeTransport())

    def test_no_p6_skips_schema_and_uses_six_fake_requests(self) -> None:
        fixture = json.loads((FIXTURE.parent / "periods_without_p6.json").read_text(encoding="utf-8"))
        result, transport = self._run(fixture)
        self.assertEqual(result["fake_request_count"], 6)
        self.assertEqual(len(transport.requests), 6)
        self.assertEqual(result["outcome"], "2025_PERIODS_OBSERVED_SCHEMA_UNKNOWN")
        self.assertIsNone(result["observation_evidence"]["schema"]["all_required_gold_inputs_present"])

    def test_response_transport_and_identity_drifts_fail_closed(self) -> None:
        cases = []
        fixture = copy.deepcopy(self.fixture)
        fixture["phase_a_period_probes"][5]["response_status"] = 500
        cases.append((fixture, "HTTP_STATUS_P6"))
        fixture = copy.deepcopy(self.fixture)
        fixture["phase_a_period_probes"][5]["content_type"] = "text/plain"
        cases.append((fixture, "CONTENT_TYPE_P6"))
        fixture = copy.deepcopy(self.fixture)
        fixture["phase_a_period_probes"][5]["response_byte_count"] = 262145
        cases.append((fixture, "RESPONSE_LIMIT_P6"))
        fixture = copy.deepcopy(self.fixture)
        fixture["phase_a_period_probes"][5]["redirect_followed"] = True
        cases.append((fixture, "REDIRECT_P6"))
        fixture = copy.deepcopy(self.fixture)
        fixture["phase_a_period_probes"][5]["retry_performed"] = True
        cases.append((fixture, "RETRY_P6"))
        fixture = copy.deepcopy(self.fixture)
        fixture["phase_a_period_probes"][5]["nextlink_present"] = True
        cases.append((fixture, "NEXTLINK_P6"))
        fixture = copy.deepcopy(self.fixture)
        fixture["phase_a_period_probes"][5]["records"][0]["COD_MUNI"] = 999999
        cases.append((fixture, "IDENTITY_P6"))
        fixture = copy.deepcopy(self.fixture)
        fixture["phase_a_period_probes"][5]["records"][0]["NUM_ANO"] = 2026
        cases.append((fixture, "IDENTITY_P6"))
        fixture = copy.deepcopy(self.fixture)
        fixture["phase_a_period_probes"][5]["records"][0]["NUM_PERI"] = 5
        cases.append((fixture, "IDENTITY_PERIOD_P6"))

        for changed, code in cases:
            with self.subTest(code=code):
                with self.assertRaisesRegex(Siope2025BoundedRunnerError, code):
                    self._run(changed)

    def test_request_plan_pins_all_runtime_limits(self) -> None:
        plan = materialize_request_plan(self.design)
        self.assertEqual([item.ordinal for item in plan], list(range(1, 8)))
        self.assertEqual([item.period for item in plan], [1, 2, 3, 4, 5, 6, 6])
        self.assertTrue(all(item.method == "GET" for item in plan))
        self.assertTrue(all(item.host == "www.fnde.gov.br" for item in plan))
        self.assertTrue(all(item.path == EXPECTED_PATH for item in plan))
        self.assertTrue(all(item.timeout_seconds == 60 for item in plan))
        self.assertTrue(all(item.max_response_bytes == 262144 for item in plan))
        self.assertTrue(all(item.max_attempts == 1 for item in plan))
        self.assertTrue(all(item.retry_authorized is False for item in plan))
        self.assertTrue(all(item.follow_redirects is False for item in plan))
        self.assertTrue(all(item.pagination_authorized is False for item in plan))
        self.assertTrue(all(item.follow_nextlink is False for item in plan))
        self.assertEqual(plan[6].precondition, PHASE_B_PRECONDITION)

    def test_request_plan_drifts_fail_closed(self) -> None:
        plan = materialize_request_plan(self.design)
        mutations = (
            (0, {"method": "POST"}, "METHOD_DRIFT"),
            (0, {"host": "example.invalid"}, "HOST_DRIFT"),
            (0, {"path": "/olinda-ide/other"}, "PATH_DRIFT"),
            (0, {"year": 2026}, "TARGET_DRIFT"),
            (5, {"period": 5}, "PERIOD_ORDER"),
            (0, {"timeout_seconds": 61}, "TIMEOUT_DRIFT"),
            (0, {"max_response_bytes": 262145}, "RESPONSE_LIMIT_DRIFT"),
            (0, {"max_attempts": 2}, "ATTEMPT_DRIFT"),
            (0, {"retry_authorized": True}, "RETRY_DRIFT"),
            (0, {"follow_redirects": True}, "REDIRECT_DRIFT"),
            (0, {"pagination_authorized": True}, "PAGINATION_DRIFT"),
            (0, {"follow_nextlink": True}, "NEXTLINK_DRIFT"),
            (6, {"precondition": "ALWAYS"}, "PHASE_B_PRECONDITION_DRIFT"),
        )
        for index, kwargs, code in mutations:
            changed = list(plan)
            changed[index] = replace(changed[index], **kwargs)
            with self.subTest(code=code):
                with self.assertRaisesRegex(Siope2025RequestPlanError, code):
                    validate_request_plan(tuple(changed))

    def test_ledger_stops_duplicate_and_eighth_request(self) -> None:
        plan = materialize_request_plan(self.design)
        ledger = RequestExecutionLedger(plan)
        ledger.consume(plan[0])
        with self.assertRaisesRegex(Siope2025RequestPlanError, "DUPLICATE_PHASE_PERIOD"):
            ledger.consume(plan[0])

        ledger = RequestExecutionLedger(plan)
        for spec in plan:
            ledger.consume(spec)
        self.assertEqual(ledger.count, 7)
        with self.assertRaisesRegex(Siope2025RequestPlanError, "REQUEST_BUDGET"):
            ledger.consume(plan[-1])

    def test_design_drift_cannot_expand_target_or_effects(self) -> None:
        changed = copy.deepcopy(self.config)
        changed["target"]["year"] = 2026
        with self.assertRaisesRegex(Siope2025BoundedRunnerError, "TARGET"):
            run_bounded(runner_config=changed, design=self.design, transport=FakeSiope2025Transport(self.fixture))
        changed = copy.deepcopy(self.config)
        changed["execution"]["maximum_request_count"] = 8
        with self.assertRaisesRegex(Siope2025BoundedRunnerError, "EXECUTION_CONTRACT"):
            run_bounded(runner_config=changed, design=self.design, transport=FakeSiope2025Transport(self.fixture))
        changed = copy.deepcopy(self.config)
        changed["semantic_guards"]["include_2026_authorized"] = True
        with self.assertRaisesRegex(Siope2025BoundedRunnerError, "SEMANTIC_2026"):
            run_bounded(runner_config=changed, design=self.design, transport=FakeSiope2025Transport(self.fixture))
        for key in self.config["effects"]:
            changed = copy.deepcopy(self.config)
            changed["effects"][key] = True
            with self.subTest(effect=key):
                with self.assertRaisesRegex(Siope2025BoundedRunnerError, "EFFECTS"):
                    run_bounded(runner_config=changed, design=self.design, transport=FakeSiope2025Transport(self.fixture))

    def test_semantic_promotions_fail_closed(self) -> None:
        statuses = {metric_id: "UNKNOWN" for metric_id in METRIC_IDS}
        validate_semantic_state(
            year=2025,
            state="SP",
            municipality_code=352690,
            annual_closure_status="UNKNOWN",
            promote_2025_to_proven=False,
            metric_statuses=statuses,
        )
        promoted = dict(statuses)
        promoted[METRIC_IDS[0]] = "PROVEN"
        with self.assertRaisesRegex(Siope2025BoundedRunnerError, "METRIC_PROMOTION"):
            validate_semantic_state(
                year=2025,
                state="SP",
                municipality_code=352690,
                annual_closure_status="UNKNOWN",
                promote_2025_to_proven=False,
                metric_statuses=promoted,
            )
        with self.assertRaisesRegex(Siope2025BoundedRunnerError, "ANNUAL_CLOSURE_PROMOTION"):
            validate_semantic_state(
                year=2025,
                state="SP",
                municipality_code=352690,
                annual_closure_status="CLOSED",
                promote_2025_to_proven=False,
                metric_statuses=statuses,
            )
        with self.assertRaisesRegex(Siope2025BoundedRunnerError, "SEMANTIC_YEAR"):
            validate_semantic_state(
                year=2026,
                state="SP",
                municipality_code=352690,
                annual_closure_status="UNKNOWN",
                promote_2025_to_proven=False,
                metric_statuses=statuses,
            )

    def test_missing_required_gold_field_stops_and_is_summarizable(self) -> None:
        fixture = copy.deepcopy(self.fixture)
        phase_b = fixture["phase_b_schema_probe"]
        phase_b["schema_fields"].remove("VAL_RECE_REAL")
        summary = summarize_schema(phase_b, required_fields=self.required_fields)
        self.assertEqual(summary["required_gold_input_status"]["VAL_RECE_REAL"], "ABSENT")
        self.assertIn("VAL_RECE_REAL", summary["missing_required_gold_input_fields"])
        self.assertFalse(summary["all_required_gold_inputs_present"])
        with self.assertRaisesRegex(Siope2025BoundedRunnerError, "PHASE_B_SCHEMA_DRIFT"):
            self._run(fixture)

    def test_cli_default_is_plan_only_and_live_is_distinct_stop(self) -> None:
        plan_only = run_cli(fixture_name=None)
        self.assertEqual(plan_only["status"], "PASS_SIOPE_2025_PLAN_ONLY_T0")
        self.assertEqual(plan_only["source_get_count"], 0)
        self.assertEqual(plan_only["request_plan_evidence"]["request_shape_count"], 0)
        with self.assertRaisesRegex(Siope2025BoundedRunnerError, f"^{STOP_LIVE_NOT_AUTHORIZED}$"):
            run_cli(fixture_name=None, live=True)
        with self.assertRaisesRegex(Siope2025BoundedRunnerError, "FIXTURE_NOT_ALLOWED"):
            run_cli(fixture_name="identity_mismatch_stop.json")

    def test_cli_persists_only_sanitized_result_when_explicitly_requested(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "sanitized" / "result.json"
            result = run_cli(fixture_name="p6_exact_schema.json", output=output)
            persisted = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(persisted, result)
        text = json.dumps(persisted, sort_keys=True)
        self.assertNotIn('"records"', text)
        self.assertNotIn('"NOM_MUNI": "Limeira"', text)
        self.assertNotIn('"COD_MUNI": 352690', text)
        self.assertFalse(persisted["observation_evidence"]["response_body_persisted"])
        self.assertFalse(persisted["observation_evidence"]["record_values_persisted"])

    def test_gate_exercises_live_guard_plan_only_and_fake_success(self) -> None:
        result = validate_gate()
        self.assertEqual(result["live_guard"], STOP_LIVE_NOT_AUTHORIZED)
        self.assertEqual(result["fake_request_count"], 7)
        self.assertEqual(result["source_get_count"], 0)
        self.assertEqual(result["drive_read_count"], 0)
        self.assertEqual(result["drive_write_count"], 0)
        self.assertFalse(result["publication"])
        self.assertFalse(result["live_execution_authorized"])

    def test_core_modules_have_no_network_drive_environment_or_filesystem_dependency(self) -> None:
        paths = [
            Path("robo_dados_publicos/sources/siope_2025_bounded_runner.py"),
            Path("robo_dados_publicos/sources/siope_2025_fake_transport.py"),
            Path("robo_dados_publicos/sources/siope_2025_request_plan.py"),
            Path("robo_dados_publicos/sources/siope_2025_evidence.py"),
        ]
        allowed = {"__future__", "copy", "dataclasses", "hashlib", "json", "robo_dados_publicos"}
        for path in paths:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            imports = {
                alias.name.split(".")[0]
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            } | {
                (node.module or "").split(".")[0]
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
            }
            with self.subTest(path=str(path)):
                self.assertLessEqual(imports, allowed)
                lowered = source.lower()
                for forbidden in ("import urllib", "import requests", "import httpx", "import socket", "google_drive", "os.environ", "getenv", "open("):
                    self.assertNotIn(forbidden, lowered)


if __name__ == "__main__":
    unittest.main()

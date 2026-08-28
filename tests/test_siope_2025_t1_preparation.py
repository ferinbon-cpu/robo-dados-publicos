from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import unittest

from robo_dados_publicos.sources.siope_2025_request_plan import materialize_request_plan
from robo_dados_publicos.sources.siope_2025_t1_authorization import (
    AUTH_PATH,
    AuthorizationGrant,
    Siope2025T1AuthorizationError,
    validate_authorization_document,
    validate_preparation_contract,
)
from robo_dados_publicos.sources.siope_2025_t1_discovery import execute_authorized_discovery
from robo_dados_publicos.sources.siope_2025_t1_transport import (
    Siope2025T1HttpTransport,
    Siope2025T1TransportError,
)
from robo_dados_publicos.sources.siope_client import SiopeClientPolicy, SiopePage

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = "232bd69c456c4e0035fecf73473d9e7356f52c1d"
HEAD_SHA = "a" * 40
NOW = datetime(2026, 8, 28, 18, 0, tzinfo=timezone.utc)
RUN_NUMBER = 1
RUN_ATTEMPT = 1
RUN_REF = "refs/heads/main"


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def valid_authorization() -> dict:
    return {
        "schema": "SIOPE_2025_T1_FIRST_LIVE_AUTHORIZATION_V1",
        "authorized": True,
        "authorization_id": "SIOPE2025-T1-FIRST001",
        "approval_kind": "OWNER_EXPLICIT_SINGLE_BOUNDED_RUN",
        "approved_by": "ferinbon-cpu",
        "approved_at_utc": "2026-08-28T17:50:00Z",
        "expires_at_utc": "2026-08-28T19:00:00Z",
        "authorized_base_sha": BASE_SHA,
        "authorized_workflow_run_number": RUN_NUMBER,
        "authorized_workflow_run_attempt": RUN_ATTEMPT,
        "authorized_workflow_ref": RUN_REF,
        "one_shot": True,
        "max_live_runs": 1,
        "target": {"year": 2025, "state": "SP", "municipality_code": 352690, "municipality_name": "Limeira"},
        "request_contract": {
            "maximum_source_get_count": 7,
            "timeout_seconds": 60,
            "max_response_bytes": 262144,
            "max_attempts": 1,
            "retry_authorized": False,
            "follow_redirects": False,
            "pagination_authorized": False,
            "follow_nextlink": False,
        },
        "effects": {
            "drive_read_count": 0,
            "drive_write_count": 0,
            "response_persistence": False,
            "bronze_silver_gold_creation": False,
            "publication": False,
            "future_batch_execution_authorized": False,
        },
        "semantic_guards": {
            "annual_closure_status": "UNKNOWN",
            "promote_2025_to_proven": False,
            "metric_status_required": "UNKNOWN",
            "include_2026_authorized": False,
        },
    }


class StubSiopeClient:
    def __init__(self, *, p6_present: bool = True):
        self.policy = SiopeClientPolicy(
            timeout_seconds=60,
            max_response_bytes=262144,
            max_attempts=1,
            follow_redirects=False,
            follow_nextlink=False,
        )
        self.calls: list[dict] = []
        self.p6_present = p6_present

    def get_dados_gerais_page(self, *, ano, periodo, uf, municipality_code, select_fields):
        self.calls.append({"ano": ano, "periodo": periodo, "uf": uf, "municipality_code": municipality_code})
        if len(select_fields) == 5:
            records = []
            if periodo == 6 and self.p6_present:
                records = [{
                    "COD_MUNI": 352690,
                    "NOM_MUNI": "Limeira",
                    "NUM_ANO": 2025,
                    "NUM_PERI": 6,
                    "SIG_UF": "SP",
                }]
        else:
            records = [{field: None for field in select_fields}]
        return SiopePage(
            records=records,
            status=200,
            content_type="application/json",
            response_byte_count=128,
            odata_context_present=True,
            nextlink_present=False,
            request_count=1,
            response_sha256="b" * 64,
        )


class Task004PreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preparation = load("config/siope_2025_t1_first_live_preparation.v1.json")
        cls.design = load("config/siope_2025_readonly_discovery_design.v1.json")
        cls.policy = load("config/automation_policy.v1.json")

    def validate_auth(self, authorization: dict, **overrides) -> AuthorizationGrant:
        args = {
            "current_head_sha": HEAD_SHA,
            "current_parent_sha": BASE_SHA,
            "changed_paths_since_base": [AUTH_PATH],
            "current_workflow_run_number": RUN_NUMBER,
            "current_workflow_run_attempt": RUN_ATTEMPT,
            "current_workflow_ref": RUN_REF,
            "now_utc": NOW,
        }
        args.update(overrides)
        return validate_authorization_document(authorization, self.preparation, **args)

    def grant(self) -> AuthorizationGrant:
        return self.validate_auth(valid_authorization())

    def test_preparation_contract_is_default_block(self):
        validate_preparation_contract(self.preparation, self.design, self.policy)
        self.assertFalse(self.preparation["live_execution_authorized_by_task_004a"])
        self.assertFalse(self.preparation["source_get_authorized_by_task_004a"])
        self.assertEqual(self.policy["default_decision"], "BLOCK")

    def test_authorization_artifact_transition_is_structurally_safe(self):
        template = load("config/siope_2025_t1_first_live_authorization.template.v1.json")
        self.assertIs(template["authorized"], False)
        self.assertIsNone(template["authorized_base_sha"])
        self.assertIsNone(template["authorized_workflow_run_number"])
        self.assertEqual(template["authorized_workflow_run_attempt"], 1)
        self.assertEqual(template["authorized_workflow_ref"], RUN_REF)
        if (ROOT / AUTH_PATH).exists():
            actual = load(AUTH_PATH)
            self.assertIs(actual["authorized"], True)
            self.assertIs(actual["one_shot"], True)
            self.assertEqual(actual["max_live_runs"], 1)
            self.assertEqual(actual["authorized_workflow_run_attempt"], 1)
            self.assertEqual(actual["authorized_workflow_ref"], RUN_REF)
            self.assertEqual(actual["effects"]["drive_write_count"], 0)
            self.assertFalse(actual["effects"]["publication"])

    def test_missing_false_or_wrong_run_identity_stops(self):
        cases = [
            (None, {}),
            ({**valid_authorization(), "authorized": False}, {}),
            (valid_authorization(), {"current_workflow_run_number": 2}),
            (valid_authorization(), {"current_workflow_run_attempt": 2}),
            (valid_authorization(), {"current_workflow_ref": "refs/heads/other"}),
        ]
        for authorization, overrides in cases:
            with self.assertRaises(Siope2025T1AuthorizationError):
                self.validate_auth(authorization, **overrides)

    def test_authorization_is_exactly_one_commit_and_one_file(self):
        with self.assertRaises(Siope2025T1AuthorizationError):
            self.validate_auth(valid_authorization(), current_parent_sha="c" * 40)
        with self.assertRaises(Siope2025T1AuthorizationError):
            self.validate_auth(valid_authorization(), changed_paths_since_base=[AUTH_PATH, "other.py"])

    def test_authorization_limits_effects_semantics_and_expiry(self):
        mutations = []
        wrong_target = valid_authorization(); wrong_target["target"]["year"] = 2026; mutations.append(wrong_target)
        retry = valid_authorization(); retry["request_contract"]["retry_authorized"] = True; mutations.append(retry)
        write = valid_authorization(); write["effects"]["drive_write_count"] = 1; mutations.append(write)
        promote = valid_authorization(); promote["semantic_guards"]["promote_2025_to_proven"] = True; mutations.append(promote)
        expired = valid_authorization(); expired["expires_at_utc"] = "2026-08-28T17:55:00Z"; mutations.append(expired)
        for authorization in mutations:
            with self.assertRaises(Siope2025T1AuthorizationError):
                self.validate_auth(authorization)

    def test_transport_rejects_drift_and_duplicate(self):
        plan = materialize_request_plan(self.design)
        for spec in (
            replace(plan[0], method="POST"),
            replace(plan[0], host="example.com"),
            replace(plan[0], path="/other"),
            replace(plan[0], year=2026),
        ):
            with self.assertRaises(Siope2025T1TransportError):
                Siope2025T1HttpTransport(grant=self.grant(), client=StubSiopeClient()).request(spec)
        transport = Siope2025T1HttpTransport(grant=self.grant(), client=StubSiopeClient())
        transport.request(plan[0])
        with self.assertRaises(Siope2025T1TransportError):
            transport.request(plan[0])

    def test_mock_authorized_execution_is_bounded_and_never_promotes(self):
        grant = self.grant()
        client = StubSiopeClient(p6_present=True)
        result = execute_authorized_discovery(
            grant=grant,
            design=self.design,
            transport=Siope2025T1HttpTransport(grant=grant, client=client),
        )
        self.assertEqual(result["source_get_count"], 7)
        self.assertEqual(len(client.calls), 7)
        self.assertEqual(result["annual_closure_status"], "UNKNOWN")
        self.assertFalse(result["promote_2025_to_proven"])
        self.assertTrue(all(value == "UNKNOWN" for value in result["metric_statuses"].values()))
        self.assertEqual(result["drive_read_count"], 0)
        self.assertEqual(result["drive_write_count"], 0)
        self.assertFalse(result["publication"])
        self.assertFalse(result["response_persisted"])

    def test_mock_execution_without_p6_uses_six_requests(self):
        grant = self.grant()
        client = StubSiopeClient(p6_present=False)
        result = execute_authorized_discovery(
            grant=grant,
            design=self.design,
            transport=Siope2025T1HttpTransport(grant=grant, client=client),
        )
        self.assertEqual(result["source_get_count"], 6)
        self.assertEqual(len(client.calls), 6)
        self.assertFalse(result["schema_exact"])

    def test_manual_workflow_has_one_shot_identity_and_no_automatic_trigger(self):
        text = (ROOT / ".github/workflows/siope-2025-t1-first-live-discovery.yml").read_text(encoding="utf-8")
        for required in (
            "workflow_dispatch:", "STOP_LIVE_NOT_AUTHORIZED", "persist-credentials: false",
            "--workflow-run-number", "--workflow-run-attempt", "--workflow-ref",
        ):
            self.assertIn(required, text)
        for forbidden in ("schedule:", "push:", "pull_request:", "workflow_run:", "repository_dispatch:", "workflow_call:"):
            self.assertNotIn(forbidden, text)

    def test_cli_paths_before_live_transport_are_zero_get(self):
        prepare = subprocess.run(
            [sys.executable, "scripts/run_siope_2025_t1_first_live.py", "--mode", "prepare"],
            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        if (ROOT / AUTH_PATH).exists():
            self.assertEqual(prepare.returncode, 13)
        else:
            self.assertEqual(prepare.returncode, 0, prepare.stderr)
        self.assertEqual(json.loads(prepare.stdout)["source_get_count"], 0)

        live = subprocess.run(
            [sys.executable, "scripts/run_siope_2025_t1_first_live.py", "--mode", "live", "--authorization-id", "SIOPE2025-T1-FIRST001"],
            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        self.assertEqual(live.returncode, 13)
        payload = json.loads(live.stdout)
        self.assertEqual(payload["status"], "STOP_LIVE_NOT_AUTHORIZED")
        self.assertEqual(payload["source_get_count"], 0)

    def test_offline_gate_accepts_prepared_or_authorized_state_without_source_network(self):
        gate = subprocess.run(
            [sys.executable, "scripts/github_siope_2025_t1_preparation_gate.py"],
            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        self.assertEqual(gate.returncode, 0, gate.stderr)
        self.assertIn("PASS_SIOPE_2025_T1_PREPARATION_T0", gate.stdout)
        self.assertIn('"source_get_count": 0', gate.stdout)


if __name__ == "__main__":
    unittest.main()

import copy
import json
from pathlib import Path
import unittest

from robo_dados_publicos.analytics.bi_serving import build_target
from robo_dados_publicos.analytics.bi_serving_executor import (
    BIServingExecutorError,
    PASS,
    execute_first_serving,
    load_executor_contract,
    validate_executor_authorization,
)

ROOT = Path(__file__).resolve().parents[1]
FIX = json.loads(
    (ROOT / "tests/fixtures/bi_003_serving_scenarios.json").read_text()
)
REFERENCE = json.loads(
    (
        ROOT
        / "docs/evidence/BI_002_T2_MATERIALIZATION_SANITIZED_REFERENCE_0.8.0.json"
    ).read_text()
)


def state_from_target(target):
    rows = [
        dict(zip(target.materialization.ordered_columns, row))
        for row in target.materialization.rows
    ]
    return {
        "tabs": ["DATA", "META"],
        "headers": list(target.materialization.ordered_columns),
        "ordered_columns": list(target.materialization.ordered_columns),
        "rows": rows,
        "dataset_id": target.dataset_id,
        "meta": copy.deepcopy(target.meta),
        "formula_present": False,
        "extra_cells": False,
    }


class FakeTransport:
    def __init__(self, target, *, existing=None):
        self.target = target
        self.existing = existing
        self.calls = []
        self.payload = None
        self.manifest = None
        self.fail_on = None
        self.duplicate = False
        self.wrong_mime = False
        self.manifest_collision = False
        self.readback_override = None

    def _call(self, name):
        self.calls.append(name)
        if self.fail_on == name:
            raise RuntimeError(name)

    def discover_exact(self, *, parent_path, title):
        self._call("discover")
        if self.duplicate:
            return [
                {
                    "spreadsheet_id": "fake-a",
                    "title": title,
                    "mime": "application/vnd.google-apps.spreadsheet",
                },
                {
                    "spreadsheet_id": "fake-b",
                    "title": title,
                    "mime": "application/vnd.google-apps.spreadsheet",
                },
            ]
        if self.existing is None:
            return []
        return [
            {
                "spreadsheet_id": "fake-existing",
                "title": title,
                "mime": (
                    "text/plain"
                    if self.wrong_mime
                    else "application/vnd.google-apps.spreadsheet"
                ),
            }
        ]

    def create_spreadsheet(self, *, parent_path, title, tabs):
        self._call("create")
        return {
            "spreadsheet_id": "fake-created",
            "title": title,
            "mime": "application/vnd.google-apps.spreadsheet",
            "tabs": tabs,
        }

    def batch_update(self, *, spreadsheet_id, payload, clear_grid):
        self._call("batch")
        self.payload = payload
        return {"logical_batch_update_count": 1, "retry_count": 0}

    def readback(self, *, spreadsheet_id):
        self._call("readback")
        if self.readback_override is not None:
            return self.readback_override
        return self.existing or state_from_target(self.target)

    def create_manifest(self, *, parent_path, filename, content):
        self._call("manifest")
        self.manifest = {
            "parent_path": parent_path,
            "filename": filename,
            "content": content,
        }
        if self.manifest_collision:
            return {"created": False, "create_only": True, "collision": True}
        return {"created": True, "create_only": True, "collision": False}


class TestBI004ServingExecutor(unittest.TestCase):
    def setUp(self):
        self.rows = FIX["rows"]["BI_SIOPE_SERIES"]
        self.target = build_target("BI_SIOPE_SERIES", self.rows)
        self.contract = copy.deepcopy(load_executor_contract())
        self.contract["selected_snapshot"] = {
            "snapshot_id": self.target.materialization.snapshot_id,
            "canonical_matrix_sha256": self.target.materialization.canonical_matrix_sha256,
            "schema_fingerprint_sha256": self.target.schema_fingerprint_sha256,
            "row_count": self.target.materialization.row_count,
        }

    def stop(self, code, fn, *args, **kwargs):
        with self.assertRaisesRegex(BIServingExecutorError, code):
            fn(*args, **kwargs)

    def auth(self, **updates):
        value = {
            "authorization_id": "SYNTHETIC-BI004-AUTH",
            "authorized": True,
            "repository": "ferinbon-cpu/robo-dados-publicos",
            "tier": "T3_MUTATING_OR_PUBLICATION",
            "drive_root": "13_BI",
            "parent_path": "13_BI/02_SERVING",
            "task": "BI_004_FIRST_BOUNDED_SERVING_PROOF",
            "scope": "BI_SIOPE_SERIES_CREATE_OR_IDEMPOTENT_READBACK_ONLY",
            "implementation_sha": "a" * 40,
            "selected_datasets": ["BI_SIOPE_SERIES"],
            "selected_snapshots": {
                "BI_SIOPE_SERIES": self.target.materialization.snapshot_id
            },
            "consumed": False,
            "test_only": False,
            "serving_mutation_authorized": True,
            "looker_publication_authorized": False,
            "first_live_proof_only": True,
            "replace_existing_authorized": False,
            "retry_authorized": False,
            "cleanup_authorized": False,
            "generation_manifest_create_only_authorized": True,
        }
        value.update(updates)
        return value

    def execute(self, transport, **updates):
        kwargs = {
            "rows": self.rows,
            "transport": transport,
            "authorization": self.auth(),
            "implementation_sha": "a" * 40,
            "snapshot_validated": True,
            "manifest_validated": True,
            "contract": self.contract,
        }
        kwargs.update(updates)
        return execute_first_serving(**kwargs)

    def test_production_contract_pins_real_siope_snapshot(self):
        contract = load_executor_contract()
        siope = next(
            item
            for item in REFERENCE["snapshots"]
            if item["dataset_id"] == "BI_SIOPE_SERIES"
        )
        self.assertEqual(contract["selected_snapshot"], {
            "snapshot_id": siope["snapshot_id"],
            "canonical_matrix_sha256": siope["canonical_matrix_sha256"],
            "schema_fingerprint_sha256": siope["schema_fingerprint_sha256"],
            "row_count": siope["row_count"],
        })
        self.assertEqual(
            contract["first_live_operation_allowlist"],
            ["CREATE_INITIAL_SERVING", "NO_CHANGE_IDEMPOTENT"],
        )
        self.assertFalse(contract["remote_execution_authorized"])
        self.assertIsNone(contract["active_authorization"])
        self.assertFalse(contract["replace_existing_authorized_first_live"])
        self.assertEqual(contract["limits"]["retry_count"], 0)
        self.assertEqual(contract["limits"]["delete_count"], 0)
        self.assertEqual(contract["limits"]["cleanup_count"], 0)
        self.assertEqual(contract["limits"]["looker_publication_count"], 0)

    def test_authorization_is_exact_sha_snapshot_and_scope_bound(self):
        self.assertEqual(
            validate_executor_authorization(
                self.auth(),
                implementation_sha="a" * 40,
                target=self.target,
                contract=self.contract,
            ),
            "PASS_BI_SERVING_EXECUTOR_AUTHORIZATION_VALID",
        )
        for updates, code in [
            ({"implementation_sha": "b" * 40}, "AUTHORIZATION_MISMATCH"),
            ({"selected_datasets": []}, "DATASET_NOT_AUTHORIZED"),
            ({"selected_snapshots": {}}, "SNAPSHOT_NOT_AUTHORIZED"),
            ({"looker_publication_authorized": True}, "INCLUDES_LOOKER"),
            ({"replace_existing_authorized": True}, "REPLACE_NOT_AUTHORIZED"),
            ({"retry_authorized": True}, "RETRY_NOT_AUTHORIZED"),
            ({"cleanup_authorized": True}, "CLEANUP_NOT_AUTHORIZED"),
            (
                {"generation_manifest_create_only_authorized": False},
                "MANIFEST_NOT_AUTHORIZED",
            ),
            ({"consumed": True}, "AUTHORIZATION_CONSUMED"),
            ({"test_only": True}, "AUTHORIZATION_TEST_ONLY"),
        ]:
            self.stop(
                code,
                validate_executor_authorization,
                self.auth(**updates),
                implementation_sha="a" * 40,
                target=self.target,
                contract=self.contract,
            )
        self.stop(
            "IMPLEMENTATION_SHA_INVALID",
            validate_executor_authorization,
            self.auth(),
            implementation_sha="not-a-sha",
            target=self.target,
            contract=self.contract,
        )

    def test_create_initial_serving_is_bounded_and_semantically_verified(self):
        transport = FakeTransport(self.target)
        result = self.execute(transport)
        self.assertEqual(result["status"], PASS)
        self.assertEqual(result["operation"], "CREATE_INITIAL_SERVING")
        self.assertTrue(result["semantic_readback_verified"])
        self.assertEqual(
            transport.calls,
            ["discover", "create", "batch", "readback", "manifest"],
        )
        self.assertEqual(result["discovery_read_count"], 1)
        self.assertEqual(result["spreadsheet_create_count"], 1)
        self.assertEqual(result["logical_batch_update_count"], 1)
        self.assertEqual(result["semantic_readback_count"], 1)
        self.assertEqual(result["manifest_create_count"], 1)
        self.assertEqual(result["retry_count"], 0)
        self.assertEqual(result["delete_count"], 0)
        self.assertEqual(result["cleanup_count"], 0)
        self.assertEqual(result["looker_publication_count"], 0)
        self.assertFalse(result["remote_ids_included"])
        self.assertEqual(transport.payload["value_input_option"], "RAW")
        self.assertEqual(set(transport.payload["tabs"]), {"DATA", "META"})
        self.assertNotIn("formulaValue", json.dumps(transport.payload))
        self.assertEqual(
            transport.manifest["parent_path"], "13_BI/00_MANIFESTS"
        )
        self.assertTrue(
            transport.manifest["content"]["generation_manifest_create_only"]
        )

    def test_existing_identical_serving_is_no_change(self):
        transport = FakeTransport(
            self.target, existing=state_from_target(self.target)
        )
        result = self.execute(transport)
        self.assertEqual(result["operation"], "NO_CHANGE_IDEMPOTENT")
        self.assertEqual(transport.calls, ["discover", "readback"])
        self.assertEqual(result["spreadsheet_create_count"], 0)
        self.assertEqual(result["logical_batch_update_count"], 0)
        self.assertEqual(result["manifest_create_count"], 0)

    def test_existing_different_serving_cannot_be_replaced_on_first_proof(self):
        changed_rows = [
            {**self.rows[0], "metric_value": self.rows[0]["metric_value"] + 1}
        ]
        changed_target = build_target("BI_SIOPE_SERIES", changed_rows)
        transport = FakeTransport(
            self.target, existing=state_from_target(changed_target)
        )
        self.stop("REPLACE_NOT_AUTHORIZED_FIRST_LIVE", self.execute, transport)
        self.assertEqual(transport.calls, ["discover", "readback"])

    def test_duplicate_or_wrong_mime_stops_before_write(self):
        transport = FakeTransport(self.target)
        transport.duplicate = True
        self.stop("DUPLICATE_REMOTE_NAME", self.execute, transport)
        self.assertEqual(transport.calls, ["discover"])

        transport = FakeTransport(
            self.target, existing=state_from_target(self.target)
        )
        transport.wrong_mime = True
        self.stop("WRONG_MIME", self.execute, transport)
        self.assertEqual(transport.calls, ["discover"])

    def test_authorization_and_pin_stop_before_transport(self):
        transport = FakeTransport(self.target)
        self.stop(
            "T3_NOT_AUTHORIZED",
            self.execute,
            transport,
            authorization=None,
        )
        self.assertEqual(transport.calls, [])

        wrong_contract = copy.deepcopy(self.contract)
        wrong_contract["selected_snapshot"]["snapshot_id"] = "0" * 24
        self.stop(
            "SNAPSHOT_PIN_MISMATCH",
            self.execute,
            transport,
            contract=wrong_contract,
        )
        self.assertEqual(transport.calls, [])

    def test_partial_creation_failure_has_no_retry_or_cleanup(self):
        transport = FakeTransport(self.target)
        transport.fail_on = "batch"
        self.stop(
            "PARTIAL_INITIAL_CREATION_OWNER_DECISION_REQUIRED",
            self.execute,
            transport,
        )
        self.assertEqual(transport.calls, ["discover", "create", "batch"])

        transport = FakeTransport(self.target)
        bad = state_from_target(self.target)
        bad["rows"][0]["metric_value"] = 999
        transport.readback_override = bad
        self.stop(
            "PARTIAL_INITIAL_CREATION_OWNER_DECISION_REQUIRED",
            self.execute,
            transport,
        )
        self.assertEqual(
            transport.calls, ["discover", "create", "batch", "readback"]
        )

    def test_manifest_collision_stops_without_retry(self):
        transport = FakeTransport(self.target)
        transport.manifest_collision = True
        self.stop("MANIFEST_CREATE_RESPONSE_INVALID", self.execute, transport)
        self.assertEqual(
            transport.calls,
            ["discover", "create", "batch", "readback", "manifest"],
        )

    def test_snapshot_validation_is_required(self):
        transport = FakeTransport(self.target)
        self.stop(
            "SNAPSHOT_NOT_VALIDATED",
            self.execute,
            transport,
            snapshot_validated=False,
        )
        self.assertEqual(transport.calls, [])

    def test_executor_source_has_no_remote_client(self):
        source = (
            ROOT
            / "robo_dados_publicos/analytics/bi_serving_executor.py"
        ).read_text().lower()
        for term in (
            "googleapiclient",
            "gspread",
            "requests",
            "socket",
            "drive_service",
            "service_account",
        ):
            self.assertNotIn(term, source)


if __name__ == "__main__":
    unittest.main()

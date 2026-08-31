import copy
import json
from pathlib import Path
import unittest

from robo_dados_publicos.analytics.bi_serving import build_target
from robo_dados_publicos.analytics.bi_serving_executor_multi import (
    BIMultiServingExecutorError,
    PASS,
    execute_serving,
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
SHA = "a" * 40


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


def synthetic_contract():
    contract = copy.deepcopy(load_executor_contract())
    for dataset_id in contract["dataset_allowlist"]:
        target = build_target(dataset_id, FIX["rows"][dataset_id])
        contract["dataset_pins"][dataset_id] = {
            "serving_name": target.serving_name,
            "row_count": target.materialization.row_count,
            "snapshot_id": target.materialization.snapshot_id,
            "canonical_matrix_sha256": target.materialization.canonical_matrix_sha256,
            "schema_fingerprint_sha256": target.schema_fingerprint_sha256,
        }
    return contract


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
        self.wrong_title = False
        self.bad_create = False
        self.bad_write = False
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
                "title": "WRONG" if self.wrong_title else title,
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
            "title": "WRONG" if self.bad_create else title,
            "mime": "application/vnd.google-apps.spreadsheet",
            "tabs": tabs,
        }

    def batch_update(self, *, spreadsheet_id, payload, clear_grid):
        self._call("batch")
        self.payload = payload
        if self.bad_write:
            return {"logical_batch_update_count": 2, "retry_count": 0}
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


class TestBI005GeneralizedServingExecutor(unittest.TestCase):
    def setUp(self):
        self.contract = synthetic_contract()

    def stop(self, code, fn, *args, **kwargs):
        with self.assertRaisesRegex(BIMultiServingExecutorError, code):
            fn(*args, **kwargs)

    def target(self, dataset_id):
        return build_target(dataset_id, FIX["rows"][dataset_id])

    def auth(self, dataset_id, **updates):
        target = self.target(dataset_id)
        value = {
            "authorization_id": f"SYNTHETIC-BI005-{dataset_id}",
            "authorized": True,
            "repository": "ferinbon-cpu/robo-dados-publicos",
            "tier": "T3_MUTATING_OR_PUBLICATION",
            "drive_root": "13_BI",
            "parent_path": "13_BI/02_SERVING",
            "task": "BI_005_BOUNDED_SERVING",
            "scope": "SINGLE_PINNED_STABLE_SERVING_FROM_IMMUTABLE_SNAPSHOT",
            "implementation_sha": SHA,
            "selected_datasets": [dataset_id],
            "selected_snapshots": {dataset_id: target.materialization.snapshot_id},
            "selected_serving_names": [target.serving_name],
            "consumed": False,
            "test_only": False,
            "serving_mutation_authorized": True,
            "looker_publication_authorized": False,
            "replace_existing_authorized": False,
            "retry_authorized": False,
            "cleanup_authorized": False,
            "generation_manifest_create_only_authorized": True,
        }
        value.update(updates)
        return value

    def execute(self, dataset_id, transport, **updates):
        kwargs = {
            "dataset_id": dataset_id,
            "rows": FIX["rows"][dataset_id],
            "transport": transport,
            "authorization": self.auth(dataset_id),
            "implementation_sha": SHA,
            "snapshot_validated": True,
            "manifest_validated": True,
            "contract": self.contract,
        }
        kwargs.update(updates)
        return execute_serving(**kwargs)

    def test_production_contract_matches_all_six_materialized_pins(self):
        contract = load_executor_contract()
        reference = {
            item["dataset_id"]: item for item in REFERENCE["snapshots"]
        }
        self.assertEqual(contract["dataset_allowlist"], list(reference))
        self.assertEqual(len(contract["dataset_pins"]), 6)
        for dataset_id in contract["dataset_allowlist"]:
            pin = contract["dataset_pins"][dataset_id]
            source = reference[dataset_id]
            self.assertEqual(pin["serving_name"], f"{dataset_id}__SERVING")
            for key in (
                "row_count",
                "snapshot_id",
                "canonical_matrix_sha256",
                "schema_fingerprint_sha256",
            ):
                self.assertEqual(pin[key], source[key])
        self.assertTrue(contract["one_dataset_per_execution"])
        self.assertFalse(contract["remote_execution_authorized"])
        self.assertIsNone(contract["active_authorization"])
        self.assertEqual(contract["limits"]["retry_count"], 0)
        self.assertEqual(contract["limits"]["delete_count"], 0)
        self.assertEqual(contract["limits"]["cleanup_count"], 0)
        self.assertEqual(contract["limits"]["looker_publication_count"], 0)

    def test_all_six_datasets_create_with_recomputed_target(self):
        for dataset_id in self.contract["dataset_allowlist"]:
            with self.subTest(dataset_id=dataset_id):
                target = self.target(dataset_id)
                transport = FakeTransport(target)
                result = self.execute(dataset_id, transport)
                self.assertEqual(result["status"], PASS)
                self.assertEqual(result["operation"], "CREATE_INITIAL_SERVING")
                self.assertTrue(result["semantic_readback_verified"])
                self.assertEqual(
                    transport.calls,
                    ["discover", "create", "batch", "readback", "manifest"],
                )
                self.assertEqual(result["spreadsheet_create_count"], 1)
                self.assertEqual(result["logical_batch_update_count"], 1)
                self.assertEqual(result["semantic_readback_count"], 1)
                self.assertEqual(result["manifest_create_count"], 1)
                self.assertEqual(
                    (result["retry_count"], result["delete_count"], result["cleanup_count"], result["looker_publication_count"]),
                    (0, 0, 0, 0),
                )
                self.assertFalse(result["remote_ids_included"])
                self.assertEqual(transport.payload["value_input_option"], "RAW")
                self.assertEqual(set(transport.payload["tabs"]), {"DATA", "META"})
                self.assertTrue(transport.manifest["content"]["generation_manifest_create_only"])
                self.assertEqual(transport.manifest["content"]["task"], "BI_005")
                self.assertEqual(transport.manifest["content"]["retry_count"], 0)

    def test_all_six_idempotent_paths_perform_read_only_semantic_verification(self):
        for dataset_id in self.contract["dataset_allowlist"]:
            with self.subTest(dataset_id=dataset_id):
                target = self.target(dataset_id)
                transport = FakeTransport(target, existing=state_from_target(target))
                result = self.execute(dataset_id, transport)
                self.assertEqual(result["operation"], "NO_CHANGE_IDEMPOTENT")
                self.assertEqual(transport.calls, ["discover", "readback"])
                self.assertEqual(result["spreadsheet_create_count"], 0)
                self.assertEqual(result["logical_batch_update_count"], 0)
                self.assertEqual(result["manifest_create_count"], 0)

    def test_unknown_dataset_and_pin_drift_stop_before_transport(self):
        target = self.target("BI_SIOPE_SERIES")
        transport = FakeTransport(target)
        self.stop(
            "UNKNOWN_DATASET",
            execute_serving,
            dataset_id="BI_ALL",
            rows=FIX["rows"]["BI_SIOPE_SERIES"],
            transport=transport,
            authorization=None,
            implementation_sha=SHA,
            snapshot_validated=True,
            manifest_validated=True,
            contract=self.contract,
        )
        self.assertEqual(transport.calls, [])

        wrong = copy.deepcopy(self.contract)
        wrong["dataset_pins"]["BI_SIOPE_SERIES"]["snapshot_id"] = "0" * 24
        self.stop(
            "SNAPSHOT_PIN_MISMATCH",
            self.execute,
            "BI_SIOPE_SERIES",
            transport,
            contract=wrong,
        )
        self.assertEqual(transport.calls, [])

    def test_row_mutation_is_recomputed_and_rejected_by_pin(self):
        dataset_id = "BI_SIOPE_SERIES"
        target = self.target(dataset_id)
        transport = FakeTransport(target)
        rows = copy.deepcopy(FIX["rows"][dataset_id])
        rows[0]["metric_value"] = rows[0]["metric_value"] + 1
        self.stop(
            "SNAPSHOT_PIN_MISMATCH",
            self.execute,
            dataset_id,
            transport,
            rows=rows,
        )
        self.assertEqual(transport.calls, [])

    def test_schema_mutation_and_siope_2025_stop_before_transport(self):
        dataset_id = "BI_SIOPE_SERIES"
        target = self.target(dataset_id)
        transport = FakeTransport(target)
        rows = copy.deepcopy(FIX["rows"][dataset_id])
        rows[0]["unexpected_field"] = "x"
        self.stop("INVALID_TARGET", self.execute, dataset_id, transport, rows=rows)
        self.assertEqual(transport.calls, [])

        rows = copy.deepcopy(FIX["rows"][dataset_id])
        rows[0]["year"] = 2025
        rows[0]["annual_period"] = "P6"
        self.stop("INVALID_TARGET", self.execute, dataset_id, transport, rows=rows)
        self.assertEqual(transport.calls, [])

    def test_authorization_is_single_dataset_snapshot_serving_and_sha_bound(self):
        dataset_id = "BI_JORNAL_EVENTOS"
        target = self.target(dataset_id)
        self.assertEqual(
            validate_executor_authorization(
                self.auth(dataset_id),
                implementation_sha=SHA,
                target=target,
                contract=self.contract,
            ),
            "PASS_BI_005_SINGLE_DATASET_AUTHORIZATION_VALID",
        )
        cases = [
            ({"implementation_sha": "b" * 40}, "AUTHORIZATION_MISMATCH"),
            ({"selected_datasets": ["BI_DICIONARIO"]}, "DATASET_NOT_AUTHORIZED"),
            ({"selected_snapshots": {dataset_id: "0" * 24}}, "SNAPSHOT_NOT_AUTHORIZED"),
            ({"selected_serving_names": ["BI_DICIONARIO__SERVING"]}, "SERVING_NAME_NOT_AUTHORIZED"),
            ({"consumed": True}, "AUTHORIZATION_CONSUMED"),
            ({"test_only": True}, "AUTHORIZATION_TEST_ONLY"),
            ({"looker_publication_authorized": True}, "INCLUDES_LOOKER"),
            ({"replace_existing_authorized": True}, "REPLACE_NOT_AUTHORIZED"),
            ({"retry_authorized": True}, "RETRY_NOT_AUTHORIZED"),
            ({"cleanup_authorized": True}, "CLEANUP_NOT_AUTHORIZED"),
            ({"generation_manifest_create_only_authorized": False}, "MANIFEST_NOT_AUTHORIZED"),
        ]
        for updates, code in cases:
            with self.subTest(code=code):
                self.stop(
                    code,
                    validate_executor_authorization,
                    self.auth(dataset_id, **updates),
                    implementation_sha=SHA,
                    target=target,
                    contract=self.contract,
                )
        self.stop(
            "IMPLEMENTATION_SHA_INVALID",
            validate_executor_authorization,
            self.auth(dataset_id),
            implementation_sha="not-a-sha",
            target=target,
            contract=self.contract,
        )

    def test_multi_dataset_authorization_is_rejected(self):
        dataset_id = "BI_DICIONARIO"
        target = self.target(dataset_id)
        auth = self.auth(dataset_id)
        auth["selected_datasets"].append("BI_FONTES_STATUS")
        auth["selected_snapshots"]["BI_FONTES_STATUS"] = "0" * 24
        auth["selected_serving_names"].append("BI_FONTES_STATUS__SERVING")
        self.stop(
            "DATASET_NOT_AUTHORIZED",
            validate_executor_authorization,
            auth,
            implementation_sha=SHA,
            target=target,
            contract=self.contract,
        )

    def test_duplicate_wrong_title_and_wrong_mime_stop_before_write(self):
        dataset_id = "BI_FONTES_STATUS"
        target = self.target(dataset_id)
        for attribute, code in [
            ("duplicate", "DUPLICATE_REMOTE_NAME"),
            ("wrong_title", "WRONG_TITLE"),
            ("wrong_mime", "WRONG_MIME"),
        ]:
            transport = FakeTransport(target, existing=state_from_target(target))
            setattr(transport, attribute, True)
            self.stop(code, self.execute, dataset_id, transport)
            self.assertEqual(transport.calls, ["discover"])

    def test_existing_different_valid_snapshot_requires_owner_decision(self):
        dataset_id = "BI_SIOPE_SERIES"
        target = self.target(dataset_id)
        changed_rows = copy.deepcopy(FIX["rows"][dataset_id])
        changed_rows[0]["metric_value"] = changed_rows[0]["metric_value"] + 1
        changed_target = build_target(dataset_id, changed_rows)
        transport = FakeTransport(target, existing=state_from_target(changed_target))
        self.stop("REPLACE_NOT_AUTHORIZED", self.execute, dataset_id, transport)
        self.assertEqual(transport.calls, ["discover", "readback"])

    def test_create_write_and_readback_failures_have_no_retry_or_cleanup(self):
        dataset_id = "BI_EXECUCOES_ROBO"
        target = self.target(dataset_id)
        for stage in ("create", "batch", "readback"):
            transport = FakeTransport(target)
            transport.fail_on = stage
            code = (
                "CREATE_FAILED_AMBIGUOUS"
                if stage == "create"
                else "PARTIAL_INITIAL_CREATION_OWNER_DECISION_REQUIRED"
            )
            self.stop(code, self.execute, dataset_id, transport)
            self.assertEqual(transport.calls.count(stage), 1)
            self.assertNotIn("manifest", transport.calls)
        transport = FakeTransport(target)
        transport.bad_write = True
        self.stop("WRITE_RESPONSE_INVALID", self.execute, dataset_id, transport)
        self.assertEqual(transport.calls, ["discover", "create", "batch"])

    def test_semantic_readback_mismatch_stops_before_manifest(self):
        dataset_id = "BI_RECONCILIACAO"
        target = self.target(dataset_id)
        bad = state_from_target(target)
        first = next(iter(bad["rows"][0]))
        bad["rows"][0][first] = "corrupted"
        transport = FakeTransport(target)
        transport.readback_override = bad
        self.stop(
            "PARTIAL_INITIAL_CREATION_OWNER_DECISION_REQUIRED",
            self.execute,
            dataset_id,
            transport,
        )
        self.assertEqual(transport.calls, ["discover", "create", "batch", "readback"])

    def test_manifest_collision_stops_without_retry(self):
        dataset_id = "BI_DICIONARIO"
        target = self.target(dataset_id)
        transport = FakeTransport(target)
        transport.manifest_collision = True
        self.stop("MANIFEST_CREATE_RESPONSE_INVALID", self.execute, dataset_id, transport)
        self.assertEqual(
            transport.calls, ["discover", "create", "batch", "readback", "manifest"]
        )

    def test_jornal_null_and_reconciliation_semantics_are_preserved(self):
        jornal = self.target("BI_JORNAL_EVENTOS")
        supplier = jornal.materialization.ordered_columns.index("supplier_name")
        self.assertIsNone(jornal.materialization.rows[0][supplier])
        rec = self.target("BI_RECONCILIACAO")
        status = rec.materialization.ordered_columns.index("status")
        proven = rec.materialization.ordered_columns.index("financial_identity_proven")
        self.assertEqual(rec.materialization.rows[0][status], "MATCH_CANDIDATE")
        self.assertFalse(rec.materialization.rows[0][proven])

    def test_module_contains_no_remote_client(self):
        import robo_dados_publicos.analytics.bi_serving_executor_multi as module

        source = Path(module.__file__).read_text().lower()
        for term in ("googleapiclient", "requests", "socket", "httplib", "lookerstudio"):
            self.assertNotIn(term, source)


if __name__ == "__main__":
    unittest.main()

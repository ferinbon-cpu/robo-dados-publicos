import copy
from decimal import Decimal
import json
from pathlib import Path
import unittest

from robo_dados_publicos.analytics.bi_materialization import build_plan, plan_serving
from robo_dados_publicos.analytics.bi_serving import (
    BIServingError,
    META_KEYS,
    build_target,
    classify_remote_failure,
    load_serving_contract,
    plan_looker_publication,
    plan_serving_mutation,
    schema_fingerprint,
    semantic_readback,
    serialize_cell,
    serialize_target,
    serving_generation_manifest,
    validate_existing,
    validate_remote_preflight,
    validate_serving_authorization,
)

ROOT = Path(__file__).resolve().parents[1]
FIX = json.loads((ROOT / "tests/fixtures/bi_003_serving_scenarios.json").read_text())
ROWS = FIX["rows"]
REFERENCE = json.loads(
    (ROOT / "docs/evidence/BI_002_T2_MATERIALIZATION_SANITIZED_REFERENCE_0.8.0.json").read_text()
)
REFERENCE_BY_DATASET = {item["dataset_id"]: item for item in REFERENCE["snapshots"]}


class TestBI003Serving(unittest.TestCase):
    def setUp(self):
        self.target = build_target("BI_DICIONARIO", ROWS["BI_DICIONARIO"])

    def stop(self, code, fn, *args, **kwargs):
        with self.assertRaisesRegex(BIServingError, code):
            fn(*args, **kwargs)

    def existing(self, target=None):
        target = target or self.target
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

    def auth(self):
        return {
            "authorization_id": "SYNTHETIC-AUTH",
            "authorized": True,
            "repository": "ferinbon-cpu/robo-dados-publicos",
            "tier": "T3_MUTATING_OR_PUBLICATION",
            "drive_root": "13_BI",
            "parent_path": "13_BI/02_SERVING",
            "task": "BI_003_STABLE_SERVING_MATERIALIZATION",
            "scope": "STABLE_SERVING_SHEETS_FROM_PINNED_BI_SNAPSHOTS",
            "implementation_sha": "a" * 40,
            "selected_datasets": [self.target.dataset_id],
            "selected_snapshots": {
                self.target.dataset_id: self.target.materialization.snapshot_id
            },
            "consumed": False,
            "test_only": False,
            "serving_mutation_authorized": True,
            "looker_publication_authorized": False,
        }

    def test_contract_names_parent_tabs(self):
        contract = load_serving_contract()
        self.assertEqual(contract["parent_path"], "13_BI/02_SERVING")
        self.assertEqual(contract["tabs"], ["DATA", "META"])
        self.assertEqual(len(contract["dataset_allowlist"]), 6)
        self.assertEqual(
            contract["serving_names"],
            [dataset + "__SERVING" for dataset in contract["dataset_allowlist"]],
        )
        self.assertIsNone(contract["active_authorization"])
        self.assertFalse(contract["remote_execution_authorized"])
        self.assertTrue(contract["looker_is_separate"])

    def test_all_six_targets_and_real_schema_fingerprints(self):
        self.assertEqual(set(ROWS), set(REFERENCE_BY_DATASET))
        for dataset, rows in ROWS.items():
            target = build_target(dataset, rows)
            plan = build_plan(dataset, rows)
            self.assertEqual(target.serving_name, dataset + "__SERVING")
            self.assertEqual(target.schema_fingerprint_sha256, plan.schema_fingerprint_sha256)
            self.assertEqual(schema_fingerprint(dataset), plan.schema_fingerprint_sha256)
            self.assertEqual(
                target.schema_fingerprint_sha256,
                REFERENCE_BY_DATASET[dataset]["schema_fingerprint_sha256"],
            )

    def test_typed_serializer(self):
        self.assertEqual(
            serialize_cell("abc", "text"),
            {"userEnteredValue": {"stringValue": "abc"}},
        )
        self.assertEqual(
            serialize_cell(True, "boolean"),
            {"userEnteredValue": {"boolValue": True}},
        )
        self.assertEqual(serialize_cell(None, "text"), {})
        for kind, value in [
            ("integer", 2),
            ("number", 1.5),
            ("currency", Decimal("3.25")),
        ]:
            self.assertEqual(
                serialize_cell(value, kind)["userEnteredValue"],
                {"numberValue": float(value)},
            )
        date_cell = serialize_cell("2024-02-29", "date")
        datetime_cell = serialize_cell("2024-02-29T12:30:00Z", "datetime")
        self.assertIsInstance(date_cell["userEnteredValue"]["numberValue"], float)
        self.assertEqual(
            date_cell["userEnteredFormat"]["numberFormat"]["pattern"],
            "yyyy-mm-dd",
        )
        self.assertIsInstance(datetime_cell["userEnteredValue"]["numberValue"], float)
        self.assertEqual(
            datetime_cell["userEnteredFormat"]["numberFormat"]["pattern"],
            "yyyy-mm-dd hh:mm:ss",
        )
        self.stop("INVALID_TYPED_VALUE", serialize_cell, 123, "text")
        self.stop("INVALID_TYPED_VALUE", serialize_cell, True, "integer")
        self.stop("INVALID_TYPED_VALUE", serialize_cell, "1,23", "currency")

    def test_serialized_sheet_is_raw_two_tabs_no_formula(self):
        payload = serialize_target(self.target)
        self.assertEqual(set(payload["tabs"]), {"DATA", "META"})
        self.assertEqual(payload["value_input_option"], "RAW")
        self.assertNotIn("formulaValue", json.dumps(payload))
        self.assertEqual(len(payload["tabs"]["DATA"]), 2)
        self.assertEqual(len(payload["tabs"]["META"]), len(META_KEYS) + 1)

    def test_modes_and_trailing_union(self):
        self.assertEqual(
            plan_serving_mutation(
                self.target, None, snapshot_validated=True
            ).operation,
            "CREATE_INITIAL_SERVING",
        )
        self.assertEqual(
            plan_serving_mutation(
                self.target, self.existing(), snapshot_validated=True
            ).operation,
            "NO_CHANGE_IDEMPOTENT",
        )
        old_rows = ROWS["BI_SIOPE_SERIES"]
        old = build_target("BI_SIOPE_SERIES", old_rows)
        changed = {**old_rows[0], "metric_value": 999}
        new = build_target("BI_SIOPE_SERIES", [changed])
        state = self.existing(old)
        plan = plan_serving_mutation(new, state, snapshot_validated=True)
        self.assertEqual(plan.operation, "REPLACE_SERVING_FROM_NEW_SNAPSHOT")
        self.assertEqual(plan.logical_batch_update_count, 1)
        self.assertEqual(plan.automatic_retry_count, 0)

        many = [
            {**ROWS["BI_DICIONARIO"][0], "field": f"field_{index}"}
            for index in range(303)
        ]
        old_many = build_target("BI_DICIONARIO", many)
        state = self.existing(old_many)
        plan = plan_serving_mutation(self.target, state, snapshot_validated=True)
        self.assertEqual(plan.clear_grid["rows"], 304)
        self.assertFalse(plan.cleanup_on_failure)

    def test_schema_drift_and_invalid_existing(self):
        state = self.existing()
        state["meta"]["schema_fingerprint_sha256"] = "0" * 64
        self.stop(
            "SCHEMA_DRIFT_REQUIRES_MIGRATION",
            plan_serving_mutation,
            self.target,
            state,
            snapshot_validated=True,
        )

        state = self.existing()
        state["meta"]["canonical_matrix_sha256"] = "0" * 64
        self.stop("EXISTING_STATE_INVALID", validate_existing, state)

        state = self.existing()
        del state["meta"]["row_count"]
        self.stop("INVALID_META", validate_existing, state)

        state = self.existing()
        state["meta"]["quality_status"] = "UNKNOWN"
        self.stop("INVALID_META", validate_existing, state)

        state = self.existing()
        state["meta"]["unexpected"] = "x"
        self.stop("INVALID_META", validate_existing, state)

    def test_unexpected_content_stops(self):
        for field, code, value in [
            ("tabs", "UNEXPECTED_TAB", ["DATA", "META", "EXTRA"]),
            ("formula_present", "FORMULA_PRESENT", True),
            ("extra_cells", "EXTRA_CELLS", True),
        ]:
            state = self.existing()
            state[field] = value
            self.stop(code, validate_existing, state)
        state = self.existing()
        state["headers"].append("extra")
        self.stop("EXTRA_CELLS", validate_existing, state)

    def test_remote_preflight(self):
        kwargs = {
            "parent": "13_BI/02_SERVING",
            "remote_matches": 0,
            "mime": None,
            "snapshot_validated": True,
            "manifest_validated": True,
        }
        validate_remote_preflight(self.target, **kwargs)
        self.stop(
            "WRONG_PARENT",
            validate_remote_preflight,
            self.target,
            **{**kwargs, "parent": "13_BI"},
        )
        self.stop(
            "WRONG_TITLE",
            validate_remote_preflight,
            self.target,
            **{**kwargs, "title": "WRONG"},
        )
        self.stop(
            "DUPLICATE_REMOTE_NAME",
            validate_remote_preflight,
            self.target,
            **{**kwargs, "remote_matches": 2},
        )
        self.stop(
            "WRONG_MIME",
            validate_remote_preflight,
            self.target,
            **{**kwargs, "remote_matches": 1, "mime": "text/plain"},
        )
        self.stop(
            "SNAPSHOT_NOT_VALIDATED",
            validate_remote_preflight,
            self.target,
            **{**kwargs, "snapshot_validated": False},
        )
        self.stop(
            "REMOTE_STATE_INVALID",
            validate_remote_preflight,
            self.target,
            **{**kwargs, "remote_matches": -1},
        )

    def test_authorization_hardening(self):
        self.stop(
            "T3_NOT_AUTHORIZED",
            validate_serving_authorization,
            None,
            implementation_sha="a" * 40,
            target=self.target,
        )
        self.assertEqual(
            validate_serving_authorization(
                self.auth(), implementation_sha="a" * 40, target=self.target
            ),
            "PASS_BI_SERVING_AUTHORIZATION_VALID",
        )
        cases = [
            ("consumed", True, "CONSUMED"),
            ("test_only", True, "TEST_ONLY"),
            ("implementation_sha", "b" * 40, "MISMATCH"),
            ("selected_datasets", [], "DATASET_NOT_AUTHORIZED"),
            ("selected_snapshots", {}, "SNAPSHOT_NOT_AUTHORIZED"),
            ("looker_publication_authorized", True, "INCLUDES_LOOKER"),
        ]
        for field, value, code in cases:
            auth = self.auth()
            auth[field] = value
            self.stop(
                code,
                validate_serving_authorization,
                auth,
                implementation_sha="a" * 40,
                target=self.target,
            )

        auth = self.auth()
        del auth["authorization_id"]
        self.stop(
            "MISMATCH",
            validate_serving_authorization,
            auth,
            implementation_sha="a" * 40,
            target=self.target,
        )

        self.stop(
            "IMPLEMENTATION_SHA_INVALID",
            validate_serving_authorization,
            self.auth(),
            implementation_sha="not-a-sha",
            target=self.target,
        )
        auth = self.auth()
        auth["implementation_sha"] = "g" * 40
        self.stop(
            "IMPLEMENTATION_SHA_INVALID",
            validate_serving_authorization,
            auth,
            implementation_sha="a" * 40,
            target=self.target,
        )

    def test_serving_and_looker_are_separate(self):
        self.assertEqual(
            plan_serving(snapshot_validated=True, t3_authorized=True),
            "PASS_BI_MATERIALIZATION_PLAN_OFFLINE",
        )
        with self.assertRaisesRegex(Exception, "LOOKER_SEPARATE_AUTHORIZATION_REQUIRED"):
            plan_serving(
                snapshot_validated=True,
                t3_authorized=True,
                looker_authorized=True,
            )
        self.stop("LOOKER_SEPARATE_AUTHORIZATION_REQUIRED", plan_looker_publication)

    def test_semantic_readback(self):
        state = self.existing()
        self.assertEqual(
            semantic_readback(self.target, state),
            "PASS_BI_SERVING_SEMANTIC_READBACK_VERIFIED",
        )
        state["rows"][0]["definition"] = "changed"
        self.stop("READBACK_MISMATCH", semantic_readback, self.target, state)

    def test_generation_manifest(self):
        plan = plan_serving_mutation(self.target, None, snapshot_validated=True)
        manifest = serving_generation_manifest(plan, "AUTH", "a" * 40)
        self.assertTrue(manifest["filename"].endswith("__manifest.json"))
        self.assertTrue(manifest["generation_manifest_create_only"])
        self.assertFalse(manifest["looker_publication"])
        self.assertFalse(manifest["source_snapshot_modified"])
        self.stop(
            "IMPLEMENTATION_SHA_INVALID",
            serving_generation_manifest,
            plan,
            "AUTH",
            "bad",
        )

    def test_failures_have_no_retry_cleanup(self):
        self.stop(
            "AMBIGUOUS_READBACK_REQUIRED",
            classify_remote_failure,
            ambiguous=True,
        )
        self.stop(
            "PARTIAL_INITIAL_CREATION_OWNER_DECISION_REQUIRED",
            classify_remote_failure,
            partial_initial_creation=True,
        )

    def test_semantic_invariants_and_offline_surface(self):
        self.stop(
            "INVALID_SCHEMA",
            build_target,
            "BI_SIOPE_SERIES",
            [{**ROWS["BI_SIOPE_SERIES"][0], "year": 2025, "annual_period": "P6"}],
        )
        self.stop(
            "INVALID_SCHEMA",
            build_target,
            "BI_RECONCILIACAO",
            [{**ROWS["BI_RECONCILIACAO"][0], "financial_identity_proven": True}],
        )
        source = (ROOT / "robo_dados_publicos/analytics/bi_serving.py").read_text()
        lowered = source.lower()
        for term in ("googleapiclient", "csv import", "user_entered", "requests", "socket"):
            self.assertNotIn(term, lowered)
        self.assertEqual(FIX["classification"], "SYNTHETIC_SANITIZED_TEST_ONLY")
        self.assertEqual(len(FIX["scenario_names"]), 22)


if __name__ == "__main__":
    unittest.main()

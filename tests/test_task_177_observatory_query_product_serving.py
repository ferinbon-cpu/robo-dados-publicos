import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.analytics.observatory_products import (
    build_product_catalog,
    materialize_product,
)
from robo_dados_publicos.analytics.observatory_query_serving import (
    Task177Stop,
    build_target,
    generation_manifest,
    plan_serving,
    semantic_readback,
    serialize_target,
    validate_authorization,
    validate_contract,
    validate_product_snapshot,
    validate_remote_preflight,
)


ROOT = Path(__file__).resolve().parents[1]
GENERATED_AT = "2026-09-06T00:00:00Z"
SOFTWARE = "0.8.0"
SHA = "a" * 64
IMPL_SHA = "b" * 40


def common(source_family, caution="fixture"):
    return {
        "observation_period": "2026",
        "source_family": source_family,
        "source_sha256": SHA,
        "provenance_ref": f"PROV_{source_family}",
        "quality_status": "VALIDATED",
        "caution": caution,
    }


def school(value=100, **extra):
    row = {
        "scope_level": "SCHOOL",
        "scope_id": "SCHOOL_1",
        "school_code": "35000001",
        "school_name": "Escola Municipal Exemplo",
        "network": "MUNICIPAL",
        "period": "2026",
        "indicator_id": "enrollment",
        "indicator_name": "Matrículas",
        "value": value,
        "unit": "COUNT",
        "context": "Fixture sanitizada.",
        **common("CENSO_ESCOLAR", "Ranking requires context."),
        **extra,
    }
    return materialize_product(
        "SCHOOL_INDICATOR_SERIES",
        [row],
        generated_at=GENERATED_AT,
        software_version=SOFTWARE,
    )


def jom():
    row = {
        "event_id": "JOEV_1",
        "publication_date": "2026-09-05",
        "event_type": "DECRETO",
        "policy_domains": ["EDUCATION"],
        "evidence_layers": ["NORMATIVE"],
        "financial_stages": [],
        "education_topics": ["SCHOOL_CALENDAR"],
        "source_locator": {"source_id": "LIMEIRA_JO_07310", "page_number": 2},
        **common("JORNAL_OFICIAL", "Publication is not implementation."),
    }
    return materialize_product(
        "JOM_EVENT_INDEX",
        [row],
        generated_at=GENERATED_AT,
        software_version=SOFTWARE,
    )


def accounting():
    row = {
        "observation_id": "ACCTOBS_1",
        "fiscal_year": 2026,
        "stage": "COMMITMENT",
        "amount_semantic": "COMMITTED_VALUE",
        "amount_brl": "150000.00",
        "transaction_keys": {
            "source_expense_identifier": "EXP-1",
            "fiscal_year_plus_empenho": "2026:1234",
        },
        "programmatic_dimensions": {
            "function": "Educação",
            "program_code": "2001",
            "action_code": "2010",
        },
        "evidence_status": "DIRECT_EXPLICIT_CONTROL_RECORD",
        **common("TCE_SP_EXPENSES", "Commitment is not payment."),
    }
    return materialize_product(
        "ACCOUNTING_LEDGER",
        [row],
        generated_at=GENERATED_AT,
        software_version=SOFTWARE,
    )


def fiscal():
    row = {
        "entity_id": "3526902",
        "period": "2025",
        "metric_id": "education_initial_appropriation",
        "metric_name": "Dotação inicial Educação",
        "value": 465355000,
        "unit": "BRL",
        "stage_semantic": "BUDGET_AUTHORIZATION",
        **common("SICONFI_STN", "Authorization is not execution."),
    }
    return materialize_product(
        "FISCAL_SERIES",
        [row],
        generated_at=GENERATED_AT,
        software_version=SOFTWARE,
    )


def planning():
    row = {
        "document_id": "PPA_2022_2025",
        "document_type": "PPA",
        "period": "2022-2025",
        "evidence_role": "PLANNING_PRIMARY",
        "locator": "page:10#paragraph:3",
        "text_redacted": "Programa municipal de educação.",
        **common("PPA", "Planning is not execution."),
    }
    return materialize_product(
        "PLANNING_DOCUMENT_INDEX",
        [row],
        generated_at=GENERATED_AT,
        software_version=SOFTWARE,
    )


def bundle_without_catalog():
    return {
        "SCHOOL_INDICATOR_SERIES": school(),
        "JOM_EVENT_INDEX": jom(),
        "ACCOUNTING_LEDGER": accounting(),
        "FISCAL_SERIES": fiscal(),
        "PLANNING_DOCUMENT_INDEX": planning(),
    }


def all_products():
    bundle = bundle_without_catalog()
    catalog = build_product_catalog(
        bundle,
        generated_at=GENERATED_AT,
        software_version=SOFTWARE,
    )
    return {**bundle, "QUERY_PRODUCT_CATALOG": catalog}


def existing_from_target(target):
    return {
        "tabs": ["DATA", "META"],
        "formula_present": False,
        "extra_cells": False,
        "headers": list(target.ordered_columns),
        "rows": [list(row) for row in target.rows],
        "meta": dict(target.meta),
    }


class TestTask177ObservatoryQueryProductServing(unittest.TestCase):
    def test_contract_passes_and_legacy_bi_allowlist_stays_unchanged(self):
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["product_count"], 6)
        self.assertTrue(got["legacy_bi_allowlist_unchanged"])
        legacy = json.loads((ROOT / "config/bi/serving.v1.json").read_text(encoding="utf-8"))
        self.assertEqual(len(legacy["dataset_allowlist"]), 6)
        self.assertFalse(any(x.startswith("OBS_") for x in legacy["serving_names"]))

    def test_all_six_products_have_exact_obs_serving_names(self):
        expected = {
            "SCHOOL_INDICATOR_SERIES": "OBS_SCHOOL_INDICATOR_SERIES__SERVING",
            "JOM_EVENT_INDEX": "OBS_JOM_EVENT_INDEX__SERVING",
            "ACCOUNTING_LEDGER": "OBS_ACCOUNTING_LEDGER__SERVING",
            "FISCAL_SERIES": "OBS_FISCAL_SERIES__SERVING",
            "PLANNING_DOCUMENT_INDEX": "OBS_PLANNING_DOCUMENT_INDEX__SERVING",
            "QUERY_PRODUCT_CATALOG": "OBS_QUERY_PRODUCT_CATALOG__SERVING",
        }
        products = all_products()
        for name, serving_name in expected.items():
            target = build_target(products[name])
            self.assertEqual(target.serving_name, serving_name)
            self.assertEqual(target.product_name, name)

    def test_snapshot_validation_recomputes_hash_and_detects_tamper(self):
        product = school()
        self.assertEqual(validate_product_snapshot(product)["status"], "PASS")
        bad = copy.deepcopy(product)
        bad["rows"][0]["value"] = 999
        with self.assertRaisesRegex(Task177Stop, "TASK177_CONTENT_HASH"):
            validate_product_snapshot(bad)

    def test_serializer_has_only_data_meta_and_serializes_nested_json_as_text(self):
        target = build_target(accounting())
        payload = serialize_target(target)
        self.assertEqual(set(payload["tabs"]), {"DATA", "META"})
        self.assertEqual(payload["value_input_option"], "RAW")
        headers = target.ordered_columns
        idx = headers.index("programmatic_dimensions")
        cell = payload["tabs"]["DATA"][1][idx]
        self.assertIn("stringValue", cell["userEnteredValue"])
        self.assertTrue(cell["userEnteredValue"]["stringValue"].startswith("{"))

    def test_create_initial_serving_plan(self):
        target = build_target(school())
        plan = plan_serving(target, None, snapshot_validated=True)
        self.assertEqual(plan.operation, "CREATE_INITIAL_SERVING")
        self.assertEqual(plan.logical_batch_update_count, 1)
        self.assertTrue(plan.semantic_readback_required)

    def test_same_snapshot_is_idempotent(self):
        target = build_target(school())
        existing = existing_from_target(target)
        plan = plan_serving(target, existing, snapshot_validated=True)
        self.assertEqual(plan.operation, "NO_CHANGE_IDEMPOTENT")
        self.assertEqual(plan.logical_batch_update_count, 0)
        self.assertFalse(plan.semantic_readback_required)
        self.assertEqual(semantic_readback(target, existing), "PASS_TASK177_SEMANTIC_READBACK_VERIFIED")

    def test_new_snapshot_same_schema_can_replace(self):
        old_target = build_target(school(100))
        new_target = build_target(school(101))
        self.assertNotEqual(old_target.snapshot_id, new_target.snapshot_id)
        self.assertEqual(old_target.schema_fingerprint_sha256, new_target.schema_fingerprint_sha256)
        plan = plan_serving(new_target, existing_from_target(old_target), snapshot_validated=True)
        self.assertEqual(plan.operation, "REPLACE_SERVING_FROM_NEW_SNAPSHOT")
        self.assertEqual(plan.logical_batch_update_count, 1)

    def test_schema_drift_requires_migration(self):
        old_target = build_target(school(100))
        new_target = build_target(school(101, new_optional_field="new"))
        self.assertNotEqual(old_target.schema_fingerprint_sha256, new_target.schema_fingerprint_sha256)
        with self.assertRaisesRegex(Task177Stop, "TASK177_SCHEMA_DRIFT_REQUIRES_MIGRATION"):
            plan_serving(new_target, existing_from_target(old_target), snapshot_validated=True)

    def test_corrupt_existing_content_fails_closed_before_replace(self):
        old_target = build_target(school(100))
        new_target = build_target(school(101))
        existing = existing_from_target(old_target)
        existing["rows"][0][list(old_target.ordered_columns).index("value")] = 777
        with self.assertRaisesRegex(Task177Stop, "TASK177_EXISTING_CONTENT_HASH"):
            plan_serving(new_target, existing, snapshot_validated=True)

    def test_formula_extra_cells_and_wrong_tabs_fail_closed(self):
        target = build_target(school())
        for field, value, code in (
            ("formula_present", True, "TASK177_FORMULA_PRESENT"),
            ("extra_cells", True, "TASK177_EXTRA_CELLS"),
        ):
            existing = existing_from_target(target)
            existing[field] = value
            with self.assertRaisesRegex(Task177Stop, code):
                plan_serving(target, existing, snapshot_validated=True)
        existing = existing_from_target(target)
        existing["tabs"] = ["DATA"]
        with self.assertRaisesRegex(Task177Stop, "TASK177_EXISTING_TABS"):
            plan_serving(target, existing, snapshot_validated=True)

    def test_remote_preflight_rejects_duplicate_wrong_mime_and_unvalidated_snapshot(self):
        target = build_target(school())
        with self.assertRaisesRegex(Task177Stop, "TASK177_DUPLICATE_REMOTE_NAME"):
            validate_remote_preflight(
                target,
                parent="13_BI/02_SERVING",
                title=target.serving_name,
                remote_matches=2,
                mime="application/vnd.google-apps.spreadsheet",
                snapshot_validated=True,
            )
        with self.assertRaisesRegex(Task177Stop, "TASK177_REMOTE_MIME"):
            validate_remote_preflight(
                target,
                parent="13_BI/02_SERVING",
                title=target.serving_name,
                remote_matches=1,
                mime="text/csv",
                snapshot_validated=True,
            )
        with self.assertRaisesRegex(Task177Stop, "TASK177_SNAPSHOT_NOT_VALIDATED"):
            validate_remote_preflight(
                target,
                parent="13_BI/02_SERVING",
                title=target.serving_name,
                remote_matches=0,
                mime=None,
                snapshot_validated=False,
            )

    def valid_auth(self, target):
        return {
            "authorization_id": "AUTH_TASK177_TEST",
            "authorized": True,
            "repository": "ferinbon-cpu/robo-dados-publicos",
            "tier": "T3_MUTATING_OR_PUBLICATION",
            "drive_root": "13_BI",
            "parent_path": "13_BI/02_SERVING",
            "task": "TASK_177_OBSERVATORY_QUERY_PRODUCT_SERVING_MATERIALIZATION",
            "scope": "SINGLE_PINNED_QUERY_PRODUCT_SNAPSHOT_TO_STABLE_SERVING",
            "implementation_sha": IMPL_SHA,
            "selected_product": target.product_name,
            "selected_snapshot_id": target.snapshot_id,
            "consumed": False,
            "test_only": False,
            "serving_mutation_authorized": True,
            "looker_publication_authorized": False,
        }

    def test_authorization_is_exact_snapshot_and_task_scoped(self):
        target = build_target(school())
        with self.assertRaisesRegex(Task177Stop, "TASK177_T3_NOT_AUTHORIZED"):
            validate_authorization(None, implementation_sha=IMPL_SHA, target=target)

        auth = self.valid_auth(target)
        self.assertEqual(
            validate_authorization(auth, implementation_sha=IMPL_SHA, target=target),
            "PASS_TASK177_T3_AUTHORIZATION_VALID",
        )

        wrong_snapshot = self.valid_auth(target)
        wrong_snapshot["selected_snapshot_id"] = "0" * 24
        with self.assertRaisesRegex(Task177Stop, "TASK177_AUTH_SNAPSHOT"):
            validate_authorization(wrong_snapshot, implementation_sha=IMPL_SHA, target=target)

        old_bi_auth = self.valid_auth(target)
        old_bi_auth["task"] = "BI_003_STABLE_SERVING_MATERIALIZATION"
        with self.assertRaisesRegex(Task177Stop, "TASK177_AUTH_TASK"):
            validate_authorization(old_bi_auth, implementation_sha=IMPL_SHA, target=target)

    def test_generation_manifest_preserves_source_snapshot_and_blocks_looker_recurring_semantics(self):
        target = build_target(school())
        plan = plan_serving(target, None, snapshot_validated=True)
        manifest = generation_manifest(
            plan,
            authorization_id="AUTH_TASK177_TEST",
            implementation_sha=IMPL_SHA,
        )
        self.assertEqual(manifest["selected_snapshot_id"], target.snapshot_id)
        self.assertFalse(manifest["source_snapshot_modified"])
        self.assertFalse(manifest["source_layers_replaced"])
        self.assertFalse(manifest["looker_publication"])
        self.assertFalse(manifest["recurrence"])
        self.assertFalse(manifest["schedule"])


if __name__ == "__main__":
    unittest.main()

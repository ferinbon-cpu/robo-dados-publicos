from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from robo_dados_publicos.analytics.observatory_knowledge_pack import fused_source_rows
from robo_dados_publicos.analytics.observatory_products import build_fiscal_series

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task190_rreo_education_spending_2026.v1.json"


class Task190Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task190Stop(code)


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK190_RREO_EDUCATION_SPENDING_2026_V1", "TASK190_SCHEMA")
    _stop(obj.get("mode") == "T0_OFFLINE_EXISTING_CUSTODY_FISCAL_OVERLAY", "TASK190_MODE")
    source = obj["source"]
    _stop(source["sha256"] == "539144ae70edbcb3ca4662b9460c869ad4b21a6e6b027f3f3c332a0372e08361", "TASK190_SOURCE_SHA")
    _stop(source["readback_byte_identity_verified"] is True, "TASK190_SOURCE_READBACK")
    _stop(source["silver_v1_logical_sha256"] == "72cc2cb29990809c043877ef8b0ef19d61f1064b093ef58fdb8fcc0f87386c81", "TASK190_SILVER_LOGICAL_SHA")
    _stop(len(obj.get("fiscal_metrics") or []) == 3, "TASK190_METRIC_COUNT")
    _stop(obj["interim_semantics"]["canonical_current_spending_metric"] == "EDUCATION_EXPENDITURE", "TASK190_CANONICAL_METRIC")
    _stop(obj["interim_semantics"]["canonical_current_spending_stage"] == "LIQUIDATED_TO_DATE", "TASK190_CANONICAL_STAGE")
    _stop(obj["enrollment_candidate_not_promoted"]["status"] == "VALIDATED_CANDIDATE_NOT_MATERIALIZED_IN_TASK190", "TASK190_ENROLLMENT_GUARD")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK190_REMOTE_EFFECT")
    return obj


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    contract = load_contract(path)
    observed = contract["source_observation"]
    metrics = {row["metric_id"]: row for row in contract["fiscal_metrics"]}
    _stop(
        Decimal(metrics["EDUCATION_COMMITTED_EXPENDITURE"]["value"])
        == Decimal(observed["committed_brl"]),
        "TASK190_COMMITTED_VALUE",
    )
    _stop(
        Decimal(metrics["EDUCATION_EXPENDITURE"]["value"])
        == Decimal(observed["liquidated_brl"]),
        "TASK190_LIQUIDATED_VALUE",
    )
    _stop(
        Decimal(metrics["EDUCATION_PAID_EXPENDITURE"]["value"])
        == Decimal(observed["paid_brl"]),
        "TASK190_PAID_VALUE",
    )
    _stop(
        Decimal(observed["paid_brl"]) <= Decimal(observed["liquidated_brl"])
        <= Decimal(observed["committed_brl"]),
        "TASK190_STAGE_ORDER",
    )
    _stop(
        Decimal(observed["current_assets"]["committed_brl"])
        + Decimal(observed["capital_expenses"]["committed_brl"])
        == Decimal(observed["committed_brl"]),
        "TASK190_COMMITTED_COMPONENTS",
    )
    _stop(
        Decimal(observed["current_assets"]["liquidated_brl"])
        + Decimal(observed["capital_expenses"]["liquidated_brl"])
        == Decimal(observed["liquidated_brl"]),
        "TASK190_LIQUIDATED_COMPONENTS",
    )
    _stop(
        Decimal(observed["current_assets"]["paid_brl"])
        + Decimal(observed["capital_expenses"]["paid_brl"])
        == Decimal(observed["paid_brl"]),
        "TASK190_PAID_COMPONENTS",
    )
    context = contract["contextual_reconciliation"]
    _stop(context["rreo_anexo_2_function_education"]["equality_expected"] is False, "TASK190_ANEXO2_EQUALITY")
    _stop(context["accounting_ledger"]["equality_expected"] is False, "TASK190_LEDGER_EQUALITY")
    return {
        "schema": "TASK190_RREO_EDUCATION_SPENDING_VALIDATION_V1",
        "status": "PASS",
        "metric_count": 3,
        "canonical_spending_metric": "EDUCATION_EXPENDITURE",
        "canonical_stage_semantic": "LIQUIDATED_TO_DATE",
        "network": False,
        "drive_write": False,
    }


def overlay_rows(path: str | Path = DEFAULT_CONTRACT) -> list[dict[str, Any]]:
    contract = load_contract(path)
    source = contract["source"]
    observed = contract["source_observation"]
    rows: list[dict[str, Any]] = []
    for metric in contract["fiscal_metrics"]:
        rows.append({
            "entity_id": contract["entity"]["entity_id"],
            "period": source["period"],
            "metric_id": metric["metric_id"],
            "metric_name": metric["metric_name"],
            "value": float(Decimal(metric["value"])),
            "unit": metric["unit"],
            "stage_semantic": metric["stage_semantic"],
            "observation_period": f"{source['period_start']}/{source['period_end']}",
            "source_family": source["family"],
            "source_sha256": source["sha256"],
            "provenance_ref": (
                f"DRIVE:{source['bronze_drive_id']}#"
                f"{observed['locator']}:{metric['provenance_suffix']}"
            ),
            "quality_status": "VALIDATED",
            "caution": (
                "INTERIM_2026_BIMONTHLY_NE_ANNUAL_FINAL;"
                "LIQUIDATED_NE_PAID_NE_COMMITTED;"
                "RREO_MDE_TOTAL_NE_TCE_FUNCTION_TOTAL;"
                "NOMINAL_NE_REAL"
            ),
        })
    rows.sort(key=lambda row: row["metric_id"])
    return rows


def build_fiscal_overlay(
    *,
    generated_at: str,
    software_version: str,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    validate_contract(contract_path)
    base = fused_source_rows()["fiscal_rows"]
    product = build_fiscal_series(
        [*base, *overlay_rows(contract_path)],
        generated_at=generated_at,
        software_version=software_version,
    )
    product["overlay_scope"] = {
        "base_task183_rows": len(base),
        "task190_rows": 3,
        "rreo_period": "2026-04",
        "canonical_spending_metric": "EDUCATION_EXPENDITURE",
        "canonical_stage_semantic": "LIQUIDATED_TO_DATE",
        "annual_final": False,
        "real_terms": False,
        "per_student_metric_materialized": False,
        "tcesp_equality_claim": False,
    }
    return product

from __future__ import annotations

import csv
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

from robo_dados_publicos.analytics.observatory_knowledge_pack import fused_source_rows
from robo_dados_publicos.analytics.observatory_products import (
    build_fiscal_series,
    build_school_indicator_series,
)
from robo_dados_publicos.analytics.task190_rreo_education_spending import overlay_rows as task190_fiscal_rows

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task191_education_spending_per_student_2025.v1.json"


class Task191Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task191Stop(code)


def _load(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = _load(path)
    _stop(obj.get("schema") == "TASK191_EDUCATION_SPENDING_PER_STUDENT_2025_V1", "TASK191_SCHEMA")
    _stop(obj.get("mode") == "T0_OFFLINE_EXISTING_CUSTODY_SAME_PERIOD_DERIVATION", "TASK191_MODE")
    _stop(obj["period"] == "2025", "TASK191_PERIOD")
    fiscal = obj["fiscal_source"]
    _stop(
        fiscal["fixture_sha256"] == "a190bf8ac3f11e5d0e84f2dba56d286e128f577c0d9b426f82a852ca3a4f2a30",
        "TASK191_FISCAL_FIXTURE_SHA",
    )
    _stop(fiscal["liquidated_reconciliation_status"] == "PROVEN_EXACT_OPERATIONAL", "TASK191_FISCAL_STATUS")
    _stop(Decimal(fiscal["liquidated_variance_brl"]) == Decimal("0.00"), "TASK191_FISCAL_VARIANCE")
    _stop(fiscal["immutable_finality_proven"] is False, "TASK191_FINALITY_GUARD")
    enrollment = obj["enrollment_source"]
    _stop(enrollment["active_units"] == 69, "TASK191_UNITS")
    _stop(enrollment["basic_education_enrollment"] == 22788, "TASK191_ENROLLMENT")
    _stop(enrollment["row_sum_verified"] is True, "TASK191_ROW_SUM")
    _stop(enrollment["imputations"] == 0, "TASK191_IMPUTATION")
    _stop(enrollment["full_panel_runtime_transfer_complete"] is False, "TASK191_PANEL_TRANSFER_GUARD")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK191_REMOTE_EFFECT")
    return obj


def _fiscal_observation(contract: dict[str, Any]) -> dict[str, Any]:
    fixture = _load(ROOT / contract["fiscal_source"]["fixture"])
    _stop(fixture["identity"] == {
        "NUM_ANO": 2025,
        "NUM_PERI": 6,
        "SIG_UF": "SP",
        "COD_MUNI": 352690,
        "NOM_MUNI": "Limeira",
    }, "TASK191_FISCAL_IDENTITY")
    observed = fixture.get("rreo_anexo_8_line_33") or {}
    _stop(observed.get("line") == contract["fiscal_source"]["label"], "TASK191_RREO_LABEL")
    _stop(observed.get("DE") == contract["fiscal_source"]["committed_brl"], "TASK191_COMMITTED")
    _stop(observed.get("DL") == contract["fiscal_source"]["liquidated_brl"], "TASK191_LIQUIDATED")
    _stop(observed.get("DP") == contract["fiscal_source"]["paid_brl"], "TASK191_PAID")
    return observed


def _enrollment_observation(contract: dict[str, Any]) -> dict[str, str]:
    path = ROOT / contract["enrollment_source"]["sanitized_aggregate_fixture"]
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    _stop(len(rows) == 1, "TASK191_ENROLLMENT_FIXTURE_ROWS")
    row = rows[0]
    _stop(row["period"] == "2025", "TASK191_ENROLLMENT_PERIOD")
    _stop(int(row["active_units"]) == 69, "TASK191_ENROLLMENT_UNITS")
    _stop(int(row["basic_education_enrollment"]) == 22788, "TASK191_ENROLLMENT_VALUE")
    _stop(row["source_xlsx_sha256"] == contract["enrollment_source"]["xlsx_sha256"], "TASK191_ENROLLMENT_SHA")
    _stop(row["status"] == "USER_LIBRARY_MEDIATED_AGGREGATE_ROW_SUM_VERIFIED", "TASK191_ENROLLMENT_STATUS")
    return row


def fiscal_2025_rows(path: str | Path = DEFAULT_CONTRACT) -> list[dict[str, Any]]:
    contract = load_contract(path)
    _fiscal_observation(contract)
    source = contract["fiscal_source"]
    definitions = [
        ("EDUCATION_COMMITTED_EXPENDITURE", "Despesa total com Educação empenhada em 2025 — observação anual", source["committed_brl"], "COMMITTED_ANNUAL_OBSERVED", "DE"),
        ("EDUCATION_EXPENDITURE", "Despesa total com Educação liquidada em 2025 — observação anual", source["liquidated_brl"], "LIQUIDATED_ANNUAL_OBSERVED", "DL"),
        ("EDUCATION_PAID_EXPENDITURE", "Despesa total com Educação paga em 2025 — observação anual", source["paid_brl"], "PAID_ANNUAL_OBSERVED", "DP"),
    ]
    rows = []
    for metric_id, metric_name, value, stage, suffix in definitions:
        rows.append({
            "entity_id": contract["entity"]["entity_id"],
            "period": "2025",
            "metric_id": metric_id,
            "metric_name": metric_name,
            "value": float(Decimal(value)),
            "unit": "BRL",
            "stage_semantic": stage,
            "observation_period": "2025-01-01/2025-12-31",
            "source_family": "RREO",
            "source_sha256": source["fixture_sha256"],
            "provenance_ref": (
                f"GITHUB:{source['fixture']}#rreo_anexo_8_line_33:{suffix};"
                f"EVIDENCE:{source['evidence']}"
            ),
            "quality_status": "VALIDATED",
            "caution": (
                "USER_MEDIATED_OFFICIAL_OBSERVATION;"
                "ANNUAL_SUBMISSION_OBSERVED_NE_IMMUTABLE_FINALITY;"
                "LIQUIDATED_NE_PAID_NE_COMMITTED;"
                "EDUCATION_TOTAL_NE_MDE_CONSTITUTIONAL_BASE;"
                "NOMINAL_NE_REAL"
            ),
            "source_hash_role": "SANITIZED_MINIMAL_OFFICIAL_OBSERVATION_FIXTURE_SHA256",
        })
    return rows


def enrollment_2025_row(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    contract = load_contract(path)
    _enrollment_observation(contract)
    source = contract["enrollment_source"]
    return {
        "scope_level": "NETWORK",
        "scope_id": source["scope_id"],
        "network": "MUNICIPAL",
        "period": "2025",
        "indicator_id": "BASIC_EDUCATION_ENROLLMENT",
        "indicator_name": "Matrículas da educação básica — rede municipal, 69 unidades observadas",
        "value": source["basic_education_enrollment"],
        "unit": "COUNT",
        "context": (
            "2025 annual Censo Escolar aggregate across the 69 observed municipal units; "
            "row sum verified in user-library-mediated extraction; no imputation."
        ),
        "observation_period": "2025",
        "source_family": "CENSO_ESCOLAR",
        "source_sha256": source["xlsx_sha256"],
        "provenance_ref": (
            "FILE_LIBRARY:CAMADA_ANALITICA_V06_40_ESCOLAS_V08.xlsx"
            "#81 Censo 69 2018-25:2025:SUM(mat_bas):69_units"
        ),
        "quality_status": "VALIDATED",
        "caution": (
            "USER_LIBRARY_MEDIATED_AGGREGATE_ROW_SUM_VERIFIED;"
            "CURRENT_69_UNIT_UNIVERSE_2025;"
            "MISSING_NE_ZERO;NO_IMPUTATION;"
            "FULL_PANEL_RUNTIME_TRANSFER_FALSE"
        ),
    }


def build_fiscal_2025_overlay(
    *,
    generated_at: str,
    software_version: str,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    validate_contract(contract_path)
    base = fused_source_rows()["fiscal_rows"]
    rows = [*base, *task190_fiscal_rows(), *fiscal_2025_rows(contract_path)]
    product = build_fiscal_series(rows, generated_at=generated_at, software_version=software_version)
    product["overlay_scope"] = {
        "base_task183_rows": len(base),
        "task190_2026_rows": 3,
        "task191_2025_rows": 3,
        "annual_observed_2025": True,
        "immutable_finality_2025": False,
        "real_terms": False,
    }
    return product


def build_school_2025_overlay(
    *,
    generated_at: str,
    software_version: str,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    validate_contract(contract_path)
    base = fused_source_rows()["school_rows"]
    row = enrollment_2025_row(contract_path)
    product = build_school_indicator_series(
        [*base, row],
        generated_at=generated_at,
        software_version=software_version,
    )
    product["overlay_scope"] = {
        "base_task183_rows": len(base),
        "task191_network_enrollment_rows": 1,
        "period": "2025",
        "scope_id": row["scope_id"],
        "active_units": 69,
        "row_sum_verified": True,
        "full_panel_runtime_transfer_complete": False,
    }
    return product


def derive_spending_per_student(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    contract = load_contract(path)
    _fiscal_observation(contract)
    _enrollment_observation(contract)
    numerator = Decimal(contract["derivation"]["numerator_brl"])
    denominator = Decimal(contract["derivation"]["denominator_count"])
    exact = numerator / denominator
    rounded = exact.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    _stop(str(exact) == contract["derivation"]["exact_quotient_brl_per_student"], "TASK191_EXACT_RATIO")
    _stop(f"{rounded:.2f}" == contract["derivation"]["rounded_brl_per_student"], "TASK191_ROUNDED_RATIO")
    _stop(contract["derivation"]["periods_match"] is True, "TASK191_PERIOD_MATCH")
    return {
        "schema": "TASK191_EDUCATION_FINANCE_DERIVED_V1",
        "period": "2025",
        "metric_id": "EDUCATION_EXPENDITURE_PER_STUDENT",
        "value_exact": str(exact),
        "value_brl_per_student": f"{rounded:.2f}",
        "unit": "BRL_PER_STUDENT_YEAR",
        "numerator": {
            "metric_id": "EDUCATION_EXPENDITURE",
            "stage_semantic": "LIQUIDATED_ANNUAL_OBSERVED",
            "value_brl": f"{numerator:.2f}",
            "source_family": "RREO",
            "source_sha256": contract["fiscal_source"]["fixture_sha256"],
        },
        "denominator": {
            "indicator_id": "BASIC_EDUCATION_ENROLLMENT",
            "value": int(denominator),
            "source_family": "CENSO_ESCOLAR",
            "source_sha256": contract["enrollment_source"]["xlsx_sha256"],
            "scope_id": contract["enrollment_source"]["scope_id"],
        },
        "same_period": True,
        "derived_not_source": True,
        "immutable_finality_claim": False,
        "real_terms": False,
        "caution": (
            "ANNUAL_OBSERVED_SUBMISSION_NE_IMMUTABLE_FINALITY;"
            "DERIVED_RATIO_NE_SOURCE_REPORTED_METRIC;"
            "NOMINAL_NE_REAL"
        ),
    }


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    contract = load_contract(path)
    _fiscal_observation(contract)
    _enrollment_observation(contract)
    derived = derive_spending_per_student_unchecked(contract)
    _stop(derived["value_brl_per_student"] == contract["derivation"]["rounded_brl_per_student"], "TASK191_DERIVED")
    return {
        "schema": "TASK191_EDUCATION_SPENDING_PER_STUDENT_VALIDATION_V1",
        "status": "PASS",
        "period": "2025",
        "fiscal_rows_added": 3,
        "school_rows_added": 1,
        "spending_per_student_brl": derived["value_brl_per_student"],
        "network": False,
        "drive_write": False,
    }


def derive_spending_per_student_unchecked(contract: dict[str, Any]) -> dict[str, Any]:
    numerator = Decimal(contract["derivation"]["numerator_brl"])
    denominator = Decimal(contract["derivation"]["denominator_count"])
    exact = numerator / denominator
    rounded = exact.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    _stop(str(exact) == contract["derivation"]["exact_quotient_brl_per_student"], "TASK191_EXACT_RATIO")
    return {
        "value_exact": str(exact),
        "value_brl_per_student": f"{rounded:.2f}",
    }

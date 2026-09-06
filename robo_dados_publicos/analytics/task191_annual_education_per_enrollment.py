from __future__ import annotations

import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

from robo_dados_publicos.analytics.observatory_knowledge_pack import fused_source_rows
from robo_dados_publicos.analytics.observatory_products import (
    build_fiscal_series,
    build_school_indicator_series,
)
from robo_dados_publicos.analytics.task190_rreo_education_spending import overlay_rows as task190_overlay_rows


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task191_annual_education_per_enrollment_2025.v1.json"


class Task191Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task191Stop(code)


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK191_ANNUAL_EDUCATION_PER_ENROLLMENT_2025_V1", "TASK191_SCHEMA")
    _stop(obj.get("mode") == "T0_OFFLINE_EXISTING_CUSTODY_SAME_YEAR_BRIDGE", "TASK191_MODE")
    spending = obj["annual_spending_source"]
    enrollment = obj["enrollment_source"]
    derivation = obj["derivation"]
    _stop(spending["period"] == enrollment["period"] == "2025", "TASK191_PERIOD_ALIGNMENT")
    _stop(derivation["numerator_period"] == derivation["denominator_period"] == "2025", "TASK191_DERIVATION_PERIOD")
    _stop(spending["annual_canonical_stage"] == "COMMITTED_FINAL_BIMESTER", "TASK191_ANNUAL_STAGE")
    _stop(enrollment["row_sum_verified"] is True, "TASK191_ENROLLMENT_SUM")
    _stop(enrollment["active_units"] == 69, "TASK191_ENROLLMENT_UNITS")
    _stop(enrollment["basic_education_enrollment"] == 22788, "TASK191_ENROLLMENT_VALUE")
    _stop(derivation["individual_student_cost_claim"] is False, "TASK191_COST_GUARD")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK191_REMOTE_EFFECT")
    return obj


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(path)
    spending = obj["annual_spending_source"]
    derivation = obj["derivation"]
    committed = Decimal(spending["committed_brl"])
    liquidated = Decimal(spending["liquidated_brl"])
    paid = Decimal(spending["paid_brl"])
    _stop(paid <= liquidated <= committed, "TASK191_STAGE_ORDER")
    denominator = Decimal(str(obj["enrollment_source"]["basic_education_enrollment"]))
    _stop(denominator > 0, "TASK191_DENOMINATOR")
    calculated = (committed / denominator).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    _stop(calculated == Decimal(derivation["expected_value_brl_per_enrollment"]), "TASK191_RATIO")
    return {
        "schema": "TASK191_ANNUAL_EDUCATION_PER_ENROLLMENT_VALIDATION_V1",
        "status": "PASS",
        "period": "2025",
        "annual_spending_brl": str(committed),
        "enrollment": int(denominator),
        "spending_per_enrollment_brl": str(calculated),
        "network": False,
        "drive_write": False,
    }


def school_overlay_row(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(path)
    source = obj["enrollment_source"]
    return {
        "scope_level": source["scope_level"],
        "scope_id": source["scope_id"],
        "network": "MUNICIPAL",
        "period": source["period"],
        "indicator_id": "BASIC_EDUCATION_ENROLLMENT",
        "indicator_name": "Matrículas na educação básica nas 69 unidades municipais atuais observadas",
        "value": source["basic_education_enrollment"],
        "unit": "COUNT",
        "context": (
            "Soma de mat_bas no painel Censo Escolar V08 para as 69 unidades atuais em 2025; "
            "denominador censitário de matrícula, não contagem de pessoa-ano nem custo individual."
        ),
        "observation_period": source["period"],
        "source_family": source["source_family"],
        "source_sha256": source["xlsx_sha256"],
        "provenance_ref": (
            "FILE_LIBRARY:CAMADA_ANALITICA_V06_40_ESCOLAS_V08.xlsx"
            "#81 Censo 69 2018-25:2025:SUM(mat_bas):69_units"
        ),
        "quality_status": source["quality_status"],
        "caution": "ENROLLMENT_COUNT_NE_PERSON_YEAR_COST;CURRENT_69_UNIT_PANEL_SCOPE_EXPLICIT",
    }


def annual_fiscal_overlay_row(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(path)
    source = obj["annual_spending_source"]
    return {
        "entity_id": obj["entity"]["entity_id"],
        "period": source["period"],
        "metric_id": "EDUCATION_EXPENDITURE",
        "metric_name": "Despesa anual total com Educação empenhada no fechamento do 6º bimestre de 2025",
        "value": float(Decimal(source["committed_brl"])),
        "unit": "BRL",
        "stage_semantic": "COMMITTED_FINAL_BIMESTER",
        "observation_period": "2025-01-01/2025-12-31",
        "source_family": "RREO",
        "source_sha256": source["observation_digest_sha256"],
        "provenance_ref": (
            "REPO:tests/fixtures/siope_2025_operational_financial_alias_bridge/"
            "official_observations.json#rreo_anexo_8_line_33:DE"
        ),
        "quality_status": "VALIDATED",
        "caution": (
            "LAST_BIMESTER_COMMITTED_NE_INTERIM_LIQUIDATED;"
            "SANITIZED_OBSERVATION_DIGEST_NE_SOURCE_BINARY_HASH;"
            "RREO_EDUCATION_TOTAL_NE_SCHOOL_LEVEL_EXPENDITURE;"
            "NOMINAL_NE_REAL"
        ),
    }


def derive_spending_per_enrollment(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(path)
    spending = Decimal(obj["annual_spending_source"]["committed_brl"])
    enrollment = Decimal(str(obj["enrollment_source"]["basic_education_enrollment"]))
    value = (spending / enrollment).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {
        "metric_id": obj["derivation"]["metric_id"],
        "period": "2025",
        "value": str(value),
        "unit": "BRL_PER_ENROLLMENT",
        "numerator_metric_id": "EDUCATION_EXPENDITURE",
        "numerator_value_brl": str(spending),
        "numerator_stage_semantic": "COMMITTED_FINAL_BIMESTER",
        "denominator_indicator_id": "BASIC_EDUCATION_ENROLLMENT",
        "denominator_value": int(enrollment),
        "same_year_verified": True,
        "semantic_label": obj["derivation"]["semantic_label"],
        "individual_student_cost_claim": False,
        "caution": (
            "DESPESA_ANUAL_EMPENHADA_POR_MATRICULA_CENSO;"
            "PER_ENROLLMENT_NE_INDIVIDUAL_STUDENT_COST;"
            "NOMINAL_NE_REAL"
        ),
    }


def build_task191_products(
    *,
    generated_at: str,
    software_version: str,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    validation = validate_contract(contract_path)
    source = fused_source_rows()
    school_rows = [*source["school_rows"], school_overlay_row(contract_path)]
    fiscal_rows = [
        *source["fiscal_rows"],
        *task190_overlay_rows(),
        annual_fiscal_overlay_row(contract_path),
    ]
    school = build_school_indicator_series(
        school_rows,
        generated_at=generated_at,
        software_version=software_version,
    )
    fiscal = build_fiscal_series(
        fiscal_rows,
        generated_at=generated_at,
        software_version=software_version,
    )
    school["overlay_scope"] = {
        "base_task183_rows": len(source["school_rows"]),
        "task191_rows": 1,
        "basic_education_enrollment_2025": 22788,
        "period": "2025",
    }
    fiscal["overlay_scope"] = {
        "base_task183_rows": len(source["fiscal_rows"]),
        "task190_rows": len(task190_overlay_rows()),
        "task191_rows": 1,
        "annual_2025_canonical_stage": "COMMITTED_FINAL_BIMESTER",
        "current_2026_canonical_stage_preserved": "LIQUIDATED_TO_DATE",
        "real_terms": False,
    }
    return {
        "validation": validation,
        "SCHOOL_INDICATOR_SERIES": school,
        "FISCAL_SERIES": fiscal,
        "derived": derive_spending_per_enrollment(contract_path),
    }

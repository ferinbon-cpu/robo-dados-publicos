from __future__ import annotations

import hashlib
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
from robo_dados_publicos.analytics.task191_annual_education_per_enrollment import (
    annual_fiscal_overlay_row,
    school_overlay_row,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task192_ipca_real_education_expenditure_2016_2025.v1.json"
CENT = Decimal("0.01")


class Task192Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task192Stop(code)


def _sha(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _pct_change(first: Decimal, last: Decimal) -> Decimal:
    _stop(first != 0, "TASK192_ZERO_BASE")
    return (((last / first) - Decimal(1)) * Decimal(100)).quantize(
        CENT,
        rounding=ROUND_HALF_UP,
    )


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK192_IPCA_REAL_EDUCATION_EXPENDITURE_2016_2025_V1", "TASK192_SCHEMA")
    _stop(obj.get("mode") == "T0_OFFLINE_EXISTING_CUSTODY_OFFICIAL_DEFLATOR", "TASK192_MODE")
    observations = list(obj.get("nominal_observations") or [])
    _stop([row["year"] for row in observations] == list(range(2016, 2026)), "TASK192_YEARS")
    _stop(observations[0]["period"] == 1, "TASK192_2016_PERIOD")
    _stop(all(row["period"] == 6 for row in observations[1:]), "TASK192_POST_2016_PERIOD")
    _stop(all(row["source_family"] == "SIOPE" for row in observations[:-1]), "TASK192_HISTORICAL_SOURCE")
    _stop(observations[-1]["source_family"] == "RREO", "TASK192_2025_SOURCE")
    rates = obj["deflator"]["annual_rates_pct"]
    _stop(sorted(map(int, rates)) == list(range(2016, 2026)), "TASK192_IPCA_YEARS")
    _stop(obj["deflator"]["authority"] == "IBGE", "TASK192_IPCA_AUTHORITY")
    _stop(obj["deflator"]["index"] == "IPCA", "TASK192_IPCA_INDEX")
    _stop(obj["deflator"]["base_price_period"] == "2025-12", "TASK192_BASE_PRICE_PERIOD")
    _stop(obj["deflator"]["annual_flow_monthly_weighted"] is False, "TASK192_FLOW_WEIGHTING")
    _stop(obj["nominal_series_semantics"]["compliance_claim"] is False, "TASK192_COMPLIANCE_GUARD")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK192_REMOTE_EFFECT")
    return obj


def _obs_by_year(obj: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(row["year"]): row for row in obj["nominal_observations"]}


def deflator_factor(year: int, path: str | Path = DEFAULT_CONTRACT) -> Decimal:
    obj = load_contract(path)
    _stop(2016 <= year <= 2025, "TASK192_FACTOR_YEAR")
    rates = {int(k): Decimal(v) for k, v in obj["deflator"]["annual_rates_pct"].items()}
    factor = Decimal(1)
    for target_year in range(year + 1, 2026):
        factor *= Decimal(1) + rates[target_year] / Decimal(100)
    return factor


def real_value(year: int, path: str | Path = DEFAULT_CONTRACT) -> Decimal:
    obj = load_contract(path)
    obs = _obs_by_year(obj)
    _stop(year in obs, "TASK192_REAL_YEAR")
    nominal = Decimal(obs[year]["value_brl"])
    return (nominal * deflator_factor(year, path)).quantize(CENT, rounding=ROUND_HALF_UP)


def trend_summary(path: str | Path = DEFAULT_CONTRACT) -> dict[str, str]:
    obj = load_contract(path)
    obs = _obs_by_year(obj)
    nominal_2016 = Decimal(obs[2016]["value_brl"])
    nominal_2024 = Decimal(obs[2024]["value_brl"])
    nominal_2025 = Decimal(obs[2025]["value_brl"])
    real_2016 = real_value(2016, path)
    real_2024 = real_value(2024, path)
    real_2025 = real_value(2025, path)
    return {
        "nominal_2016_to_2025_pct": str(_pct_change(nominal_2016, nominal_2025)),
        "real_2016_to_2025_pct": str(_pct_change(real_2016, real_2025)),
        "nominal_2024_to_2025_pct": str(_pct_change(nominal_2024, nominal_2025)),
        "real_2024_to_2025_pct": str(_pct_change(real_2024, real_2025)),
    }


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(path)
    expected_real = obj["expected_real_brl"]
    calculated_real = {
        str(year): str(real_value(year, path))
        for year in range(2016, 2026)
    }
    _stop(calculated_real == expected_real, "TASK192_REAL_VALUES")
    expected_changes = obj["expected_changes_pct"]
    got_changes = trend_summary(path)
    _stop(got_changes["nominal_2016_to_2025_pct"] == expected_changes["nominal_2016_to_2025"], "TASK192_NOMINAL_LONG_CHANGE")
    _stop(got_changes["real_2016_to_2025_pct"] == expected_changes["real_2016_to_2025"], "TASK192_REAL_LONG_CHANGE")
    _stop(got_changes["nominal_2024_to_2025_pct"] == expected_changes["nominal_2024_to_2025"], "TASK192_NOMINAL_RECENT_CHANGE")
    _stop(got_changes["real_2024_to_2025_pct"] == expected_changes["real_2024_to_2025"], "TASK192_REAL_RECENT_CHANGE")
    return {
        "schema": "TASK192_IPCA_REAL_EDUCATION_EXPENDITURE_VALIDATION_V1",
        "status": "PASS",
        "years": list(range(2016, 2026)),
        "base_price_period": "2025-12",
        "real_metric_id": "REAL_EDUCATION_EXPENDITURE",
        "trend": got_changes,
        "network": False,
        "drive_write": False,
    }


def nominal_history_overlay_rows(path: str | Path = DEFAULT_CONTRACT) -> list[dict[str, Any]]:
    obj = load_contract(path)
    rows: list[dict[str, Any]] = []
    for source in obj["nominal_observations"]:
        year = int(source["year"])
        if year == 2025:
            continue
        rows.append({
            "entity_id": obj["entity"]["entity_id"],
            "period": str(year),
            "metric_id": "EDUCATION_EXPENDITURE",
            "metric_name": "Despesa anual com Educação empenhada informada no SIOPE",
            "value": float(Decimal(source["value_brl"])),
            "unit": "BRL",
            "stage_semantic": "COMMITTED_ANNUAL_SIOPE",
            "observation_period": f"{year}-01-01/{year}-12-31",
            "source_family": "SIOPE",
            "source_sha256": source["source_sha256"],
            "provenance_ref": f"DRIVE:{source['drive_id']}#input_facts.VL_DESP_EMPE_EDU",
            "quality_status": "VALIDATED",
            "caution": (
                "SIOPE_ANNUAL_EDUCATION_COMMITTED_EXPENDITURE;"
                "COMMITTED_NE_LIQUIDATED_NE_PAID;"
                "NOMINAL_NE_REAL;"
                "COMPLIANCE_CLAIM_NOT_AUTHORIZED"
            ),
        })
    _stop(len(rows) == 9, "TASK192_NOMINAL_ROW_COUNT")
    return rows


def real_overlay_rows(path: str | Path = DEFAULT_CONTRACT) -> list[dict[str, Any]]:
    obj = load_contract(path)
    rows: list[dict[str, Any]] = []
    ipca = obj["deflator"]
    for source in obj["nominal_observations"]:
        year = int(source["year"])
        composite_sha = _sha({
            "year": year,
            "nominal_source_sha256": source["source_sha256"],
            "ipca_observation_sha256": ipca["normalized_observation_sha256"],
            "base_price_period": ipca["base_price_period"],
            "formula": ipca["conversion_formula"],
        })
        provenance = (
            f"DRIVE:{source['drive_id']}#input_facts.VL_DESP_EMPE_EDU"
            if source.get("drive_id")
            else "REPO:tests/fixtures/siope_2025_operational_financial_alias_bridge/official_observations.json#rreo_anexo_8_line_33:DE"
        )
        rows.append({
            "entity_id": obj["entity"]["entity_id"],
            "period": str(year),
            "metric_id": "REAL_EDUCATION_EXPENDITURE",
            "metric_name": "Despesa anual empenhada com Educação em reais equivalentes a dezembro de 2025 pelo IPCA",
            "value": float(real_value(year, path)),
            "unit": "BRL_DEC_2025_EQUIVALENT",
            "stage_semantic": "COMMITTED_ANNUAL_DEFLATED_YEAR_END_EQUIVALENT",
            "observation_period": f"{year}-01-01/{year}-12-31",
            "source_family": source["source_family"],
            "source_sha256": composite_sha,
            "provenance_ref": (
                f"{provenance};IBGE_IPCA:{ipca['locator']};"
                f"BASE_PRICE_PERIOD:{ipca['base_price_period']}"
            ),
            "quality_status": "VALIDATED",
            "caution": (
                "NOMINAL_NE_REAL;"
                "YEAR_END_IPCA_DEFLATION_NE_MONTHLY_FLOW_DEFLATION;"
                "BRL_DEC_2025_EQUIVALENT_NE_NOMINAL_BRL;"
                "REAL_EDUCATION_EXPENDITURE_NE_COMPLIANCE_CLAIM"
            ),
        })
    _stop(len(rows) == 10, "TASK192_REAL_ROW_COUNT")
    _stop(all(row["period"] != "2026" for row in rows), "TASK192_2026_REAL_GUARD")
    return rows


def build_task192_products(
    *,
    generated_at: str,
    software_version: str,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    validation = validate_contract(contract_path)
    source = fused_source_rows()
    school_rows = [*source["school_rows"], school_overlay_row()]
    fiscal_rows = [
        *source["fiscal_rows"],
        *task190_overlay_rows(),
        annual_fiscal_overlay_row(),
        *nominal_history_overlay_rows(contract_path),
        *real_overlay_rows(contract_path),
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
    current_2026 = [
        row for row in fiscal["rows"]
        if row["period"] == "2026-04"
        and row["metric_id"] == "EDUCATION_EXPENDITURE"
    ]
    _stop(len(current_2026) == 1, "TASK192_CURRENT_2026_COUNT")
    _stop(current_2026[0]["stage_semantic"] == "LIQUIDATED_TO_DATE", "TASK192_CURRENT_2026_STAGE")
    _stop(Decimal(str(current_2026[0]["value"])) == Decimal("138279835.79"), "TASK192_CURRENT_2026_VALUE")
    school["overlay_scope"] = {
        "base_task183_rows": len(source["school_rows"]),
        "task191_rows": 1,
        "basic_education_enrollment_2025": 22788,
    }
    fiscal["overlay_scope"] = {
        "base_task183_rows": len(source["fiscal_rows"]),
        "task190_rows": len(task190_overlay_rows()),
        "task191_rows": 1,
        "task192_nominal_history_rows": len(nominal_history_overlay_rows(contract_path)),
        "task192_real_rows": len(real_overlay_rows(contract_path)),
        "annual_nominal_years": list(range(2016, 2026)),
        "annual_real_years": list(range(2016, 2026)),
        "base_price_period": "2025-12",
        "current_2026_canonical_stage_preserved": "LIQUIDATED_TO_DATE",
        "annualized_2026": False,
        "monthly_weighted_deflation": False,
    }
    return {
        "validation": validation,
        "SCHOOL_INDICATOR_SERIES": school,
        "FISCAL_SERIES": fiscal,
        "trend": trend_summary(contract_path),
    }

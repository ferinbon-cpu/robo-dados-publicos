from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from robo_dados_publicos.analytics.observatory_products import build_territory_profile
from robo_dados_publicos.analytics.task199e_school_sector_expansion import (
    load_held_fixture as task199e_held,
    territory_rows as task199e_rows,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task199f_same_parity_address_bracket.v1.json"


class Task199FStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task199FStop(code)


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK199F_SAME_PARITY_ADDRESS_BRACKET_V1", "TASK199F_SCHEMA")
    _stop(obj.get("issue") == 628, "TASK199F_ISSUE")
    _stop(obj.get("base_main_sha") == "c32fe72d3af1c1b493666c72b694b6606dcded52", "TASK199F_BASE")
    _stop(obj["scope"]["active_school_denominator_2025"] == 69, "TASK199F_DENOM")
    _stop(len(obj["promotions"]) == 2, "TASK199F_PROMOTIONS")
    for row in obj["promotions"]:
        _stop(row["lower_sector"] == row["upper_sector"], "TASK199F_SECTOR_BRACKET")
        _stop(row["lower_cnefe_number"] < row["sme_number"] < row["upper_cnefe_number"], "TASK199F_NUMBER_BRACKET")
        _stop(row["lower_cnefe_number"] % 2 == row["sme_number"] % 2, "TASK199F_LOWER_PARITY")
        _stop(row["upper_cnefe_number"] % 2 == row["sme_number"] % 2, "TASK199F_UPPER_PARITY")
    cw = obj["crosswalk"]
    _stop(cw["before_strong_links"] == 57 and cw["after_strong_links"] == 59, "TASK199F_COVERAGE")
    _stop(cw["tier_D_same_parity_bracket"] == 2 and cw["held_after"] == 10, "TASK199F_TIER_D")
    _stop(cw["full_network_link"] is False, "TASK199F_NOT_FULL")
    _stop(obj["expected_product"]["row_count"] == 247, "TASK199F_EXPECTED_ROWS")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK199F_REMOTE")
    return obj


def held_after_task199f(path: str | Path = DEFAULT_CONTRACT) -> list[dict[str, Any]]:
    obj = load_contract(path)
    promoted = {row["codigo_inep"] for row in obj["promotions"]}
    rows = [row for row in task199e_held() if row["codigo_inep"] not in promoted]
    _stop(len(rows) == 10, "TASK199F_HELD_ROWS")
    _stop(all(row["promotion_status"] == "HELD" for row in rows), "TASK199F_HELD_STATUS")
    return rows


def _common(source_sha256: str, provenance_ref: str, caution: str) -> dict[str, Any]:
    return {
        "observation_period": "2022",
        "source_family": "IBGE_CENSO_2022",
        "source_sha256": source_sha256,
        "provenance_ref": provenance_ref,
        "quality_status": "VALIDATED",
        "caution": caution,
    }


def territory_rows(path: str | Path = DEFAULT_CONTRACT) -> list[dict[str, Any]]:
    obj = load_contract(path)
    rows = list(task199e_rows())
    _stop(len(rows) == 239, "TASK199F_BASE_ROWS")

    basic_sha = obj["sources"]["basic_sector_zip_sha256"]
    income_sha = obj["sources"]["income_sector_zip_sha256"]
    dict_sha = obj["sources"]["income_dictionary_sha256"]
    cnefe_sha = obj["sources"]["cnefe_archive_sha256"]

    for item in obj["promotions"]:
        base = {
            "geo_level": "SCHOOL_LOCATION_CENSUS_SECTOR",
            "geo_id": item["codigo_inep"],
            "municipality_code": "3526902",
            "school_code": item["codigo_inep"],
            "school_name": item["school"],
            "sector_id": item["sector_id"],
            "period": "2022",
            "school_sector_match_tier": "D",
            "school_sector_match_method": "D_CURRENT_SME_NUMBER_BRACKETED_BY_SAME_PARITY_CNEFE_ADDRESSES_BOTH_IN_SAME_SECTOR",
        }
        caution = (
            "SCHOOL_LOCATION_CONTEXT_NE_STUDENT_SOCIOECONOMIC_PROFILE;"
            "PARTIAL_59_OF_69_NETWORK;"
            "SECTOR_INCOME_NE_ENROLLED_HOUSEHOLD_INCOME;"
            "SAME_PARITY_ADDRESS_BRACKET_SAME_SECTOR"
        )
        rows.extend([
            {
                **base,
                "metric_id": "SECTOR_POPULATION",
                "metric_name": "População residente no setor censitário da localização escolar",
                "value": float(item["sector_population_2022"]),
                "unit": "PERSONS",
                "context": "Setor adjudicado por endereço atual SME entre dois endereços CNEFE da mesma paridade, ambos no mesmo setor.",
                **_common(basic_sha, f"TASK199F_BASIC#V0001;CNEFE_SHA256_{cnefe_sha}", caution),
            },
            {
                **base,
                "metric_id": "SECTOR_RESPONSIBLE_INCOME_MEAN",
                "metric_name": "Rendimento nominal médio mensal dos responsáveis com rendimentos no setor",
                "value": float(item["responsible_income_mean_nominal_monthly_brl"]),
                "unit": "BRL_NOMINAL_MONTHLY",
                "context": "V06004 do setor da localização escolar; não descreve a renda dos alunos.",
                **_common(income_sha, f"TASK199F_INCOME#V06004;DICT_SHA256_{dict_sha};CNEFE_SHA256_{cnefe_sha}", caution),
            },
            {
                **base,
                "metric_id": "SECTOR_RESPONSIBLE_INCOME_MEDIAN",
                "metric_name": "Rendimento nominal mediano mensal dos responsáveis com rendimentos no setor",
                "value": float(item["responsible_income_median_nominal_monthly_brl"]),
                "unit": "BRL_NOMINAL_MONTHLY",
                "context": "V06006 do setor da localização escolar; não descreve a renda dos alunos.",
                **_common(income_sha, f"TASK199F_INCOME#V06006;DICT_SHA256_{dict_sha};CNEFE_SHA256_{cnefe_sha}", caution),
            },
            {
                **base,
                "metric_id": "SECTOR_RESPONSIBLE_INCOME_MEAN_PERCENTILE",
                "metric_name": "Percentil setorial não ponderado de V06004 em Limeira",
                "value": float(item["V06004_sector_percentile_unweighted"]),
                "unit": "PERCENTILE_0_100",
                "context": "Posição do V06004 do setor entre os 718 setores com valor numérico; comparação setorial não ponderada.",
                **_common(income_sha, f"TASK199F_DERIVED_PERCENTILE_FROM_718_NUMERIC_V06004;DICT_SHA256_{dict_sha}", caution),
            },
        ])

    _stop(len(rows) == 247, "TASK199F_PRODUCT_ROWS")
    school_codes = {row["school_code"] for row in rows if row["geo_level"] == "SCHOOL_LOCATION_CENSUS_SECTOR"}
    _stop(len(school_codes) == 59, "TASK199F_UNIQUE_SCHOOLS")
    return rows


def build_task199f_territory_profile(
    *,
    generated_at: str,
    software_version: str,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    obj = load_contract(contract_path)
    product = build_territory_profile(
        territory_rows(contract_path),
        generated_at=generated_at,
        software_version=software_version,
        capabilities=obj["expected_product"]["capabilities"],
    )
    _stop(product["row_count"] == 247, "TASK199F_PRODUCT_ROW_COUNT")
    return product


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(path)
    rows = territory_rows(path)
    held = held_after_task199f(path)
    return {
        "schema": "TASK199F_SAME_PARITY_ADDRESS_BRACKET_VALIDATION_V1",
        "status": "PASS",
        "territory_rows": len(rows),
        "strong_school_links": obj["crosswalk"]["after_strong_links"],
        "held_school_links": len(held),
        "coverage_rate": obj["crosswalk"]["coverage_rate"],
        "full_network_school_link": False,
        "network": False,
        "drive_write": False,
    }

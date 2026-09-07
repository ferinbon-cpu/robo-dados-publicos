from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from robo_dados_publicos.analytics.observatory_products import build_territory_profile
from robo_dados_publicos.analytics.task199d_territory_profile_product import territory_rows as task199d_rows

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task199e_school_sector_expansion.v1.json"


class Task199EStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task199EStop(code)


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK199E_SCHOOL_SECTOR_EXPANSION_V1", "TASK199E_SCHEMA")
    _stop(obj.get("issue") == 628, "TASK199E_ISSUE")
    _stop(obj.get("base_main_sha") == "3658a533f3609003e232da54d7ff9077f23226b9", "TASK199E_BASE")
    _stop(obj["scope"]["active_school_denominator_2025"] == 69, "TASK199E_DENOM")
    bridge = obj["identity_bridge"]
    _stop(bridge["verified_rows"] == 69 and bridge["passed_rows"] == 69, "TASK199E_CIE_BRIDGE")
    cw = obj["crosswalk"]
    _stop(cw["strong_links"] == 57 and cw["held"] == 12, "TASK199E_COVERAGE")
    _stop(cw["years_initial_links"] == 32 and cw["early_childhood_only_links"] == 25, "TASK199E_STAGE_COUNTS")
    _stop(cw["tier_A_exact_current_address_unique_sector"] == 41, "TASK199E_TIER_A")
    _stop(cw["tier_B_same_street_named_cnefe_school_missing_number"] == 15, "TASK199E_TIER_B")
    _stop(cw["tier_C_source_format_anomaly_reconciled"] == 1, "TASK199E_TIER_C")
    _stop(cw["full_network_link"] is False, "TASK199E_NOT_FULL")
    _stop(obj["expected_product"]["row_count"] == 239, "TASK199E_EXPECTED_ROWS")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK199E_REMOTE")
    return obj


def load_school_fixture(path: str | Path = DEFAULT_CONTRACT) -> list[dict[str, Any]]:
    obj = load_contract(path)
    fixture = ROOT / obj["github_fixtures"]["strong_compact"]["path"]
    rows = list(csv.DictReader(fixture.read_text(encoding="utf-8").splitlines()))
    _stop(len(rows) == 57, "TASK199E_FIXTURE_ROWS")
    _stop(len({row["codigo_inep"] for row in rows}) == 57, "TASK199E_FIXTURE_INEP")
    tier_counts = Counter(row["match_tier"] for row in rows)
    _stop(tier_counts == Counter({"A": 41, "B": 15, "C": 1}), "TASK199E_FIXTURE_TIERS")
    return rows


def load_held_fixture(path: str | Path = DEFAULT_CONTRACT) -> list[dict[str, Any]]:
    obj = load_contract(path)
    fixture = ROOT / obj["github_fixtures"]["held_compact"]["path"]
    rows = list(csv.DictReader(fixture.read_text(encoding="utf-8").splitlines()))
    _stop(len(rows) == 12, "TASK199E_HELD_ROWS")
    _stop(all(row["promotion_status"] == "HELD" for row in rows), "TASK199E_HELD_STATUS")
    _stop(all(bool(row["hold_reason"]) for row in rows), "TASK199E_HELD_REASON")
    return rows


def _common(source_family: str, source_sha256: str, provenance_ref: str, caution: str) -> dict[str, Any]:
    return {
        "observation_period": "2022",
        "source_family": source_family,
        "source_sha256": source_sha256,
        "provenance_ref": provenance_ref,
        "quality_status": "VALIDATED",
        "caution": caution,
    }


def territory_rows(path: str | Path = DEFAULT_CONTRACT) -> list[dict[str, Any]]:
    obj = load_contract(path)
    # Reuse the 11 already-validated municipal rows from TASK 199D and replace
    # the former 14-school slice with the expanded 57-school strong crosswalk.
    rows = [row for row in task199d_rows() if row["geo_level"] == "MUNICIPAL"]
    _stop(len(rows) == 11, "TASK199E_MUNICIPAL_ROWS")

    basic_sha = obj["sources"]["basic_sector_zip_sha256"]
    income_sha = obj["sources"]["income_sector_zip_sha256"]
    dict_sha = obj["sources"]["income_dictionary_sha256"]
    cnefe_sha = obj["sources"]["cnefe"]["archive_sha256"]

    for item in load_school_fixture(path):
        base = {
            "geo_level": "SCHOOL_LOCATION_CENSUS_SECTOR",
            "geo_id": item["codigo_inep"],
            "municipality_code": "3526902",
            "school_code": item["codigo_inep"],
            "school_name": item["unidade"],
            "sector_id": item["ibge_sector_code_2022"],
            "period": "2022",
            "school_sector_match_tier": item["match_tier"],
            "school_sector_match_method": item["match_method"],
        }
        caution = (
            "SCHOOL_LOCATION_CONTEXT_NE_STUDENT_SOCIOECONOMIC_PROFILE;"
            "PARTIAL_57_OF_69_NETWORK;"
            "SECTOR_INCOME_NE_ENROLLED_HOUSEHOLD_INCOME"
        )
        rows.extend([
            {
                **base,
                "metric_id": "SECTOR_POPULATION",
                "metric_name": "População residente no setor censitário da localização escolar",
                "value": float(item["sector_population_2022"]),
                "unit": "PERSONS",
                "context": "Contexto do setor censitário ligado à localização escolar por crosswalk forte.",
                **_common("IBGE_CENSO_2022", basic_sha, f"TASK199E_BASIC#V0001;CNEFE_SHA256_{cnefe_sha}", caution),
            },
            {
                **base,
                "metric_id": "SECTOR_RESPONSIBLE_INCOME_MEAN",
                "metric_name": "Rendimento nominal médio mensal dos responsáveis com rendimentos no setor",
                "value": float(item["responsible_income_mean_nominal_monthly_brl"]),
                "unit": "BRL_NOMINAL_MONTHLY",
                "context": "V06004 do setor da localização escolar; não descreve a renda dos alunos.",
                **_common("IBGE_CENSO_2022", income_sha, f"TASK199E_INCOME#V06004;DICT_SHA256_{dict_sha};CNEFE_SHA256_{cnefe_sha}", caution),
            },
            {
                **base,
                "metric_id": "SECTOR_RESPONSIBLE_INCOME_MEDIAN",
                "metric_name": "Rendimento nominal mediano mensal dos responsáveis com rendimentos no setor",
                "value": float(item["responsible_income_median_nominal_monthly_brl"]),
                "unit": "BRL_NOMINAL_MONTHLY",
                "context": "V06006 do setor da localização escolar; não descreve a renda dos alunos.",
                **_common("IBGE_CENSO_2022", income_sha, f"TASK199E_INCOME#V06006;DICT_SHA256_{dict_sha};CNEFE_SHA256_{cnefe_sha}", caution),
            },
            {
                **base,
                "metric_id": "SECTOR_RESPONSIBLE_INCOME_MEAN_PERCENTILE",
                "metric_name": "Percentil setorial não ponderado de V06004 em Limeira",
                "value": float(item["V06004_sector_percentile_unweighted"]),
                "unit": "PERCENTILE_0_100",
                "context": "Posição do V06004 do setor entre os 718 setores de Limeira com valor numérico; comparação setorial não ponderada.",
                **_common("IBGE_CENSO_2022", income_sha, f"TASK199E_DERIVED_PERCENTILE_FROM_718_NUMERIC_V06004;DICT_SHA256_{dict_sha}", caution),
            },
        ])

    _stop(len(rows) == 239, "TASK199E_PRODUCT_ROWS")
    return rows


def build_task199e_territory_profile(
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
    _stop(product["row_count"] == 239, "TASK199E_PRODUCT_ROW_COUNT")
    return product


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(path)
    rows = territory_rows(path)
    held = load_held_fixture(path)
    return {
        "schema": "TASK199E_SCHOOL_SECTOR_EXPANSION_VALIDATION_V1",
        "status": "PASS",
        "territory_rows": len(rows),
        "strong_school_links": obj["crosswalk"]["strong_links"],
        "held_school_links": len(held),
        "coverage_rate": obj["crosswalk"]["coverage_rate"],
        "full_network_school_link": False,
        "network": False,
        "drive_write": False,
    }

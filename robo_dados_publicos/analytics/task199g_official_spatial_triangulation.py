from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from robo_dados_publicos.analytics.observatory_products import build_territory_profile
from robo_dados_publicos.analytics.task199f_same_parity_address_bracket import (
    held_after_task199f,
    territory_rows as task199f_rows,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task199g_official_spatial_triangulation.v1.json"


class Task199GStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task199GStop(code)


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK199G_OFFICIAL_SPATIAL_TRIANGULATION_V1", "TASK199G_SCHEMA")
    _stop(obj.get("issue") == 628, "TASK199G_ISSUE")
    _stop(obj.get("base_main_sha") == "074c5415d9b71312692a4e034ff5a020406358b3", "TASK199G_BASE")
    _stop(obj["scope"]["active_school_denominator_2025"] == 69, "TASK199G_DENOM")

    promotions = obj["promotions"]
    _stop(len(promotions) == 5, "TASK199G_PROMOTION_COUNT")
    _stop(len({row["codigo_inep"] for row in promotions}) == 5, "TASK199G_PROMOTION_UNIQUE")
    _stop(
        {row["codigo_inep"] for row in promotions}
        == {"35470600", "35656823", "35217924", "35217992", "35223359"},
        "TASK199G_PROMOTION_SET",
    )

    rafael = next(row for row in promotions if row["codigo_inep"] == "35470600")
    _stop(rafael["cnefe_landmark"]["number"] == 250, "TASK199G_RAFAEL_LANDMARK")
    _stop(rafael["cnefe_landmark"]["row_count"] == 64, "TASK199G_RAFAEL_LANDMARK_ROWS")
    _stop(
        rafael["cnefe_landmark"]["unique_sector"] == rafael["cnefe_named"]["sector"],
        "TASK199G_RAFAEL_SECTOR",
    )
    _stop(rafael["anchor_distance_m"] <= 100.0, "TASK199G_RAFAEL_DISTANCE")

    alfredo = next(row for row in promotions if row["codigo_inep"] == "35656823")
    _stop(alfredo["cnefe_exact_km"]["number"] == 10, "TASK199G_ALFREDO_KM")
    _stop(
        alfredo["cnefe_exact_km"]["sector"] == alfredo["cnefe_named"]["sector"],
        "TASK199G_ALFREDO_SECTOR",
    )
    _stop(
        alfredo["cnefe_exact_km"]["locality"] == alfredo["cnefe_named"]["locality"] == "DOS FRADES",
        "TASK199G_ALFREDO_LOCALITY",
    )

    jose = next(row for row in promotions if row["codigo_inep"] == "35217924")
    _stop(jose["superseded_sme_number"] == 3, "TASK199G_JOSE_STALE_NUMBER")
    _stop(jose["cnefe_named"]["number"] == 38, "TASK199G_JOSE_EXACT_NUMBER")
    _stop("38_JARDIM_ESTEVES" in jose["current_claim"], "TASK199G_JOSE_CURRENT_CLAIM")

    martim = next(row for row in promotions if row["codigo_inep"] == "35217992")
    _stop(len(martim["cnefe_exact_km_candidates_same_sector"]) == 2, "TASK199G_MARTIM_KM_ROWS")
    _stop(
        all(row["number"] == 3 for row in martim["cnefe_exact_km_candidates_same_sector"]),
        "TASK199G_MARTIM_KM",
    )
    _stop(
        all(row["sector"] == martim["cnefe_named"]["sector"] for row in martim["cnefe_exact_km_candidates_same_sector"]),
        "TASK199G_MARTIM_SECTOR",
    )
    _stop(martim["max_anchor_distance_m"] <= 450.0, "TASK199G_MARTIM_DISTANCE")

    ary = next(row for row in promotions if row["codigo_inep"] == "35223359")
    _stop("PREFEITO_ARY_LEVY_PEREIRA" in ary["historical_claim"], "TASK199G_ARY_NAMED_HISTORY")
    _stop(ary["cnefe_generic"]["establishment"] == "CRECHE MUNICIPAL", "TASK199G_ARY_CNEFE_KIND")
    _stop(ary["cnefe_generic"]["matching_generic_creche_count_on_street"] == 1, "TASK199G_ARY_UNIQUE")
    _stop(ary["cnefe_generic"]["number"] == 0, "TASK199G_ARY_SN")

    cw = obj["crosswalk"]
    _stop(cw["before_strong_links"] == 59 and cw["after_strong_links"] == 64, "TASK199G_COVERAGE")
    _stop(cw["held_after"] == 5 and cw["full_network_link"] is False, "TASK199G_HELD")
    _stop(set(obj["held_after"]) == {"35208437", "35286229", "35004773", "35099569", "35241885"}, "TASK199G_HELD_SET")
    _stop(obj["expected_product"]["row_count"] == 267, "TASK199G_EXPECTED_ROWS")
    _stop("SCHOOL_TO_SECTOR_LINK_FULL_NETWORK" not in obj["expected_product"]["capabilities"], "TASK199G_NO_FULL_CAPABILITY")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK199G_REMOTE")
    return obj


def held_after_task199g(path: str | Path = DEFAULT_CONTRACT) -> list[dict[str, Any]]:
    obj = load_contract(path)
    promoted = {row["codigo_inep"] for row in obj["promotions"]}
    rows = [row for row in held_after_task199f() if row["codigo_inep"] not in promoted]
    _stop(len(rows) == 5, "TASK199G_HELD_ROWS")
    _stop({row["codigo_inep"] for row in rows} == set(obj["held_after"]), "TASK199G_HELD_IDENTITY")
    _stop(all(row["promotion_status"] == "HELD" for row in rows), "TASK199G_HELD_STATUS")
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
    rows = list(task199f_rows())
    _stop(len(rows) == 247, "TASK199G_BASE_ROWS")
    cnefe_sha = obj["sources"]["cnefe"]["archive_sha256"]
    basic_sha = obj["sources"]["basic_sector_zip_sha256"]
    income_sha = obj["sources"]["income_sector_zip_sha256"]
    dict_sha = obj["sources"]["income_dictionary_sha256"]

    for item in obj["promotions"]:
        base = {
            "geo_level": "SCHOOL_LOCATION_CENSUS_SECTOR",
            "geo_id": item["codigo_inep"],
            "municipality_code": "3526902",
            "school_code": item["codigo_inep"],
            "school_name": item["school"],
            "sector_id": item["sector_id"],
            "period": "2022",
            "school_sector_match_tier": "E",
            "school_sector_match_method": item["method"],
        }
        caution = (
            "SCHOOL_LOCATION_CONTEXT_NE_STUDENT_SOCIOECONOMIC_PROFILE;"
            "PARTIAL_64_OF_69_NETWORK;"
            "SECTOR_INCOME_NE_ENROLLED_HOUSEHOLD_INCOME;"
            "MULTI_ANCHOR_OFFICIAL_SPATIAL_TRIANGULATION"
        )
        context = (
            "Setor adjudicado somente após triangulação de múltiplas âncoras oficiais "
            "municipais/SME com endereço ou marco atual e CNEFE 2022 georreferenciado."
        )
        rows.extend([
            {
                **base,
                "metric_id": "SECTOR_POPULATION",
                "metric_name": "População residente no setor censitário da localização escolar",
                "value": float(item["sector_population_2022"]),
                "unit": "PERSONS",
                "context": context,
                **_common(basic_sha, f"TASK199G_BASIC#V0001;CNEFE_SHA256_{cnefe_sha};METHOD:{item['method']}", caution),
            },
            {
                **base,
                "metric_id": "SECTOR_RESPONSIBLE_INCOME_MEAN",
                "metric_name": "Rendimento nominal médio mensal dos responsáveis com rendimentos no setor",
                "value": float(item["responsible_income_mean_nominal_monthly_brl"]),
                "unit": "BRL_NOMINAL_MONTHLY",
                "context": "V06004 do setor da localização escolar; não descreve a renda dos alunos.",
                **_common(income_sha, f"TASK199G_INCOME#V06004;DICT_SHA256_{dict_sha};CNEFE_SHA256_{cnefe_sha}", caution),
            },
            {
                **base,
                "metric_id": "SECTOR_RESPONSIBLE_INCOME_MEDIAN",
                "metric_name": "Rendimento nominal mediano mensal dos responsáveis com rendimentos no setor",
                "value": float(item["responsible_income_median_nominal_monthly_brl"]),
                "unit": "BRL_NOMINAL_MONTHLY",
                "context": "V06006 do setor da localização escolar; não descreve a renda dos alunos.",
                **_common(income_sha, f"TASK199G_INCOME#V06006;DICT_SHA256_{dict_sha};CNEFE_SHA256_{cnefe_sha}", caution),
            },
            {
                **base,
                "metric_id": "SECTOR_RESPONSIBLE_INCOME_MEAN_PERCENTILE",
                "metric_name": "Percentil setorial não ponderado de V06004 em Limeira",
                "value": float(item["V06004_sector_percentile_unweighted"]),
                "unit": "PERCENTILE_0_100",
                "context": "Posição do V06004 do setor entre os 718 setores com valor numérico; comparação setorial não ponderada.",
                **_common(income_sha, f"TASK199G_DERIVED_PERCENTILE_FROM_718_NUMERIC_V06004;DICT_SHA256_{dict_sha}", caution),
            },
        ])

    _stop(len(rows) == 267, "TASK199G_PRODUCT_ROWS")
    school_codes = {row["school_code"] for row in rows if row["geo_level"] == "SCHOOL_LOCATION_CENSUS_SECTOR"}
    _stop(len(school_codes) == 64, "TASK199G_UNIQUE_SCHOOLS")
    return rows


def build_task199g_territory_profile(
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
    _stop(product["row_count"] == 267, "TASK199G_PRODUCT_ROW_COUNT")
    return product


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(path)
    rows = territory_rows(path)
    held = held_after_task199g(path)
    return {
        "schema": "TASK199G_OFFICIAL_SPATIAL_TRIANGULATION_VALIDATION_V1",
        "status": "PASS",
        "territory_rows": len(rows),
        "strong_school_links": obj["crosswalk"]["after_strong_links"],
        "held_school_links": len(held),
        "coverage_rate": obj["crosswalk"]["coverage_rate"],
        "full_network_school_link": False,
        "promotion_codes": sorted(row["codigo_inep"] for row in obj["promotions"]),
        "held_codes": sorted(row["codigo_inep"] for row in held),
        "network": False,
        "drive_write": False,
    }

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from robo_dados_publicos.analytics.observatory_products import build_territory_profile
from robo_dados_publicos.analytics.task199g_official_spatial_triangulation import territory_rows as task199g_rows

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task199h_full_network_official_point_in_polygon.v1.json"


class Task199HStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task199HStop(code)


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK199H_FULL_NETWORK_OFFICIAL_POINT_IN_POLYGON_V1", "TASK199H_SCHEMA")
    _stop(obj.get("issue") == 628, "TASK199H_ISSUE")
    _stop(obj.get("base_main_sha") == "f0ab72b6a001e9c2e074c473066977da5f6ed995", "TASK199H_BASE")
    scope = obj["scope"]
    _stop(scope["active_school_denominator_2025"] == 69, "TASK199H_DENOM")
    _stop(scope["before_strong_links"] == 64 and scope["after_strong_links"] == 69, "TASK199H_COVERAGE")
    _stop(scope["full_network"] is True, "TASK199H_FULL_NETWORK")
    promos = obj["promotions"]
    _stop(len(promos) == 5 and len({x["codigo_inep"] for x in promos}) == 5, "TASK199H_PROMOTIONS")
    _stop(
        {x["codigo_inep"] for x in promos}
        == {"35208437", "35286229", "35004773", "35099569", "35241885"},
        "TASK199H_PROMOTION_SET",
    )
    pip = obj["point_in_polygon"]
    _stop(pip["status"] == "PASS_FIVE_UNIQUE_INTERIOR_SECTOR_MATCHES", "TASK199H_PIP")
    _stop(pip["all_unique"] is True and pip["all_interior_not_boundary"] is True, "TASK199H_PIP_UNIQUE")
    geometry = obj["sources"]["ibge_sector_geometry"]
    _stop(geometry["bytes"] == 182128640, "TASK199H_GPKG_BYTES")
    _stop(geometry["sha256"] == "07affc966f82292d6f9a359adccc49e69ed55d2075936ef6d1e9c346b29a04bc", "TASK199H_GPKG_SHA")
    _stop(geometry["limeira_sector_rows"] == 735, "TASK199H_GPKG_ROWS")
    mauricio = next(x for x in promos if x["codigo_inep"] == "35286229")
    _stop(mauricio["income_status"] == "SOURCE_EXPLICIT_X", "TASK199H_MAURICIO_X")
    _stop(mauricio["income_rows_materialized"] == 0, "TASK199H_MAURICIO_NO_INCOME")
    theresa = next(x for x in promos if x["codigo_inep"] == "35241885")
    _stop(theresa["geoportal_gid"] == 80, "TASK199H_THERESA_MAIN")
    _stop(theresa["extension_excluded"]["geoportal_gid"] == 38, "TASK199H_THERESA_EXTENSION")
    neusa = next(x for x in promos if x["codigo_inep"] == "35099569")
    _stop(bool(neusa.get("address_conflict_preserved")), "TASK199H_NEUSA_CONFLICT")
    exp = obj["expected_product"]
    _stop(exp["row_count"] == 284, "TASK199H_ROWS")
    _stop(exp["school_links"] == 69 and exp["full_network_school_link"] is True, "TASK199H_PRODUCT_FULL")
    _stop(exp["schools_with_numeric_income_context"] == 68, "TASK199H_INCOME_COVERAGE")
    _stop(exp["schools_with_explicit_sector_income_missingness"] == 1, "TASK199H_INCOME_MISSING")
    _stop("SCHOOL_TO_SECTOR_LINK_FULL_NETWORK" in exp["capabilities"], "TASK199H_FULL_CAPABILITY")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK199H_REMOTE")
    return obj


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
    rows = list(task199g_rows())
    _stop(len(rows) == 267, "TASK199H_BASE_ROWS")
    basic_sha = obj["sources"]["basic_sector_zip_sha256"]
    income_sha = obj["sources"]["income_sector_zip_sha256"]
    dict_sha = obj["sources"]["income_dictionary_sha256"]
    gpkg_sha = obj["sources"]["ibge_sector_geometry"]["sha256"]

    for item in obj["promotions"]:
        base = {
            "geo_level": "SCHOOL_LOCATION_CENSUS_SECTOR",
            "geo_id": item["codigo_inep"],
            "municipality_code": "3526902",
            "school_code": item["codigo_inep"],
            "school_name": item["school"],
            "sector_id": item["sector_id"],
            "period": "2022",
            "school_sector_match_tier": "F",
            "school_sector_match_method": "OFFICIAL_MUNICIPAL_POINT_TO_IBGE_2022_SECTOR_POINT_IN_POLYGON",
        }
        caution = (
            "SCHOOL_LOCATION_CONTEXT_NE_STUDENT_SOCIOECONOMIC_PROFILE;"
            "SECTOR_INCOME_NE_ENROLLED_HOUSEHOLD_INCOME;"
            "FULL_NETWORK_GEOGRAPHY_NE_COMPLETE_INCOME_FOR_EVERY_SECTOR"
        )
        point_ref = f"GEOPORTAL_THEME_1234_GID_{item['geoportal_gid']};IBGE_GPKG_SHA256_{gpkg_sha};UNIQUE_INTERIOR_PIP"
        rows.append({
            **base,
            "metric_id": "SECTOR_POPULATION",
            "metric_name": "População residente no setor censitário da localização escolar",
            "value": float(item["sector_population_2022"]),
            "unit": "PERSONS",
            "context": "Ponto oficial municipal da escola contido de forma única no setor IBGE 2022; localização da escola não descreve o perfil dos alunos.",
            **_common(basic_sha, f"TASK199H_BASIC#V0001;{point_ref}", caution),
        })
        if item.get("income_status") == "SOURCE_EXPLICIT_X":
            continue
        rows.extend([
            {
                **base,
                "metric_id": "SECTOR_RESPONSIBLE_INCOME_MEAN",
                "metric_name": "Rendimento nominal médio mensal dos responsáveis com rendimentos no setor",
                "value": float(item["responsible_income_mean_nominal_monthly_brl"]),
                "unit": "BRL_NOMINAL_MONTHLY",
                "context": "V06004 do setor da localização escolar; não descreve a renda dos alunos.",
                **_common(income_sha, f"TASK199H_INCOME#V06004;DICT_SHA256_{dict_sha};{point_ref}", caution),
            },
            {
                **base,
                "metric_id": "SECTOR_RESPONSIBLE_INCOME_MEDIAN",
                "metric_name": "Rendimento nominal mediano mensal dos responsáveis com rendimentos no setor",
                "value": float(item["responsible_income_median_nominal_monthly_brl"]),
                "unit": "BRL_NOMINAL_MONTHLY",
                "context": "V06006 do setor da localização escolar; não descreve a renda dos alunos.",
                **_common(income_sha, f"TASK199H_INCOME#V06006;DICT_SHA256_{dict_sha};{point_ref}", caution),
            },
            {
                **base,
                "metric_id": "SECTOR_RESPONSIBLE_INCOME_MEAN_PERCENTILE",
                "metric_name": "Percentil setorial não ponderado de V06004 em Limeira",
                "value": float(item["V06004_sector_percentile_unweighted"]),
                "unit": "PERCENTILE_0_100",
                "context": "Posição do V06004 do setor entre 718 setores com valor numérico; X é excluído e nunca convertido em zero.",
                **_common(income_sha, f"TASK199H_DERIVED_PERCENTILE_FROM_718_NUMERIC_V06004;DICT_SHA256_{dict_sha};{point_ref}", caution),
            },
        ])

    _stop(len(rows) == 284, "TASK199H_PRODUCT_ROWS")
    linked = {str(r["school_code"]) for r in rows if r.get("geo_level") == "SCHOOL_LOCATION_CENSUS_SECTOR"}
    _stop(len(linked) == 69, "TASK199H_LINKED_69")
    mauricio_income = [
        r for r in rows
        if r.get("school_code") == "35286229" and str(r.get("metric_id", "")).startswith("SECTOR_RESPONSIBLE_INCOME")
    ]
    _stop(not mauricio_income, "TASK199H_X_NOT_MATERIALIZED_AS_NUMBER")
    return rows


def build_task199h_territory_profile(*, generated_at: str, software_version: str, contract_path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(contract_path)
    product = build_territory_profile(
        territory_rows(contract_path),
        generated_at=generated_at,
        software_version=software_version,
        capabilities=obj["expected_product"]["capabilities"],
    )
    _stop(product["row_count"] == 284, "TASK199H_PRODUCT_ROW_COUNT")
    return product


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(path)
    rows = territory_rows(path)
    linked = {str(r["school_code"]) for r in rows if r.get("geo_level") == "SCHOOL_LOCATION_CENSUS_SECTOR"}
    return {
        "schema": "TASK199H_FULL_NETWORK_OFFICIAL_POINT_IN_POLYGON_VALIDATION_V1",
        "status": "PASS",
        "territory_rows": len(rows),
        "strong_school_links": len(linked),
        "held_school_links": 0,
        "coverage_rate": len(linked) / 69,
        "full_network_school_link": True,
        "schools_with_numeric_income_context": obj["expected_product"]["schools_with_numeric_income_context"],
        "schools_with_explicit_sector_income_missingness": obj["expected_product"]["schools_with_explicit_sector_income_missingness"],
        "network": False,
        "drive_write": False,
    }

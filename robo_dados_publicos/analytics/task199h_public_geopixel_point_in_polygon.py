from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from robo_dados_publicos.analytics.observatory_products import build_territory_profile
from robo_dados_publicos.analytics.task199g_official_spatial_triangulation import (
    held_after_task199g,
    territory_rows as task199g_rows,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task199h_public_geopixel_point_in_polygon.v1.json"


class Task199HStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task199HStop(code)


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK199H_PUBLIC_GEOPIXEL_POINT_IN_POLYGON_V1", "TASK199H_SCHEMA")
    _stop(obj.get("issue") == 628, "TASK199H_ISSUE")
    _stop(obj.get("base_main_sha") == "f0ab72b6a001e9c2e074c473066977da5f6ed995", "TASK199H_BASE")
    _stop(obj["scope"]["active_school_denominator_2025"] == 69, "TASK199H_DENOM")

    src = obj["sources"]
    geo = src["limeira_geopixel"]
    _stop(geo["configuration_sha256"] == "7e91395faef1b827518df8d85555b0d0992ba1508ea40d4b2e3bf63a954a5ceb", "TASK199H_GEOPIXEL_CONFIG_SHA")
    _stop(geo["frontend_bundle_sha256"] == "ebb776c3de11c8db56afa0ec1a7c5488fd11c5661054ecb6d914bd8d0931ecc1", "TASK199H_GEOPIXEL_BUNDLE_SHA")
    _stop(geo["server_path"].endswith("/geopixelcidades3_server"), "TASK199H_SERVER_PATH")
    _stop(geo["public_access_contract"]["profile_id"] == 2, "TASK199H_PUBLIC_PROFILE_ID")
    _stop(geo["public_access_contract"]["profile_name"] == "Público", "TASK199H_PUBLIC_PROFILE_NAME")
    _stop(geo["public_access_contract"]["credentials_required"] is False, "TASK199H_NO_CREDENTIALS")
    _stop(geo["public_access_contract"]["registration_required"] is False, "TASK199H_NO_REGISTRATION")
    _stop(geo["public_access_contract"]["token_persisted"] is False, "TASK199H_TOKEN_PERSIST")
    _stop(geo["school_theme"]["theme_id"] == 1234, "TASK199H_THEME_ID")
    _stop(geo["school_theme"]["layer"] == "limeira:escola_municipal_limeira", "TASK199H_THEME_LAYER")
    _stop(geo["school_theme"]["source_srid"] == 3857, "TASK199H_SOURCE_SRID")

    gpkg = src["ibge_sector_geometry"]
    _stop(gpkg["sha256"] == "07affc966f82292d6f9a359adccc49e69ed55d2075936ef6d1e9c346b29a04bc", "TASK199H_GPKG_SHA")
    _stop(gpkg["bytes"] == 182128640, "TASK199H_GPKG_BYTES")
    _stop(gpkg["feature_table"] == "SP_setores_CD2022", "TASK199H_GPKG_TABLE")
    _stop(gpkg["sector_code_field"] == "CD_SETOR", "TASK199H_GPKG_CODE")
    _stop(gpkg["srs_id"] == 4674, "TASK199H_GPKG_SRID")
    _stop(gpkg["limeira_sector_rows"] == 735 == gpkg["parsed_sector_rows"], "TASK199H_GPKG_ROWS")
    _stop(gpkg["geometry_parse_errors"] == 0, "TASK199H_GPKG_PARSE")

    inc = src["income_sector"]
    _stop(inc["numeric_v06004_sector_count"] == 718, "TASK199H_V06004_DENOM")
    _stop(inc["missing_marker"] == "X", "TASK199H_MISSING_MARKER")
    _stop(inc["percentile_rule"] == "ROUND_1DP(COUNT_NUMERIC_V06004_LE_VALUE / 718 * 100)", "TASK199H_PERCENTILE_RULE")

    promotions = obj["promotions"]
    expected_codes = {"35208437", "35286229", "35004773", "35099569", "35241885"}
    _stop(len(promotions) == 5, "TASK199H_PROMOTION_COUNT")
    _stop({row["codigo_inep"] for row in promotions} == expected_codes, "TASK199H_PROMOTION_SET")
    _stop({row["codigo_inep"] for row in held_after_task199g()} == expected_codes, "TASK199H_UPSTREAM_HELD_SET")
    _stop(len({row["point_in_polygon"]["sector_id"] for row in promotions}) == 5, "TASK199H_SECTOR_UNIQUE")
    for row in promotions:
        _stop(row["method"] == "H_CURRENT_OFFICIAL_GEOPIXEL_POINT_IN_OFFICIAL_IBGE_2022_POLYGON", "TASK199H_METHOD")
        _stop(row["point_in_polygon"]["match_count"] == 1, "TASK199H_SINGLE_SECTOR")
        _stop(row["point_in_polygon"]["on_boundary"] is False, "TASK199H_INTERIOR_ONLY")
        _stop(str(row["point_in_polygon"]["sector_id"]).startswith("3526902"), "TASK199H_LIMEIRA_SECTOR")
        _stop(isinstance(row["geoportal"]["lon"], (int, float)), "TASK199H_LON")
        _stop(isinstance(row["geoportal"]["lat"], (int, float)), "TASK199H_LAT")

    neusa = next(row for row in promotions if row["codigo_inep"] == "35099569")
    _stop("MARIO_ALVES_FERRAZ_185" in neusa["conflict_preserved"], "TASK199H_NEUSA_SME_CONFLICT")
    _stop("OLIVIA_SACCO_IAQUINTA_SN" in neusa["conflict_preserved"], "TASK199H_NEUSA_GEO_CONFLICT")

    theresa = next(row for row in promotions if row["codigo_inep"] == "35241885")
    _stop(theresa["geoportal"]["gid"] == 80, "TASK199H_THERESA_MAIN_GID")
    _stop(theresa["extension_excluded"]["gid"] == 38, "TASK199H_THERESA_EXTENSION_GID")
    _stop("Extensão" in theresa["extension_excluded"]["returned_name"], "TASK199H_THERESA_EXTENSION_LABEL")
    _stop(theresa["extension_excluded"]["reason"] == "EXPLICIT_EXTENSION_NOT_MAIN_UNIT", "TASK199H_THERESA_EXTENSION_RULE")

    mauricio = next(row for row in promotions if row["codigo_inep"] == "35286229")
    _stop(mauricio["income"]["status"] == "OFFICIAL_X_MISSING", "TASK199H_MAURICIO_MISSING")
    _stop(all(mauricio["income"][f"V0600{i}"] == "X" for i in range(1, 7)), "TASK199H_MAURICIO_X_VALUES")
    numeric = [row for row in promotions if row["income"]["status"] == "NUMERIC"]
    _stop(len(numeric) == 4, "TASK199H_NUMERIC_INCOME_COUNT")

    cw = obj["crosswalk"]
    _stop(cw["before_strong_links"] == 64 and cw["after_strong_links"] == 69, "TASK199H_COVERAGE")
    _stop(cw["held_after"] == 0 and cw["full_network_link"] is True, "TASK199H_FULL_NETWORK")
    exp = obj["expected_product"]
    _stop(exp["row_count"] == 284 and exp["school_links"] == 69, "TASK199H_EXPECTED_PRODUCT")
    _stop(exp["new_school_metric_rows"] == 17, "TASK199H_NEW_ROWS")
    _stop(exp["income_missing_school_codes"] == ["35286229"], "TASK199H_INCOME_MISSING_SET")
    caps = set(exp["capabilities"])
    _stop("SCHOOL_TO_SECTOR_LINK_FULL_NETWORK" in caps, "TASK199H_FULL_CAPABILITY")
    _stop("SCHOOL_TO_SECTOR_LINK_COVERAGE_69_OF_69" in caps, "TASK199H_69_CAPABILITY")
    _stop("SCHOOL_TO_SECTOR_LINK_PARTIAL" not in caps, "TASK199H_NO_PARTIAL_CAPABILITY")
    _stop("SCHOOL_TO_SECTOR_LINK_COVERAGE_64_OF_69" not in caps, "TASK199H_NO_STALE_64_CAPABILITY")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK199H_REMOTE")
    return obj


def held_after_task199h(path: str | Path = DEFAULT_CONTRACT) -> list[dict[str, Any]]:
    obj = load_contract(path)
    promoted = {row["codigo_inep"] for row in obj["promotions"]}
    held = [row for row in held_after_task199g() if row["codigo_inep"] not in promoted]
    _stop(held == [], "TASK199H_HELD_REMAINS")
    return held


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
    src = obj["sources"]
    basic_sha = src["basic_sector"]["zip_sha256"]
    income_sha = src["income_sector"]["zip_sha256"]
    dict_sha = src["income_sector"]["dictionary_sha256"]
    gpkg_sha = src["ibge_sector_geometry"]["sha256"]
    config_sha = src["limeira_geopixel"]["configuration_sha256"]
    bundle_sha = src["limeira_geopixel"]["frontend_bundle_sha256"]

    for item in obj["promotions"]:
        code = item["codigo_inep"]
        sector_id = item["point_in_polygon"]["sector_id"]
        base = {
            "geo_level": "SCHOOL_LOCATION_CENSUS_SECTOR",
            "geo_id": code,
            "municipality_code": "3526902",
            "school_code": code,
            "school_name": item["school"],
            "sector_id": sector_id,
            "period": "2022",
            "school_sector_match_tier": "H",
            "school_sector_match_method": item["method"],
        }
        caution_parts = [
            "SCHOOL_LOCATION_CONTEXT_NE_STUDENT_SOCIOECONOMIC_PROFILE",
            "CURRENT_2026_SCHOOL_SITE_MAPPED_TO_2022_CENSUS_GEOGRAPHY",
            "SECTOR_INCOME_NE_ENROLLED_HOUSEHOLD_INCOME",
            "OFFICIAL_GEOPIXEL_POINT_IN_OFFICIAL_IBGE_2022_POLYGON",
        ]
        if code == "35099569":
            caution_parts.append("NEUSA_CURRENT_OFFICIAL_ADDRESS_CONFLICT_PRESERVED")
        if item["income"]["status"] == "OFFICIAL_X_MISSING":
            caution_parts.append("OFFICIAL_SECTOR_INCOME_X_MISSING_NE_ZERO")
        caution = ";".join(caution_parts)
        provenance_base = (
            f"TASK199H_GEOPIXEL_THEME_1234_GID_{item['geoportal']['gid']};"
            f"CONFIG_SHA256_{config_sha};BUNDLE_SHA256_{bundle_sha};"
            f"IBGE_GPKG_SHA256_{gpkg_sha};SECTOR_{sector_id}"
        )
        rows.append({
            **base,
            "metric_id": "SECTOR_POPULATION",
            "metric_name": "População residente no setor censitário da localização escolar",
            "value": float(item["sector_population_2022"]),
            "unit": "PERSONS",
            "context": (
                "Ponto atual da unidade municipal, publicado no GeoPortal de Limeira, "
                "intersectado com a malha oficial de setores do Censo 2022; o valor é V0001 do setor."
            ),
            **_common(basic_sha, provenance_base + ";BASIC_V0001", caution),
        })

        income = item["income"]
        if income["status"] == "OFFICIAL_X_MISSING":
            continue
        _stop(income["status"] == "NUMERIC", "TASK199H_UNKNOWN_INCOME_STATUS")
        rows.extend([
            {
                **base,
                "metric_id": "SECTOR_RESPONSIBLE_INCOME_MEAN",
                "metric_name": "Rendimento nominal médio mensal dos responsáveis com rendimentos no setor",
                "value": float(income["responsible_income_mean_nominal_monthly_brl"]),
                "unit": "BRL_NOMINAL_MONTHLY",
                "context": "V06004 do setor da localização escolar atual; não descreve a renda dos alunos.",
                **_common(income_sha, provenance_base + f";INCOME_V06004;DICT_SHA256_{dict_sha}", caution),
            },
            {
                **base,
                "metric_id": "SECTOR_RESPONSIBLE_INCOME_MEDIAN",
                "metric_name": "Rendimento nominal mediano mensal dos responsáveis com rendimentos no setor",
                "value": float(income["responsible_income_median_nominal_monthly_brl"]),
                "unit": "BRL_NOMINAL_MONTHLY",
                "context": "V06006 do setor da localização escolar atual; não descreve a renda dos alunos.",
                **_common(income_sha, provenance_base + f";INCOME_V06006;DICT_SHA256_{dict_sha}", caution),
            },
            {
                **base,
                "metric_id": "SECTOR_RESPONSIBLE_INCOME_MEAN_PERCENTILE",
                "metric_name": "Percentil setorial não ponderado de V06004 em Limeira",
                "value": float(income["V06004_sector_percentile_unweighted"]),
                "unit": "PERCENTILE_0_100",
                "context": "Posição do V06004 do setor entre os 718 setores com valor numérico; comparação setorial não ponderada.",
                **_common(income_sha, provenance_base + f";DERIVED_PERCENTILE_FROM_718_NUMERIC_V06004;DICT_SHA256_{dict_sha}", caution),
            },
        ])

    _stop(len(rows) == 284, "TASK199H_PRODUCT_ROWS")
    school_codes = {row["school_code"] for row in rows if row.get("geo_level") == "SCHOOL_LOCATION_CENSUS_SECTOR"}
    _stop(len(school_codes) == 69, "TASK199H_UNIQUE_SCHOOLS")
    _stop({row["codigo_inep"] for row in held_after_task199h(path)} == set(), "TASK199H_NO_HELD")
    mauricio_metrics = {
        row["metric_id"]
        for row in rows
        if row.get("school_code") == "35286229"
    }
    _stop(mauricio_metrics == {"SECTOR_POPULATION"}, "TASK199H_MAURICIO_NO_FAKE_INCOME_ROWS")
    return rows


def build_task199h_territory_profile(
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
    _stop(product["row_count"] == 284, "TASK199H_PRODUCT_ROW_COUNT")
    return product


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(path)
    rows = territory_rows(path)
    held = held_after_task199h(path)
    linked = {
        str(row["school_code"])
        for row in rows
        if row.get("geo_level") == "SCHOOL_LOCATION_CENSUS_SECTOR"
    }
    return {
        "schema": "TASK199H_PUBLIC_GEOPIXEL_POINT_IN_POLYGON_VALIDATION_V1",
        "status": "PASS",
        "territory_rows": len(rows),
        "strong_school_links": len(linked),
        "held_school_links": len(held),
        "coverage_rate": len(linked) / obj["scope"]["active_school_denominator_2025"],
        "full_network_school_link": len(linked) == 69 and not held,
        "promotion_codes": sorted(row["codigo_inep"] for row in obj["promotions"]),
        "income_missing_school_codes": list(obj["expected_product"]["income_missing_school_codes"]),
        "network": False,
        "drive_write": False,
    }

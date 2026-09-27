"""Current territorial product and coverage derived from its validated rows."""
from __future__ import annotations

from typing import Any, Mapping

from robo_dados_publicos.analytics.observatory_query_serving import validate_product_snapshot
from robo_dados_publicos.analytics.task199h_full_network_official_point_in_polygon import (
    build_task199h_territory_profile,
    load_contract,
)


def coverage_context(product: Mapping[str, Any]) -> dict[str, Any]:
    validate_product_snapshot(product)
    if product.get("product_name") != "TERRITORY_PROFILE":
        raise ValueError("CURRENT_TERRITORY_PRODUCT_REQUIRED")
    contract = load_contract()
    denominator = contract["scope"]["active_school_denominator_2025"]
    school_rows = [r for r in product["rows"] if r.get("geo_level") == "SCHOOL_LOCATION_CENSUS_SECTOR"]
    links: dict[str, str] = {}
    for row in school_rows:
        code, sector = str(row["school_code"]), str(row["sector_id"])
        if code in links and links[code] != sector:
            raise ValueError("CURRENT_TERRITORY_CONFLICTING_SECTOR")
        links[code] = sector
    if not 0 < len(links) <= denominator:
        raise ValueError("CURRENT_TERRITORY_COVERAGE_RANGE")
    income_codes = {str(r["school_code"]) for r in school_rows if r["metric_id"] == "SECTOR_RESPONSIBLE_INCOME_MEAN"}
    explicit_x = []
    for item in contract["promotions"]:
        code = item["codigo_inep"]
        if item.get("income_status") == "SOURCE_EXPLICIT_X" and links.get(code) == item["sector_id"]:
            if any(r["school_code"] == code and "INCOME" in r["metric_id"] for r in school_rows):
                raise ValueError("CURRENT_TERRITORY_SOURCE_X_BECAME_NUMERIC")
            explicit_x.append(code)
    full = len(links) == denominator
    if "SCHOOL_TO_SECTOR_LINK_FULL_NETWORK" in product.get("capabilities", []) and not full:
        raise ValueError("CURRENT_TERRITORY_FULL_CAPABILITY_WITH_PARTIAL_ROWS")
    return {
        "strong_links": len(links), "denominator": denominator,
        "held": denominator - len(links), "full_network": full,
        "numeric_income_schools": len(income_codes),
        "explicit_income_missingness_codes": sorted(explicit_x),
        "snapshot_id": product["snapshot_id"],
        "content_sha256": product["content_sha256"],
    }


def coverage_caution(coverage: Mapping[str, Any]) -> str:
    if coverage["full_network"]:
        return "FULL_NETWORK_GEOGRAPHY_NE_COMPLETE_INCOME_FOR_EVERY_SECTOR"
    return (f"TERRITORY_COVERAGE_{coverage['strong_links']}_OF_{coverage['denominator']}_"
            f"{coverage['held']}_HELD_NE_FULL_NETWORK")


def coverage_fact(product: Mapping[str, Any]) -> dict[str, Any]:
    coverage = coverage_context(product)
    text = (f"Cobertura territorial escolar validada: {coverage['strong_links']}/{coverage['denominator']} "
            f"vínculos fortes; {coverage['held']} escolas permanecem HELD; "
            f"cobertura total da rede = {'sim' if coverage['full_network'] else 'não'}.")
    if coverage["explicit_income_missingness_codes"]:
        text += (f" Renda setorial numérica disponível para {coverage['numeric_income_schools']} escolas; "
                 f"{len(coverage['explicit_income_missingness_codes'])} com X explícito do IBGE. X não é zero.")
    return {"kind": "TERRITORY_LINK_COVERAGE", "strong_school_links": coverage["strong_links"],
            "active_school_denominator": coverage["denominator"], "held": coverage["held"],
            "full_network_link": coverage["full_network"], "text": text,
            "source_snapshot_id": coverage["snapshot_id"],
            "source_content_sha256": coverage["content_sha256"]}


def income_missingness_facts(product: Mapping[str, Any], school_code: str | None) -> list[dict[str, Any]]:
    coverage = coverage_context(product)
    codes = coverage["explicit_income_missingness_codes"]
    if school_code is not None:
        codes = [code for code in codes if code == school_code]
    return [{"kind": "EXPLICIT_SECTOR_INCOME_MISSINGNESS", "school_code": code,
             "status": "SOURCE_EXPLICIT_X", "value": None,
             "source_snapshot_id": product["snapshot_id"],
             "source_evidence_path": "docs/evidence/TASK_199H_FULL_NETWORK_OFFICIAL_POINT_IN_POLYGON_0.8.0.json",
             "text": f"Escola INEP {code}: setor identificado; renda setorial publicada como X pelo IBGE. X é ausência explícita, não renda zero."}
            for code in codes]


def build_current_territory_profile(*, generated_at: str, software_version: str) -> dict[str, Any]:
    product = build_task199h_territory_profile(generated_at=generated_at, software_version=software_version)
    coverage = coverage_context(product)
    if not (coverage["full_network"] and coverage["numeric_income_schools"] == 68
            and coverage["explicit_income_missingness_codes"] == ["35286229"]):
        raise ValueError("CURRENT_TERRITORY_199H_INTEGRATION_DRIFT")
    # Full validated coverage also satisfies the existing V4 minimum-coverage gate.
    # Preserve that gate and the historical TASK202 builder for old snapshots.
    product["capabilities"] = sorted(set(product["capabilities"]) | {
        "SCHOOL_TO_SECTOR_LINK_SUBSTANTIAL_COVERAGE_WITH_EXPLICIT_MISSINGNESS"
    })
    return product

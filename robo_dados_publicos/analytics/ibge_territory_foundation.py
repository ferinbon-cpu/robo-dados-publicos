from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/ibge_limeira_territorial_foundation.v1.json"
DEFAULT_OVERLAY = ROOT / "config/observatory_territory_answerability_overlay.v1.json"


class Task199AStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task199AStop(code)


def _load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_foundation(
    config_path: str | Path = DEFAULT_CONFIG,
    overlay_path: str | Path = DEFAULT_OVERLAY,
) -> dict[str, Any]:
    cfg = _load(config_path)
    overlay = _load(overlay_path)

    _stop(cfg["schema"] == "IBGE_LIMEIRA_TERRITORIAL_FOUNDATION_V1", "TASK199A_SCHEMA")
    _stop(cfg["scope"]["ibge_code_7"] == "3526902", "TASK199A_IBGE_CODE")
    _stop(cfg["scope"]["municipality"] == "Limeira", "TASK199A_MUNICIPALITY")
    _stop(cfg["scope"]["uf"] == "SP", "TASK199A_UF")

    sources = {row["id"]: row for row in cfg["official_source_registry"]}
    required = {
        "IBGE_CIDADES_LIMEIRA",
        "IBGE_CENSO2022_SECTOR_BASIC_BR_20260520",
        "IBGE_CENSO2022_SECTOR_INCOME_RESP_BR_20260508",
        "IBGE_CENSO2022_SP_SECTOR_GPKG",
        "IBGE_CNEFE_LIMEIRA_2022",
    }
    _stop(set(sources) == required, "TASK199A_SOURCE_SET")
    _stop(all(row["authority"] == "IBGE" for row in sources.values()), "TASK199A_AUTHORITY")

    cidades = sources["IBGE_CIDADES_LIMEIRA"]["observed_values"]
    _stop(cidades["population_census_2022"] == 291869, "TASK199A_POP_CENSUS")
    _stop(cidades["population_estimate_2025"] == 301292, "TASK199A_POP_ESTIMATE")
    _stop(cidades["pib_per_capita_brl_2023"] == "71528.46", "TASK199A_PIB_PC")

    guards = set(cfg["guards"])
    for guard in {
        "SCHOOL_LOCATION_CONTEXT_NE_STUDENT_SOCIOECONOMIC_PROFILE",
        "PIB_PER_CAPITA_NE_INCOME",
        "ESTIMATE_NE_CENSUS_COUNT",
        "NO_SYNTHETIC_VULNERABILITY_INDEX_WITHOUT_EXPLICIT_METHOD",
        "MISSING_GEOGRAPHY_NE_ZERO",
    }:
        _stop(guard in guards, f"TASK199A_GUARD_{guard}")

    join = cfg["school_to_sector_join_contract"]
    _stop("POINT_IN_POLYGON" in join["preferred"], "TASK199A_SPATIAL_JOIN")
    _stop("CNEFE" in join["fallback"], "TASK199A_CNEFE_FALLBACK")

    _stop(overlay["schema"] == "OBSERVATORY_TERRITORY_ANSWERABILITY_OVERLAY_V1", "TASK199A_OVERLAY_SCHEMA")
    _stop(overlay["status"] == "DESIGNED_NOT_CANONICALLY_APPLIED", "TASK199A_OVERLAY_STATUS")
    _stop(overlay["replaces_problematic_rule"]["old_match"] == "ANY", "TASK199A_OLD_ANY")
    _stop(
        overlay["target_rule"]["municipal_context_requires_all_capabilities"]
        == ["MUNICIPAL_DEMOGRAPHY", "MUNICIPAL_ECONOMY_OR_INCOME"],
        "TASK199A_MINIMUM_CONTEXT",
    )

    _stop(cfg["current_state"]["territory_profile_materialized"] is False, "TASK199A_NO_FALSE_MATERIALIZATION")
    _stop(cfg["current_state"]["canonical_answerability_change"] is False, "TASK199A_NO_FALSE_ANSWERABILITY")
    _stop(all(v is False for v in cfg["remote_effects"].values()), "TASK199A_REMOTE_EFFECT")

    return {
        "schema": "TASK199A_IBGE_TERRITORIAL_FOUNDATION_VALIDATION_V1",
        "status": "PASS_SOURCE_FOUNDATION_READY_BINARY_INGESTION_PENDING",
        "source_count": len(sources),
        "first_binary_target": cfg["binary_acquisition_order"][0],
        "territory_profile_materialized": False,
        "canonical_answerability_change": False,
        "network": False,
        "drive_write": False,
        "serving": False,
    }


def binary_acquisition_plan(config_path: str | Path = DEFAULT_CONFIG) -> list[dict[str, Any]]:
    cfg = _load(config_path)
    sources = {row["id"]: row for row in cfg["official_source_registry"]}
    return [
        {
            "order": i + 1,
            "source_id": source_id,
            "url": sources[source_id]["url"],
            "status": sources[source_id]["status"],
        }
        for i, source_id in enumerate(cfg["binary_acquisition_order"])
    ]

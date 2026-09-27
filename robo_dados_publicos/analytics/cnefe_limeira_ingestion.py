from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/task199b_cnefe_limeira_ingestion.v1.json"


class Task199BStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task199BStop(code)


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_cnefe_ingestion(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    cfg = load_config(path)

    _stop(cfg["schema"] == "TASK199B_CNEFE_LIMEIRA_INGESTION_V1", "TASK199B_SCHEMA")
    _stop(cfg["scope"]["ibge_code_7"] == "3526902", "TASK199B_IBGE_CODE")
    _stop(cfg["scope"]["municipality"] == "Limeira", "TASK199B_MUNICIPALITY")

    archive = cfg["archive"]
    member = cfg["member"]
    _stop(archive["bytes"] == 3486586, "TASK199B_ARCHIVE_BYTES")
    _stop(
        archive["sha256"] == "ab73250df889effcb01ddc2d060bddd3252e995468e97ef93b048564763626a7",
        "TASK199B_ARCHIVE_SHA",
    )
    _stop(archive["member_count"] == 1, "TASK199B_ARCHIVE_MEMBER_COUNT")

    _stop(member["filename"] == "3526902_LIMEIRA.csv", "TASK199B_MEMBER_NAME")
    _stop(member["bytes"] == 26082570, "TASK199B_MEMBER_BYTES")
    _stop(
        member["sha256"] == "8adb17d18a8c0a4de9e6d48b31ed63f74e0bfde27f11f63154c17456d35218b3",
        "TASK199B_MEMBER_SHA",
    )
    _stop(member["rows"] == 150450, "TASK199B_ROWS")
    _stop(member["columns"] == 34, "TASK199B_COLUMNS")
    _stop(member["expected_identity"]["COD_UF"] == "35", "TASK199B_UF")
    _stop(member["expected_identity"]["COD_MUNICIPIO"] == "3526902", "TASK199B_MUNI")

    geo = cfg["geography"]
    _stop(geo["unique_sector_codes"] == 724, "TASK199B_SECTOR_COUNT")
    _stop(geo["rows_with_latitude_longitude"] == 150450, "TASK199B_COORD_ROWS")
    _stop(geo["coordinate_coverage_rate"] == 1.0, "TASK199B_COORD_COVERAGE")

    example = cfg["rafael_candidate_example"]
    _stop(example["COD_SETOR"] == "352690205000136P", "TASK199B_RAFFAEL_SECTOR_CANDIDATE")
    _stop(example["status"] == "CANDIDATE_ONLY_NOT_CANONICAL_SCHOOL_JOIN", "TASK199B_RAFFAEL_GUARD")

    adj = cfg["adjudication"]
    _stop(adj["cnefe_ingested"] is True, "TASK199B_CNEFE_INGESTED")
    _stop(adj["school_to_sector_crosswalk_materialized"] is False, "TASK199B_NO_FALSE_CROSSWALK")
    _stop(adj["territory_profile_materialized"] is False, "TASK199B_NO_FALSE_TERRITORY")
    _stop(adj["canonical_answerability_change"] is False, "TASK199B_NO_FALSE_ANSWERABILITY")

    guards = set(cfg["guards"])
    required_guards = {
        "SCHOOL_NAME_NE_CANONICAL_IDENTITY_WHEN_INEP_CODE_AVAILABLE",
        "CNEFE_ESTABLISHMENT_TEXT_NE_OFFICIAL_SCHOOL_ROSTER_IDENTITY",
        "SCHOOL_LOCATION_CONTEXT_NE_STUDENT_SOCIOECONOMIC_PROFILE",
        "MISSING_GEOGRAPHY_NE_ZERO",
    }
    _stop(required_guards <= guards, "TASK199B_GUARDS")
    _stop(all(v is False for v in cfg["remote_effects"].values()), "TASK199B_REMOTE_EFFECT")

    return {
        "schema": "TASK199B_CNEFE_LIMEIRA_INGESTION_VALIDATION_V1",
        "status": "PASS_CNEFE_RAW_AND_MEMBER_CUSTODY_PROVEN_CROSSWALK_PENDING",
        "archive_sha256": archive["sha256"],
        "member_sha256": member["sha256"],
        "row_count": member["rows"],
        "sector_count": geo["unique_sector_codes"],
        "school_candidate_rows": cfg["establishments"]["clear_municipal_school_name_candidate_rows"],
        "school_to_sector_crosswalk_materialized": False,
        "territory_profile_materialized": False,
        "canonical_answerability_change": False,
    }

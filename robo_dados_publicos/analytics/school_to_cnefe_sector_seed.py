from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/task199b_school_to_cnefe_sector_strong_seed.v1.json"


class Task199BStrongSeedStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task199BStrongSeedStop(code)


def _load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_seed(config_path: str | Path = DEFAULT_CONFIG) -> list[dict[str, str]]:
    cfg = _load(config_path)
    path = ROOT / cfg["seed_fixture"]["path"]
    _stop(path.exists(), "TASK199B_STRONG_SEED_FIXTURE_MISSING")
    _stop(_sha(path) == cfg["seed_fixture"]["sha256"], "TASK199B_STRONG_SEED_SHA")
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def validate_strong_seed(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    cfg = _load(config_path)
    rows = load_seed(config_path)

    _stop(cfg["schema"] == "TASK199B_SCHOOL_TO_CNEFE_SECTOR_STRONG_SEED_V1", "TASK199B_STRONG_SEED_SCHEMA")
    _stop(cfg["scope"]["ibge_code_7"] == "3526902", "TASK199B_STRONG_SEED_MUNICIPALITY")
    _stop(len(rows) == 14, "TASK199B_STRONG_SEED_ROW_COUNT")
    _stop(len({r["codigo_inep"] for r in rows}) == 14, "TASK199B_STRONG_SEED_INEP_UNIQUE")
    _stop(len({r["cnefe_cod_setor"] for r in rows}) == 14, "TASK199B_STRONG_SEED_SECTOR_UNIQUE")
    _stop(all(r["identity_status"] == "PROVEN_SEED" for r in rows), "TASK199B_STRONG_SEED_STATUS")
    _stop(
        all(r["match_strength"] == "STRONG_EXACT_STREET_NUMBER_PLUS_COMPATIBLE_SCHOOL_DESCRIPTION" for r in rows),
        "TASK199B_STRONG_SEED_STRENGTH",
    )
    _stop(
        all(r["sme_current_street"] == r["cnefe_street"] and r["sme_current_number"] == r["cnefe_number"] for r in rows),
        "TASK199B_STRONG_SEED_ADDRESS_EXACT",
    )
    _stop("35470600" not in {r["codigo_inep"] for r in rows}, "TASK199B_RAFAEL_MUST_NOT_PROMOTE")

    adj = cfg["adjudication"]
    _stop(adj["full_69_school_crosswalk_materialized"] is False, "TASK199B_NO_FALSE_69")
    _stop(adj["territory_profile_materialized"] is False, "TASK199B_NO_FALSE_TERRITORY")
    _stop(adj["canonical_answerability_change"] is False, "TASK199B_NO_FALSE_ANSWERABILITY")

    guards = set(cfg["guards"])
    for guard in {
        "NAME_ONLY_NE_IDENTITY",
        "FUZZY_MATCH_NE_CANONICAL_IDENTITY",
        "SCHOOL_LOCATION_CONTEXT_NE_STUDENT_SOCIOECONOMIC_PROFILE",
        "PARTIAL_CROSSWALK_NE_FULL_NETWORK_COVERAGE",
    }:
        _stop(guard in guards, f"TASK199B_MISSING_GUARD_{guard}")

    _stop(all(v is False for v in cfg["remote_effects"].values()), "TASK199B_STRONG_SEED_REMOTE_EFFECT")

    return {
        "schema": "TASK199B_SCHOOL_TO_CNEFE_SECTOR_STRONG_SEED_VALIDATION_V1",
        "status": "PASS_PARTIAL_STRONG_SEED_14_OF_40",
        "row_count": len(rows),
        "unique_sector_count": len({r["cnefe_cod_setor"] for r in rows}),
        "full_69_school_crosswalk_materialized": False,
        "territory_profile_materialized": False,
        "canonical_answerability_change": False,
    }

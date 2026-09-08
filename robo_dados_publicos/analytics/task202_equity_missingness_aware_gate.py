from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Mapping

from robo_dados_publicos.analytics.observatory_knowledge_pack import question_answerability
from robo_dados_publicos.analytics.observatory_products import build_territory_profile
from robo_dados_publicos.analytics.task199f_same_parity_address_bracket import (
    held_after_task199f,
    territory_rows,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task202_equity_missingness_aware_gate.v1.json"
ANSWERABILITY_V3 = ROOT / "config/observatory_semantic_answerability.v3.json"
ANSWERABILITY_V4_OVERLAY = ROOT / "config/observatory_semantic_answerability.v4.overlay.json"


class Task202Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task202Stop(code)


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK202_EQUITY_MISSINGNESS_AWARE_GATE_V1", "TASK202_SCHEMA")
    _stop(obj.get("issue") == 644, "TASK202_ISSUE")
    _stop(obj.get("base_main_sha") == "074c5415d9b71312692a4e034ff5a020406358b3", "TASK202_BASE")
    cov = obj["coverage"]
    _stop(cov["active_school_denominator"] == 69, "TASK202_DENOM")
    _stop(cov["strong_links"] == 59, "TASK202_LINKS")
    _stop(cov["held"] == 10, "TASK202_HELD")
    _stop(abs(float(cov["rate"]) - 59 / 69) < 0.000001, "TASK202_RATE")
    _stop(float(cov["rate"]) >= float(cov["minimum_rate"]), "TASK202_RATE_MIN")
    _stop(cov["full_network"] is False, "TASK202_NOT_FULL")
    roster = obj["held_roster"]
    _stop(roster["drive_id"] == "1E_gMOxkvgaQpJ_mgI8GQeu9usQxyWeqN", "TASK202_HELD_DRIVE")
    _stop(roster["sha256"] == "e99ccaf6e091c66a3a49845a003da4402651f74cd3df6a1cf1003700f163ded6", "TASK202_HELD_SHA")
    _stop(roster["bytes"] == 2651, "TASK202_HELD_BYTES")
    _stop(len(roster["codes"]) == 10 and len(set(roster["codes"])) == 10, "TASK202_HELD_CODES")
    _stop(
        obj["capability"]["id"]
        == "SCHOOL_TO_SECTOR_LINK_SUBSTANTIAL_COVERAGE_WITH_EXPLICIT_MISSINGNESS",
        "TASK202_CAPABILITY",
    )
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK202_REMOTE")
    return obj


def validated_coverage(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(path)
    rows = territory_rows()
    linked = {
        str(row["school_code"])
        for row in rows
        if row.get("geo_level") == "SCHOOL_LOCATION_CENSUS_SECTOR"
    }
    held_rows = held_after_task199f()
    held = {str(row["codigo_inep"]) for row in held_rows}
    expected_held = set(obj["held_roster"]["codes"])
    _stop(len(linked) == obj["coverage"]["strong_links"], "TASK202_OBSERVED_LINKS")
    _stop(len(held) == obj["coverage"]["held"], "TASK202_OBSERVED_HELD")
    _stop(held == expected_held, "TASK202_HELD_ROSTER_DRIFT")
    _stop(not (linked & held), "TASK202_LINK_HELD_OVERLAP")
    _stop(len(linked | held) == obj["coverage"]["active_school_denominator"], "TASK202_NETWORK_PARTITION")
    _stop(all(row.get("promotion_status") == "HELD" for row in held_rows), "TASK202_HELD_STATUS")
    return {
        "strong_links": len(linked),
        "held": len(held),
        "denominator": len(linked | held),
        "coverage_rate": len(linked) / len(linked | held),
        "linked_codes": sorted(linked),
        "held_codes": sorted(held),
        "unresolved_promoted": 0,
        "full_network": False,
    }


def build_task202_territory_profile(
    *,
    generated_at: str,
    software_version: str,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    obj = load_contract(contract_path)
    coverage = validated_coverage(contract_path)
    _stop(coverage["strong_links"] >= 59, "TASK202_MIN_LINKS")
    _stop(coverage["coverage_rate"] >= obj["coverage"]["minimum_rate"], "TASK202_MIN_COVERAGE")
    capabilities = [
        "CENSUS_SECTOR_CONTEXT",
        "MUNICIPAL_DEMOGRAPHY",
        "OFFICIAL_INCOME_DICTIONARY",
        "SCHOOL_TO_SECTOR_LINK_PARTIAL",
        "SCHOOL_TO_SECTOR_LINK_COVERAGE_59_OF_69",
        "SCHOOL_TO_SECTOR_LINK_SUBSTANTIAL_COVERAGE_WITH_EXPLICIT_MISSINGNESS",
        "SECTOR_INCOME_CONTEXT",
    ]
    _stop("SCHOOL_TO_SECTOR_LINK_FULL_NETWORK" not in capabilities, "TASK202_NO_FULL_CAPABILITY")
    product = build_territory_profile(
        territory_rows(),
        generated_at=generated_at,
        software_version=software_version,
        capabilities=capabilities,
    )
    _stop(product["row_count"] == 247, "TASK202_ROWS")
    return product


def current_answerability_config_v4() -> dict[str, Any]:
    base = json.loads(ANSWERABILITY_V3.read_text(encoding="utf-8"))
    overlay = json.loads(ANSWERABILITY_V4_OVERLAY.read_text(encoding="utf-8"))
    _stop(overlay.get("schema") == "OBSERVATORY_SEMANTIC_ANSWERABILITY_OVERLAY_V1", "TASK202_OVERLAY_SCHEMA")
    _stop(overlay.get("version") == 4, "TASK202_OVERLAY_VERSION")
    _stop(overlay.get("base_config") == "config/observatory_semantic_answerability.v3.json", "TASK202_OVERLAY_BASE")
    _stop(set(overlay.get("replace_recipes", {})) == {"EQUITY_CONTEXT"}, "TASK202_OVERLAY_SCOPE")
    _stop(all(v is False for v in overlay["remote_effects"].values()), "TASK202_OVERLAY_REMOTE")
    base["version"] = 4
    base["task"] = "TASK_202_EQUITY_MISSINGNESS_AWARE_GATE"
    base["prior_current_config"] = "config/observatory_semantic_answerability.v3.json"
    base["current_overlay"] = "config/observatory_semantic_answerability.v4.overlay.json"
    base["recipes"]["EQUITY_CONTEXT"] = overlay["replace_recipes"]["EQUITY_CONTEXT"]
    return base


def current_question_answerability_v4(
    products: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    config = current_answerability_config_v4()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8") as handle:
        json.dump(config, handle, ensure_ascii=False, sort_keys=True)
        handle.flush()
        return question_answerability(products, answerability_path=handle.name)


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(path)
    coverage = validated_coverage(path)
    config = current_answerability_config_v4()
    equity = config["recipes"]["EQUITY_CONTEXT"]
    _stop(len(equity["signals"]) == 2, "TASK202_EQUITY_SIGNALS")
    metric = equity["signals"][0]
    territory = equity["signals"][1]
    _stop(metric["match"] == "ALL", "TASK202_EQUITY_METRIC_ALL")
    _stop(set(metric["ids"]) == {"PPI_SHARE", "INSE", "SPECIAL_EDUCATION_ENROLLMENT"}, "TASK202_EQUITY_METRICS")
    required = set(territory["required_capabilities"])
    _stop("CENSUS_SECTOR_CONTEXT" in required, "TASK202_SECTOR_CONTEXT")
    _stop(obj["capability"]["id"] in required, "TASK202_SUBSTANTIAL_GATE")
    _stop("SCHOOL_TO_SECTOR_LINK_FULL_NETWORK" not in required, "TASK202_REMOVE_FULL_GATE")
    return {
        "schema": "TASK202_EQUITY_MISSINGNESS_AWARE_GATE_VALIDATION_V1",
        "status": "PASS",
        "strong_links": coverage["strong_links"],
        "held": coverage["held"],
        "coverage_rate": coverage["coverage_rate"],
        "unresolved_promoted": coverage["unresolved_promoted"],
        "full_network": False,
        "answerability_version": 4,
        "network": False,
        "drive_write": False,
    }

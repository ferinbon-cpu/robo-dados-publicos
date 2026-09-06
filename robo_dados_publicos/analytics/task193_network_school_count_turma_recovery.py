from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from robo_dados_publicos.analytics.observatory_knowledge_pack import fused_source_rows
from robo_dados_publicos.analytics.observatory_products import build_school_indicator_series
from robo_dados_publicos.analytics.task191_annual_education_per_enrollment import school_overlay_row
from robo_dados_publicos.analytics.task192_ipca_real_education_expenditure import build_task192_products


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task193_network_school_count_turma_recovery.v1.json"


class Task193Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task193Stop(code)


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK193_NETWORK_SCHOOL_COUNT_TURMA_RECOVERY_V1", "TASK193_SCHEMA")
    _stop(obj.get("mode") == "T0_OFFLINE_EXISTING_CUSTODY_FAIL_CLOSED", "TASK193_MODE")
    scope = obj["network_scope"]
    schools = obj["school_count_source"]
    classes = obj["class_count_recovery"]
    _stop(scope["period"] == "2025", "TASK193_PERIOD")
    _stop(scope["scope_id"] == "3526902:MUNICIPAL:CURRENT_69_UNITS", "TASK193_SCOPE")
    _stop(schools["value"] == 69, "TASK193_SCHOOL_COUNT")
    _stop(schools["early_years_units"] + schools["early_childhood_only_units"] == 69, "TASK193_40_PLUS_29")
    _stop(classes["canonical_materialization_authorized"] is False, "TASK193_CLASS_COUNT_MUST_REMAIN_BLOCKED")
    _stop(classes["official_md5"] == "438A3A3FC37F28E7E50E57D7CD8B9DAC", "TASK193_TURMA_MD5")
    _stop(classes["direct_validated_subgroup"]["units"] == 29, "TASK193_EI29_UNITS")
    _stop(classes["direct_validated_subgroup"]["units_found_in_tabela_turma"] == 29, "TASK193_EI29_FOUND")
    _stop(classes["direct_validated_subgroup"]["class_count"] == 294, "TASK193_EI29_CLASSES")
    _stop(classes["remaining_required_subgroup"]["units"] == 40, "TASK193_AI40_UNITS")
    _stop(classes["remaining_required_subgroup"]["class_count"] is None, "TASK193_AI40_COUNT_MUST_BE_UNKNOWN")
    _stop(classes["network_class_count"] is None, "TASK193_NETWORK_CLASS_COUNT_MUST_BE_UNKNOWN")
    _stop(classes["proxy_forbidden"] is True, "TASK193_PROXY_GUARD")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK193_REMOTE_EFFECT")
    return obj


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(path)
    expected = obj["expected_semantic_transition"]
    _stop(expected["missing_after"] == ["CLASS_COUNT"], "TASK193_EXPECTED_MISSING")
    _stop(expected["school_indicator_rows_after"] == 1019, "TASK193_EXPECTED_SCHOOL_ROWS")
    _stop(expected["fiscal_rows_must_remain"] == 61, "TASK193_EXPECTED_FISCAL_ROWS")
    return {
        "schema": "TASK193_NETWORK_SCHOOL_COUNT_TURMA_RECOVERY_VALIDATION_V1",
        "status": "PASS",
        "school_count": 69,
        "class_count": None,
        "ei29_direct_class_count": 294,
        "official_turma_md5": obj["class_count_recovery"]["official_md5"],
        "network": False,
        "drive_write": False,
    }


def school_count_overlay_row(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(path)
    source = obj["school_count_source"]
    scope = obj["network_scope"]
    return {
        "scope_level": scope["scope_level"],
        "scope_id": scope["scope_id"],
        "network": "MUNICIPAL",
        "period": scope["period"],
        "indicator_id": "SCHOOL_COUNT",
        "indicator_name": "Estabelecimentos municipais ativos na rede de Limeira",
        "value": source["value"],
        "unit": source["unit"],
        "context": (
            "Contagem de estabelecimentos municipais ativos em 2025 no universo atual: "
            "40 unidades com anos iniciais + 29 unidades exclusivamente de Educação Infantil."
        ),
        "observation_period": "2025",
        "source_family": source["source_family"],
        "source_sha256": source["xlsx_sha256"],
        "provenance_ref": (
            "FILE_LIBRARY:CAMADA_ANALITICA_V06_40_ESCOLAS_V08.xlsx"
            "#81 Censo 69 2018-25:2025:ACTIVE_MUNICIPAL_ESTABLISHMENTS"
        ),
        "quality_status": source["quality_status"],
        "caution": (
            "SCHOOL_COUNT_ACTIVE_ESTABLISHMENTS_NE_BUILDINGS;"
            "CURRENT_69_UNIT_PANEL_SCOPE_EXPLICIT;"
            "69_EQUALS_40_PLUS_29"
        ),
    }


def class_count_gap(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(path)
    recovery = obj["class_count_recovery"]
    return {
        "metric_id": "CLASS_COUNT",
        "status": "BLOCKED_PRIMARY_RAW_RECOVERY_REQUIRED",
        "network_value": None,
        "official_source_file": recovery["official_source_file"],
        "official_md5": recovery["official_md5"],
        "validated_subgroup": recovery["direct_validated_subgroup"],
        "remaining_required_subgroup": recovery["remaining_required_subgroup"],
        "secondary_web_mirror_status": recovery["secondary_web_mirror_status"],
        "proxy_forbidden": True,
        "next_action": obj["next_action"],
    }


def build_task193_products(
    *,
    generated_at: str,
    software_version: str,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    validation = validate_contract(contract_path)
    base = fused_source_rows()
    school = build_school_indicator_series(
        [
            *base["school_rows"],
            school_overlay_row(),
            school_count_overlay_row(contract_path),
        ],
        generated_at=generated_at,
        software_version=software_version,
    )
    previous = build_task192_products(
        generated_at=generated_at,
        software_version=software_version,
    )
    fiscal = previous["FISCAL_SERIES"]
    _stop(fiscal["row_count"] == 61, "TASK193_FISCAL_ROW_COUNT")
    school["overlay_scope"] = {
        "base_task183_rows": len(base["school_rows"]),
        "task191_enrollment_rows": 1,
        "task193_school_count_rows": 1,
        "period": "2025",
        "scope_id": "3526902:MUNICIPAL:CURRENT_69_UNITS",
        "basic_education_enrollment": 22788,
        "school_count": 69,
        "class_count_materialized": False,
    }
    return {
        "validation": validation,
        "SCHOOL_INDICATOR_SERIES": school,
        "FISCAL_SERIES": fiscal,
        "CLASS_COUNT_GAP": class_count_gap(contract_path),
    }

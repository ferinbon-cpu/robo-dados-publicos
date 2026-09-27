from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from robo_dados_publicos.analytics.observatory_knowledge_pack import fused_source_rows
from robo_dados_publicos.analytics.observatory_products import build_school_indicator_series
from robo_dados_publicos.analytics.task191_annual_education_per_enrollment import school_overlay_row
from robo_dados_publicos.analytics.task193_network_school_count_turma_recovery import (
    build_task193_products,
    school_count_overlay_row,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task194k_miest_class_count_materialization.v1.json"


class Task194KStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task194KStop(code)


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK194K_MIEST_CLASS_COUNT_MATERIALIZATION_V1", "TASK194K_SCHEMA")
    _stop(obj.get("mode") == "T0_OFFLINE_USER_MEDIATED_OFFICIAL_ARTIFACT_MATERIALIZATION", "TASK194K_MODE")
    _stop(obj.get("issue") == 621, "TASK194K_ISSUE")
    _stop(obj.get("base_main_sha") == "031c9597ab801a98d083c56579fe2a9f04f02290", "TASK194K_BASE_MAIN")

    provenance = obj["provenance"]
    _stop(
        provenance["classification"] == "USER_MEDIATED_OFFICIAL_DOWNLOAD_CANDIDATE_VALIDATED_OFFLINE",
        "TASK194K_PROVENANCE",
    )
    _stop(provenance["automated_task194j_transport_result"] == "HTTP_403_FORBIDDEN", "TASK194K_194J_HISTORY")
    _stop(provenance["raw_files_committed"] is False, "TASK194K_RAW_REPO")
    _stop(provenance["raw_files_persisted_by_task"] is False, "TASK194K_RAW_PERSISTENCE")

    artifacts = obj["artifacts"]
    csv = artifacts["miests_ciclo_2025_12"]
    dictionary = artifacts["dictionary"]
    _stop(csv["sha256"] == "72577ea79fcdacd22f96daf114b25fa49f623bd3496ca0bba619e43c291f2b6b", "TASK194K_CSV_SHA")
    _stop(dictionary["sha256"] == "4444763557f26e76164a331a495601b042ce161f1fa4eb0ba26a93e163392391", "TASK194K_DICT_SHA")
    _stop(csv["row_count"] == 30244 and csv["column_count"] == 183, "TASK194K_CSV_SHAPE")
    _stop(dictionary["field"] == "CLASSESEC", "TASK194K_DICT_FIELD")
    _stop(dictionary["official_label"] == "CLASSES EDUCAÇÃO COMPLIMENTAR", "TASK194K_DICT_LABEL")
    _stop(dictionary["normalized_semantic"] == "CLASSES_EDUCACAO_COMPLEMENTAR", "TASK194K_DICT_SEMANTIC")

    scope = obj["network_scope"]
    _stop(scope["period"] == "2025", "TASK194K_PERIOD")
    _stop(scope["scope_id"] == "3526902:MUNICIPAL:CURRENT_69_UNITS", "TASK194K_SCOPE")
    _stop(scope["municipal_school_rows"] == 69, "TASK194K_69")
    _stop(scope["unique_inep_codes"] == 69, "TASK194K_UNIQUE_69")

    rec = obj["reconciliation"]
    _stop(rec["task180_ai40_expected_codes"] == 40, "TASK194K_AI40_EXPECTED")
    _stop(rec["task180_ai40_codes_found"] == 40 and rec["ai40_missing_codes"] == 0, "TASK194K_AI40_FOUND")
    _stop(rec["complement_ei29_units"] == 29, "TASK194K_EI29_UNITS")
    _stop(rec["ai40_curricular_class_count"] == 816, "TASK194K_AI40_COUNT")
    _stop(rec["ei29_curricular_class_count"] == 294, "TASK194K_EI29_COUNT")
    _stop(rec["independently_validated_task193_ei29_class_count"] == 294, "TASK194K_EI29_INDEPENDENT")
    _stop(rec["ei29_exact_reconciliation"] is True, "TASK194K_EI29_RECONCILIATION")
    _stop(rec["network_curricular_class_count"] == 1110, "TASK194K_NETWORK_COUNT")
    _stop(rec["ai40_curricular_class_count"] + rec["ei29_curricular_class_count"] == rec["network_curricular_class_count"], "TASK194K_SUM")

    classes = obj["curricular_class_count"]
    _stop(classes["metric_id"] == "CLASS_COUNT", "TASK194K_METRIC")
    _stop(classes["value"] == 1110, "TASK194K_VALUE")
    _stop(classes["source_family"] == "SEDUC_SP_MIEST", "TASK194K_SOURCE_FAMILY")
    _stop(classes["stage_totals"] == {
        "EDUCACAO_INFANTIL": 538,
        "ENSINO_FUNDAMENTAL": 565,
        "EJA": 7,
        "OTHER_CURRICULAR_NONZERO": 0,
    }, "TASK194K_STAGE_TOTALS")
    _stop(sum(classes["stage_totals"].values()) == 1110, "TASK194K_STAGE_SUM")
    comp = classes["complementary_classes_excluded"]
    _stop(comp["field"] == "CLASSESEC" and comp["value"] == 131, "TASK194K_COMP_EXCLUDED")
    _stop(comp["dictionary_semantic"] == "CLASSES_EDUCACAO_COMPLEMENTAR", "TASK194K_COMP_SEMANTIC")
    _stop(classes["proxy_used"] is False, "TASK194K_PROXY")

    transition = obj["expected_semantic_transition"]
    _stop(transition["network_q1_before"] == "MATERIALIZED_PARTIAL", "TASK194K_Q1_BEFORE")
    _stop(transition["network_q1_after"] == "MATERIALIZED_ANSWERABLE", "TASK194K_Q1_AFTER")
    _stop(transition["missing_after"] == [], "TASK194K_NO_MISSING")
    _stop(transition["school_indicator_rows_after"] == 1020, "TASK194K_SCHOOL_ROWS")
    _stop(transition["fiscal_rows_must_remain"] == 61, "TASK194K_FISCAL_ROWS")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK194K_REMOTE_EFFECT")
    return obj


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(path)
    return {
        "schema": "TASK194K_MIEST_CLASS_COUNT_MATERIALIZATION_VALIDATION_V1",
        "status": "PASS",
        "class_count": obj["curricular_class_count"]["value"],
        "school_count": obj["network_scope"]["municipal_school_rows"],
        "ei29_class_count": obj["reconciliation"]["ei29_curricular_class_count"],
        "ai40_class_count": obj["reconciliation"]["ai40_curricular_class_count"],
        "complementary_classes_excluded": obj["curricular_class_count"]["complementary_classes_excluded"]["value"],
        "network": False,
        "drive_write": False,
    }


def class_count_overlay_row(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(path)
    metric = obj["curricular_class_count"]
    scope = obj["network_scope"]
    return {
        "scope_level": scope["scope_level"],
        "scope_id": scope["scope_id"],
        "network": "MUNICIPAL",
        "period": scope["period"],
        "indicator_id": "CLASS_COUNT",
        "indicator_name": "Turmas curriculares da educação básica na rede municipal de Limeira",
        "value": metric["value"],
        "unit": metric["unit"],
        "context": (
            "Contagem direta no MIEST Ciclo 12/2025: 538 turmas de Educação Infantil, "
            "565 de Ensino Fundamental e 7 de EJA. As 131 CLASSESEC são Educação "
            "Complementar segundo o dicionário oficial e ficam fora deste indicador."
        ),
        "observation_period": scope["period"],
        "source_family": metric["source_family"],
        "source_sha256": obj["artifacts"]["miests_ciclo_2025_12"]["sha256"],
        "provenance_ref": (
            "TASK_194K_ISSUE_621#USER_MEDIATED_OFFICIAL_MIEST_12_2025;"
            "DICT_SHA256_4444763557f26e76164a331a495601b042ce161f1fa4eb0ba26a93e163392391"
        ),
        "quality_status": "VALIDATED",
        "caution": (
            "USER_MEDIATED_OFFICIAL_DOWNLOAD_CANDIDATE_VALIDATED_OFFLINE;"
            "CLASS_COUNT_NE_ATU_PROXY;"
            "EI29_294_INDEPENDENT_RECONCILIATION;"
            "CLASSESEC_131_COMPLEMENTARY_EXCLUDED;"
            "TASK194J_HTTP403_HISTORY_PRESERVED"
        ),
    }


def build_task194k_products(
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
            school_count_overlay_row(),
            class_count_overlay_row(contract_path),
        ],
        generated_at=generated_at,
        software_version=software_version,
    )
    previous = build_task193_products(
        generated_at=generated_at,
        software_version=software_version,
    )
    fiscal = previous["FISCAL_SERIES"]
    _stop(fiscal["row_count"] == 61, "TASK194K_FISCAL_ROW_COUNT")
    _stop(school["row_count"] == 1020, "TASK194K_SCHOOL_ROW_COUNT")
    school["overlay_scope"] = {
        "base_task183_rows": len(base["school_rows"]),
        "task191_enrollment_rows": 1,
        "task193_school_count_rows": 1,
        "task194k_class_count_rows": 1,
        "period": "2025",
        "scope_id": "3526902:MUNICIPAL:CURRENT_69_UNITS",
        "basic_education_enrollment": 22788,
        "school_count": 69,
        "class_count": 1110,
        "class_count_materialized": True,
        "education_complementary_classes_excluded": 131,
    }
    return {
        "validation": validation,
        "SCHOOL_INDICATOR_SERIES": school,
        "FISCAL_SERIES": fiscal,
        "CLASS_COUNT": {
            "status": "MATERIALIZED_VALIDATED",
            "network_value": 1110,
            "ai40": 816,
            "ei29": 294,
            "complementary_excluded": 131,
        },
    }

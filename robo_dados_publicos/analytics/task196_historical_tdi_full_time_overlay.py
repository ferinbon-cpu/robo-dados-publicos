from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from robo_dados_publicos.analytics.observatory_knowledge_pack import fused_source_rows
from robo_dados_publicos.analytics.observatory_products import build_school_indicator_series
from robo_dados_publicos.analytics.task191_annual_education_per_enrollment import school_overlay_row
from robo_dados_publicos.analytics.task193_network_school_count_turma_recovery import school_count_overlay_row
from robo_dados_publicos.analytics.task194k_miest_class_count_materialization import (
    build_task194k_products,
    class_count_overlay_row,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task196_historical_tdi_full_time_overlay.v1.json"


class Task196Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task196Stop(code)


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK196_HISTORICAL_TDI_FULL_TIME_OVERLAY_V1", "TASK196_SCHEMA")
    _stop(obj.get("issue") == 631, "TASK196_ISSUE")
    _stop(obj.get("base_main_sha") == "799fad7316765ccd654322526135fc212eb8882a", "TASK196_BASE")
    _stop(obj["canonical_asset"]["sha256"] == "0516868e06685aebe8254b11ca6488ef26b03dea61f927ff637840cf2a21e865", "TASK196_V08_SHA")
    _stop(obj["file_library_text_evidence"]["sha256"] is None, "TASK196_NO_FAKE_V56_SHA")
    _stop(obj["file_library_text_evidence"]["hash_status"] == "NOT_AVAILABLE_NOT_INVENTED", "TASK196_V56_HASH_STATUS")

    ft = obj["full_time_network_series"]
    _stop(ft["indicator_id"] == "FULL_TIME_SHARE", "TASK196_FT_METRIC")
    _stop(ft["scope_id"] == "3526902:MUNICIPAL:YEARS_INITIAL_ACTIVE_EDITION", "TASK196_FT_SCOPE")
    _stop(ft["stage_scope"] == "ANOS_INICIAIS", "TASK196_FT_STAGE")
    _stop(len(ft["rows"]) == 8, "TASK196_FT_ROWS")
    _stop([r["period"] for r in ft["rows"]] == [str(y) for y in range(2018, 2026)], "TASK196_FT_PERIODS")
    _stop([r["value"] for r in ft["rows"]] == [11.1,13.2,11.5,9.2,14.9,26.7,30.0,30.7], "TASK196_FT_VALUES")
    _stop(ft["rows"][0]["active_units"] == 77, "TASK196_2018_UNITS")
    _stop(all(r["active_units"] == 69 for r in ft["rows"][1:]), "TASK196_2019_2025_UNITS")

    tdi = obj["tdi_network_anchor_series"]
    _stop(tdi["indicator_id"] == "TDI", "TASK196_TDI_METRIC")
    _stop(tdi["scope_id"] == "3526902:MUNICIPAL:YEARS_INITIAL_TOTAL_LOCATION", "TASK196_TDI_SCOPE")
    _stop(tdi["materialized_anchor_rows_only"] is True, "TASK196_TDI_ANCHOR_FLAG")
    _stop(
        [(r["period"], r["value"]) for r in tdi["rows"]]
        == [("2006",3.4),("2011",0.9),("2012",0.9),("2017",4.0),("2023",1.0),("2024",1.0),("2025",1.0)],
        "TASK196_TDI_ANCHORS",
    )

    exp = obj["expected_transition"]
    _stop(exp["school_indicator_rows_before"] == 1020, "TASK196_ROWS_BEFORE")
    _stop(exp["school_indicator_rows_after"] == 1035, "TASK196_ROWS_AFTER")
    _stop(exp["fiscal_rows_must_remain"] == 61, "TASK196_FISCAL_ROWS")
    _stop(set(exp["changed_questions"]) == {"NETWORK_Q2","LEARN_Q3"}, "TASK196_CHANGED_QUESTIONS")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK196_REMOTE_EFFECT")
    return obj


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(path)
    return {
        "schema": "TASK196_HISTORICAL_TDI_FULL_TIME_OVERLAY_VALIDATION_V1",
        "status": "PASS",
        "full_time_periods": len(obj["full_time_network_series"]["rows"]),
        "tdi_anchor_periods": len(obj["tdi_network_anchor_series"]["rows"]),
        "network": False,
        "drive_write": False,
    }


def full_time_overlay_rows(path: str | Path = DEFAULT_CONTRACT) -> list[dict[str, Any]]:
    obj = load_contract(path)
    src = obj["canonical_asset"]
    spec = obj["full_time_network_series"]
    rows = []
    for r in spec["rows"]:
        rows.append({
            "scope_level": spec["scope_level"],
            "scope_id": spec["scope_id"],
            "network": spec["network"],
            "period": r["period"],
            "indicator_id": "FULL_TIME_SHARE",
            "indicator_name": "Percentual de matrículas em tempo integral nos anos iniciais da rede municipal",
            "value": r["value"],
            "unit": spec["unit"],
            "context": (
                f"Rede municipal de Limeira; anos iniciais; conjunto de unidades que ofertava anos iniciais "
                f"na edição {r['period']}; unidades ativas no recorte={r['active_units']}; "
                f"matrículas anos iniciais={r['enrollment_ai']}."
            ),
            "observation_period": r["period"],
            "source_family": spec["source_family"],
            "source_sha256": src["sha256"],
            "provenance_ref": (
                "CAMADA_ANALITICA_V06_40_ESCOLAS_V08#CENSO_REDE_HISTORICA;"
                "FILE_LIBRARY:ESTUDO_V5_6(2).docx#APENDICE_G_TABELA_V5.6-G1"
            ),
            "quality_status": "READY_WITH_CAUTION",
            "caution": (
                "FILE_LIBRARY_MEDIATED_EXACT_TEXTUAL_VALUE;"
                "V08_CANONICAL_ASSET_SHA_PINNED;"
                "YEARS_INITIAL_ACTIVE_EDITION_SCOPE;"
                "2018_77_UNITS_NE_CURRENT_69_FIXED_PANEL"
            ),
        })
    return rows


def tdi_anchor_overlay_rows(path: str | Path = DEFAULT_CONTRACT) -> list[dict[str, Any]]:
    obj = load_contract(path)
    src = obj["canonical_asset"]
    spec = obj["tdi_network_anchor_series"]
    rows = []
    for r in spec["rows"]:
        rows.append({
            "scope_level": spec["scope_level"],
            "scope_id": spec["scope_id"],
            "network": spec["network"],
            "period": r["period"],
            "indicator_id": "TDI",
            "indicator_name": "Taxa de distorção idade-série da rede municipal nos anos iniciais",
            "value": r["value"],
            "unit": spec["unit"],
            "context": (
                "Dependência municipal; localização total; anos iniciais. "
                "A série oficial declarada cobre 2006–2025, mas esta materialização contém apenas "
                "os pontos explicitamente publicados em texto, sem interpolar anos intermediários."
            ),
            "observation_period": r["period"],
            "source_family": spec["source_family"],
            "source_sha256": src["sha256"],
            "provenance_ref": (
                "CAMADA_ANALITICA_V06_40_ESCOLAS_V08#TDI_COVERAGE;"
                "FILE_LIBRARY:ESTUDO_V5_6(1).docx#7.3_7.6"
            ),
            "quality_status": "READY_WITH_CAUTION",
            "caution": (
                "TDI_ANCHOR_ONLY_NOT_COMPLETE_ANNUAL_TABLE;"
                "NO_INTERPOLATION;"
                "FILE_LIBRARY_MEDIATED_EXACT_TEXTUAL_VALUE;"
                "V08_CANONICAL_ASSET_SHA_PINNED"
            ),
        })
    return rows


def build_task196_products(
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
            class_count_overlay_row(),
            *full_time_overlay_rows(contract_path),
            *tdi_anchor_overlay_rows(contract_path),
        ],
        generated_at=generated_at,
        software_version=software_version,
    )
    previous = build_task194k_products(
        generated_at=generated_at,
        software_version=software_version,
    )
    fiscal = previous["FISCAL_SERIES"]
    _stop(fiscal["row_count"] == 61, "TASK196_FISCAL_ROW_COUNT")
    _stop(school["row_count"] == 1035, "TASK196_SCHOOL_ROW_COUNT")
    school["overlay_scope"] = {
        "base_task183_rows": len(base["school_rows"]),
        "task191_enrollment_rows": 1,
        "task193_school_count_rows": 1,
        "task194k_class_count_rows": 1,
        "task196_full_time_network_rows": 8,
        "task196_tdi_network_anchor_rows": 7,
        "full_time_scope_id": "3526902:MUNICIPAL:YEARS_INITIAL_ACTIVE_EDITION",
        "tdi_scope_id": "3526902:MUNICIPAL:YEARS_INITIAL_TOTAL_LOCATION",
        "tdi_complete_annual_table_materialized": False,
    }
    return {
        "validation": validation,
        "SCHOOL_INDICATOR_SERIES": school,
        "FISCAL_SERIES": fiscal,
        "FULL_TIME_SHARE": {
            "status": "MATERIALIZED_HISTORICAL_NETWORK_SERIES",
            "period_count": 8,
            "first_value": 11.1,
            "last_value": 30.7,
            "change_pp_2018_2025": 19.6,
        },
        "TDI": {
            "status": "MATERIALIZED_OFFICIAL_NETWORK_ANCHORS",
            "anchor_period_count": 7,
            "series_declared_coverage": "2006-2025",
            "complete_annual_table_materialized": False,
        },
    }

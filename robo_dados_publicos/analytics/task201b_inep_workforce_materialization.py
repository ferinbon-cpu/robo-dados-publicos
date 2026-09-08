from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from robo_dados_publicos.analytics.observatory_knowledge_pack import fused_source_rows
from robo_dados_publicos.analytics.observatory_products import build_school_indicator_series
from robo_dados_publicos.analytics.task191_annual_education_per_enrollment import school_overlay_row
from robo_dados_publicos.analytics.task193_network_school_count_turma_recovery import school_count_overlay_row
from robo_dados_publicos.analytics.task194k_miest_class_count_materialization import class_count_overlay_row
from robo_dados_publicos.analytics.task196_historical_tdi_full_time_overlay import (
    full_time_overlay_rows,
    tdi_anchor_overlay_rows,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task201b_inep_workforce_materialization.v1.json"


class Task201BStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task201BStop(code)


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK201B_INEP_WORKFORCE_MATERIALIZATION_V1", "TASK201B_SCHEMA")
    _stop(obj.get("parent_issue") == 639, "TASK201B_ISSUE")
    _stop(obj.get("base_main_sha") == "c997529f76c817b3d11232475918c5e4e3d9f0a5", "TASK201B_BASE")
    src = obj["source"]
    _stop(src["zip_sha256"] == "a8a41fcd487e98dc26c9107dfd92f403641983b2737d50497bac3e47b4f051c8", "TASK201B_ZIP_SHA")
    _stop(src["xlsx_sha256"] == "af3a0f13731214730c4baa362bfc542c526c8c81d31c48e699919623c491462c", "TASK201B_XLSX_SHA")
    _stop(src["xlsx_md5"] == "07461C4FD19E120EF31945AF8A3D0625", "TASK201B_XLSX_MD5")
    _stop(src["official_manifest_md5_verified"] is True, "TASK201B_MANIFEST")
    _stop(obj["staff_count"]["value"] == 1280, "TASK201B_STAFF_COUNT")
    _stop(obj["staff_count"]["sheet"] == "2.2" and obj["staff_count"]["row"] == 3608, "TASK201B_STAFF_LOCATOR")
    bonds = obj["employment_bonds"]
    _stop(bonds["sheet"] == "2.6" and bonds["row"] == 3607, "TASK201B_BOND_LOCATOR")
    _stop(
        [(x["id"], x["value"]) for x in bonds["categories"]]
        == [
            ("CONCURSADO_EFETIVO_ESTAVEL", 681),
            ("CONTRATO_TEMPORARIO", 291),
            ("CONTRATO_TERCEIRIZADO", 0),
            ("CONTRATO_CLT", 400),
        ],
        "TASK201B_BOND_VALUES",
    )
    _stop(bonds["category_sum"] == 1372 and bonds["additive"] is False, "TASK201B_NON_ADDITIVE")
    sme = obj["sme_current_context"]
    _stop(sme["live_run_id"] == 34164903116, "TASK201B_SME_RUN")
    _stop(sme["unique_contracted_teachers"] == 842, "TASK201B_SME_UNIQUE")
    _stop(sme["assignment_rows"] == 843, "TASK201B_SME_ROWS")
    _stop(sme["canonical_staff_count"] is False, "TASK201B_SME_NOT_CANONICAL_TOTAL")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK201B_REMOTE")
    return obj


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(path)
    return {
        "schema": "TASK201B_INEP_WORKFORCE_MATERIALIZATION_VALIDATION_V1",
        "status": "PASS",
        "staff_count": obj["staff_count"]["value"],
        "bond_category_count": len(obj["employment_bonds"]["categories"]),
        "bond_category_sum_non_additive": obj["employment_bonds"]["category_sum"],
        "sme_current_contracted_teachers": obj["sme_current_context"]["unique_contracted_teachers"],
        "network": False,
        "drive_write": False,
    }


def workforce_overlay_rows(path: str | Path = DEFAULT_CONTRACT) -> list[dict[str, Any]]:
    obj = load_contract(path)
    src = obj["source"]
    scope_id = "3526902:MUNICIPAL:EDUCATION_BASIC_CLASSROOM_DOCENTES"
    provenance_base = (
        "USER_HANDOFF:sinopse_estatistica_censo_escolar_2025.zip;"
        f"XLSX_SHA256:{src['xlsx_sha256']}"
    )
    rows: list[dict[str, Any]] = [
        {
            "scope_level": "NETWORK",
            "scope_id": scope_id,
            "network": "MUNICIPAL",
            "period": "2025",
            "indicator_id": "STAFF_COUNT",
            "indicator_name": "Docentes únicos em efetiva regência na dependência municipal",
            "value": 1280,
            "unit": "COUNT",
            "context": (
                "Censo Escolar 2025, Limeira, dependência administrativa municipal. "
                "Docentes são indivíduos em efetiva regência de classe na data de referência. "
                "Não representa todos os trabalhadores da Educação."
            ),
            "observation_period": "2025",
            "source_family": "CENSO_ESCOLAR",
            "source_sha256": src["xlsx_sha256"],
            "provenance_ref": provenance_base + ";SHEET:2.2;ROW:3608;MUNICIPAL_COLUMN",
            "quality_status": "VALIDATED",
            "caution": (
                "DOCENTES_NE_ALL_EDUCATION_WORKERS;"
                "EXCLUDES_COMPLEMENTARY_ACTIVITY_AND_AEE_CLASS_TEACHERS;"
                "EXCLUDES_EARLY_CHILDHOOD_AUXILIARIES"
            ),
        },
        {
            "scope_level": "NETWORK",
            "scope_id": scope_id,
            "network": "MUNICIPAL",
            "period": "2025",
            "indicator_id": "EMPLOYMENT_BOND",
            "indicator_name": "Tipos de vínculo funcional dos docentes municipais",
            "value": 4,
            "unit": "CATEGORY_COUNT",
            "context": (
                "Quatro categorias publicadas pelo Inep para docentes da dependência municipal: "
                "concursado/efetivo/estável=681; contrato temporário=291; "
                "contrato terceirizado=0; contrato CLT=400. As contagens não são aditivas, "
                "pois o mesmo docente pode possuir mais de um vínculo."
            ),
            "bond_counts": {
                "CONCURSADO_EFETIVO_ESTAVEL": 681,
                "CONTRATO_TEMPORARIO": 291,
                "CONTRATO_TERCEIRIZADO": 0,
                "CONTRATO_CLT": 400,
            },
            "observation_period": "2025",
            "source_family": "CENSO_ESCOLAR",
            "source_sha256": src["xlsx_sha256"],
            "provenance_ref": provenance_base + ";SHEET:2.6;ROW:3607;MUNICIPAL_BOND_COLUMNS",
            "quality_status": "VALIDATED",
            "caution": "BOND_COUNTS_NON_ADDITIVE;SAME_DOCENTE_MAY_APPEAR_IN_MULTIPLE_BOND_CATEGORIES",
        },
    ]
    labels = {
        "CONCURSADO_EFETIVO_ESTAVEL": "Docentes concursados/efetivos/estáveis",
        "CONTRATO_TEMPORARIO": "Docentes com contrato temporário",
        "CONTRATO_TERCEIRIZADO": "Docentes com contrato terceirizado",
        "CONTRATO_CLT": "Docentes com contrato CLT",
    }
    for bond in obj["employment_bonds"]["categories"]:
        bond_id = bond["id"]
        rows.append(
            {
                "scope_level": "NETWORK",
                "scope_id": scope_id,
                "network": "MUNICIPAL",
                "period": "2025",
                "indicator_id": f"EMPLOYMENT_BOND_{bond_id}_COUNT",
                "indicator_name": labels[bond_id],
                "value": bond["value"],
                "unit": "COUNT",
                "context": (
                    "Contagem única dentro desta célula vínculo funcional x dependência municipal. "
                    "Não somar as categorias para reconstruir o total de docentes."
                ),
                "observation_period": "2025",
                "source_family": "CENSO_ESCOLAR",
                "source_sha256": src["xlsx_sha256"],
                "provenance_ref": provenance_base + f";SHEET:2.6;ROW:3607;BOND:{bond_id}",
                "quality_status": "VALIDATED",
                "caution": "BOND_CATEGORY_COUNT_NON_ADDITIVE_ACROSS_CATEGORIES",
            }
        )

    sme = obj["sme_current_context"]
    rows.append(
        {
            "scope_level": "NETWORK",
            "scope_id": "3526902:MUNICIPAL:CURRENT_CONTRACTED_TEACHERS_IN_CLASS",
            "network": "MUNICIPAL",
            "period": "2026-09-07",
            "indicator_id": "CONTRACTED_TEACHER_CURRENT_COUNT",
            "indicator_name": "Professores contratados únicos em classe na página operacional da SME",
            "value": sme["unique_contracted_teachers"],
            "unit": "COUNT",
            "context": (
                f"Snapshot operacional SME impresso em 07/09/2026: {sme['assignment_rows']} linhas de atribuição "
                f"correspondem a {sme['unique_contracted_teachers']} professores contratados únicos; "
                f"{sme['people_with_multiple_assignment_rows']} pessoa possui múltiplas linhas. "
                "Não é comparável diretamente ao Censo Escolar 2025."
            ),
            "observation_period": "2026-09-07",
            "source_family": "MUNICIPAL_REPORTS",
            "source_sha256": sme["source_sha256"],
            "provenance_ref": (
                f"GITHUB_ACTIONS_RUN:{sme['live_run_id']};"
                f"ARTIFACT:{sme['artifact_id']};SME_CONTRATADO_CLASSE"
            ),
            "quality_status": "VALIDATED",
            "caution": "CURRENT_OPERATIONAL_SNAPSHOT_NE_2025_CENSUS_TOTAL_OR_BOND_COUNTS;NO_PERSON_LEVEL_DATA",
        }
    )
    return rows


def build_task201b_school_indicator(
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
            *full_time_overlay_rows(),
            *tdi_anchor_overlay_rows(),
            *workforce_overlay_rows(contract_path),
        ],
        generated_at=generated_at,
        software_version=software_version,
    )
    _stop(school["row_count"] == 1042, "TASK201B_SCHOOL_ROW_COUNT")
    school["overlay_scope"] = {
        "task196_prior_rows": 1035,
        "task201b_workforce_rows": 7,
        "canonical_2025_staff_count": 1280,
        "canonical_bond_category_count": 4,
        "sme_current_contracted_teacher_count": 842,
        "sme_current_snapshot_is_not_census_comparable": True,
    }
    return {
        "validation": validation,
        "SCHOOL_INDICATOR_SERIES": school,
    }

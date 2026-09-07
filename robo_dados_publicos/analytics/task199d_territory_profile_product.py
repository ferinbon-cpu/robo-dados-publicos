from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from robo_dados_publicos.analytics.observatory_products import build_territory_profile

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task199d_territory_profile_product.v1.json"


class Task199DStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task199DStop(code)


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK199D_TERRITORY_PROFILE_PRODUCT_V1", "TASK199D_SCHEMA")
    _stop(obj.get("issue") == 628, "TASK199D_ISSUE")
    _stop(obj.get("base_main_sha") == "747feb9233ce488344f428c72bc500963322429f", "TASK199D_BASE")
    _stop(obj["scope"]["ibge_code"] == "3526902", "TASK199D_MUNICIPALITY")
    _stop(obj["sources"]["basic_zip"]["sha256"] == "ec04624286233d699ebe69c7b9625744a1cfdfc8352126f30245bdef5e9bdc63", "TASK199D_BASIC_SHA")
    _stop(obj["sources"]["income_zip"]["sha256"] == "141c83e7635674e7e2c941e55f98811e538fcbf2e1e1125b0aa7892c260f4a23", "TASK199D_INCOME_SHA")
    _stop(obj["sources"]["income_dictionary"]["sha256"] == "fea6e2b2439eeb167c6fa9c136ed7cb13ebcb06f4c875d634e3e2578c668a48d", "TASK199D_DICT_SHA")
    sem = obj["sources"]["income_dictionary"]["semantics"]
    _stop(sem["V06004"].startswith("Valor do rendimento nominal médio mensal"), "TASK199D_V06004")
    _stop(sem["V06006"].startswith("Valor do rendimento nominal mediano mensal"), "TASK199D_V06006")
    m = obj["materialized_summary"]
    _stop(m["population_2022"] == 291869 and m["population_reconciliation_difference"] == 0, "TASK199D_POP")
    _stop(m["basic_sector_rows"] == 735, "TASK199D_BASIC_ROWS")
    _stop(m["urban_sector_rows"] + m["rural_sector_rows"] == 735, "TASK199D_URBAN_RURAL")
    _stop(m["income_sector_rows"] == 728 and m["income_nonmissing_v06004_rows"] == 718, "TASK199D_INCOME_ROWS")
    _stop(obj["school_context"]["proven_school_links"] == 14, "TASK199D_SCHOOL_LINKS")
    _stop(obj["school_context"]["network_denominator"] == 69, "TASK199D_NETWORK_DENOM")
    _stop(obj["school_context"]["full_network_link"] is False, "TASK199D_NO_FULL_LINK")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK199D_REMOTE")
    return obj


def load_school_fixture(path: str | Path = DEFAULT_CONTRACT) -> list[dict[str, Any]]:
    obj = load_contract(path)
    fixture = ROOT / obj["school_context"]["fixture"]
    rows = list(csv.DictReader(fixture.read_text(encoding="utf-8").splitlines()))
    _stop(len(rows) == 14, "TASK199D_FIXTURE_ROWS")
    _stop(len({row["codigo_inep"] for row in rows}) == 14, "TASK199D_FIXTURE_INEP")
    _stop(len({row["ibge_sector_code_2022"] for row in rows}) == 14, "TASK199D_FIXTURE_SECTOR")
    return rows


def _common(source_family: str, source_sha256: str, provenance_ref: str, caution: str) -> dict[str, Any]:
    return {
        "observation_period": "2022",
        "source_family": source_family,
        "source_sha256": source_sha256,
        "provenance_ref": provenance_ref,
        "quality_status": "VALIDATED",
        "caution": caution,
    }


def territory_rows(path: str | Path = DEFAULT_CONTRACT) -> list[dict[str, Any]]:
    obj = load_contract(path)
    m = obj["materialized_summary"]
    basic_sha = obj["sources"]["basic_zip"]["sha256"]
    income_sha = obj["sources"]["income_zip"]["sha256"]
    dict_sha = obj["sources"]["income_dictionary"]["sha256"]
    cnefe_sha = obj["sources"]["cnefe_zip"]["sha256"]
    rows: list[dict[str, Any]] = []

    def municipal(metric_id: str, metric_name: str, value: Any, unit: str, *, source_sha: str, context: str, provenance: str):
        rows.append({
            "geo_level": "MUNICIPAL",
            "geo_id": "3526902",
            "municipality_code": "3526902",
            "period": "2022",
            "metric_id": metric_id,
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            "context": context,
            **_common("IBGE_CENSO_2022", source_sha, provenance, "MUNICIPAL_CONTEXT_NE_SCHOOL_OR_STUDENT_PROFILE"),
        })

    municipal("POPULATION", "População residente", m["population_2022"], "PERSONS", source_sha=basic_sha,
              context="Soma de V0001 nos 735 setores de Limeira; reconciliação exata com 291.869 habitantes do Censo 2022.",
              provenance="TASK199D_BASIC_ZIP#V0001")
    municipal("BASIC_CENSUS_SECTOR_COUNT", "Setores censitários no arquivo básico", m["basic_sector_rows"], "SECTORS", source_sha=basic_sha,
              context="Setores do município no agregado básico 2022.", provenance="TASK199D_BASIC_ZIP#CD_SETOR")
    municipal("URBAN_CENSUS_SECTOR_COUNT", "Setores censitários urbanos", m["urban_sector_rows"], "SECTORS", source_sha=basic_sha,
              context="Classificação SITUACAO=Urbana no agregado básico.", provenance="TASK199D_BASIC_ZIP#SITUACAO")
    municipal("RURAL_CENSUS_SECTOR_COUNT", "Setores censitários rurais", m["rural_sector_rows"], "SECTORS", source_sha=basic_sha,
              context="Classificação SITUACAO=Rural no agregado básico.", provenance="TASK199D_BASIC_ZIP#SITUACAO")
    municipal("INCOME_CENSUS_SECTOR_COUNT", "Setores censitários no arquivo de renda", m["income_sector_rows"], "SECTORS", source_sha=income_sha,
              context="Setores de Limeira presentes no agregado de renda do responsável.", provenance="TASK199D_INCOME_ZIP#CD_SETOR")
    municipal("INCOME_MEAN_NONMISSING_SECTOR_COUNT", "Setores com V06004 não ausente", m["income_nonmissing_v06004_rows"], "SECTORS", source_sha=income_sha,
              context="Quantidade de setores com valor publicado para V06004.", provenance="TASK199D_INCOME_ZIP#V06004")

    labels = {
        "min": "Mínimo",
        "q1": "Primeiro quartil",
        "median": "Mediana",
        "q3": "Terceiro quartil",
        "max": "Máximo",
    }
    for key, value in m["v06004_unweighted_sector_distribution"].items():
        municipal(
            f"SECTOR_RESPONSIBLE_INCOME_MEAN_{key.upper()}",
            f"{labels[key]} da distribuição setorial de V06004",
            value,
            "BRL_NOMINAL_MONTHLY",
            source_sha=income_sha,
            context=(
                "Distribuição não ponderada entre os 718 setores com V06004 publicado. "
                "V06004 = rendimento nominal médio mensal das pessoas responsáveis com rendimentos "
                "por domicílios particulares permanentes ocupados."
            ),
            provenance=f"TASK199D_INCOME_ZIP#V06004;DICT_SHA256_{dict_sha}",
        )

    for item in load_school_fixture(path):
        base = {
            "geo_level": "SCHOOL_LOCATION_CENSUS_SECTOR",
            "geo_id": item["codigo_inep"],
            "municipality_code": "3526902",
            "school_code": item["codigo_inep"],
            "school_name": item["unidade"],
            "sector_id": item["ibge_sector_code_2022"],
            "period": "2022",
        }
        caution = (
            "SCHOOL_LOCATION_CONTEXT_NE_STUDENT_SOCIOECONOMIC_PROFILE;"
            "PARTIAL_14_OF_69_NETWORK;"
            "SECTOR_INCOME_NE_ENROLLED_HOUSEHOLD_INCOME"
        )
        rows.extend([
            {
                **base,
                "metric_id": "SECTOR_POPULATION",
                "metric_name": "População residente no setor censitário da localização escolar",
                "value": float(item["sector_population_2022"]),
                "unit": "PERSONS",
                "context": "Contexto do setor censitário onde a escola foi ligada por evidência forte de endereço.",
                **_common("IBGE_CENSO_2022", basic_sha, f"TASK199D_BASIC#V0001;CNEFE_SHA256_{cnefe_sha}", caution),
            },
            {
                **base,
                "metric_id": "SECTOR_RESPONSIBLE_INCOME_MEAN",
                "metric_name": "Rendimento nominal médio mensal dos responsáveis com rendimentos no setor",
                "value": float(item["responsible_income_mean_nominal_monthly_brl"]),
                "unit": "BRL_NOMINAL_MONTHLY",
                "context": "V06004 do setor da localização escolar; não descreve a renda dos alunos.",
                **_common("IBGE_CENSO_2022", income_sha, f"TASK199D_INCOME#V06004;DICT_SHA256_{dict_sha};CNEFE_SHA256_{cnefe_sha}", caution),
            },
            {
                **base,
                "metric_id": "SECTOR_RESPONSIBLE_INCOME_MEDIAN",
                "metric_name": "Rendimento nominal mediano mensal dos responsáveis com rendimentos no setor",
                "value": float(item["responsible_income_median_nominal_monthly_brl"]),
                "unit": "BRL_NOMINAL_MONTHLY",
                "context": "V06006 do setor da localização escolar; não descreve a renda dos alunos.",
                **_common("IBGE_CENSO_2022", income_sha, f"TASK199D_INCOME#V06006;DICT_SHA256_{dict_sha};CNEFE_SHA256_{cnefe_sha}", caution),
            },
            {
                **base,
                "metric_id": "SECTOR_RESPONSIBLE_INCOME_MEAN_PERCENTILE",
                "metric_name": "Percentil setorial não ponderado de V06004 em Limeira",
                "value": float(item["V06004_sector_percentile_unweighted"]),
                "unit": "PERCENTILE_0_100",
                "context": "Posição do V06004 do setor entre os setores de Limeira com valor não ausente; comparação setorial não ponderada.",
                **_common("IBGE_CENSO_2022", income_sha, f"TASK199D_DERIVED_PERCENTILE_FROM_V06004;DICT_SHA256_{dict_sha}", caution),
            },
        ])
    _stop(len(rows) == 67, "TASK199D_PRODUCT_ROWS")
    return rows


def build_task199d_territory_profile(
    *,
    generated_at: str,
    software_version: str,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    obj = load_contract(contract_path)
    capabilities = obj["expected_product"]["capabilities"]
    product = build_territory_profile(
        territory_rows(contract_path),
        generated_at=generated_at,
        software_version=software_version,
        capabilities=capabilities,
    )
    _stop(product["row_count"] == 67, "TASK199D_PRODUCT_ROW_COUNT")
    return product


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(path)
    rows = territory_rows(path)
    return {
        "schema": "TASK199D_TERRITORY_PROFILE_PRODUCT_VALIDATION_V1",
        "status": "PASS",
        "territory_rows": len(rows),
        "school_links": obj["school_context"]["proven_school_links"],
        "full_network_school_link": False,
        "network": False,
        "drive_write": False,
    }

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from robo_dados_publicos.analytics.observatory_products import build_school_indicator_series


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/v08_censo_panel.v1.json"


class Task182Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task182Stop(code)


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK182_V08_CENSO_PANEL_V1", "TASK182_SCHEMA")
    _stop(obj["source"]["binary_import_complete"] is False, "TASK182_BINARY_IMPORT")
    _stop(obj["full_panel"]["runtime_row_transfer_complete"] is False, "TASK182_PANEL_TRANSFER_GUARD")
    _stop(obj["full_panel"]["import_rules"]["missing_is_zero"] is False, "TASK182_MISSING_ZERO")
    _stop(obj["full_panel"]["import_rules"]["no_partial_snippet_reconstruction"] is True, "TASK182_SNIPPET_GUARD")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK182_REMOTE_EFFECT")
    return obj


def _parse_number(value: str) -> int | float | None:
    text = (value or "").strip()
    if not text:
        return None
    try:
        number = float(text.replace(",", "."))
    except ValueError as exc:
        raise Task182Stop("TASK182_NON_NUMERIC") from exc
    return int(number) if number.is_integer() else number


def read_aggregate_fixture(contract_path: str | Path = DEFAULT_CONTRACT) -> list[dict[str, str]]:
    contract = load_contract(contract_path)
    path = ROOT / contract["aggregate_seed"]["path"]
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    expected = {"ano", *contract["aggregate_metric_map"].keys()}
    _stop(bool(rows), "TASK182_EMPTY_AGGREGATE")
    _stop(set(rows[0]) == expected, "TASK182_AGGREGATE_COLUMNS")
    years = [int(row["ano"]) for row in rows]
    _stop(years == contract["aggregate_seed"]["expected_years"], "TASK182_AGGREGATE_YEARS")
    return rows


def aggregate_long_rows(contract_path: str | Path = DEFAULT_CONTRACT) -> list[dict[str, Any]]:
    contract = load_contract(contract_path)
    source_rows = read_aggregate_fixture(contract_path)
    rows: list[dict[str, Any]] = []
    for source_row in source_rows:
        year = str(source_row["ano"])
        for source_column, meta in contract["aggregate_metric_map"].items():
            value = _parse_number(source_row[source_column])
            _stop(value is not None, "TASK182_AGGREGATE_MISSING")
            rows.append({
                "scope_level": "NETWORK_SUBGROUP",
                "scope_id": meta["scope_id"],
                "network": "MUNICIPAL",
                "period": year,
                "indicator_id": meta["indicator_id"],
                "indicator_name": meta["indicator_name"],
                "value": value,
                "unit": meta["unit"],
                "context": (
                    meta["scope_context"]
                    + " "
                    + contract["aggregate_seed"]["caution"]
                ),
                "source_column": source_column,
                "observation_period": year,
                "source_family": contract["aggregate_seed"]["source_family"],
                "source_sha256": contract["source"]["sha256"],
                "provenance_ref": (
                    "FILE_LIBRARY:CAMADA_ANALITICA_V06_40_ESCOLAS_V08.xlsx"
                    f"#88 Dashboard V08:{year}:{source_column}"
                ),
                "quality_status": contract["aggregate_seed"]["quality_status"],
                "caution": contract["aggregate_seed"]["caution"],
            })
    rows.sort(key=lambda row: (row["scope_id"], row["period"], row["indicator_id"]))
    return rows


def validate_aggregate(contract_path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    contract = load_contract(contract_path)
    rows = aggregate_long_rows(contract_path)
    _stop(
        len(rows) == contract["aggregate_seed"]["expected_long_rows"],
        "TASK182_AGGREGATE_ROW_COUNT",
    )
    return {
        "schema": "TASK182_V08_AGGREGATE_VALIDATION_V1",
        "status": "PASS",
        "row_count": len(rows),
        "year_count": len(contract["aggregate_seed"]["expected_years"]),
        "metric_count": contract["aggregate_seed"]["expected_metric_count"],
        "source_sha256": contract["source"]["sha256"],
        "network": False,
        "drive_write": False,
        "serving": False,
    }


def materialize_aggregate(
    *,
    generated_at: str,
    software_version: str,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    validation = validate_aggregate(contract_path)
    product = build_school_indicator_series(
        aggregate_long_rows(contract_path),
        generated_at=generated_at,
        software_version=software_version,
    )
    return {
        "schema": "TASK182_V08_AGGREGATE_MATERIALIZATION_V1",
        "validation": validation,
        "product": product,
        "full_panel_materialized": False,
        "full_panel_row_transfer_complete": False,
        "source_layers_replaced": False,
    }


def validate_full_panel_rows(
    rows: Iterable[Mapping[str, Any]],
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    rows_list = [dict(row) for row in rows]
    panel = contract["full_panel"]
    _stop(len(rows_list) == panel["expected_rows"], "TASK182_PANEL_ROW_COUNT")
    _stop(bool(rows_list), "TASK182_PANEL_EMPTY")
    _stop(set(rows_list[0]) == set(panel["header"]), "TASK182_PANEL_COLUMNS")
    _stop(all(set(row) == set(panel["header"]) for row in rows_list), "TASK182_PANEL_COLUMN_DRIFT")

    years = sorted({int(row["ano"]) for row in rows_list})
    _stop(years == panel["years"], "TASK182_PANEL_YEARS")
    codes_2025 = {
        str(row["codigo_inep"]).strip()
        for row in rows_list
        if int(row["ano"]) == 2025
    }
    _stop(len(codes_2025) == panel["expected_2025_units"], "TASK182_PANEL_2025_UNITS")
    groups_2025 = {
        "ANOS_INICIAIS": set(),
        "EDUCACAO_INFANTIL": set(),
    }
    for row in rows_list:
        if int(row["ano"]) != 2025:
            continue
        group = str(row["grupo_v06"])
        if group in groups_2025:
            groups_2025[group].add(str(row["codigo_inep"]).strip())
    _stop(len(groups_2025["ANOS_INICIAIS"]) == panel["expected_2025_ai"], "TASK182_PANEL_2025_AI")
    _stop(len(groups_2025["EDUCACAO_INFANTIL"]) == panel["expected_2025_ei"], "TASK182_PANEL_2025_EI")
    return {
        "schema": "TASK182_FULL_PANEL_VALIDATION_V1",
        "status": "PASS",
        "row_count": len(rows_list),
        "year_count": len(years),
        "units_2025": len(codes_2025),
        "ai_2025": len(groups_2025["ANOS_INICIAIS"]),
        "ei_2025": len(groups_2025["EDUCACAO_INFANTIL"]),
    }


def full_panel_to_long_rows(
    rows: Iterable[Mapping[str, Any]],
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    contract = load_contract(contract_path)
    rows_list = [dict(row) for row in rows]
    validate_full_panel_rows(rows_list, contract_path)
    panel = contract["full_panel"]
    output: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for row in rows_list:
        year = str(row["ano"])
        code = str(row["codigo_inep"]).strip()
        for source_column, meta in panel["long_metric_map"].items():
            value = _parse_number(str(row.get(source_column, "")))
            locator = (
                "FILE_LIBRARY:CAMADA_ANALITICA_V06_40_ESCOLAS_V08.xlsx"
                f"#81 Censo 69 2018-25:{year}:{code}:{source_column}"
            )
            if value is None:
                missing.append({
                    "school_code": code,
                    "period": year,
                    "source_column": source_column,
                    "indicator_id": meta["indicator_id"],
                    "status": "MISSING_SOURCE_CELL_NOT_ZERO",
                    "provenance_ref": locator,
                })
                continue
            output.append({
                "scope_level": "SCHOOL",
                "scope_id": code,
                "school_code": code,
                "school_name": str(row["unidade"]),
                "network": "MUNICIPAL",
                "period": year,
                "indicator_id": meta["indicator_id"],
                "indicator_name": meta["indicator_id"],
                "value": value,
                "unit": meta["unit"],
                "context": (
                    f"group={row['grupo_v06']}; status={row['status']}; "
                    f"first_year_same_code={row['primeiro_ano_mesmo_codigo']}; "
                    "cadastral presence does not measure quality/sufficiency/use"
                ),
                "source_record_status": row["status"],
                "source_file_declared": row["arquivo_fonte"],
                "observation_period": year,
                "source_family": panel["import_rules"]["source_family"],
                "source_sha256": contract["source"]["sha256"],
                "provenance_ref": locator,
                "quality_status": "VALIDATED",
                "caution": "CENSO_CADASTRAL_PRESENCE_NE_QUALITY;OBSERVED_UNIVERSE_AND_SOURCE_STATUS_PRESERVED",
            })
    output.sort(key=lambda r: (r["school_code"], r["period"], r["indicator_id"]))
    missing.sort(key=lambda r: (r["school_code"], r["period"], r["source_column"]))
    return output, missing


if __name__ == "__main__":
    print(json.dumps(validate_aggregate(), ensure_ascii=False, indent=2, sort_keys=True))

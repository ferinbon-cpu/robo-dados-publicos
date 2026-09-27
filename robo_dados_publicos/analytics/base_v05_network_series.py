from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from robo_dados_publicos.analytics.observatory_products import (
    build_fiscal_series,
    build_school_indicator_series,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/base_v05_network_series.v1.json"


class Task181Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task181Stop(code)


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK181_BASE_V05_NETWORK_SERIES_V1", "TASK181_SCHEMA")
    _stop(obj["source"]["binary_import_complete"] is False, "TASK181_BINARY_IMPORT")
    _stop(obj["quality"]["blank_is_zero"] is False, "TASK181_BLANK_ZERO")
    _stop(obj["quality"]["published_zero_is_observed_zero"] is True, "TASK181_ZERO_GUARD")
    _stop(obj["quality"]["simple_school_mean_equals_official_mean"] is False, "TASK181_SARESP_MEAN_GUARD")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK181_REMOTE_EFFECT")
    return obj


def _parse_number(value: str) -> int | float | None:
    text = (value or "").strip()
    if text == "":
        return None
    try:
        number = float(text.replace(",", "."))
    except ValueError as exc:
        raise Task181Stop("TASK181_NON_NUMERIC") from exc
    return int(number) if number.is_integer() else number


def read_fixture(contract_path: str | Path = DEFAULT_CONTRACT) -> list[dict[str, str]]:
    contract = load_contract(contract_path)
    path = ROOT / contract["fixture"]["path"]
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    expected_columns = {
        "Ano",
        *contract["school_indicator_map"].keys(),
        *contract["fiscal_map"].keys(),
        *contract["deferred_source_role_review"].keys(),
    }
    _stop(bool(rows), "TASK181_EMPTY_FIXTURE")
    _stop(set(rows[0]) == expected_columns, "TASK181_FIXTURE_COLUMNS")
    _stop(len(rows) == contract["fixture"]["expected_year_rows"], "TASK181_YEAR_ROW_COUNT")
    years = [int(row["Ano"]) for row in rows]
    _stop(
        years == list(range(contract["source"]["period_start"], contract["source"]["period_end"] + 1)),
        "TASK181_YEAR_SEQUENCE",
    )
    return rows


def validate_series(contract_path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    contract = load_contract(contract_path)
    rows = read_fixture(contract_path)

    school_non_null = school_missing = 0
    fiscal_non_null = fiscal_missing = 0
    deferred_non_null = deferred_missing = 0
    published_zero_count = 0

    for row in rows:
        for column in contract["school_indicator_map"]:
            if _parse_number(row[column]) is None:
                school_missing += 1
            else:
                school_non_null += 1
        for column in contract["fiscal_map"]:
            value = _parse_number(row[column])
            if value is None:
                fiscal_missing += 1
            else:
                fiscal_non_null += 1
                if value == 0:
                    published_zero_count += 1
        for column in contract["deferred_source_role_review"]:
            if _parse_number(row[column]) is None:
                deferred_missing += 1
            else:
                deferred_non_null += 1

    f = contract["fixture"]
    _stop(school_non_null == f["expected_school_indicator_non_null"], "TASK181_SCHOOL_NON_NULL")
    _stop(school_missing == f["expected_school_indicator_missing"], "TASK181_SCHOOL_MISSING")
    _stop(fiscal_non_null == f["expected_fiscal_non_null"], "TASK181_FISCAL_NON_NULL")
    _stop(fiscal_missing == f["expected_fiscal_missing"], "TASK181_FISCAL_MISSING")
    _stop(deferred_non_null == f["expected_deferred_non_null"], "TASK181_DEFERRED_NON_NULL")
    _stop(deferred_missing == f["expected_deferred_missing"], "TASK181_DEFERRED_MISSING")
    _stop(published_zero_count >= 2, "TASK181_PUBLISHED_ZERO_PRESERVATION")

    return {
        "schema": "TASK181_BASE_V05_NETWORK_SERIES_VALIDATION_V1",
        "status": "PASS",
        "year_count": len(rows),
        "school_indicator_non_null": school_non_null,
        "school_indicator_missing": school_missing,
        "fiscal_non_null": fiscal_non_null,
        "fiscal_missing": fiscal_missing,
        "deferred_non_null": deferred_non_null,
        "deferred_missing": deferred_missing,
        "published_zero_count": published_zero_count,
        "source_sha256": contract["source"]["sha256"],
        "network": False,
        "drive_write": False,
        "serving": False,
    }


def to_product_rows(
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, list[dict[str, Any]]]:
    contract = load_contract(contract_path)
    source_rows = read_fixture(contract_path)
    school_rows: list[dict[str, Any]] = []
    fiscal_rows: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    deferred: list[dict[str, Any]] = []

    for source_row in source_rows:
        year = str(source_row["Ano"])
        for source_column, meta in contract["school_indicator_map"].items():
            value = _parse_number(source_row[source_column])
            locator = contract["provenance"]["school_locator_template"].format(
                year=year, source_column=source_column
            )
            if value is None:
                missing.append({
                    "product_name": "SCHOOL_INDICATOR_SERIES",
                    "period": year,
                    "source_column": source_column,
                    "indicator_id": meta["indicator_id"],
                    "status": "MISSING_SOURCE_CELL_NOT_ZERO",
                    "provenance_ref": locator,
                })
                continue
            school_rows.append({
                "scope_level": contract["scope"]["scope_level"],
                "scope_id": contract["scope"]["scope_id"],
                "network": contract["scope"]["network"],
                "period": year,
                "indicator_id": meta["indicator_id"],
                "indicator_name": meta["indicator_name"],
                "value": value,
                "unit": meta["unit"],
                "context": contract["scope"]["caution"],
                "source_column": source_column,
                "observation_period": year,
                "source_family": meta["source_family"],
                "source_sha256": contract["source"]["sha256"],
                "provenance_ref": locator,
                "quality_status": contract["quality"]["quality_status"],
                "caution": contract["quality"]["caution"],
            })

        for source_column, meta in contract["fiscal_map"].items():
            value = _parse_number(source_row[source_column])
            locator = contract["provenance"]["fiscal_locator_template"].format(
                year=year, source_column=source_column
            )
            if value is None:
                missing.append({
                    "product_name": "FISCAL_SERIES",
                    "period": year,
                    "source_column": source_column,
                    "metric_id": meta["metric_id"],
                    "status": "MISSING_SOURCE_CELL_NOT_ZERO",
                    "provenance_ref": locator,
                })
                continue
            fiscal_rows.append({
                "entity_id": contract["scope"]["entity_id"],
                "period": year,
                "metric_id": meta["metric_id"],
                "metric_name": meta["metric_name"],
                "value": value,
                "unit": meta["unit"],
                "stage_semantic": meta["stage_semantic"],
                "observation_period": year,
                "source_family": meta["source_family"],
                "source_sha256": contract["source"]["sha256"],
                "provenance_ref": locator,
                "quality_status": contract["quality"]["quality_status"],
                "caution": contract["quality"]["caution"],
            })

        for source_column, meta in contract["deferred_source_role_review"].items():
            value = _parse_number(source_row[source_column])
            deferred.append({
                "period": year,
                "source_column": source_column,
                "value": value,
                "unit": "BRL",
                "status": meta["status"] if value is not None else "MISSING_SOURCE_CELL_NOT_ZERO",
                "reason": meta["reason"],
                "source_sha256": contract["source"]["sha256"],
                "provenance_ref": contract["provenance"]["school_locator_template"].format(
                    year=year, source_column=source_column
                ),
            })

    school_rows.sort(key=lambda row: (row["period"], row["indicator_id"], row["source_family"]))
    fiscal_rows.sort(key=lambda row: (row["period"], row["metric_id"]))
    missing.sort(key=lambda row: (row["product_name"], row["period"], row["source_column"]))
    deferred.sort(key=lambda row: (row["period"], row["source_column"]))
    return {
        "school_rows": school_rows,
        "fiscal_rows": fiscal_rows,
        "missing_ledger": missing,
        "deferred_source_role_review": deferred,
    }


def materialize_series(
    *,
    generated_at: str,
    software_version: str,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    validation = validate_series(contract_path)
    rows = to_product_rows(contract_path)
    school = build_school_indicator_series(
        rows["school_rows"],
        generated_at=generated_at,
        software_version=software_version,
    )
    fiscal = build_fiscal_series(
        rows["fiscal_rows"],
        generated_at=generated_at,
        software_version=software_version,
    )
    return {
        "schema": "TASK181_BASE_V05_NETWORK_MATERIALIZATION_V1",
        "validation": validation,
        "school_indicator_product": school,
        "fiscal_product": fiscal,
        "missing_ledger": rows["missing_ledger"],
        "deferred_source_role_review": rows["deferred_source_role_review"],
        "library_mediated": True,
        "binary_import_complete": False,
        "source_layers_replaced": False,
    }


if __name__ == "__main__":
    print(json.dumps(validate_series(), ensure_ascii=False, indent=2, sort_keys=True))

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Mapping

from robo_dados_publicos.analytics.observatory_products import build_school_indicator_series


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/school_indicator_library_seed.v1.json"


class Task180Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task180Stop(code)


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = _load_json(path)
    _stop(obj.get("schema") == "TASK180_SCHOOL_INDICATOR_LIBRARY_SEED_V1", "TASK180_CONTRACT_SCHEMA")
    _stop(obj.get("mode") == "T0_OFFLINE_USER_LIBRARY_MEDIATED_SANITIZED_SEED", "TASK180_CONTRACT_MODE")
    _stop(obj["source"]["binary_import_complete"] is False, "TASK180_BINARY_IMPORT_GUARD")
    _stop(obj["quality"]["missing_is_zero"] is False, "TASK180_MISSING_ZERO_GUARD")
    _stop(obj["quality"]["not_applicable_is_missing"] is False, "TASK180_NA_MISSING_GUARD")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK180_REMOTE_EFFECT")
    return obj


def _parse_number(value: str) -> int | float | None:
    text = (value or "").strip()
    if text == "":
        return None
    text = text.replace(",", ".")
    try:
        number = float(text)
    except ValueError as exc:
        raise Task180Stop("TASK180_NON_NUMERIC_VALUE") from exc
    if number.is_integer():
        return int(number)
    return number


def read_wide_fixture(
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> list[dict[str, Any]]:
    contract = load_contract(contract_path)
    path = ROOT / contract["fixture"]["path"]
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    expected = {
        contract["fixture"]["identity_column"],
        contract["fixture"]["name_column"],
        *contract["metric_map"].keys(),
    }
    _stop(set(rows[0]) == expected if rows else False, "TASK180_FIXTURE_COLUMNS")
    _stop(len(rows) == contract["fixture"]["expected_school_rows"], "TASK180_SCHOOL_ROW_COUNT")
    codes = [str(row[contract["fixture"]["identity_column"]]).strip() for row in rows]
    _stop(all(code.isdigit() and len(code) == 8 for code in codes), "TASK180_INEP_CODE")
    _stop(len(set(codes)) == len(codes), "TASK180_DUPLICATE_INEP_CODE")
    return rows


def validate_seed(
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    rows = read_wide_fixture(contract_path)
    metric_map = contract["metric_map"]
    _stop(len(metric_map) == contract["fixture"]["expected_metric_columns"], "TASK180_METRIC_COUNT")

    missing: list[dict[str, str]] = []
    non_null = 0
    for row in rows:
        code = str(row[contract["fixture"]["identity_column"]]).strip()
        for source_column in metric_map:
            value = _parse_number(row.get(source_column, ""))
            if value is None:
                missing.append({"codigo_inep": code, "source_column": source_column})
            else:
                non_null += 1

    _stop(non_null == contract["fixture"]["expected_non_null_long_rows"], "TASK180_NON_NULL_COUNT")
    _stop(len(missing) == contract["fixture"]["expected_missing_values"], "TASK180_MISSING_COUNT")
    expected_missing = sorted(
        contract["fixture"]["expected_missing"],
        key=lambda x: (x["codigo_inep"], x["source_column"]),
    )
    _stop(
        sorted(missing, key=lambda x: (x["codigo_inep"], x["source_column"])) == expected_missing,
        "TASK180_MISSING_LEDGER",
    )
    return {
        "schema": "TASK180_SEED_VALIDATION_V1",
        "status": "PASS",
        "school_count": len(rows),
        "metric_count": len(metric_map),
        "non_null_long_rows": non_null,
        "missing_count": len(missing),
        "missing": missing,
        "source_sha256": contract["source"]["sha256"],
        "binary_import_complete": False,
        "network": False,
        "drive_write": False,
        "serving": False,
    }


def to_long_rows(
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    contract = load_contract(contract_path)
    wide = read_wide_fixture(contract_path)
    metric_map = contract["metric_map"]
    rows: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []

    for wide_row in wide:
        code = str(wide_row[contract["fixture"]["identity_column"]]).strip()
        school_name = " ".join(str(wide_row[contract["fixture"]["name_column"]]).split())
        for source_column, meta in metric_map.items():
            value = _parse_number(wide_row.get(source_column, ""))
            locator = contract["provenance"]["locator_template"].format(
                codigo_inep=code,
                source_column=source_column,
            )
            if value is None:
                missing.append(
                    {
                        "school_code": code,
                        "school_name": school_name,
                        "source_column": source_column,
                        "indicator_id": meta["indicator_id"],
                        "period": meta["period"],
                        "status": "MISSING_SOURCE_CELL_NOT_ZERO",
                        "source_sha256": contract["source"]["sha256"],
                        "provenance_ref": locator,
                    }
                )
                continue
            rows.append(
                {
                    "scope_level": "SCHOOL",
                    "scope_id": code,
                    "school_code": code,
                    "school_name": school_name,
                    "network": contract["provenance"]["network"],
                    "period": meta["period"],
                    "indicator_id": meta["indicator_id"],
                    "indicator_name": meta["indicator_name"],
                    "value": value,
                    "unit": meta["unit"],
                    "context": contract["provenance"]["context"],
                    "source_column": source_column,
                    "observation_period": meta["period"],
                    "source_family": meta["source_family"],
                    "source_sha256": contract["source"]["sha256"],
                    "provenance_ref": locator,
                    "quality_status": contract["quality"]["derived_row_quality_status"],
                    "caution": contract["quality"]["caution"],
                }
            )

    rows.sort(
        key=lambda row: (
            row["scope_id"],
            row["period"],
            row["indicator_id"],
            row["source_family"],
            row["source_column"],
        )
    )
    missing.sort(key=lambda row: (row["school_code"], row["source_column"]))
    return rows, missing


def materialize_seed(
    *,
    generated_at: str,
    software_version: str,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    validation = validate_seed(contract_path)
    rows, missing = to_long_rows(contract_path)
    product = build_school_indicator_series(
        rows,
        generated_at=generated_at,
        software_version=software_version,
    )
    return {
        "schema": "TASK180_SCHOOL_INDICATOR_SEED_MATERIALIZATION_V1",
        "validation": validation,
        "product": product,
        "missing_ledger": missing,
        "library_mediated": True,
        "binary_import_complete": False,
        "source_layers_replaced": False,
        "remote_effects": {
            "network": False,
            "drive_write": False,
            "serving": False,
            "publication": False,
        },
    }


def school_indicator_values(
    school_code: str,
    *,
    period: str | None = None,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> list[dict[str, Any]]:
    rows, _ = to_long_rows(contract_path)
    result = [row for row in rows if row["school_code"] == str(school_code)]
    if period is not None:
        result = [row for row in result if row["period"] == str(period)]
    return result


if __name__ == "__main__":
    print(json.dumps(validate_seed(), ensure_ascii=False, indent=2, sort_keys=True))

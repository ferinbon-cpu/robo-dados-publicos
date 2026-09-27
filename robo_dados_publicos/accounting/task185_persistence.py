from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task185_real_tce_accounting_persistence.v1.json"
TASK172_CONTRACT = ROOT / "config/task172_observatory_fiscal_machine_readable_batch.v1.json"
TASK173_ADAPTER = ROOT / "config/tcesp_current_expense_adapter.v1.json"
TASK173_OBSERVATION = ROOT / "config/municipal_accounting_observation.v1.json"
TASK176_PRODUCTS = ROOT / "config/observatory_query_products.v1.json"


class Task185Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task185Stop(code)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK185_REAL_TCE_ACCOUNTING_PERSISTENCE_V1", "TASK185_CONTRACT_SCHEMA")
    _stop(obj.get("stage") == "A", "TASK185_STAGE")
    _stop(obj.get("mode") == "T0_OFFLINE_DESIGN_ONLY", "TASK185_MODE")
    return obj


def validate_stage_a_design(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    contract = load_contract(path)
    task172 = json.loads(TASK172_CONTRACT.read_text(encoding="utf-8"))
    adapter = json.loads(TASK173_ADAPTER.read_text(encoding="utf-8"))
    observation = json.loads(TASK173_OBSERVATION.read_text(encoding="utf-8"))
    products = json.loads(TASK176_PRODUCTS.read_text(encoding="utf-8"))

    source = next(
        (x for x in task172["sources"] if x.get("id") == contract["source"]["source_id"]),
        None,
    )
    _stop(source is not None, "TASK185_TASK172_SOURCE_NOT_FOUND")
    _stop(source["url"] == contract["source"]["url"], "TASK185_SOURCE_URL_DRIFT")
    _stop(source["format"] == "ZIP", "TASK185_SOURCE_FORMAT_DRIFT")
    _stop(contract["source"]["max_requests"] == 1, "TASK185_REQUEST_BUDGET")
    _stop(contract["source"]["retry"] == 0, "TASK185_RETRY")
    _stop(contract["source"]["follow_redirects"] is False, "TASK185_REDIRECT")

    _stop(
        adapter.get("schema") == "TCESP_LIMEIRA_CURRENT_EXPENSE_ADAPTER_V1",
        "TASK185_ADAPTER_SCHEMA",
    )
    _stop(
        observation.get("schema") == "MUNICIPAL_ACCOUNTING_OBSERVATION_V1",
        "TASK185_OBSERVATION_SCHEMA",
    )
    _stop(
        set(contract["csv_schema"]["required_headers"]) == set(adapter["proven_columns"]),
        "TASK185_REQUIRED_HEADERS_DRIFT",
    )
    _stop(
        observation["stages"] == contract["stage_c"]["preserve_stages"],
        "TASK185_STAGE_SEMANTICS_DRIFT",
    )
    _stop(
        products["products"]["ACCOUNTING_LEDGER"]["schema"] == "ACCOUNTING_LEDGER_V1",
        "TASK185_PRODUCT_SCHEMA",
    )
    _stop(
        "TCE_SP_EXPENSES" in products["products"]["ACCOUNTING_LEDGER"]["source_families"],
        "TASK185_PRODUCT_SOURCE_FAMILY",
    )

    custody = contract["custody"]
    _stop(custody["target_layer"] == "01_BRONZE", "TASK185_CUSTODY_LAYER")
    _stop(bool(custody["target_folder_id"]), "TASK185_CUSTODY_FOLDER_ID")
    _stop(custody["drive_write_authorized_in_stage_a"] is False, "TASK185_STAGE_A_DRIVE_WRITE")
    _stop(custody["create_only"] is True, "TASK185_CREATE_ONLY")
    _stop(custody["overwrite"] is False, "TASK185_OVERWRITE")
    _stop(custody["delete"] is False, "TASK185_DELETE")

    auth = contract["stage_b_authorization"]
    _stop(auth["required"] is True, "TASK185_STAGE_B_AUTH_REQUIRED")
    _stop(auth["prior_task172_authorization_reusable"] is False, "TASK185_PRIOR_AUTH_REUSE")
    _stop(auth["authorization_artifact_required_before_network"] is True, "TASK185_AUTH_ARTIFACT")
    _stop(auth["bind_max_requests"] == 1, "TASK185_AUTH_REQUEST_BOUND")

    effects = contract["stage_a_remote_effects"]
    _stop(all(value is False for value in effects.values()), "TASK185_STAGE_A_REMOTE_EFFECT")

    return {
        "schema": "TASK185_STAGE_A_DESIGN_VALIDATION_V1",
        "status": "PASS",
        "source_id": contract["source"]["source_id"],
        "source_url": contract["source"]["url"],
        "expected_member": contract["source"]["expected_member_exact"],
        "required_header_count": len(contract["csv_schema"]["required_headers"]),
        "custody_folder_id": custody["target_folder_id"],
        "historical_row_count": contract["source"]["previous_observation"]["observed_record_count"],
        "historical_row_count_is_future_requirement": False,
        "stage_b_authorization_required": True,
        "network": False,
        "drive_write": False,
        "serving": False,
        "publication": False,
    }


def _decode_csv(payload: bytes) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return payload.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise Task185Stop("TASK185_CSV_ENCODING")


def _detect_delimiter(header_line: str, required_headers: set[str]) -> tuple[str, list[str]]:
    candidates: list[tuple[str, list[str]]] = []
    for delimiter in (";", ","):
        parsed = next(csv.reader([header_line], delimiter=delimiter))
        headers = [x.strip().lstrip("\ufeff") for x in parsed]
        if required_headers.issubset(set(headers)):
            candidates.append((delimiter, headers))
    _stop(len(candidates) == 1, "TASK185_CSV_DELIMITER_OR_HEADER_AMBIGUOUS")
    return candidates[0]


def inspect_zip_bytes(
    payload: bytes,
    *,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    _stop(bool(payload), "TASK185_ZIP_EMPTY")
    _stop(
        len(payload) <= int(contract["source"]["max_response_bytes"]),
        "TASK185_ZIP_RESPONSE_TOO_LARGE",
    )
    buffer = io.BytesIO(payload)
    _stop(zipfile.is_zipfile(buffer), "TASK185_NOT_ZIP")

    expected_member = contract["source"]["expected_member_exact"]
    max_uncompressed = int(contract["source"].get("max_member_uncompressed_bytes", 100_000_000))
    max_members = int(contract["source"].get("max_archive_members", 16))

    with zipfile.ZipFile(buffer) as archive:
        infos = archive.infolist()
        _stop(len(infos) <= max_members, "TASK185_TOO_MANY_ZIP_MEMBERS")
        for info in infos:
            name = info.filename.replace("\\", "/")
            _stop(not name.startswith("/") and ".." not in name.split("/"), "TASK185_UNSAFE_ZIP_MEMBER")
        exact = [info for info in infos if info.filename == expected_member]
        _stop(len(exact) == 1, "TASK185_EXPECTED_MEMBER")
        member_info = exact[0]
        _stop(member_info.file_size <= max_uncompressed, "TASK185_CSV_UNCOMPRESSED_TOO_LARGE")
        csv_bytes = archive.read(member_info)

    _stop(bool(csv_bytes), "TASK185_CSV_EMPTY")
    text, encoding = _decode_csv(csv_bytes)
    first_line = text.splitlines()[0] if text.splitlines() else ""
    required_headers = set(contract["csv_schema"]["required_headers"])
    delimiter, headers = _detect_delimiter(first_line, required_headers)
    _stop(len(headers) == len(set(headers)), "TASK185_DUPLICATE_HEADERS")

    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    normalized_headers = [str(x or "").strip().lstrip("\ufeff") for x in (reader.fieldnames or [])]
    _stop(set(normalized_headers) == set(headers), "TASK185_HEADER_READBACK_DRIFT")
    missing = sorted(required_headers - set(normalized_headers))
    _stop(not missing, "TASK185_SOURCE_SCHEMA_MISSING_COLUMNS")
    extra = sorted(set(normalized_headers) - required_headers)

    record_count = 0
    for row in reader:
        if any(str(value or "").strip() for value in row.values()):
            record_count += 1
    _stop(record_count > 0, "TASK185_CSV_NO_DATA_ROWS")

    return {
        "schema": "TASK185_TCE_ZIP_INSPECTION_V1",
        "source_id": contract["source"]["source_id"],
        "zip_sha256": _sha256(payload),
        "zip_bytes": len(payload),
        "member_name": expected_member,
        "csv_sha256": _sha256(csv_bytes),
        "csv_bytes": len(csv_bytes),
        "csv_encoding": encoding,
        "csv_delimiter": delimiter,
        "csv_headers": normalized_headers,
        "extra_headers": extra,
        "record_count": record_count,
        "historical_task172_record_count": contract["source"]["previous_observation"]["observed_record_count"],
        "record_count_must_equal_historical": False,
        "network_performed": False,
        "drive_write_performed": False,
    }


def build_custody_manifest_plan(
    inspection: dict[str, Any],
    *,
    retrieved_at: str,
    authorization_artifact: str,
    implementation_sha: str,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    _stop(inspection.get("schema") == "TASK185_TCE_ZIP_INSPECTION_V1", "TASK185_INSPECTION_SCHEMA")
    _stop(bool(retrieved_at), "TASK185_RETRIEVED_AT")
    _stop(bool(authorization_artifact), "TASK185_AUTHORIZATION_REFERENCE")
    _stop(len(implementation_sha) == 40, "TASK185_IMPLEMENTATION_SHA")

    custody = contract["custody"]
    artifacts = custody["artifacts"]
    zip_sha = inspection["zip_sha256"]
    csv_sha = inspection["csv_sha256"]

    names = {
        "zip": artifacts["zip_name_template"].format(zip_sha256=zip_sha, csv_sha256=csv_sha),
        "csv": artifacts["csv_name_template"].format(zip_sha256=zip_sha, csv_sha256=csv_sha),
        "manifest": artifacts["manifest_name_template"].format(zip_sha256=zip_sha, csv_sha256=csv_sha),
    }
    _stop(len(set(names.values())) == 3, "TASK185_CUSTODY_NAME_COLLISION")

    return {
        "schema": "TASK185_TCE_CUSTODY_MANIFEST_PLAN_V1",
        "source_id": contract["source"]["source_id"],
        "source_url": contract["source"]["url"],
        "retrieved_at": retrieved_at,
        "zip_sha256": zip_sha,
        "zip_bytes": inspection["zip_bytes"],
        "member_name": inspection["member_name"],
        "csv_sha256": csv_sha,
        "csv_bytes": inspection["csv_bytes"],
        "csv_headers": inspection["csv_headers"],
        "extra_headers": inspection["extra_headers"],
        "record_count": inspection["record_count"],
        "task173_adapter_schema": "TCESP_LIMEIRA_CURRENT_EXPENSE_ADAPTER_V1",
        "task173_observation_schema": "MUNICIPAL_ACCOUNTING_OBSERVATION_V1",
        "stage_counts": "COMPUTED_ONLY_AFTER_REAL_ROW_NORMALIZATION",
        "custody_folder_id": custody["target_folder_id"],
        "authorization_artifact": authorization_artifact,
        "implementation_sha": implementation_sha,
        "artifact_names": names,
        "create_only": True,
        "collision_policy": "STOP_BEFORE_FIRST_WRITE",
        "manifest_written_last": True,
        "drive_write_performed": False,
    }


if __name__ == "__main__":
    print(json.dumps(validate_stage_a_design(), ensure_ascii=False, indent=2, sort_keys=True))

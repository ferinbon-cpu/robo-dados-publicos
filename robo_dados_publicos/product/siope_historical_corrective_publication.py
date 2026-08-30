"""Fail-closed, one-shot corrective M8 publication for the R2 objects.

This module deliberately does not expose update, replace, delete, retry, or
source collection operations.  Its only mutating path is the ordered sequence
guarded by :func:`execute_corrective_publication`.
"""
from __future__ import annotations

import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Any

from robo_dados_publicos.product.publication import (
    GOOGLE_SHEETS_MIME,
    JSON_MIME,
    PDF_MIME,
    ProductPublicationError,
    PublicationNames,
    validate_bundle_integrity,
)
from robo_dados_publicos.product.siope_historical_publication_gate import (
    EXPECTED_ZIP_MEMBERS,
    extract_product_bundle,
    output_parent_id,
    validate_source_zip,
)

CONFIG_PATH = Path("config/m8_siope_historical_corrective_publication.v1.json")
REMOTE_BASENAME = "SIOPE_LIMEIRA_HISTORICAL_2016_2024_V0_8_0_R2"
OLD_REMOTE_BASENAME = "SIOPE_LIMEIRA_HISTORICAL_2016_2024_V0_8_0"
GATE_ID = "M8_SIOPE_HISTORICAL_CORRECTIVE_PUBLICATION_0_8_0_R2"
PASS = "PASS_M8_SIOPE_HISTORICAL_CORRECTIVE_PUBLICATION_GATE"
PASS_DRY_RUN = "PASS_M8_SIOPE_HISTORICAL_CORRECTIVE_PUBLICATION_DRY_RUN"
ERROR = "STOP_M8_SIOPE_HISTORICAL_CORRECTIVE_PUBLICATION"
EXPECTED_ROWS = 9
EXPECTED_COLUMNS = 7
SHEET_RANGE = "A1:G9"


class CorrectivePublicationError(ProductPublicationError):
    pass


def _stop(code: str, *, created_count: int = 0) -> None:
    raise CorrectivePublicationError(f"{ERROR}_{code}", created_count=created_count)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def matrix_sha256(matrix: list[list[str]]) -> str:
    canonical = json.dumps(matrix, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def parse_canonical_matrix(path: str | Path) -> list[list[str]]:
    """Parse the pinned comma-delimited UTF-8 CSV without locale inference."""
    try:
        with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
            matrix = [[cell.replace("\r\n", "\n").replace("\r", "\n") for cell in row]
                      for row in csv.reader(handle, dialect="excel", delimiter=",")]
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        raise CorrectivePublicationError(f"{ERROR}_CANONICAL_MATRIX_PARSE") from exc
    validate_matrix(matrix, expected=None)
    return matrix


def validate_matrix(matrix: Any, *, expected: list[list[str]] | None) -> dict[str, Any]:
    created = 1 if expected is not None else 0
    if not isinstance(matrix, list) or len(matrix) != EXPECTED_ROWS:
        _stop("MATRIX_ROW_COUNT", created_count=created)
    if any(not isinstance(row, list) or len(row) != EXPECTED_COLUMNS for row in matrix):
        _stop("MATRIX_COLUMN_COUNT", created_count=created)
    if any(not isinstance(cell, str) for row in matrix for cell in row):
        _stop("MATRIX_CELL_TYPE", created_count=created)
    if expected is not None and matrix != expected:
        _stop("SHEET_SEMANTIC_MISMATCH", created_count=1)
    return {
        "rows": EXPECTED_ROWS,
        "columns": EXPECTED_COLUMNS,
        "matrix_sha256": matrix_sha256(matrix),
    }


def _load_contract(root: Path) -> dict[str, Any]:
    try:
        contract = json.loads((root / CONFIG_PATH).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CorrectivePublicationError(f"{ERROR}_CONTRACT_READ") from exc
    names = PublicationNames.from_basename(REMOTE_BASENAME)
    required_false = (
        "overwrite_allowed", "replace_allowed", "delete_allowed", "retry_allowed",
        "schedule_enabled", "recurrence_enabled", "source_collection_allowed",
        "processing_rerun_allowed", "reconciliation_rerun_allowed", "include_2025",
        "release_0_8_0_promotion", "compliance_claim_promotion",
    )
    checks = (
        contract.get("schema") == "M8_SIOPE_HISTORICAL_CORRECTIVE_PUBLICATION_V1",
        contract.get("gate_id") == GATE_ID,
        contract.get("tier") == "T3_MUTATING_OR_PUBLICATION",
        contract.get("drive_target") == "08_OUTPUTS",
        contract.get("remote_names") == list(names.all()),
        contract.get("expected_matrix") == {"rows": 9, "columns": 7},
        contract.get("write_mechanism") == "SHEETS_API_VALUES_UPDATE_RAW",
        contract.get("readback_mechanism") == "SHEETS_API_VALUES_GET_UNFORMATTED",
        all(contract.get(key) is True for key in (
            "create_only", "one_shot", "manual", "preflight_all_names_before_first_write",
            "completion_manifest_written_last",
        )),
        all(contract.get(key) is False for key in required_false),
        not any(name in set(contract.get("remote_names") or []) for name in PublicationNames.from_basename(OLD_REMOTE_BASENAME).all()),
    )
    if not all(checks):
        _stop("CONTRACT_POLICY")
    return contract


def prepare_source(*, root: str | Path, source_zip: str | Path, work_dir: str | Path) -> tuple[Path, list[list[str]], dict[str, Any]]:
    repo = Path(root)
    contract = _load_contract(repo)
    source = validate_source_zip(source_zip)
    bundle = extract_product_bundle(source_zip, work_dir)
    validated = validate_bundle_integrity(bundle, "READY_WITH_CAUTION")
    matrix = parse_canonical_matrix(bundle / "table.csv")
    if validated["table_matrix"] != matrix:
        _stop("CANONICAL_MATRIX_DRIFT")
    expected_table = EXPECTED_ZIP_MEMBERS["product/table.csv"][1]
    expected_pdf = EXPECTED_ZIP_MEMBERS["product/report.pdf"][1]
    expected_manifest = EXPECTED_ZIP_MEMBERS["product/manifest.json"][1]
    if _sha256(bundle / "table.csv") != expected_table:
        _stop("TABLE_SOURCE_HASH")
    if _sha256(bundle / "report.pdf") != expected_pdf:
        _stop("PDF_SOURCE_HASH")
    if _sha256(bundle / "manifest.json") != expected_manifest:
        _stop("MANIFEST_SOURCE_HASH")
    return bundle, matrix, {"contract": contract, "source": source}


def dry_run_result(matrix: list[list[str]], source: dict[str, Any]) -> dict[str, Any]:
    semantic = validate_matrix(matrix, expected=matrix)
    return {
        "status": PASS_DRY_RUN,
        "gate_id": GATE_ID,
        "drive_target": "08_OUTPUTS",
        "remote_names": list(PublicationNames.from_basename(REMOTE_BASENAME).all()),
        "canonical_matrix": semantic,
        "sheet_write": "SHEETS_API_VALUES_UPDATE_RAW",
        "sheet_readback": "SHEETS_API_VALUES_GET_UNFORMATTED",
        "would_create": 3,
        "drive_writes": 0,
        "network_called": False,
        "completion_manifest_written_last": True,
        "source_artifact_zip_sha256": source["source"]["zip_sha256"],
        "source_collection_performed": False,
        "processing_rerun_performed": False,
        "reconciliation_rerun_performed": False,
        "include_2025": False,
        "release_promotion_performed": False,
    }


def _metadata_ok(meta: dict, name: str, mime: str, parent: str) -> bool:
    return meta.get("name") == name and meta.get("mimeType") == mime and parent in (meta.get("parents") or [])


def execute_corrective_publication(drive, *, root: str | Path, source_zip: str | Path, published_at: str) -> dict[str, Any]:
    """Execute the only permitted Sheet -> validation -> PDF -> manifest path."""
    with tempfile.TemporaryDirectory(prefix="m8-corrective-r2-") as raw:
        # Contract/timestamp policy preflight, then exact-name collision
        # preflight, precede loading the pinned product as required by TASK 012.
        _load_contract(Path(root))
        try:
            parsed_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        except (AttributeError, ValueError) as exc:
            raise CorrectivePublicationError(f"{ERROR}_TIMESTAMP") from exc
        if parsed_at.tzinfo is None or parsed_at.utcoffset() is None:
            _stop("TIMESTAMP_TIMEZONE")
        parent = output_parent_id(root=root)
        names = PublicationNames.from_basename(REMOTE_BASENAME)

        # One inventory request checks all exact names before the first write.
        try:
            children = drive.list_children(parent)
        except Exception as exc:
            raise CorrectivePublicationError(f"{ERROR}_COLLISION_PREFLIGHT") from exc
        existing = {item.get("name") for item in children if isinstance(item, dict)}
        if set(names.all()) & existing:
            _stop("R2_NAME_COLLISION")

        bundle, matrix, source = prepare_source(
            root=root, source_zip=source_zip, work_dir=Path(raw) / "source"
        )

        manifest_payload = {
            "schema": "M8_SIOPE_HISTORICAL_CORRECTIVE_PUBLICATION_RECEIPT_V1",
            "gate_id": GATE_ID, "published_at": published_at, "drive_target": "08_OUTPUTS",
            "remote_names": list(names.all()), "canonical_matrix_sha256": matrix_sha256(matrix),
            "matrix_rows": 9, "matrix_columns": 7,
            "table_csv_sha256": _sha256(bundle / "table.csv"),
            "report_pdf_sha256": _sha256(bundle / "report.pdf"),
            "bundle_manifest_sha256": _sha256(bundle / "manifest.json"),
            "sheet_write_mechanism": "SHEETS_API_VALUES_UPDATE_RAW",
            "sheet_semantic_readback_verified": True, "completion_manifest_written_last": True,
            "overwrite_allowed": False, "remote_identifiers_recorded": False,
        }
        manifest_path = Path(raw) / "publication_manifest.json"
        manifest_path.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        created = 0
        try:
            sheet = drive.create_google_sheet(names.sheet, parent)
            created = 1
            sheet_id = str(sheet.get("id") or "")
            if not sheet_id or not _metadata_ok(drive.metadata(sheet_id), names.sheet, GOOGLE_SHEETS_MIME, parent):
                _stop("SHEET_METADATA", created_count=created)
            update = drive.sheets_values_update_raw(sheet_id, SHEET_RANGE, matrix)
            if int(update.get("updatedRows") or -1) != 9 or int(update.get("updatedColumns") or -1) != 7 or int(update.get("updatedCells") or -1) != 63:
                _stop("SHEET_WRITE_COUNT", created_count=created)
            readback = drive.sheets_values_get(sheet_id, SHEET_RANGE)
            observed = readback.get("values") if isinstance(readback, dict) else None
            validate_matrix(observed, expected=matrix)

            pdf = drive.put(bundle / "report.pdf", names.pdf, parent, PDF_MIME)
            created = 2
            pdf_id = str(pdf.get("id") or "")
            if not pdf_id or not _metadata_ok(drive.metadata(pdf_id), names.pdf, PDF_MIME, parent):
                _stop("PDF_METADATA", created_count=created)
            pdf_readback = Path(raw) / "pdf.readback"
            drive.get(pdf_id, pdf_readback)
            if _sha256(pdf_readback) != _sha256(bundle / "report.pdf"):
                _stop("PDF_READBACK_HASH", created_count=created)

            receipt = drive.put(manifest_path, names.manifest, parent, JSON_MIME)
            created = 3
            manifest_id = str(receipt.get("id") or "")
            if not manifest_id or not _metadata_ok(drive.metadata(manifest_id), names.manifest, JSON_MIME, parent):
                _stop("MANIFEST_METADATA", created_count=created)
            manifest_readback = Path(raw) / "manifest.readback"
            drive.get(manifest_id, manifest_readback)
            if _sha256(manifest_readback) != _sha256(manifest_path):
                _stop("MANIFEST_READBACK_HASH", created_count=created)
            final_sheet = drive.sheets_values_get(sheet_id, SHEET_RANGE)
            validate_matrix(final_sheet.get("values") if isinstance(final_sheet, dict) else None, expected=matrix)
            final = drive.list_children(parent)
            final_names = {item.get("name") for item in final if isinstance(item, dict)}
            if not set(names.all()).issubset(final_names):
                _stop("FINAL_READBACK", created_count=created)
        except ProductPublicationError:
            raise
        except Exception as exc:
            raise CorrectivePublicationError(f"{ERROR}_REMOTE_OPERATION", created_count=created) from exc

    return {
        "status": PASS, "gate_id": GATE_ID, "created_count": 3,
        "remote_names": list(names.all()), "sheet_rows": 9, "sheet_columns": 7,
        "canonical_matrix_sha256": matrix_sha256(matrix),
        "sheet_semantic_readback_verified": True, "pdf_readback_hash_verified": True,
        "completion_manifest_written_last": True, "final_readback_verified": True,
        "overwrite_performed": False, "replace_performed": False, "delete_performed": False,
        "retry_performed": False, "source_collection_performed": False,
        "processing_rerun_performed": False, "reconciliation_rerun_performed": False,
        "include_2025": False, "release_promotion_performed": False,
        "remote_identifiers_exposed": False, "secret_values_exposed": False,
        "source_artifact_zip_sha256": source["source"]["zip_sha256"],
    }

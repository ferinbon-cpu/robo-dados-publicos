"""Fail-closed, one-shot corrective M8 publication for the R3 objects.

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
import subprocess
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

CONFIG_PATH = Path("config/m8_siope_historical_corrective_r3_publication.v1.json")
OWNER_AUTHORIZATION_PATH = Path("docs/evidence/TASK_014_M8_CORRECTIVE_R3_OWNER_AUTHORIZATION_0.8.0.json")
REMOTE_BASENAME = "SIOPE_LIMEIRA_HISTORICAL_2016_2024_V0_8_0_R3"
R2_REMOTE_BASENAME = "SIOPE_LIMEIRA_HISTORICAL_2016_2024_V0_8_0_R2"
GATE_ID = "M8_SIOPE_HISTORICAL_CORRECTIVE_PUBLICATION_0_8_0_R3"
PASS = "PASS_M8_SIOPE_HISTORICAL_CORRECTIVE_PUBLICATION_GATE"
PASS_DRY_RUN = "PASS_M8_SIOPE_HISTORICAL_CORRECTIVE_PUBLICATION_DRY_RUN"
ERROR = "STOP_M8_SIOPE_HISTORICAL_CORRECTIVE_PUBLICATION"
EXPECTED_ROWS = 9
EXPECTED_COLUMNS = 7
WRITE_RANGE = "A1:G9"
SEMANTIC_READBACK_RANGE = "A:Z"
R2_SHEET_NAME = f"{R2_REMOTE_BASENAME}_TABELA"


class CorrectivePublicationError(ProductPublicationError):
    def __init__(self, code: str, *, created_count: int = 0, remote_stage: str | None = None,
                 remote_operation_class: str | None = None, error_type: str | None = None,
                 http_status_if_safe: int | None = None):
        super().__init__(code, created_count=created_count)
        self.remote_stage = remote_stage
        self.remote_operation_class = remote_operation_class
        self.error_type = error_type
        self.http_status_if_safe = http_status_if_safe
        self.retryable = False


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
        "overwrite_allowed", "replace_allowed", "delete_allowed", "retry_allowed", "pagination_allowed",
        "schedule_enabled", "recurrence_enabled", "source_collection_allowed",
        "processing_rerun_allowed", "reconciliation_rerun_allowed", "include_2025",
        "release_0_8_0_promotion", "compliance_claim_promotion",
    )
    checks = (
        contract.get("schema") == "M8_SIOPE_HISTORICAL_CORRECTIVE_PUBLICATION_V1",
        contract.get("gate_id") == GATE_ID,
        contract.get("tier") == "T3_REMOTE_WRITE",
        contract.get("drive_target") == "08_OUTPUTS",
        contract.get("remote_names") == list(names.all()),
        contract.get("expected_matrix") == {"rows": 9, "columns": 7},
        contract.get("write_mechanism") == "SHEETS_API_VALUES_UPDATE_RAW",
        contract.get("readback_mechanism") == "SHEETS_API_VALUES_GET_UNFORMATTED_A_TO_Z_FULL_USED_MATRIX",
        contract.get("write_range") == WRITE_RANGE,
        contract.get("semantic_readback_range") == SEMANTIC_READBACK_RANGE,
        all(contract.get(key) is True for key in (
            "create_only", "one_shot", "manual", "preflight_all_names_before_first_write",
            "completion_manifest_written_last",
        )),
        all(contract.get(key) is False for key in required_false),
        not any(name in set(contract.get("remote_names") or []) for name in PublicationNames.from_basename(R2_REMOTE_BASENAME).all()),
    )
    if not all(checks):
        _stop("CONTRACT_POLICY")
    return contract


def _valid_sha(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 40 and all(char in "0123456789abcdef" for char in value)


def validate_owner_authorization(*, root: str | Path) -> dict[str, Any]:
    """Validate owner authorization pinned to the audited implementation SHA."""
    try:
        evidence = json.loads((Path(root) / OWNER_AUTHORIZATION_PATH).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CorrectivePublicationError(f"{ERROR}_OWNER_AUTHORIZATION_MISSING") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CorrectivePublicationError(f"{ERROR}_OWNER_AUTHORIZATION_READ") from exc
    if not isinstance(evidence, dict):
        _stop("OWNER_AUTHORIZATION_OBJECT_REQUIRED")
    implementation_sha = evidence.get("authorized_implementation_sha")
    required_false = (
        "overwrite_allowed", "replace_allowed", "delete_allowed", "retry_allowed",
        "schedule_allowed", "recurrence_allowed", "future_batch_execution_authorized",
    )
    valid = (
        evidence.get("schema") == "TASK_014_M8_CORRECTIVE_R3_OWNER_AUTHORIZATION_V1"
        and evidence.get("status") == "AUTHORIZED_FOR_SINGLE_CORRECTIVE_R3_T3_PUBLICATION"
        and evidence.get("gate_id") == GATE_ID
        and evidence.get("drive_target") == "08_OUTPUTS"
        and evidence.get("remote_names") == list(PublicationNames.from_basename(REMOTE_BASENAME).all())
        and all(evidence.get(key) is True for key in ("create_only", "single_execution", "manual_execution_required"))
        and all(evidence.get(key) is False for key in required_false)
        and _valid_sha(implementation_sha)
    )
    if not valid:
        _stop("OWNER_AUTHORIZATION_INVALID")
    return evidence


def validate_authorization_repository_boundary(
    *, root: str | Path, authorized_implementation_sha: str, execution_sha: str,
    runner=subprocess.run,
) -> dict[str, Any]:
    """Prove audited SHA ancestry and an authorization-file-only Git diff."""
    if not _valid_sha(authorized_implementation_sha):
        _stop("AUTHORIZED_IMPLEMENTATION_SHA_INVALID")
    if not _valid_sha(execution_sha):
        _stop("EXECUTION_SHA_INVALID")
    repo = Path(root)
    try:
        ancestor = runner(
            ["git", "merge-base", "--is-ancestor", authorized_implementation_sha, execution_sha],
            cwd=repo, capture_output=True, text=True, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise CorrectivePublicationError(f"{ERROR}_AUTHORIZATION_GIT_ANCESTRY") from exc
    if ancestor.returncode != 0:
        _stop("AUTHORIZED_IMPLEMENTATION_NOT_ANCESTOR")
    try:
        changed = runner(
            ["git", "diff", "--name-only", f"{authorized_implementation_sha}..{execution_sha}", "--"],
            cwd=repo, capture_output=True, text=True, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise CorrectivePublicationError(f"{ERROR}_AUTHORIZATION_GIT_DIFF") from exc
    if changed.returncode != 0:
        _stop("AUTHORIZATION_GIT_DIFF_FAILED")
    paths = [line.strip() for line in changed.stdout.splitlines() if line.strip()]
    if paths != [OWNER_AUTHORIZATION_PATH.as_posix()]:
        _stop("POST_AUDIT_DIFF_NOT_AUTHORIZATION_ONLY")
    return {
        "authorized_implementation_sha": authorized_implementation_sha,
        "execution_sha": execution_sha,
        "changed_paths": paths,
        "implementation_is_ancestor": True,
    }


def validate_live_authorization(*, root: str | Path, execution_sha: str) -> dict[str, Any]:
    evidence = validate_owner_authorization(root=root)
    boundary = validate_authorization_repository_boundary(
        root=root,
        authorized_implementation_sha=evidence["authorized_implementation_sha"],
        execution_sha=execution_sha,
    )
    return {"evidence": evidence, "repository_boundary": boundary}


def _single_page_inventory(drive, parent: str, *, code: str, created_count: int = 0) -> list[dict[str, Any]]:
    """Make exactly one bounded list call; any continuation token is fatal."""
    try:
        page = drive.list_children_single_page(parent, page_size=1000)
    except Exception as exc:
        raise CorrectivePublicationError(f"{ERROR}_{code}", created_count=created_count) from exc
    if not isinstance(page, dict) or not isinstance(page.get("files"), list):
        _stop(f"{code}_INVALID", created_count=created_count)
    if page.get("next_page_token"):
        _stop(f"{code}_PAGINATION_PROHIBITED", created_count=created_count)
    return page["files"]


def _single_worksheet_title(metadata: Any, *, created_count: int = 0) -> str:
    sheets = metadata.get("sheets") if isinstance(metadata, dict) else None
    if not isinstance(sheets, list) or len(sheets) != 1:
        _stop("WORKSHEET_METADATA_AMBIGUOUS", created_count=created_count)
    properties = sheets[0].get("properties") if isinstance(sheets[0], dict) else None
    title = properties.get("title") if isinstance(properties, dict) else None
    if (not isinstance(title, str) or not title or properties.get("sheetType") != "GRID"
            or properties.get("index") != 0 or not isinstance(properties.get("sheetId"), int)):
        _stop("WORKSHEET_METADATA_INVALID", created_count=created_count)
    return title


def _qualified_range(title: str, cells: str) -> str:
    return "'" + title.replace("'", "''") + "'!" + cells


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
        "sheet_readback": "SHEETS_API_VALUES_GET_UNFORMATTED_A_TO_Z_FULL_USED_MATRIX",
        "semantic_readback_range": SEMANTIC_READBACK_RANGE,
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


def execute_corrective_publication(drive, *, root: str | Path, source_zip: str | Path, published_at: str, execution_sha: str) -> dict[str, Any]:
    """Execute the only permitted Sheet -> validation -> PDF -> manifest path."""
    with tempfile.TemporaryDirectory(prefix="m8-corrective-r3-") as raw:
        # Contract/timestamp policy preflight, then exact-name collision
        # preflight, precede loading the pinned product as required by TASK 014.
        _load_contract(Path(root))
        authorization = validate_live_authorization(root=root, execution_sha=execution_sha)
        try:
            parsed_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        except (AttributeError, ValueError) as exc:
            raise CorrectivePublicationError(f"{ERROR}_TIMESTAMP") from exc
        if parsed_at.tzinfo is None or parsed_at.utcoffset() is None:
            _stop("TIMESTAMP_TIMEZONE")
        parent = output_parent_id(root=root)
        names = PublicationNames.from_basename(REMOTE_BASENAME)

        # One bounded inventory checks R3 collisions and locates the immutable
        # R2 Sheet used only as a same-credential capability sentinel.
        children = _single_page_inventory(drive, parent, code="COLLISION_PREFLIGHT")
        if any(sum(item.get("name") == name for item in children if isinstance(item, dict)) for name in names.all()):
            _stop("R3_NAME_COLLISION")
        r2_sheets = [item for item in children if isinstance(item, dict) and item.get("name") == R2_SHEET_NAME]
        if len(r2_sheets) != 1:
            _stop("R2_CAPABILITY_SENTINEL_COUNT")
        if r2_sheets[0].get("mimeType") != GOOGLE_SHEETS_MIME or not r2_sheets[0].get("id"):
            _stop("R2_CAPABILITY_SENTINEL_MIME")

        remote_stage = "REMOTE_STAGE_PREMUTATION_SHEETS_CAPABILITY_GET"
        try:
            _single_worksheet_title(drive.spreadsheet_metadata_get(str(r2_sheets[0]["id"])))
        except CorrectivePublicationError:
            raise
        except Exception as exc:
            safe_status = getattr(exc, "code", None)
            safe_status = safe_status if isinstance(safe_status, int) and 400 <= safe_status <= 599 else None
            raise CorrectivePublicationError(
                f"{ERROR}_PREMUTATION_SHEETS_CAPABILITY", remote_stage=remote_stage,
                remote_operation_class="SHEETS_READONLY", error_type=type(exc).__name__,
                http_status_if_safe=safe_status,
            ) from exc

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
            "execution_sha": execution_sha,
            "authorized_implementation_sha": authorization.get("repository_boundary", {}).get("authorized_implementation_sha"),
            "source_artifact_id": 9684264254,
            "source_artifact_zip_sha256": source["source"]["zip_sha256"],
            "sheet_write_mechanism": "SHEETS_API_VALUES_UPDATE_RAW",
            "sheet_semantic_readback_verified": True, "completion_manifest_written_last": True,
            "create_only": True, "retry_performed": False, "cleanup_performed": False,
            "r2_preserved": True, "historical_series": "2016-2024", "include_2025": False,
            "release_promotion_performed": False, "overwrite_allowed": False,
            "remote_identifiers_recorded": False,
        }
        manifest_path = Path(raw) / "publication_manifest.json"
        manifest_path.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        created = 0
        remote_stage = "REMOTE_STAGE_R3_SHEET_CREATE"
        try:
            sheet = drive.create_google_sheet(names.sheet, parent)
            created = 1
            remote_stage = "REMOTE_STAGE_R3_SHEET_METADATA_GET"
            sheet_id = str(sheet.get("id") or "")
            if not sheet_id or not _metadata_ok(drive.metadata(sheet_id), names.sheet, GOOGLE_SHEETS_MIME, parent):
                _stop("SHEET_METADATA", created_count=created)
            worksheet = _single_worksheet_title(drive.spreadsheet_metadata_get(sheet_id), created_count=created)
            remote_stage = "REMOTE_STAGE_R3_SHEET_WRITE_RAW"
            update = drive.sheets_values_update_raw(sheet_id, _qualified_range(worksheet, WRITE_RANGE), matrix)
            if int(update.get("updatedRows") or -1) != 9 or int(update.get("updatedColumns") or -1) != 7 or int(update.get("updatedCells") or -1) != 63:
                _stop("SHEET_WRITE_COUNT", created_count=created)
            remote_stage = "REMOTE_STAGE_R3_SHEET_SEMANTIC_READBACK"
            qualified_readback = _qualified_range(worksheet, SEMANTIC_READBACK_RANGE)
            readback = drive.sheets_values_get(sheet_id, qualified_readback)
            observed = readback.get("values") if isinstance(readback, dict) else None
            remote_stage = "REMOTE_STAGE_SHEET_SEMANTIC_VALIDATE"
            validate_matrix(observed, expected=matrix)

            remote_stage = "REMOTE_STAGE_R3_PDF_CREATE"
            pdf = drive.put(bundle / "report.pdf", names.pdf, parent, PDF_MIME)
            created = 2
            pdf_id = str(pdf.get("id") or "")
            if not pdf_id or not _metadata_ok(drive.metadata(pdf_id), names.pdf, PDF_MIME, parent):
                _stop("PDF_METADATA", created_count=created)
            remote_stage = "REMOTE_STAGE_R3_PDF_READBACK"
            pdf_readback = Path(raw) / "pdf.readback"
            drive.get(pdf_id, pdf_readback)
            if _sha256(pdf_readback) != _sha256(bundle / "report.pdf"):
                _stop("PDF_READBACK_HASH", created_count=created)

            remote_stage = "REMOTE_STAGE_R3_MANIFEST_CREATE"
            receipt = drive.put(manifest_path, names.manifest, parent, JSON_MIME)
            created = 3
            manifest_id = str(receipt.get("id") or "")
            if not manifest_id or not _metadata_ok(drive.metadata(manifest_id), names.manifest, JSON_MIME, parent):
                _stop("MANIFEST_METADATA", created_count=created)
            manifest_readback = Path(raw) / "manifest.readback"
            drive.get(manifest_id, manifest_readback)
            if _sha256(manifest_readback) != _sha256(manifest_path):
                _stop("MANIFEST_READBACK_HASH", created_count=created)
            remote_stage = "REMOTE_STAGE_R3_FINAL_READBACK"
            final_sheet = drive.sheets_values_get(sheet_id, qualified_readback)
            validate_matrix(final_sheet.get("values") if isinstance(final_sheet, dict) else None, expected=matrix)
            final = _single_page_inventory(drive, parent, code="FINAL_INVENTORY", created_count=created)
            final_counts = {name: sum(item.get("name") == name for item in final if isinstance(item, dict)) for name in names.all()}
            if any(count != 1 for count in final_counts.values()):
                _stop("FINAL_READBACK", created_count=created)
        except ProductPublicationError as exc:
            if isinstance(exc, CorrectivePublicationError) and exc.remote_stage is None:
                exc.remote_stage = remote_stage
                exc.remote_operation_class = "DRIVE_OR_SHEETS_REMOTE_OPERATION"
                exc.error_type = type(exc).__name__
            raise
        except Exception as exc:
            safe_status = getattr(exc, "code", None)
            safe_status = safe_status if isinstance(safe_status, int) and 400 <= safe_status <= 599 else None
            raise CorrectivePublicationError(
                f"{ERROR}_REMOTE_OPERATION", created_count=created,
                remote_stage=remote_stage,
                remote_operation_class="DRIVE_OR_SHEETS_REMOTE_OPERATION",
                error_type=type(exc).__name__, http_status_if_safe=safe_status,
            ) from exc

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

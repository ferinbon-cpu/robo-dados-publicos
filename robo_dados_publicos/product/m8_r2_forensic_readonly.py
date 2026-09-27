"""TASK 013 bounded, read-only forensics for the immutable partial R2 Sheet."""
from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from robo_dados_publicos.product.publication import GOOGLE_SHEETS_MIME, PublicationNames
from robo_dados_publicos.product.siope_historical_corrective_publication import (
    EXPECTED_COLUMNS, EXPECTED_ROWS, REMOTE_BASENAME, SEMANTIC_READBACK_RANGE,
    matrix_sha256,
)
from robo_dados_publicos.storage.drive_rest import DRIVE_API, SHEETS_API

SCHEMA = "TASK_013_M8_R2_FORENSIC_READONLY_RESULT_V1"
PASS = "PASS_TASK_013_M8_R2_FORENSIC_READONLY"
STOP_BOUNDED = "STOP_FORENSIC_INVENTORY_NOT_BOUNDED"
REMOTE_STAGE_DRIVE_INVENTORY = "REMOTE_STAGE_DRIVE_INVENTORY"
REMOTE_STAGE_SHEET_METADATA_GET = "REMOTE_STAGE_SHEET_METADATA_GET"
REMOTE_STAGE_SHEET_VALUES_GET = "REMOTE_STAGE_SHEET_VALUES_GET"
DRIVE_READONLY = "DRIVE_READONLY"
SHEETS_READONLY = "SHEETS_READONLY"


class ForensicReadonlyError(RuntimeError):
    """A sanitized, non-retryable forensic stop."""


class ForensicRemoteReadError(ForensicReadonlyError):
    """Safe remote-read diagnostics that never retain the underlying exception."""

    def __init__(self, *, stage: str, operation_class: str, error_type: str,
                 http_status_if_safe: int | None):
        super().__init__("SANITIZED_REMOTE_READ_FAILED")
        self.stage = stage
        self.operation_class = operation_class
        self.error_type = error_type
        self.http_status_if_safe = http_status_if_safe

    def diagnostics(self) -> dict[str, Any]:
        return {
            "remote_stage": self.stage,
            "remote_operation_class": self.operation_class,
            "error_type": self.error_type,
            "http_status_if_safe": self.http_status_if_safe,
            "retryable": False,
        }


def _safe_error_type(exc: BaseException) -> str:
    name = type(exc).__name__
    return name if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,79}", name) else "RemoteReadError"


def _safe_http_status(exc: BaseException) -> int | None:
    """Extract only a plausible numeric status, never a response body or URL."""
    candidates = [getattr(exc, "code", None), getattr(exc, "status", None),
                  getattr(exc, "status_code", None)]
    response = getattr(exc, "response", None)
    if response is not None:
        candidates.extend((getattr(response, "status", None), getattr(response, "status_code", None)))
    return next((value for value in candidates
                 if isinstance(value, int) and not isinstance(value, bool) and 100 <= value <= 599), None)


def _sanitize_remote_error(exc: BaseException, *, stage: str,
                           operation_class: str) -> ForensicRemoteReadError:
    if isinstance(exc, ForensicRemoteReadError):
        return exc
    return ForensicRemoteReadError(
        stage=stage, operation_class=operation_class,
        error_type=_safe_error_type(exc), http_status_if_safe=_safe_http_status(exc),
    )


def _remote_call(operation, *, stage: str, operation_class: str):  # noqa: ANN001, ANN202
    try:
        return operation()
    except Exception as exc:
        raise _sanitize_remote_error(exc, stage=stage, operation_class=operation_class) from None


class ForensicReadonlyAdapter:
    """Minimal GET-only adapter; mutation verbs and mutation methods do not exist."""

    def __init__(self, token_provider, opener=urlopen):  # noqa: ANN001
        self.tokens = token_provider
        self.opener = opener

    def _get_json(self, url: str) -> dict[str, Any]:
        request = Request(url, headers={"Authorization": f"Bearer {self.tokens.access_token()}"}, method="GET")
        with self.opener(request, timeout=60) as response:
            value = json.loads(response.read().decode("utf-8"))
        if not isinstance(value, dict):
            raise ForensicReadonlyError("REMOTE_READ_RESPONSE_NOT_OBJECT")
        return value

    def list_children_single_page(self, parent_id: str, page_size: int = 1000) -> dict[str, Any]:
        if not isinstance(page_size, int) or not 1 <= page_size <= 1000:
            raise ForensicReadonlyError("INVENTORY_PAGE_SIZE_INVALID")
        query = f"'{parent_id}' in parents and trashed = false"
        params = urlencode({
            "q": query, "pageSize": str(page_size),
            "fields": "files(id,name,mimeType,size,modifiedTime),nextPageToken",
        })
        payload = _remote_call(
            lambda: self._get_json(f"{DRIVE_API}/files?{params}"),
            stage=REMOTE_STAGE_DRIVE_INVENTORY, operation_class=DRIVE_READONLY,
        )
        files = payload.get("files")
        if not isinstance(files, list):
            raise ForensicReadonlyError("INVENTORY_FILES_INVALID")
        return {"files": files, "next_page_token": payload.get("nextPageToken")}

    def sheets_values_get(self, spreadsheet_id: str, range_a1: str) -> dict[str, Any]:
        params = urlencode({
            "majorDimension": "ROWS", "valueRenderOption": "UNFORMATTED_VALUE",
            "dateTimeRenderOption": "FORMATTED_STRING",
        })
        encoded_range = quote(range_a1, safe="")
        return _remote_call(
            lambda: self._get_json(f"{SHEETS_API}/{quote(spreadsheet_id)}/values/{encoded_range}?{params}"),
            stage=REMOTE_STAGE_SHEET_VALUES_GET, operation_class=SHEETS_READONLY,
        )

    def spreadsheet_metadata_get(self, spreadsheet_id: str) -> dict[str, Any]:
        """Read only the worksheet properties needed for deterministic selection."""
        fields = quote("sheets(properties(sheetId,title,index,sheetType))")
        return _remote_call(
            lambda: self._get_json(f"{SHEETS_API}/{quote(spreadsheet_id)}?fields={fields}"),
            stage=REMOTE_STAGE_SHEET_METADATA_GET, operation_class=SHEETS_READONLY,
        )


def _single_worksheet_title(metadata: Any) -> str:
    """Select the sole worksheet because TASK 012 defines no canonical title."""
    if not isinstance(metadata, dict) or not isinstance(metadata.get("sheets"), list):
        raise ForensicReadonlyError("SHEET_WORKSHEET_METADATA_AMBIGUOUS")
    sheets = metadata["sheets"]
    if not sheets:
        raise ForensicReadonlyError("SHEET_WORKSHEET_NOT_FOUND")
    if len(sheets) != 1:
        raise ForensicReadonlyError("SHEET_WORKSHEET_AMBIGUOUS")
    properties = sheets[0].get("properties") if isinstance(sheets[0], dict) else None
    title = properties.get("title") if isinstance(properties, dict) else None
    if not isinstance(title, str) or not title or properties.get("sheetType") != "GRID":
        raise ForensicReadonlyError("SHEET_WORKSHEET_METADATA_AMBIGUOUS")
    return title


def _qualified_range(worksheet_title: str) -> str:
    """Quote a provider-returned worksheet title according to A1 notation."""
    return f"'{worksheet_title.replace(chr(39), chr(39) * 2)}'!{SEMANTIC_READBACK_RANGE}"


def _base_result() -> dict[str, Any]:
    return {
        "schema": SCHEMA, "status": PASS, "readonly": True,
        "remote_mutations_performed": 0, "retry_performed": False,
        "cleanup_performed": False, "repair_performed": False,
        "source_recollection_performed": False, "include_2025": False,
        "release_promotion_performed": False, "owner_decision_required": True,
        "historical_failed_run_status": "STOP_M8_SIOPE_HISTORICAL_CORRECTIVE_PUBLICATION_REMOTE_OPERATION",
        "historical_created_count": 1, "historical_partial_sheet_created": True,
        "historical_pdf_created": False, "historical_manifest_created": False,
        "historically_recorded_failure_stage": "UNKNOWN_REMOTE_OPERATION",
        "remote_stage": None, "remote_operation_class": None,
        "error_type": None, "http_status_if_safe": None, "retryable": False,
        "remote_identifiers_exposed": False, "secret_values_exposed": False,
    }


def classify_matrix(observed: Any, canonical: list[list[str]]) -> dict[str, Any]:
    values = observed if isinstance(observed, list) else []
    rows = len(values)
    max_columns = max((len(row) for row in values if isinstance(row, list)), default=0)
    well_typed = all(isinstance(row, list) and all(isinstance(cell, str) for cell in row) for row in values)
    extra = any(
        isinstance(row, list) and any(cell not in ("", None) for cell in row[EXPECTED_COLUMNS:])
        for row in values[:EXPECTED_ROWS]
    ) or any(
        isinstance(row, list) and any(cell not in ("", None) for cell in row)
        for row in values[EXPECTED_ROWS:]
    )
    canonical_window = [row[:EXPECTED_COLUMNS] for row in values[:EXPECTED_ROWS] if isinstance(row, list)]
    header_match = bool(canonical_window) and canonical_window[0] == canonical[0]
    exact = well_typed and values == canonical
    populated = sum(cell not in ("", None) for row in values if isinstance(row, list) for cell in row)
    if extra:
        state = "SHEET_EXTRA_POPULATED_CELLS"
    elif exact:
        state = "SHEET_EXACT_CANONICAL_9X7"
    elif populated == 0:
        state = "SHEET_EMPTY"
    elif rows < EXPECTED_ROWS or max_columns < EXPECTED_COLUMNS:
        state = "SHEET_PARTIAL"
    else:
        state = "SHEET_MALFORMED"
    return {
        "state": state, "readable": True,
        "canonical_row_count_expected": EXPECTED_ROWS,
        "canonical_column_count_expected": EXPECTED_COLUMNS,
        "observed_row_count": rows, "observed_max_column_count": max_columns,
        "header_match": header_match, "canonical_matrix_match": exact,
        "extra_populated_cells": extra,
        "canonical_matrix_sha256": matrix_sha256(canonical),
    }


def _conclusion(inventory: dict[str, Any], state: str) -> str:
    counts = (inventory["r2_sheet_exact_name_count"], inventory["r2_pdf_exact_name_count"], inventory["r2_manifest_exact_name_count"])
    if counts[0] != 1:
        return "FORENSIC_R2_INVENTORY_AMBIGUOUS"
    if counts[1:] != (0, 0):
        return "FORENSIC_R2_REMOTE_STATE_UNEXPECTED"
    return {
        "SHEET_EXACT_CANONICAL_9X7": "FORENSIC_R2_SHEET_EXACT_CANONICAL_PDF_MANIFEST_ABSENT",
        "SHEET_PARTIAL": "FORENSIC_R2_SHEET_PARTIAL_PDF_MANIFEST_ABSENT",
        "SHEET_EMPTY": "FORENSIC_R2_SHEET_EMPTY_PDF_MANIFEST_ABSENT",
        "SHEET_READ_FAILED": "FORENSIC_R2_READ_FAILED",
        "SHEET_WORKSHEET_NOT_FOUND": "FORENSIC_R2_READ_FAILED",
        "SHEET_WORKSHEET_AMBIGUOUS": "FORENSIC_R2_READ_FAILED",
        "SHEET_WORKSHEET_METADATA_AMBIGUOUS": "FORENSIC_R2_READ_FAILED",
    }.get(state, "FORENSIC_R2_REMOTE_STATE_UNEXPECTED")


def run_forensic_readonly(adapter, *, parent_id: str, canonical_matrix: list[list[str]]) -> tuple[dict[str, Any], int]:  # noqa: ANN001
    result = _base_result()
    names = PublicationNames.from_basename(REMOTE_BASENAME)
    try:
        page = adapter.list_children_single_page(parent_id, page_size=1000)
        if page.get("next_page_token"):
            raise ForensicReadonlyError(STOP_BOUNDED)
        files = page.get("files")
        if not isinstance(files, list):
            raise ForensicReadonlyError("FORENSIC_INVENTORY_INVALID")
    except Exception as exc:
        result.update(status=STOP_BOUNDED if str(exc) == STOP_BOUNDED else "STOP_FORENSIC_INVENTORY_READ_FAILED")
        result["inventory"] = {"r2_sheet_exact_name_count": 0, "r2_pdf_exact_name_count": 0, "r2_manifest_exact_name_count": 0, "pagination_observed": str(exc) == STOP_BOUNDED}
        result["sheet_forensics"] = {"state": "SHEET_READ_FAILED", "readable": False}
        result["forensic_conclusion"] = "FORENSIC_R2_READ_FAILED"
        if isinstance(exc, ForensicRemoteReadError):
            result.update(exc.diagnostics())
        elif str(exc) != STOP_BOUNDED:
            result.update(_sanitize_remote_error(
                exc, stage=REMOTE_STAGE_DRIVE_INVENTORY,
                operation_class=DRIVE_READONLY,
            ).diagnostics())
        return result, 20

    matches = {name: [item for item in files if isinstance(item, dict) and item.get("name") == name] for name in names.all()}
    inventory = {
        "r2_sheet_exact_name_count": len(matches[names.sheet]),
        "r2_pdf_exact_name_count": len(matches[names.pdf]),
        "r2_manifest_exact_name_count": len(matches[names.manifest]),
        "pagination_observed": False,
    }
    result["inventory"] = inventory
    sheet_forensics: dict[str, Any]
    if inventory["r2_sheet_exact_name_count"] == 0:
        sheet_forensics = {"state": "SHEET_NOT_FOUND", "readable": False, "mime_type_match": False}
    elif inventory["r2_sheet_exact_name_count"] > 1:
        sheet_forensics = {"state": "SHEET_DUPLICATE", "readable": False, "mime_type_match": False}
    else:
        sheet = matches[names.sheet][0]
        mime_match = sheet.get("mimeType") == GOOGLE_SHEETS_MIME
        try:
            if not mime_match or not isinstance(sheet.get("id"), str) or not sheet["id"]:
                raise ForensicReadonlyError("SHEET_METADATA_INVALID")
            metadata = _remote_call(
                lambda: adapter.spreadsheet_metadata_get(sheet["id"]),
                stage=REMOTE_STAGE_SHEET_METADATA_GET, operation_class=SHEETS_READONLY,
            )
            worksheet_title = _single_worksheet_title(metadata)
            response = _remote_call(
                lambda: adapter.sheets_values_get(sheet["id"], _qualified_range(worksheet_title)),
                stage=REMOTE_STAGE_SHEET_VALUES_GET, operation_class=SHEETS_READONLY,
            )
            sheet_forensics = classify_matrix(response.get("values", []), canonical_matrix)
            sheet_forensics["mime_type_match"] = True
            sheet_forensics["worksheet_count"] = 1
            sheet_forensics["worksheet_selection"] = "EXACTLY_ONE_WORKSHEET_EXPLICITLY_QUALIFIED"
        except Exception as exc:
            safe_states = {
                "SHEET_WORKSHEET_NOT_FOUND", "SHEET_WORKSHEET_AMBIGUOUS",
                "SHEET_WORKSHEET_METADATA_AMBIGUOUS",
            }
            state = str(exc) if str(exc) in safe_states else "SHEET_READ_FAILED"
            sheet_forensics = {
                "state": state, "readable": False, "mime_type_match": mime_match,
                "worksheet_selection": "NOT_PROVEN",
            }
            if isinstance(exc, ForensicRemoteReadError):
                result.update(exc.diagnostics())
    result["sheet_forensics"] = sheet_forensics
    result["forensically_proven_remote_state"] = sheet_forensics["state"]
    result["forensic_conclusion"] = _conclusion(inventory, sheet_forensics["state"])
    if result["forensic_conclusion"] in ("FORENSIC_R2_READ_FAILED", "FORENSIC_R2_INVENTORY_AMBIGUOUS"):
        result["status"] = "STOP_TASK_013_FORENSIC_EVIDENCE_INCOMPLETE"
        return result, 21
    return result, 0

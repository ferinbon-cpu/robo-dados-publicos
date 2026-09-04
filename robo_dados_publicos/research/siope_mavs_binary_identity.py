from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class Task120Stop(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task120Stop(code)


def validate_task120_contract(data: dict[str, Any]) -> dict[str, Any]:
    _require(data.get("schema") == "TASK120_SIOPE_MAVS_BINARY_IDENTITY_CONTRACT_V1", "TASK120_SCHEMA")
    _require(data.get("mode") == "T1_SINGLE_USE_EXACT_DRIVE_BINARY_IDENTITY", "TASK120_MODE")
    source = data.get("source") or {}
    _require(source.get("drive_file_id") == "17Fl8opb1pkqdFa485-bkQR3j6LnApnE-", "TASK120_FILE_ID")
    _require(source.get("expected_title") == "Demonstrativo SIOPE-MAVS - 1º BIMESTRE 2026.pdf", "TASK120_TITLE")
    _require(source.get("expected_mime_type") == "application/pdf", "TASK120_MIME")

    budget = data.get("request_budget") or {}
    _require(budget.get("drive_metadata_reads_max") == 1, "TASK120_METADATA_BUDGET")
    _require(budget.get("drive_media_reads_max") == 1, "TASK120_MEDIA_BUDGET")
    for key in ("drive_searches","drive_lists","drive_writes"):
        _require(budget.get(key) == 0, f"TASK120_{key.upper()}")
    for key in ("retry","recurrence","schedule"):
        _require(budget.get(key) is False, f"TASK120_{key.upper()}")

    processing = data.get("processing") or {}
    for key in ("compute_sha256","compute_bytes","verify_pdf_magic","temporary_materialization_only"):
        _require(processing.get(key) is True, f"TASK120_{key.upper()}")
    for key in ("text_extraction","ocr","ontology_scan","semantic_reinterpretation","persistent_raw_copy"):
        _require(processing.get(key) is False, f"TASK120_{key.upper()}")

    promotion = data.get("promotion") or {}
    _require(promotion.get("source_binary_identity_only") is True, "TASK120_IDENTITY_ONLY")
    for key in ("financial_identity","transaction_identity","implementation","causal_effect"):
        _require(promotion.get(key) is False, f"TASK120_PROMOTION_{key.upper()}")

    boundaries = data.get("hard_boundaries") or {}
    _require(boundaries and all(value == 0 for value in boundaries.values()), "TASK120_HARD_BOUNDARY")
    _require(data.get("future_execution_authorized") is False, "TASK120_FUTURE")
    return data


def load_task120_contract(path: str | Path) -> dict[str, Any]:
    try:
        data=json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise Task120Stop("TASK120_CONTRACT_MISSING") from exc
    except json.JSONDecodeError as exc:
        raise Task120Stop("TASK120_CONTRACT_JSON") from exc
    _require(isinstance(data,dict),"TASK120_CONTRACT_OBJECT")
    return validate_task120_contract(data)

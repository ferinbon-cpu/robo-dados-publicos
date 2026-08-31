"""Fail-closed BI projection validator used by BI-001 fixtures and future materializers.

This module deliberately contains no transport, Drive or publication dependency.
BI rows are derived projections, never a writable source of truth.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable

CONTRACT_PATH = Path(__file__).resolve().parents[2] / "config/bi/analytics_output.v1.json"
FORBIDDEN_FIELDS = {"cpf", "rg", "phone", "telephone", "email", "access_token", "refresh_token", "secret", "password", "credential", "oauth"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class BIModelError(ValueError):
    """A deterministic STOP in the analytical projection."""


def _stop(code: str) -> None:
    raise BIModelError(f"STOP_BI_001_{code}")


def load_contract(path: str | Path = CONTRACT_PATH) -> dict:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        raise BIModelError("STOP_BI_001_CONTRACT_INVALID") from exc
    if value.get("task") != "BI_001" or value.get("tier") != "T0_OFFLINE":
        _stop("CONTRACT_BOUNDARY")
    datasets = value.get("datasets")
    if not isinstance(datasets, list) or len(datasets) != 6:
        _stop("CONTRACT_DATASETS")
    return value


def deterministic_key(dataset_id: str, values: Iterable[Any]) -> str:
    payload = json.dumps([dataset_id, *values], ensure_ascii=False, separators=(",", ":"))
    return f"BI_{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:24]}"


def _valid_temporal(value: str, kind: str) -> bool:
    try:
        if kind == "date":
            date.fromisoformat(value)
        else:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                return False
        return True
    except (TypeError, ValueError):
        return False


def _validate_type(field: dict, value: Any) -> bool:
    kind = field["data_type"]
    if kind == "text":
        return isinstance(value, str)
    if kind == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind in {"number", "currency"}:
        return isinstance(value, (int, float, Decimal)) and not isinstance(value, bool)
    if kind == "boolean":
        return isinstance(value, bool)
    if kind in {"date", "datetime"}:
        return isinstance(value, str) and _valid_temporal(value, kind)
    return False


def _contains_forbidden(value: Any) -> bool:
    if isinstance(value, dict):
        return any(str(key).casefold() in FORBIDDEN_FIELDS or _contains_forbidden(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden(item) for item in value)
    return False


def build_dataset(dataset_id: str, rows: Iterable[dict], contract: dict | None = None) -> list[dict]:
    """Validate and deterministically order already-derived, sanitized rows."""
    contract = contract or load_contract()
    spec = next((item for item in contract["datasets"] if item["dataset_id"] == dataset_id), None)
    if spec is None:
        _stop("DATASET_UNKNOWN")
    fields = {field["name"]: field for field in spec["fields"]}
    primary_key = spec["primary_key"]
    output: list[dict] = []
    seen: set[tuple] = set()
    for raw in rows:
        if not isinstance(raw, dict) or _contains_forbidden(raw):
            _stop("PRIVACY")
        unknown = set(raw) - set(fields)
        if unknown:
            _stop("FIELD_NOT_PROVEN")
        normalized = {}
        for name, field in fields.items():
            value = raw.get(name)
            if value is None:
                if not field["nullable"]:
                    _stop(f"{dataset_id}_{name}_REQUIRED")
                normalized[name] = None
                continue
            if not _validate_type(field, value):
                _stop(f"{dataset_id}_{name}_TYPE")
            if field.get("enum") and value not in field["enum"]:
                _stop(f"{dataset_id}_{name}_ENUM")
            if field.get("format") == "sha256" and not HEX64.fullmatch(value):
                _stop(f"{dataset_id}_{name}_SHA256")
            normalized[name] = value
        key = tuple(normalized[name] for name in primary_key)
        if key in seen:
            _stop(f"{dataset_id}_DUPLICATE_PRIMARY_KEY")
        seen.add(key)
        if not str(normalized.get("provenance_id", normalized.get("provenance_reference", ""))).strip():
            _stop(f"{dataset_id}_PROVENANCE")
        if dataset_id == "BI_SIOPE_SERIES":
            year, period = normalized["year"], normalized["annual_period"]
            if year == 2025 or year not in range(2016, 2025) or period != ("P1" if year == 2016 else "P6"):
                _stop("SIOPE_CLOSED_SERIES_BOUNDARY")
        if dataset_id == "BI_RECONCILIACAO":
            if normalized["status"] == "MATCH_CANDIDATE" and normalized["financial_identity_proven"]:
                _stop("CANDIDATE_FINANCIAL_IDENTITY")
            if normalized["identity_status"] == "PROVEN" and not normalized["financial_identity_proven"]:
                _stop("PROVEN_IDENTITY_INCONSISTENT")
        output.append(normalized)
    return sorted(output, key=lambda row: tuple(str(row[name]) for name in primary_key))

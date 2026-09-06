from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task185_tcesp_json_api_2026.v1.json"
OBSERVATION_CONTRACT = ROOT / "config/municipal_accounting_observation.v1.json"


class Task185JsonStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task185JsonStop(code)


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split()).strip()
    return text or None


def _ascii_upper(value: Any) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.upper().split())


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _amount(value: Any) -> str:
    text = str(value or "").strip().replace("R$", "").replace(" ", "")
    _stop(bool(text), "TASK185_JSON_AMOUNT_MISSING")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    text = re.sub(r"[^0-9.\-]", "", text)
    try:
        return f"{Decimal(text):.2f}"
    except (InvalidOperation, ValueError) as exc:
        raise Task185JsonStop("TASK185_JSON_AMOUNT_INVALID") from exc


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    contract = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(contract.get("schema") == "TASK185_TCESP_JSON_API_2026_V1", "TASK185_JSON_CONTRACT_SCHEMA")
    source = contract["source"]
    _stop(source["months"] == list(range(1, 9)), "TASK185_JSON_MONTH_SCOPE")
    _stop(source["probe_month"] == 1, "TASK185_JSON_PROBE_MONTH")
    _stop(source["max_requests"] == 8, "TASK185_JSON_REQUEST_BUDGET")
    _stop(source["retry"] == 0, "TASK185_JSON_RETRY")
    _stop(source["follow_redirects"] is False, "TASK185_JSON_REDIRECT")
    _stop(int(source.get("network_timeout_seconds") or 0) == 180, "TASK185_JSON_TIMEOUT")
    _stop(contract["authorization"]["single_use"] is True, "TASK185_JSON_AUTH_SINGLE_USE")
    return contract


def validate_payload(payload: bytes, *, month: int, contract_path: str | Path = DEFAULT_CONTRACT) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    contract = load_contract(contract_path)
    source = contract["source"]
    _stop(month in source["months"], "TASK185_JSON_MONTH_NOT_AUTHORIZED")
    _stop(bool(payload), "TASK185_JSON_EMPTY_BODY")
    _stop(len(payload) <= int(source["max_response_bytes_per_month"]), "TASK185_JSON_BODY_TOO_LARGE")
    try:
        obj = json.loads(payload.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Task185JsonStop("TASK185_JSON_PARSE") from exc
    _stop(isinstance(obj, list), "TASK185_JSON_TOP_LEVEL_NOT_ARRAY")

    required = set(source["expected_fields"])
    rows: list[dict[str, Any]] = []
    extra_fields: set[str] = set()
    for raw in obj:
        _stop(isinstance(raw, dict), "TASK185_JSON_ROW_NOT_OBJECT")
        missing = required - set(raw)
        _stop(not missing, "TASK185_JSON_SCHEMA_MISSING_FIELDS")
        extra_fields.update(set(raw) - required)
        row = {str(k): raw[k] for k in raw}
        rows.append(row)

    month_names = {
        1:"JANEIRO",2:"FEVEREIRO",3:"MARCO",4:"ABRIL",5:"MAIO",6:"JUNHO",7:"JULHO",8:"AGOSTO"
    }
    observed_months = {_ascii_upper(row.get("mes")) for row in rows if row.get("mes")}
    expected_month = month_names[month]
    _stop(not observed_months or observed_months == {expected_month}, "TASK185_JSON_MONTH_CONTENT_DRIFT")

    return rows, {
        "month": month,
        "body_sha256": hashlib.sha256(payload).hexdigest(),
        "body_bytes": len(payload),
        "row_count": len(rows),
        "extra_fields": sorted(extra_fields),
        "observed_month_labels": sorted(observed_months),
    }


def normalize_stage(value: Any, contract: Mapping[str, Any]) -> tuple[str, str | None]:
    observed = _ascii_upper(value)
    for stage, aliases in contract["stage_normalization"].items():
        for alias in aliases:
            if observed == _ascii_upper(alias):
                modifier = "REINFORCEMENT" if _ascii_upper(alias) == "REFORCO" else None
                return stage, modifier
    return "OTHER_REVIEW", None


def normalize_json_expense_row(row: Mapping[str, Any], *, source_body_sha256: str, month: int) -> dict[str, Any]:
    contract = load_contract()
    observation_contract = json.loads(OBSERVATION_CONTRACT.read_text(encoding="utf-8"))
    source = contract["source"]
    required = set(source["expected_fields"])
    _stop(required <= set(row), "TASK185_JSON_NORMALIZE_SCHEMA")

    stage, modifier = normalize_stage(row.get("evento"), contract)
    amount = _amount(row.get("vl_despesa"))
    empenho = _clean(row.get("nr_empenho"))
    selected = {name: _clean(row.get(name)) for name in source["expected_fields"]}
    source_record_hash = hashlib.sha256(_canonical_bytes([source_body_sha256, selected])).hexdigest()
    observation_id = "ACCTOBS_" + hashlib.sha256(
        _canonical_bytes([
            source["source_id"],
            2026,
            month,
            empenho,
            stage,
            modifier,
            _clean(row.get("dt_emissao_despesa")),
            amount,
            source_record_hash,
        ])
    ).hexdigest()[:24]

    return {
        "observation_id": observation_id,
        "schema": observation_contract["schema"],
        "source_id": source["source_id"],
        "source_role": "OFFICIAL_EXTERNAL_CONTROL_RECORD",
        "entity_name": _clean(row.get("orgao")) or "Limeira",
        "fiscal_year": 2026,
        "stage": stage,
        "source_stage": _clean(row.get("evento")),
        "stage_modifier": modifier,
        "amount_semantic": observation_contract["amount_semantics"][stage],
        "amount_brl": amount,
        "event_date": None,
        "expense_issue_date": _clean(row.get("dt_emissao_despesa")),
        "event_month": month,
        "source_record_hash": source_record_hash,
        "identity_status": "ACCOUNTING_TRANSACTION_KEY_AVAILABLE" if empenho else "SOURCE_RECORD_ONLY",
        "transaction_keys": {
            "source_expense_identifier": None,
            "fiscal_year_plus_empenho": f"2026:{empenho}" if empenho else None,
        },
        "programmatic_dimensions": {
            "function": None,
            "subfunction": None,
            "program_code": None,
            "program_name": None,
            "action_code": None,
            "action_name": None,
            "funding_source": None,
            "application_code": None,
            "expense_element": None,
            "procurement_modality": None,
        },
        "supplier_public_id": _clean(row.get("id_fornecedor")),
        "supplier_name": _clean(row.get("nm_fornecedor")),
        "source_month": month,
        "policy_domain_hints": [],
        "policy_domain_hint_basis": {},
        "policy_link_status": "NOT_PROVEN",
        "policy_identity_proven": False,
        "financial_policy_identity_proven": False,
        "source_description": None,
        "history_text": None,
        "evidence_status": "DIRECT_EXPLICIT_CONTROL_RECORD",
    }


def source_capabilities(observations: list[Mapping[str, Any]]) -> list[str]:
    stages = {str(row.get("stage") or "") for row in observations}
    caps = {"COMMITMENT_NUMBER", "SUPPLIER_AMOUNT", "EXPENSE_ISSUE_DATE", "EVENT_MONTH"}
    if "COMMITMENT" in stages:
        caps.add("COMMITMENT_AMOUNTS")
    if "LIQUIDATION" in stages:
        caps.add("LIQUIDATION_AMOUNTS")
    if "PAYMENT" in stages:
        caps.add("PAYMENT_AMOUNTS")
    if "REVERSAL" in stages:
        caps.add("REVERSAL_EVENTS")
    return sorted(caps)

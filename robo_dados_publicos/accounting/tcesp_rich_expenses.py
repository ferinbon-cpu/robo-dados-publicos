from __future__ import annotations

import csv
import hashlib
import io
import json
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task187_tcesp_rich_expenses_2026.v1.json"


class Task187RichExpenseStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task187RichExpenseStop(code)


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
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _amount(value: Any) -> str:
    text = str(value or "").strip()
    _stop(bool(text), "TASK187_AMOUNT_EMPTY")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        return f"{Decimal(text):.2f}"
    except (InvalidOperation, ValueError) as exc:
        raise Task187RichExpenseStop("TASK187_AMOUNT_INVALID") from exc


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK187_TCESP_RICH_EXPENSES_2026_V1", "TASK187_SCHEMA")
    _stop(obj.get("mode") == "OWNER_SUPPLIED_OFFICIAL_ZIP_OFFLINE", "TASK187_MODE")
    _stop(obj["source"]["fiscal_year"] == 2026, "TASK187_YEAR")
    _stop(obj["source"]["months_expected"] == [1, 2, 3, 4, 5, 6, 7], "TASK187_MONTHS")
    _stop(obj["remote_effects"]["source_network"] is False, "TASK187_NETWORK")
    return obj


def parse_csv_bytes(
    payload: bytes,
    *,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> list[dict[str, str]]:
    contract = load_contract(contract_path)
    try:
        text = payload.decode(contract["source"]["csv_encoding"])
    except UnicodeDecodeError as exc:
        raise Task187RichExpenseStop("TASK187_ENCODING") from exc

    reader = csv.DictReader(io.StringIO(text), delimiter=contract["source"]["delimiter"])
    _stop(reader.fieldnames == contract["source"]["exact_headers"], "TASK187_HEADERS")
    rows = [dict(row) for row in reader]
    _stop(bool(rows), "TASK187_EMPTY")

    ids: set[str] = set()
    months: set[int] = set()
    allowed_missing = set(contract["source"]["allowed_empty_fields"])
    for row in rows:
        for field in contract["source"]["exact_headers"]:
            if field in allowed_missing:
                continue
            _stop(bool(str(row.get(field) or "").strip()), f"TASK187_REQUIRED_{field}")
        rid = str(row["id_despesa_detalhe"]).strip()
        _stop(rid not in ids, "TASK187_DUPLICATE_OFFICIAL_ID")
        ids.add(rid)
        _stop(row["ano_exercicio"] == "2026", "TASK187_ROW_YEAR")
        _stop(row["ds_municipio"] == "Limeira", "TASK187_MUNICIPALITY")
        month = int(row["mes_referencia"])
        _stop(month in contract["source"]["months_expected"], "TASK187_MONTH")
        months.add(month)
        _amount(row["vl_despesa"])

    _stop(sorted(months) == contract["source"]["months_expected"], "TASK187_MONTH_COVERAGE")
    _stop(len(ids) == contract["observed"]["unique_official_ids"], "TASK187_ID_COUNT")
    return rows


def validate_real_payload(
    payload: bytes,
    *,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    _stop(hashlib.sha256(payload).hexdigest() == contract["source"]["csv_sha256"], "TASK187_REAL_CSV_HASH")
    rows = parse_csv_bytes(payload, contract_path=contract_path)
    _stop(len(rows) == contract["observed"]["row_count"], "TASK187_ROW_COUNT")
    month_counts: dict[str, int] = {}
    organ_counts: dict[str, int] = {}
    event_counts: dict[str, int] = {}
    empty_element_rows = 0
    for row in rows:
        month = str(int(row["mes_referencia"]))
        month_counts[month] = month_counts.get(month, 0) + 1
        organ = str(row["ds_orgao"]).strip()
        organ_counts[organ] = organ_counts.get(organ, 0) + 1
        event = str(row["tp_despesa"]).strip()
        event_counts[event] = event_counts.get(event, 0) + 1
        if not str(row.get("ds_elemento") or "").strip():
            empty_element_rows += 1
    _stop(month_counts == contract["observed"]["month_row_counts"], "TASK187_MONTH_COUNTS")
    _stop(organ_counts == contract["observed"]["organs"], "TASK187_ORGAN_COUNTS")
    _stop(event_counts == contract["observed"]["events"], "TASK187_EVENT_COUNTS")
    _stop(empty_element_rows == contract["observed"]["expense_element_empty_rows"], "TASK187_ELEMENT_EMPTY_COUNT")
    return {
        "status": "PASS_REAL_TCESP_RICH_EXPENSE_PAYLOAD",
        "row_count": len(rows),
        "unique_official_ids": len({row["id_despesa_detalhe"] for row in rows}),
        "month_row_counts": month_counts,
        "organ_counts": organ_counts,
        "event_counts": event_counts,
        "expense_element_empty_rows": empty_element_rows,
    }


def normalize_stage(value: Any) -> tuple[str, str | None]:
    normalized = _ascii_upper(value)
    if normalized == "REFORCO":
        return "COMMITMENT", "REINFORCEMENT"
    if normalized in {"EMPENHADO", "EMPENHO", "EMISSAO DE EMPENHO"}:
        return "COMMITMENT", None
    if normalized in {"LIQUIDADO", "LIQUIDACAO"} or normalized.endswith(" LIQUIDADO"):
        return "LIQUIDATION", None
    if normalized in {"PAGO", "PAGAMENTO"} or normalized.endswith(" PAGO"):
        return "PAYMENT", None
    if normalized in {"ANULADO", "ANULACAO", "CANCELADO", "CANCELAMENTO", "ESTORNO"}:
        return "REVERSAL", None
    return "OTHER_REVIEW", None


def _policy_domain_hints(programmatic: Mapping[str, Any], contract: Mapping[str, Any]) -> tuple[list[str], dict[str, list[str]]]:
    text = _ascii_upper(
        " ".join(
            str(programmatic.get(key) or "")
            for key in ("function", "subfunction", "program_name", "action_name")
        )
    )
    hints: list[str] = []
    basis: dict[str, list[str]] = {}
    for domain, markers in contract["policy_domain_hints"].items():
        found = [marker for marker in markers if _ascii_upper(marker) in text]
        if found:
            hints.append(domain)
            basis[domain] = found
    return sorted(set(hints)), basis


def normalize_rich_expense_row(
    row: Mapping[str, Any],
    *,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    missing = [field for field in contract["source"]["exact_headers"] if field not in row]
    _stop(not missing, "TASK187_SOURCE_SCHEMA_MISSING_COLUMNS")

    official_id = _clean(row.get("id_despesa_detalhe"))
    _stop(bool(official_id), "TASK187_OFFICIAL_ID")
    stage, stage_modifier = normalize_stage(row.get("tp_despesa"))
    amount = _amount(row.get("vl_despesa"))
    empenho = _clean(row.get("nr_empenho"))
    supplier_public_id = _clean(row.get("identificador_despesa"))
    supplier_name = _clean(row.get("ds_despesa"))

    programmatic = {
        "function": _clean(row.get("ds_funcao_governo")),
        "subfunction": _clean(row.get("ds_subfuncao_governo")),
        "program_code": _clean(row.get("cd_programa")),
        "program_name": _clean(row.get("ds_programa")),
        "action_code": _clean(row.get("cd_acao")),
        "action_name": _clean(row.get("ds_acao")),
        "funding_source": _clean(row.get("ds_fonte_recurso")),
        "application_code": _clean(row.get("ds_cd_aplicacao_fixo")),
        "expense_element": _clean(row.get("ds_elemento")),
        "procurement_modality": _clean(row.get("ds_modalidade_lic")),
    }
    hints, hint_basis = _policy_domain_hints(programmatic, contract)

    selected_source = {
        field: _clean(row.get(field))
        for field in contract["source"]["exact_headers"]
    }
    source_record_hash = _sha(selected_source)
    amount_semantic = contract["amount_semantics"][stage]

    return {
        "observation_id": f"ACCTOBS_TCESP_2026_{official_id}",
        "schema": "MUNICIPAL_ACCOUNTING_OBSERVATION_V1",
        "source_id": contract["source"]["source_id"],
        "source_role": "CONTROL_PRIMARY",
        "entity_name": _clean(row.get("ds_orgao")),
        "fiscal_year": 2026,
        "stage": stage,
        "source_stage": _clean(row.get("tp_despesa")),
        "stage_modifier": stage_modifier,
        "amount_semantic": amount_semantic,
        "amount_brl": amount,
        "event_date": None,
        "expense_issue_date": _clean(row.get("dt_emissao_despesa")),
        "event_month": int(row["mes_referencia"]),
        "source_month": int(row["mes_referencia"]),
        "official_record_id": official_id,
        "source_record_hash": source_record_hash,
        "identity_status": "ACCOUNTING_TRANSACTION_KEY_AVAILABLE",
        "transaction_keys": {
            "official_detail_id": official_id,
            "source_expense_identifier": official_id,
            "fiscal_year_plus_empenho": f"2026:{empenho}" if empenho else None,
        },
        "programmatic_dimensions": programmatic,
        "policy_domain_hints": hints,
        "policy_domain_hint_basis": hint_basis,
        "policy_link_status": "NOT_PROVEN",
        "policy_identity_proven": False,
        "financial_policy_identity_proven": False,
        "supplier_public_id": supplier_public_id,
        "supplier_name": supplier_name,
        "source_description": supplier_name,
        "history_text": _clean(row.get("historico_despesa")),
        "evidence_status": "DIRECT_EXPLICIT_CONTROL_RECORD",
    }


def normalize_csv_bytes(
    payload: bytes,
    *,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> list[dict[str, Any]]:
    return [
        normalize_rich_expense_row(row, contract_path=contract_path)
        for row in parse_csv_bytes(payload, contract_path=contract_path)
    ]

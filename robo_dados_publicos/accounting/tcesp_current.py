from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ADAPTER = ROOT / "config/tcesp_current_expense_adapter.v1.json"
DEFAULT_OBSERVATION = ROOT / "config/municipal_accounting_observation.v1.json"


class Task173Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task173Stop(code)


def _ascii_upper(value: Any) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.upper().split())


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split()).strip()
    return text or None


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _amount(value: Any) -> str:
    text = str(value or "").strip()
    text = text.replace("R$", "").replace(" ", "")
    if not text:
        raise Task173Stop("TASK173_AMOUNT_MISSING")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    text = re.sub(r"[^0-9.\-]", "", text)
    try:
        return f"{Decimal(text):.2f}"
    except (InvalidOperation, ValueError):
        raise Task173Stop("TASK173_AMOUNT_INVALID")


def load_contracts(
    adapter_path: str | Path = DEFAULT_ADAPTER,
    observation_path: str | Path = DEFAULT_OBSERVATION,
) -> tuple[dict[str, Any], dict[str, Any]]:
    adapter = json.loads(Path(adapter_path).read_text(encoding="utf-8"))
    observation = json.loads(Path(observation_path).read_text(encoding="utf-8"))
    _stop(adapter.get("schema") == "TCESP_LIMEIRA_CURRENT_EXPENSE_ADAPTER_V1", "TASK173_ADAPTER_SCHEMA")
    _stop(observation.get("schema") == "MUNICIPAL_ACCOUNTING_OBSERVATION_V1", "TASK173_OBSERVATION_SCHEMA")
    _stop(adapter.get("family_wide_auto_ingest_promoted") is False, "TASK173_FAMILY_PROMOTION")
    _stop(adapter["route_schema_scope"] == "EXACT_CURRENT_2026_DECLARED_ZIP_CSV_ONLY", "TASK173_ROUTE_SCOPE")
    return adapter, observation


def validate_contracts(
    adapter_path: str | Path = DEFAULT_ADAPTER,
    observation_path: str | Path = DEFAULT_OBSERVATION,
) -> dict[str, Any]:
    adapter, observation = load_contracts(adapter_path, observation_path)
    required = {
        "tp_despesa",
        "nr_empenho",
        "identificador_despesa",
        "ds_despesa",
        "dt_emissao_despesa",
        "vl_despesa",
        "ds_funcao_governo",
        "ds_subfuncao_governo",
        "cd_programa",
        "ds_programa",
        "cd_acao",
        "ds_acao",
        "ds_fonte_recurso",
        "ds_cd_aplicacao_fixo",
        "ds_modalidade_lic",
        "ds_elemento",
        "historico_despesa",
    }
    _stop(required == set(adapter["proven_columns"]), "TASK173_PROVEN_COLUMNS")
    _stop(
        observation["stages"] == ["COMMITMENT", "LIQUIDATION", "PAYMENT", "REVERSAL", "OTHER_REVIEW"],
        "TASK173_STAGE_CONTRACT",
    )
    _stop("supplier_cnpj" in adapter["unproven_columns_not_assumed"], "TASK173_UNPROVEN_SUPPLIER_GUARD")
    _stop("SAME_AMOUNT_NE_IDENTITY" in observation["invariants"], "TASK173_AMOUNT_GUARD")
    return {
        "schema": "TASK173_CONTRACT_VALIDATION_RESULT_V1",
        "status": "PASS",
        "proven_column_count": len(adapter["proven_columns"]),
        "family_wide_auto_ingest_promoted": False,
        "network": False,
        "drive_write": False,
    }


def normalize_stage(value: Any, adapter: Mapping[str, Any]) -> str:
    normalized = _ascii_upper(value)
    for stage, aliases in adapter["stage_normalization"].items():
        for alias in aliases:
            a = _ascii_upper(alias)
            if normalized == a or normalized.startswith(a + " ") or normalized.endswith(" " + a):
                return stage
    return adapter["unknown_stage"]


def _policy_domain_hints(row: Mapping[str, Any], adapter: Mapping[str, Any]) -> tuple[list[str], dict[str, list[str]]]:
    mapping = adapter["mapping"]
    fields = [
        row.get(mapping["function"]),
        row.get(mapping["subfunction"]),
        row.get(mapping["program_name"]),
        row.get(mapping["action_name"]),
    ]
    text = _ascii_upper(" ".join(str(x) for x in fields if x))
    hints: list[str] = []
    basis: dict[str, list[str]] = {}
    for domain, markers in adapter["policy_domain_hints"].items():
        found = []
        for marker in markers:
            m = _ascii_upper(marker)
            if m and m in text:
                found.append(marker)
        if found:
            hints.append(domain)
            basis[domain] = found
    return sorted(set(hints)), basis


def normalize_tcesp_expense_row(
    row: Mapping[str, Any],
    *,
    adapter_path: str | Path = DEFAULT_ADAPTER,
    observation_path: str | Path = DEFAULT_OBSERVATION,
) -> dict[str, Any]:
    adapter, observation_contract = load_contracts(adapter_path, observation_path)
    mapping = adapter["mapping"]

    missing = [name for name in adapter["proven_columns"] if name not in row]
    _stop(not missing, "TASK173_SOURCE_SCHEMA_MISSING_COLUMNS")

    stage = normalize_stage(row.get(mapping["source_stage"]), adapter)
    amount = _amount(row.get(mapping["amount"]))
    expense_id = _clean(row.get(mapping["source_expense_identifier"]))
    empenho = _clean(row.get(mapping["commitment_number"]))
    fiscal_year = int(adapter["entity_contract"]["fiscal_year"])

    selected_source = {name: _clean(row.get(name)) for name in adapter["proven_columns"]}
    source_record_hash = hashlib.sha256(_canonical_bytes(selected_source)).hexdigest()
    observation_id = "ACCTOBS_" + hashlib.sha256(
        _canonical_bytes(
            [
                adapter["source_id"],
                expense_id,
                fiscal_year,
                empenho,
                stage,
                _clean(row.get(mapping["event_date"])),
                amount,
                source_record_hash,
            ]
        )
    ).hexdigest()[:24]

    if expense_id or empenho:
        identity_status = "ACCOUNTING_TRANSACTION_KEY_AVAILABLE"
    else:
        identity_status = "SOURCE_RECORD_ONLY"

    programmatic = {
        "function": _clean(row.get(mapping["function"])),
        "subfunction": _clean(row.get(mapping["subfunction"])),
        "program_code": _clean(row.get(mapping["program_code"])),
        "program_name": _clean(row.get(mapping["program_name"])),
        "action_code": _clean(row.get(mapping["action_code"])),
        "action_name": _clean(row.get(mapping["action_name"])),
        "funding_source": _clean(row.get(mapping["funding_source"])),
        "application_code": _clean(row.get(mapping["application_code"])),
        "expense_element": _clean(row.get(mapping["expense_element"])),
        "procurement_modality": _clean(row.get(mapping["procurement_modality"])),
    }
    policy_hints, hint_basis = _policy_domain_hints(row, adapter)

    amount_semantic = observation_contract["amount_semantics"][stage]
    transaction_keys = {
        "source_expense_identifier": expense_id,
        "fiscal_year_plus_empenho": f"{fiscal_year}:{empenho}" if empenho else None,
    }

    return {
        "observation_id": observation_id,
        "schema": observation_contract["schema"],
        "source_id": adapter["source_id"],
        "source_role": adapter["source_role"],
        "entity_name": adapter["entity_contract"]["entity_name"],
        "fiscal_year": fiscal_year,
        "stage": stage,
        "source_stage": _clean(row.get(mapping["source_stage"])),
        "amount_semantic": amount_semantic,
        "amount_brl": amount,
        "event_date": _clean(row.get(mapping["event_date"])),
        "source_record_hash": source_record_hash,
        "identity_status": identity_status,
        "transaction_keys": transaction_keys,
        "programmatic_dimensions": programmatic,
        "policy_domain_hints": policy_hints,
        "policy_domain_hint_basis": hint_basis,
        "policy_link_status": "NOT_PROVEN",
        "policy_identity_proven": False,
        "financial_policy_identity_proven": False,
        "source_description": _clean(row.get(mapping["source_description"])),
        "history_text": _clean(row.get(mapping["history_text"])),
        "evidence_status": "DIRECT_EXPLICIT_CONTROL_RECORD",
    }


_EMPENHO_PATTERNS = [
    re.compile(r"(?i)\bEMPENHO\s*(?:N[ºO°.]?\s*)?[:\-]?\s*([0-9A-Za-z./-]+)"),
    re.compile(r"(?i)\bNOTA\s+DE\s+EMPENHO\s*(?:N[ºO°.]?\s*)?[:\-]?\s*([0-9A-Za-z./-]+)"),
]


def _extract_empenho(event: Mapping[str, Any]) -> str | None:
    texts = [
        event.get("object_text"),
        event.get("excerpt_redacted"),
    ]
    for text in texts:
        if not text:
            continue
        for pattern in _EMPENHO_PATTERNS:
            m = pattern.search(str(text))
            if m:
                return m.group(1).rstrip(".,;:)")
    return None


def _candidate_years(event: Mapping[str, Any]) -> list[int]:
    years: set[int] = set()
    for key in (
        "publication_date",
        "contract_number",
        "process_number",
        "edital_number",
        "bidding_number",
        "act_number",
    ):
        for y in re.findall(r"(?:19|20)\d{2}", str(event.get(key) or "")):
            years.add(int(y))
    return sorted(years)


def route_jom_event_to_tcesp(
    event: Mapping[str, Any],
    semantics: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    event_id = str(event.get("event_id") or "")
    _stop(bool(event_id), "TASK173_JOM_EVENT_ID")
    semantics = semantics or {}

    empenho = _extract_empenho(event)
    cnpj = re.sub(r"\D", "", str(event.get("cnpj") or "")) or None
    if cnpj and len(cnpj) != 14:
        cnpj = None

    external_ids = {
        "cnpj": cnpj,
        "contract_number": _clean(event.get("contract_number")),
        "process_number": _clean(event.get("process_number")),
        "bidding_number": _clean(event.get("bidding_number")),
        "edital_number": _clean(event.get("edital_number")),
    }
    external_ids = {k: v for k, v in external_ids.items() if v is not None}

    strong_queryable = {}
    if empenho:
        strong_queryable["nr_empenho"] = empenho

    context = {
        "candidate_years": _candidate_years(event),
        "policy_domains": list(semantics.get("policy_domains") or []),
        "evidence_layers": list(semantics.get("evidence_layers") or []),
        "financial_stages": list(semantics.get("financial_stages") or []),
    }
    context = {k: v for k, v in context.items() if v}

    weak = {
        "value_brl": _clean(event.get("value_brl")),
        "publication_date": _clean(event.get("publication_date")),
        "object_text": _clean(event.get("object_text")),
    }
    weak = {k: v for k, v in weak.items() if v is not None}

    if strong_queryable:
        route_state = "READY_EXACT_ACCOUNTING_KEY_QUERY"
        priority = 100
    elif external_ids:
        route_state = "CANDIDATE_EXTERNAL_KEY_REQUIRES_TCE_COLUMN_OR_CROSSWALK"
        priority = 85
    elif context:
        route_state = "CONTEXTUAL_FILTER_ONLY_NO_IDENTITY"
        priority = 60
    else:
        route_state = "WEAK_HINTS_ONLY_REVIEW"
        priority = 30

    material = {
        "event_id": event_id,
        "strong_queryable": strong_queryable,
        "external_ids": external_ids,
        "context": context,
        "weak": weak,
    }
    query_id = "ACCTQUERY_" + hashlib.sha256(_canonical_bytes(material)).hexdigest()[:24]

    return {
        "query_id": query_id,
        "schema": "JOM_TO_TCESP_ACCOUNTING_QUERY_V1",
        "origin_event_id": event_id,
        "target_source": "TCESP_LIMEIRA_2026_DESPESAS",
        "route_state": route_state,
        "priority": priority,
        "strong_queryable_keys": strong_queryable,
        "strong_external_identity_hints_not_proven_queryable": external_ids,
        "contextual_filters": context,
        "weak_corroborators": weak,
        "minimum_identity_rule": "EXACT_EMPENHO_OR_EXACT_SOURCE_EXPENSE_IDENTIFIER_REQUIRED_FOR_ACCOUNTING_IDENTITY_UNLESS_A_SEPARATE_STRONG_CROSSWALK_IS_PROVEN",
        "amount_date_text_can_create_identity": False,
        "semantic_facets_can_create_identity": False,
        "policy_identity_proven": False,
        "financial_identity_proven": False,
        "payment_proven": False,
    }


if __name__ == "__main__":
    print(json.dumps(validate_contracts(), ensure_ascii=False, sort_keys=True))

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
import hashlib
import json
import re
import unicodedata
from typing import Any

from .f02_known_family_bundle import (
    F02KnownFamilyBundleStop,
    _read_regular_file_beneath_root,
    canonical_bytes,
)
from .mde_fundeb import inspect_f02_pdf


class F02FundebMonthlyCashStop(ValueError):
    """Fail-closed stop for the monthly FUNDEB cash/balance series."""


REMOTE_EFFECT_KEYS = {
    "bronze_write",
    "silver_write",
    "gold_write",
    "serving",
    "publication",
    "site",
    "overwrite",
    "delete",
    "move",
    "schedule",
    "recurrence",
}

MONTHS = {
    "JANEIRO": 1,
    "FEVEREIRO": 2,
    "MARCO": 3,
    "ABRIL": 4,
    "MAIO": 5,
    "JUNHO": 6,
    "JULHO": 7,
    "AGOSTO": 8,
    "SETEMBRO": 9,
    "OUTUBRO": 10,
    "NOVEMBRO": 11,
    "DEZEMBRO": 12,
}

MONEY_RE = re.compile(r"(?<!\d)(\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2})(?!\d)")


@dataclass(frozen=True)
class MonthlySource:
    source_id: str
    month: str
    drive_file_id: str
    file_name: str
    sha256: str
    bytes: int
    pages: int
    snapshot_path: Path


def _stop(code: str, detail: str | None = None) -> None:
    suffix = f": {detail}" if detail else ""
    raise F02FundebMonthlyCashStop(f"STOP_F02_FUNDEB_MONTHLY_{code}{suffix}")


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    value = value.upper().replace("\u00a0", " ")
    return re.sub(r"[ \t]+", " ", value)


def _money(value: str) -> Decimal:
    raw = value.replace(".", "").replace(",", ".")
    try:
        amount = Decimal(raw)
    except InvalidOperation as exc:
        raise F02FundebMonthlyCashStop(
            f"STOP_F02_FUNDEB_MONTHLY_BAD_MONEY: {value}"
        ) from exc
    if not amount.is_finite() or amount < 0:
        _stop("BAD_MONEY", value)
    return amount


def _amount_text(value: Decimal | None) -> str | None:
    return None if value is None else f"{value:.2f}"


def _line_values(line: str) -> list[Decimal]:
    return [_money(value) for value in MONEY_RE.findall(line)]


def _find_line(lines: list[str], marker: str) -> str:
    matches = [line for line in lines if marker in line]
    if len(matches) != 1:
        _stop("MARKER_CARDINALITY", f"{marker}:observed={len(matches)}")
    return matches[0]


def _equal_accounting_bank(lines: list[str], marker: str) -> Decimal:
    values = _line_values(_find_line(lines, marker))
    if len(values) < 2:
        _stop("ACCOUNTING_BANK_VALUES_MISSING", marker)
    if values[0] != values[1]:
        _stop(
            "ACCOUNTING_BANK_DIVERGENCE",
            f"{marker}:accounting={values[0]};bank={values[1]}",
        )
    return values[0]


def _safe_snapshot_path(value: object) -> Path:
    text = str(value or "").strip()
    path = Path(text)
    if not text or path.is_absolute() or ".." in path.parts:
        _stop("SNAPSHOT_PATH_UNSAFE", text)
    return path


def validate_contract(raw: dict[str, Any]) -> dict[str, Any]:
    if raw.get("schema") != "F02_FUNDEB_MONTHLY_CASH_SERIES_CONTRACT_V1":
        _stop("CONTRACT_SCHEMA")
    if raw.get("mode") != "OFFLINE_MONTHLY_FUNDEB_CASH_RECONCILIATION":
        _stop("CONTRACT_MODE")
    if raw.get("family") != "FUNDEB_MONTHLY_CASH_LOCAL":
        _stop("CONTRACT_FAMILY")
    semantic = raw.get("semantic_boundary")
    if not isinstance(semantic, dict):
        _stop("SEMANTIC_BOUNDARY")
    for key in (
        "eti_spending_claim_authorized",
        "eti_committed_claim_authorized",
        "eti_liquidated_claim_authorized",
        "eti_paid_claim_authorized",
        "mde_compliance_claim_authorized",
        "annual_compliance_claim_authorized",
    ):
        if semantic.get(key) is not False:
            _stop("SEMANTIC_PROMOTION_ENABLED", key)
    if semantic.get("interpretation") != "BALANCE_AND_IDENTIFIED_FLOW_ONLY_NOT_EXPENDITURE":
        _stop("SEMANTIC_INTERPRETATION")
    effects = raw.get("remote_effects")
    if not isinstance(effects, dict) or set(effects) != REMOTE_EFFECT_KEYS:
        _stop("CONTRACT_EFFECT_SET")
    if any(effects[key] is not False for key in REMOTE_EFFECT_KEYS):
        _stop("CONTRACT_REMOTE_EFFECT")
    if raw.get("silver_persistence_requires_separate_create_only_execution") is not True:
        _stop("SILVER_PERSISTENCE_BOUNDARY")
    return raw


def validate_runtime_authorization(raw: object, *, batch_id: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        _stop("AUTHORIZATION_REQUIRED")
    if raw.get("schema") != "F02_FUNDEB_MONTHLY_CASH_RUNTIME_AUTHORIZATION_V1":
        _stop("AUTHORIZATION_SCHEMA")
    if raw.get("scope") != "F02_FUNDEB_MONTHLY_CASH_LOCAL_SNAPSHOT_READ":
        _stop("AUTHORIZATION_SCOPE")
    if raw.get("batch_id") != batch_id or raw.get("authorized") is not True:
        _stop("AUTHORIZATION_BATCH_OR_STATUS")
    if not str(raw.get("owner_instruction_verbatim") or "").strip():
        _stop("AUTHORIZATION_OWNER_INSTRUCTION")
    forbidden = set(raw.get("forbidden_effects") or [])
    for effect in (
        "DELETE","OVERWRITE","SERVING","LOOKER","PUBLICATION","SITE",
        "SCHEDULE","RECURRENCE","GOLD_PROMOTION",
        "FINANCIAL_CLAIM_PROMOTION_WITHOUT_EVIDENCE",
    ):
        if effect not in forbidden:
            _stop("AUTHORIZATION_FORBIDDEN_EFFECT_MISSING", effect)
    return raw


def load_pinned_authorization(
    *, root: str | Path, relative_path: str | Path, expected_sha256: str
) -> dict[str, Any]:
    digest = str(expected_sha256 or "").lower().strip()
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        _stop("AUTHORIZATION_PIN")
    try:
        payload = _read_regular_file_beneath_root(
            Path(root), Path(relative_path), code="MONTHLY_AUTHORIZATION_PATH"
        )
    except F02KnownFamilyBundleStop as exc:
        raise F02FundebMonthlyCashStop(str(exc)) from exc
    if hashlib.sha256(payload).hexdigest() != digest:
        _stop("AUTHORIZATION_SHA_DRIFT")
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise F02FundebMonthlyCashStop(
            "STOP_F02_FUNDEB_MONTHLY_AUTHORIZATION_INVALID_JSON"
        ) from exc
    return value


def load_manifest(*, root: str | Path, relative_path: str | Path) -> dict[str, Any]:
    try:
        payload = _read_regular_file_beneath_root(
            Path(root), Path(relative_path), code="MONTHLY_MANIFEST_PATH"
        )
    except F02KnownFamilyBundleStop as exc:
        raise F02FundebMonthlyCashStop(str(exc)) from exc
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise F02FundebMonthlyCashStop(
            "STOP_F02_FUNDEB_MONTHLY_MANIFEST_INVALID_JSON"
        ) from exc
    if not isinstance(value, dict):
        _stop("MANIFEST_NOT_OBJECT")
    return value


def validate_manifest(raw: dict[str, Any]) -> tuple[str, tuple[MonthlySource, ...]]:
    if raw.get("schema") != "F02_FUNDEB_MONTHLY_CASH_SOURCE_CUSTODY_V1":
        _stop("MANIFEST_SCHEMA")
    if raw.get("mode") != "MANUAL_SUPERVISED_INGEST":
        _stop("MANIFEST_MODE")
    if raw.get("family") != "FUNDEB_MONTHLY_CASH_LOCAL":
        _stop("MANIFEST_FAMILY")
    batch_id = str(raw.get("batch_id") or "").strip()
    if not batch_id:
        _stop("BATCH_ID")
    effects = raw.get("remote_effects_authorized")
    if not isinstance(effects, dict) or set(effects) != REMOTE_EFFECT_KEYS:
        _stop("MANIFEST_EFFECT_SET")
    if any(effects[key] is not False for key in REMOTE_EFFECT_KEYS):
        _stop("MANIFEST_REMOTE_EFFECT")

    items = raw.get("sources")
    if not isinstance(items, list) or not items:
        _stop("SOURCES")
    sources: list[MonthlySource] = []
    seen_ids: set[str] = set()
    seen_months: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            _stop("SOURCE_RECORD")
        required = (
            "source_id","month","drive_file_id","file_name","sha256",
            "bytes","pages","snapshot_path",
        )
        if any(item.get(key) in (None, "") for key in required):
            _stop("SOURCE_FIELDS")
        source_id = str(item["source_id"]).strip()
        month = str(item["month"]).strip()
        if not re.fullmatch(r"20\d{2}-(0[1-9]|1[0-2])", month):
            _stop("SOURCE_MONTH", month)
        if source_id in seen_ids or month in seen_months:
            _stop("DUPLICATE_SOURCE_OR_MONTH")
        seen_ids.add(source_id)
        seen_months.add(month)
        digest = str(item["sha256"]).lower().strip()
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            _stop("SOURCE_SHA", source_id)
        try:
            size = int(item["bytes"])
            pages = int(item["pages"])
        except (TypeError, ValueError) as exc:
            raise F02FundebMonthlyCashStop(
                f"STOP_F02_FUNDEB_MONTHLY_SOURCE_SIZE: {source_id}"
            ) from exc
        if size <= 0 or pages <= 0:
            _stop("SOURCE_SIZE", source_id)
        sources.append(MonthlySource(
            source_id=source_id,
            month=month,
            drive_file_id=str(item["drive_file_id"]).strip(),
            file_name=str(item["file_name"]).strip(),
            sha256=digest,
            bytes=size,
            pages=pages,
            snapshot_path=_safe_snapshot_path(item["snapshot_path"]),
        ))
    sources.sort(key=lambda x: x.month)
    return batch_id, tuple(sources)


def _section(text: str, start_marker: str, end_marker: str | None) -> str:
    start = text.find(start_marker)
    if start < 0:
        _stop("SECTION_START", start_marker)
    if end_marker is None:
        return text[start:]
    end = text.find(end_marker, start + len(start_marker))
    if end < 0:
        _stop("SECTION_END", end_marker)
    return text[start:end]


def _explicit_eti_accounts(section: str) -> tuple[list[dict[str, str]], Decimal | None]:
    accounts: list[dict[str, str]] = []
    for line in section.splitlines():
        if "CONTA CORRENTE" not in line or not re.search(r"\bETI\b", line):
            continue
        values = _line_values(line)
        if len(values) < 2 or values[0] != values[1]:
            _stop("ETI_ACCOUNTING_BANK_DIVERGENCE", line)
        label = MONEY_RE.sub("", line)
        label = re.sub(r"\s+", " ", label).strip(" -")
        accounts.append({"label": label, "amount": _amount_text(values[0])})
    if not accounts:
        return [], None
    total = sum((Decimal(item["amount"]) for item in accounts), Decimal("0"))
    return accounts, total


def parse_monthly_text(text: str) -> dict[str, Any]:
    folded = _fold(text)
    header = re.search(
        r"DEMONSTRATIVO MENSAL - RECURSOS DO FUNDEB - ([A-Z]+)/(20\d{2})",
        folded,
    )
    if not header:
        _stop("DOCUMENT_SIGNATURE")
    month_name, year_text = header.groups()
    if month_name not in MONTHS:
        _stop("MONTH_NAME", month_name)
    period = f"{year_text}-{MONTHS[month_name]:02d}"
    lines = [re.sub(r"\s+", " ", line).strip() for line in folded.splitlines() if line.strip()]

    opening = _equal_accounting_bank(lines, "TOTAL DO SALDO INICIAL")
    inflows = _equal_accounting_bank(lines, "TOTAL DAS ENTRADAS")
    outflows = _equal_accounting_bank(lines, "TOTAL DAS SAIDAS")
    closing = _equal_accounting_bank(lines, "TOTAL DO SALDO FINAL")
    transfer = _equal_accounting_bank(lines, "TRANSFERENCIAS DE RECURSOS DO FUNDEB")
    auto_income = _equal_accounting_bank(lines, "RENDIMENTO DA APLICACAO FINANCEIRA AUTOMATICO")
    classic_income = _equal_accounting_bank(lines, "BB RF CP CLASSICO")
    fti = _equal_accounting_bank(lines, "FTI- FOMENTO TEMPO INTEGRAL")

    if opening + inflows - outflows != closing:
        _stop(
            "ACCOUNTING_IDENTITY",
            f"{opening}+{inflows}-{outflows}!={closing}",
        )

    opening_section = _section(folded, "SALDO INICIAL", "ENTRADAS")
    closing_section = _section(folded, "SALDO FINAL", None)
    eti_opening_accounts, eti_opening = _explicit_eti_accounts(opening_section)
    eti_closing_accounts, eti_closing = _explicit_eti_accounts(closing_section)

    return {
        "period": period,
        "opening_balance": _amount_text(opening),
        "fundeb_transfer_inflow": _amount_text(transfer),
        "investment_income_automatic": _amount_text(auto_income),
        "investment_income_classic": _amount_text(classic_income),
        "explicit_fti_inflow": _amount_text(fti),
        "total_inflows": _amount_text(inflows),
        "total_outflows": _amount_text(outflows),
        "closing_balance": _amount_text(closing),
        "eti_opening_labeled_accounts": eti_opening_accounts,
        "eti_opening_labeled_total": _amount_text(eti_opening),
        "eti_closing_labeled_accounts": eti_closing_accounts,
        "eti_closing_labeled_total": _amount_text(eti_closing),
        "monthly_identity": "PASS_OPENING_PLUS_INFLOWS_MINUS_OUTFLOWS_EQUALS_CLOSING",
        "accounting_bank_totals": "PASS_EXACT_EQUALITY",
        "semantic_scope": {
            "eti_spending_claim_authorized": False,
            "eti_committed_claim_authorized": False,
            "eti_liquidated_claim_authorized": False,
            "eti_paid_claim_authorized": False,
            "interpretation": "BALANCE_AND_IDENTIFIED_FLOW_ONLY_NOT_EXPENDITURE",
        },
    }


def _month_index(period: str) -> int:
    year, month = (int(part) for part in period.split("-"))
    return year * 12 + month


def reconcile_series(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        _stop("EMPTY_SERIES")
    ordered = sorted(records, key=lambda x: x["period"])
    if [x["period"] for x in ordered] != [x["period"] for x in records]:
        _stop("SERIES_ORDER")
    continuity: list[dict[str, Any]] = []
    for previous, current in zip(ordered, ordered[1:]):
        if _month_index(current["period"]) - _month_index(previous["period"]) != 1:
            _stop("SERIES_MONTH_GAP")
        if previous["closing_balance"] != current["opening_balance"]:
            _stop(
                "SERIES_BALANCE_CONTINUITY",
                f"{previous['period']}->{current['period']}",
            )
        eti_status = "NOT_APPLICABLE_MISSING_EXPLICIT_LABEL"
        prev_eti = previous["eti_closing_labeled_total"]
        current_eti = current["eti_opening_labeled_total"]
        if prev_eti is not None and current_eti is not None:
            if prev_eti != current_eti:
                _stop(
                    "SERIES_ETI_LABEL_CONTINUITY",
                    f"{previous['period']}->{current['period']}",
                )
            eti_status = "PASS_EXPLICIT_ETI_BALANCE_CONTINUITY"
        continuity.append({
            "from": previous["period"],
            "to": current["period"],
            "total_balance": "PASS_EXACT_CONTINUITY",
            "explicit_eti_balance": eti_status,
        })
    return {
        "status": "PASS_F02_FUNDEB_MONTHLY_SERIES_RECONCILIATION",
        "period_start": ordered[0]["period"],
        "period_end": ordered[-1]["period"],
        "months": len(ordered),
        "continuity": continuity,
    }


def validate_offline_telemetry(raw: object) -> dict[str, Any]:
    if not isinstance(raw, dict):
        _stop("TELEMETRY_NOT_OBJECT")
    if raw.get("remote_effects") != 0:
        _stop("TELEMETRY_REMOTE_EFFECT")
    if raw.get("silver_persisted") is not False:
        _stop("TELEMETRY_SILVER_PERSISTED")
    if raw.get("gold_authorized") is not False:
        _stop("TELEMETRY_GOLD_AUTHORIZED")
    return raw


def run_monthly_series(
    contract: dict[str, Any],
    manifest: dict[str, Any],
    *,
    root: str | Path,
    authorization: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    validate_contract(contract)
    batch_id, sources = validate_manifest(manifest)
    validate_runtime_authorization(authorization, batch_id=batch_id)
    root = Path(root)
    records: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    for source in sources:
        try:
            payload = _read_regular_file_beneath_root(
                root, source.snapshot_path, code="MONTHLY_SNAPSHOT_PATH"
            )
        except F02KnownFamilyBundleStop as exc:
            raise F02FundebMonthlyCashStop(str(exc)) from exc
        digest = hashlib.sha256(payload).hexdigest()
        pdf = inspect_f02_pdf(payload)
        mismatches: dict[str, Any] = {}
        if digest != source.sha256:
            mismatches["sha256"] = {"expected": source.sha256, "observed": digest}
        if len(payload) != source.bytes:
            mismatches["bytes"] = {"expected": source.bytes, "observed": len(payload)}
        if pdf["pages"] != source.pages:
            mismatches["pages"] = {"expected": source.pages, "observed": pdf["pages"]}
        if not pdf["has_text_layer"]:
            mismatches["text_layer"] = {"expected": "ALL_PAGES_NONEMPTY", "observed": pdf["text_pages"]}
        if mismatches:
            _stop("SOURCE_IMMUTABLE_MISMATCH", json.dumps(mismatches, sort_keys=True))
        record = parse_monthly_text(pdf["text"])
        if record["period"] != source.month:
            _stop("SOURCE_PERIOD_DRIFT", f"{source.source_id}:{record['period']}!={source.month}")
        records.append(record)
        provenance.append({
            "source_id": source.source_id,
            "period": source.month,
            "drive_file_id": source.drive_file_id,
            "file_name": source.file_name,
            "sha256": digest,
            "bytes": len(payload),
            "pages": pdf["pages"],
            "status": "PASS_SOURCE_IMMUTABLE_IDENTITY",
        })

    series = reconcile_series(records)
    core = {
        "schema": "F02_FUNDEB_MONTHLY_CASH_SILVER_CANDIDATE_V1",
        "batch_id": batch_id,
        "family": "FUNDEB_MONTHLY_CASH_LOCAL",
        "provenance": provenance,
        "records": records,
        "series_reconciliation": series,
        "semantic_scope": {
            "eti_spending_claim_authorized": False,
            "eti_committed_liquidated_paid_claim_authorized": False,
            "mde_compliance_claim_authorized": False,
            "annual_compliance_claim_authorized": False,
            "interpretation": "BALANCE_AND_IDENTIFIED_FLOW_ONLY_NOT_EXPENDITURE",
        },
        "effects": {
            "source_network_calls": 0,
            "drive_network_calls": 0,
            "bronze_writes": 0,
            "silver_writes": 0,
            "gold_writes": 0,
            "serving_writes": 0,
            "publication_writes": 0,
            "site_writes": 0,
            "overwrite": 0,
            "delete": 0,
            "move": 0,
            "schedule": 0,
            "recurrence": 0,
        },
        "status": "PASS_F02_FUNDEB_MONTHLY_CASH_OFFLINE_NOT_PERSISTED",
    }
    digest = hashlib.sha256(canonical_bytes(core)).hexdigest()
    result = {"content_sha256": digest, **core}
    telemetry = {
        "status": result["status"],
        "content_sha256": digest,
        "record_count": len(records),
        "remote_effects": 0,
        "silver_persisted": False,
        "gold_authorized": False,
    }
    return result, telemetry

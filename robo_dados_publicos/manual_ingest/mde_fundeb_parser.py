from __future__ import annotations

from decimal import Decimal
from datetime import date
import calendar
import re
import unicodedata

from .mde_fundeb import F02IngestStop, F02SourceContract, classify_f02_text, load_f02_contract

_AMOUNT_RE = re.compile(r"\d{1,3}(?:\.\d{3})*,\d{2}")
_DATE_RE = re.compile(r"\b(\d{2})/(\d{2})/(\d{4})\b")
_MONTHS = {
    "JANEIRO": 1, "FEVEREIRO": 2, "MARCO": 3, "ABRIL": 4,
    "MAIO": 5, "JUNHO": 6, "JULHO": 7, "AGOSTO": 8,
    "SETEMBRO": 9, "OUTUBRO": 10, "NOVEMBRO": 11, "DEZEMBRO": 12,
}


def _fold(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[ \t]+", " ", value.upper().replace("\u00a0", " ")).strip()


def _money(value: str) -> Decimal:
    return Decimal(value.replace(".", "").replace(",", "."))


def _amounts(line: str) -> list[Decimal]:
    return [_money(value) for value in _AMOUNT_RE.findall(line)]


def _line(text: str, marker: str) -> str:
    wanted = _fold(marker)
    for raw in text.splitlines():
        if wanted in _fold(raw):
            return raw
    raise F02IngestStop(f"STOP_F02_PARSE_MARKER_MISSING: {marker}")


def _line_after(text: str, marker: str, *, max_lookahead: int = 3) -> str:
    lines = text.splitlines()
    wanted = _fold(marker)
    for idx, raw in enumerate(lines):
        if wanted in _fold(raw):
            for candidate in lines[idx: idx + max_lookahead + 1]:
                if _amounts(candidate):
                    return candidate
            break
    raise F02IngestStop(f"STOP_F02_PARSE_VALUE_AFTER_MARKER_MISSING: {marker}")


def _line_in_section(text: str, section_marker: str, line_marker: str, *, max_lookahead: int = 20) -> str:
    lines = text.splitlines()
    section = _fold(section_marker)
    wanted = _fold(line_marker)
    for idx, raw in enumerate(lines):
        if section in _fold(raw):
            for candidate in lines[idx + 1: idx + max_lookahead + 1]:
                if _fold(candidate).startswith(wanted) and _amounts(candidate):
                    return candidate
            break
    raise F02IngestStop(
        f"STOP_F02_PARSE_SECTION_VALUE_MISSING: section={section_marker};line={line_marker}"
    )


def _require_amount_count(line: str, count: int, marker: str) -> list[Decimal]:
    values = _amounts(line)
    if len(values) != count:
        raise F02IngestStop(
            f"STOP_F02_PARSE_AMOUNT_COUNT: marker={marker};expected={count};observed={len(values)}"
        )
    return values


def _iso_date(value: str) -> str:
    match = _DATE_RE.search(value)
    if not match:
        raise F02IngestStop(f"STOP_F02_PARSE_DATE_MISSING: {value[:80]}")
    day, month, year = map(int, match.groups())
    try:
        return date(year, month, day).isoformat()
    except ValueError as exc:
        raise F02IngestStop(f"STOP_F02_PARSE_BAD_DATE: {match.group(0)}") from exc


def _period_from_rreo(text: str) -> tuple[str, str]:
    folded = _fold(text)
    match = re.search(
        r"PERIODO DE REFERENCIA:\s*([A-Z]+)\s+A\s+([A-Z]+)\s+(\d{4})",
        folded,
    )
    if not match:
        raise F02IngestStop("STOP_F02_RREO_PERIOD_MISSING")
    start_name, end_name, year_raw = match.groups()
    if start_name not in _MONTHS or end_name not in _MONTHS:
        raise F02IngestStop("STOP_F02_RREO_PERIOD_BAD_MONTH")
    year = int(year_raw)
    start_month, end_month = _MONTHS[start_name], _MONTHS[end_name]
    if start_month > end_month:
        raise F02IngestStop("STOP_F02_RREO_PERIOD_REVERSED")
    start = date(year, start_month, 1)
    end = date(year, end_month, calendar.monthrange(year, end_month)[1])
    return start.isoformat(), end.isoformat()


def _position_period(text: str) -> tuple[str, str, str]:
    header = _line(text, "POSICAO EM")
    dates = _DATE_RE.findall(header)
    if len(dates) != 2:
        raise F02IngestStop(f"STOP_F02_POSITION_HEADER_DATES: observed={len(dates)}")
    generated = _iso_date("/".join(dates[0]))
    position = _iso_date("/".join(dates[1]))
    pos_date = date.fromisoformat(position)
    start = date(pos_date.year, 1, 1)
    return generated, start.isoformat(), position


def load_f02_ingest_plan(path: str) -> dict:
    import json
    from pathlib import Path

    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    contracts = load_f02_contract(path)
    expected_precedence = {
        "mde_official_claim": "RREO_MDE",
        "fundeb_local_report": "LOCAL_MONITORING_PERIOD_MATCH_REQUIRED",
        "mde_25_local_report": "AUXILIARY_MONITORING_NOT_SUBSTITUTE_FOR_RREO",
    }
    if raw.get("source_precedence") != expected_precedence:
        raise F02IngestStop("STOP_F02_PLAN_SOURCE_PRECEDENCE_MISMATCH")
    promotion = raw.get("promotion")
    if not isinstance(promotion, dict):
        raise F02IngestStop("STOP_F02_PLAN_PROMOTION_POLICY_MISSING")
    forbidden_true = sorted(key for key, value in promotion.items() if value is True)
    if forbidden_true:
        raise F02IngestStop(
            "STOP_F02_PLAN_UNAUTHORIZED_PROMOTION: " + ",".join(forbidden_true)
        )
    required_false = {
        "bronze_mutation_authorized_by_this_contract",
        "silver_authorized_by_this_contract",
        "gold_authorized",
        "serving_authorized",
        "site_mutation_authorized",
    }
    if not required_false.issubset(promotion) or any(promotion[key] is not False for key in required_false):
        raise F02IngestStop("STOP_F02_PLAN_PROMOTION_MUST_BE_EXPLICIT_FALSE")
    return {"raw": raw, "contracts": contracts}


def parse_rreo_mde(text: str) -> dict:
    if classify_f02_text(text) != "RREO_MDE":
        raise F02IngestStop("STOP_F02_PARSE_WRONG_FAMILY_RREO")
    period_start, period_end = _period_from_rreo(text)
    tax = _require_amount_count(_line(text, "3 - TOTAL DA RECEITA RESULTANTE DE IMPOSTOS"), 2, "rreo.tax")
    destined = _require_amount_count(_line(text, "4 - TOTAL DESTINADO AO FUNDEB"), 2, "rreo.destined_fundeb")
    minimum_beyond = _require_amount_count(_line(text, "25% DE ((1.1)"), 2, "rreo.minimum_beyond_fundeb")
    fundeb_received = _require_amount_count(_line(text, "6 - TOTAL DAS RECEITAS DO FUNDEB RECEBIDAS"), 2, "rreo.fundeb_received")
    fundeb_available = _require_amount_count(_line(text, "9 - TOTAL DOS RECURSOS DO FUNDEB DISPONIVEIS"), 1, "rreo.fundeb_available")
    limit_total = _require_amount_count(
        _line_after(text, "11- TOTAL DAS DESPESAS CUSTEADAS C/RECURSOS DO FUNDEB", max_lookahead=2),
        3,
        "rreo.fundeb_limit_total",
    )
    professionals = _require_amount_count(
        _line_after(text, "12- Total das Despesas do FUNDEB com Profissionais da", max_lookahead=2),
        3,
        "rreo.professionals",
    )
    professional_limit = _require_amount_count(
        _line(text, "15- Minimo de 70% do FUNDEB"),
        4,
        "rreo.professional_limit",
    )
    mde_limit = _require_amount_count(
        _line(text, "29- APLICACAO EM MDE SOBRE A RECEITA RESULTANTE DE IMPOSTOS"),
        3,
        "rreo.mde_limit",
    )
    return {
        "family": "RREO_MDE",
        "authority": "OFFICIAL_MDE_PRIMARY",
        "period_start": period_start,
        "period_end": period_end,
        "metrics": {
            "tax_revenue_realized": str(tax[1]),
            "fundeb_destined_realized": str(destined[1]),
            "minimum_beyond_fundeb": str(minimum_beyond[1]),
            "fundeb_received": str(fundeb_received[1]),
            "fundeb_available": str(fundeb_available[0]),
            "fundeb_limit_expense_committed": str(limit_total[0]),
            "fundeb_limit_expense_liquidated": str(limit_total[1]),
            "fundeb_limit_expense_paid": str(limit_total[2]),
            "fundeb_professionals_committed": str(professionals[0]),
            "fundeb_professionals_liquidated": str(professionals[1]),
            "fundeb_professionals_paid": str(professionals[2]),
            "fundeb_professionals_minimum_required": str(professional_limit[0]),
            "fundeb_professionals_considered": str(professional_limit[2]),
            "fundeb_professionals_percent": str(professional_limit[3]),
            "mde_minimum_required": str(mde_limit[0]),
            "mde_applied": str(mde_limit[1]),
            "mde_percent": str(mde_limit[2]),
        },
    }


def parse_fundeb_local(text: str) -> dict:
    if classify_f02_text(text) != "FUNDEB_LOCAL":
        raise F02IngestStop("STOP_F02_PARSE_WRONG_FAMILY_FUNDEB_LOCAL")
    generated, period_start, period_end = _position_period(text)
    principal = _require_amount_count(_line(text, "Principal (I)"), 4, "fundeb_local.principal")
    total = _require_amount_count(
        _line(text, "TOTAL (I+II+III+IV+V+VI+VII+VIII+IX+X)"),
        4,
        "fundeb_local.total",
    )
    application = _require_amount_count(
        _line(text, "TOTAL  (min. 90%)"),
        6,
        "fundeb_local.application_total",
    )
    professionals = _require_amount_count(
        _line_after(text, "PROFISSIONAIS DA EDUCACAO BASICA* - exceto", max_lookahead=2),
        6,
        "fundeb_local.professionals",
    )
    return {
        "family": "FUNDEB_LOCAL",
        "authority": "LOCAL_MONITORING",
        "generated_date": generated,
        "period_start": period_start,
        "period_end": period_end,
        "metrics": {
            "fundeb_tax_transfer_received": str(principal[1]),
            "fundeb_retained": str(principal[3]),
            "fundeb_total_received": str(total[1]),
            "fundeb_application_committed": str(application[0]),
            "fundeb_application_committed_percent": str(application[1]),
            "fundeb_application_liquidated": str(application[2]),
            "fundeb_application_liquidated_percent": str(application[3]),
            "fundeb_application_paid": str(application[4]),
            "fundeb_application_paid_percent": str(application[5]),
            "fundeb_professionals_committed": str(professionals[0]),
            "fundeb_professionals_committed_percent": str(professionals[1]),
            "fundeb_professionals_liquidated": str(professionals[2]),
            "fundeb_professionals_liquidated_percent_local": str(professionals[3]),
            "fundeb_professionals_paid": str(professionals[4]),
            "fundeb_professionals_paid_percent_local": str(professionals[5]),
        },
    }


def parse_mde_25_local(text: str) -> dict:
    if classify_f02_text(text) != "MDE_25_LOCAL":
        raise F02IngestStop("STOP_F02_PARSE_WRONG_FAMILY_MDE25_LOCAL")
    generated, period_start, period_end = _position_period(text)
    total_tax = _require_amount_count(
        _line_in_section(text, "RECEITA DE IMPOSTOS", "Total", max_lookahead=12),
        2,
        "mde25.total_tax",
    )
    retention = _require_amount_count(_line(text, "Retencoes ao FUNDEB"), 2, "mde25.retention")
    expenses = _require_amount_count(_line_after(text, "DESPESAS TOTAIS", max_lookahead=2), 6, "mde25.expenses")
    net_total = _require_amount_count(
        _line_in_section(text, "DESPESAS LIQUIDAS", "TOTAL", max_lookahead=10),
        6,
        "mde25.net_total",
    )
    return {
        "family": "MDE_25_LOCAL",
        "authority": "AUXILIARY_LOCAL_MONITORING",
        "generated_date": generated,
        "period_start": period_start,
        "period_end": period_end,
        "metrics": {
            "tax_revenue_realized": str(total_tax[1]),
            "fundeb_retained": str(retention[1]),
            "education_expense_committed": str(expenses[0]),
            "education_expense_committed_percent": str(expenses[1]),
            "education_expense_liquidated": str(expenses[2]),
            "education_expense_liquidated_percent": str(expenses[3]),
            "education_expense_paid": str(expenses[4]),
            "education_expense_paid_percent": str(expenses[5]),
            "education_net_expense_committed": str(net_total[0]),
            "education_net_expense_committed_percent": str(net_total[1]),
            "education_net_expense_liquidated": str(net_total[2]),
            "education_net_expense_liquidated_percent": str(net_total[3]),
            "education_net_expense_paid": str(net_total[4]),
            "education_net_expense_paid_percent": str(net_total[5]),
        },
    }


def normalize_f02_document(contract: F02SourceContract, text: str) -> dict:
    family = classify_f02_text(text)
    if family != contract.family:
        raise F02IngestStop(
            f"STOP_F02_CLASSIFIER_CONTRACT_MISMATCH: expected={contract.family};observed={family}"
        )
    parsers = {
        "RREO_MDE": parse_rreo_mde,
        "FUNDEB_LOCAL": parse_fundeb_local,
        "MDE_25_LOCAL": parse_mde_25_local,
    }
    result = parsers[family](text)
    result["source_id"] = contract.source_id
    result["source_role"] = contract.role
    result["drive_file_id"] = contract.drive_file_id
    return result


def reconcile_f02(records: list[dict]) -> dict:
    by_family = {}
    for record in records:
        family = record.get("family")
        if family in by_family:
            raise F02IngestStop(f"STOP_F02_RECONCILIATION_DUPLICATE_FAMILY: {family}")
        by_family[family] = record
    if set(by_family) != set(("RREO_MDE", "FUNDEB_LOCAL", "MDE_25_LOCAL")):
        raise F02IngestStop("STOP_F02_RECONCILIATION_EXACT_FAMILY_SET_REQUIRED")
    periods = {(record["period_start"], record["period_end"]) for record in records}
    if len(periods) != 1:
        raise F02IngestStop("STOP_F02_RECONCILIATION_PERIOD_MISMATCH")

    rreo = by_family["RREO_MDE"]
    fundeb = by_family["FUNDEB_LOCAL"]
    mde25 = by_family["MDE_25_LOCAL"]

    exact_checks = {
        "tax_revenue_realized_rreo_vs_mde25": (
            Decimal(rreo["metrics"]["tax_revenue_realized"]),
            Decimal(mde25["metrics"]["tax_revenue_realized"]),
        ),
        "fundeb_limit_liquidated_rreo_vs_local": (
            Decimal(rreo["metrics"]["fundeb_limit_expense_liquidated"]),
            Decimal(fundeb["metrics"]["fundeb_application_liquidated"]),
        ),
        "fundeb_professionals_liquidated_rreo_vs_local": (
            Decimal(rreo["metrics"]["fundeb_professionals_liquidated"]),
            Decimal(fundeb["metrics"]["fundeb_professionals_liquidated"]),
        ),
    }
    failures = {
        key: {"official": str(left), "local": str(right)}
        for key, (left, right) in exact_checks.items()
        if left != right
    }
    if failures:
        import json
        raise F02IngestStop(
            "STOP_F02_RECONCILIATION_EXPECTED_EXACT_MISMATCH: "
            + json.dumps(failures, sort_keys=True)
        )

    retention_delta = (
        Decimal(mde25["metrics"]["fundeb_retained"])
        - Decimal(rreo["metrics"]["fundeb_destined_realized"])
    )
    mde_percent_delta = (
        Decimal(mde25["metrics"]["education_expense_liquidated_percent"])
        - Decimal(rreo["metrics"]["mde_percent"])
    )
    return {
        "status": "PASS_F02_RECONCILIATION",
        "period_start": rreo["period_start"],
        "period_end": rreo["period_end"],
        "authority_rule": "RREO_MDE_FOR_OFFICIAL_MDE_CLAIMS",
        "exact_checks": {key: True for key in exact_checks},
        "methodology_differences": {
            "fundeb_retained_local_minus_rreo_destined": str(retention_delta),
            "mde_liquidated_percent_local_minus_rreo_official": str(mde_percent_delta),
            "interpretation": "OBSERVED_DIFFERENCE_NOT_SOURCE_SUBSTITUTION",
        },
        "promotion": {
            "gold_authorized": False,
            "serving_authorized": False,
            "publication_authorized": False,
        },
    }

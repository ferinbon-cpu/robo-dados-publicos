from __future__ import annotations

from decimal import Decimal
import json
from pathlib import Path

from .mde_fundeb import F02IngestStop, F02SourceContract, classify_f02_text
from .mde_fundeb_parser import (
    _line,
    _line_in_section,
    _position_period,
    _require_amount_count,
    parse_mde_25_local,
)


LOCAL_FAMILIES = ("FUNDEB_LOCAL", "MDE_25_LOCAL")
EXPECTED_PRECEDENCE = {
    "fundeb_local_report": "LOCAL_MONITORING_PRIMARY_FOR_THIS_LOCAL_ONLY_BATCH",
    "mde_25_local_report": "LOCAL_MONITORING_AUXILIARY_NOT_OFFICIAL_RREO_SUBSTITUTE",
    "mde_official_claim": "NOT_AUTHORIZED_NO_RREO_SAME_PERIOD",
}
EXPECTED_OFFICIAL_CONTEXT = {
    "annual_compliance_claim_authorized": False,
    "official_mde_claim_authorized": False,
    "reason": "NO_RREO_BIMONTHLY_MAY_PERIOD",
    "rreo_mde_same_period_available": False,
}
REQUIRED_PROMOTION_FALSE = {
    "bronze_mutation_authorized_by_this_contract",
    "silver_authorized_by_this_contract",
    "gold_authorized",
    "serving_authorized",
    "site_mutation_authorized",
}


def load_f02_local_monitoring_plan(path: str | Path) -> dict:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("mode") != "MANUAL_SUPERVISED_INGEST":
        raise F02IngestStop("STOP_F02_LOCAL_PLAN_BAD_MODE")
    if raw.get("contract") != "F02_LOCAL_MONITORING_PERIOD_WITHOUT_RREO_V1":
        raise F02IngestStop("STOP_F02_LOCAL_PLAN_BAD_CONTRACT")
    if raw.get("source_precedence") != EXPECTED_PRECEDENCE:
        raise F02IngestStop("STOP_F02_LOCAL_PLAN_SOURCE_PRECEDENCE_MISMATCH")
    if raw.get("official_period_context") != EXPECTED_OFFICIAL_CONTEXT:
        raise F02IngestStop("STOP_F02_LOCAL_PLAN_OFFICIAL_CONTEXT_MISMATCH")

    promotion = raw.get("promotion")
    if not isinstance(promotion, dict):
        raise F02IngestStop("STOP_F02_LOCAL_PLAN_PROMOTION_POLICY_MISSING")
    if not REQUIRED_PROMOTION_FALSE.issubset(promotion):
        raise F02IngestStop("STOP_F02_LOCAL_PLAN_PROMOTION_MUST_BE_EXPLICIT_FALSE")
    if any(promotion[key] is not False for key in REQUIRED_PROMOTION_FALSE):
        raise F02IngestStop("STOP_F02_LOCAL_PLAN_UNAUTHORIZED_PROMOTION")

    sources = raw.get("sources")
    if not isinstance(sources, list) or len(sources) != 2:
        raise F02IngestStop("STOP_F02_LOCAL_PLAN_EXACTLY_TWO_SOURCES_REQUIRED")
    contracts = tuple(F02SourceContract.from_mapping(item) for item in sources)
    source_ids = [item.source_id for item in contracts]
    if len(source_ids) != len(set(source_ids)):
        raise F02IngestStop("STOP_F02_LOCAL_PLAN_DUPLICATE_SOURCE_IDS")
    families = [item.family for item in contracts]
    if sorted(families) != sorted(LOCAL_FAMILIES):
        raise F02IngestStop("STOP_F02_LOCAL_PLAN_EXACT_LOCAL_FAMILY_SET_REQUIRED")

    reference = raw.get("reference_period")
    if not isinstance(reference, dict):
        raise F02IngestStop("STOP_F02_LOCAL_PLAN_REFERENCE_PERIOD_MISSING")
    if reference.get("closing_status") != "PARTIAL_LOCAL_MONITORING":
        raise F02IngestStop("STOP_F02_LOCAL_PLAN_CLOSING_STATUS")
    if not reference.get("start") or not reference.get("end"):
        raise F02IngestStop("STOP_F02_LOCAL_PLAN_REFERENCE_PERIOD_MISSING")
    return {"raw": raw, "contracts": contracts}


def parse_fundeb_local_monitoring(text: str) -> dict:
    if classify_f02_text(text) != "FUNDEB_LOCAL":
        raise F02IngestStop("STOP_F02_LOCAL_PARSE_WRONG_FAMILY_FUNDEB")
    generated, period_start, period_end = _position_period(text)
    principal = _require_amount_count(_line(text, "Principal (I)"), 4, "fundeb_local.principal")
    total = _require_amount_count(
        _line(text, "TOTAL (I+II+III+IV+V+VI+VII+VIII+IX+X)"),
        4,
        "fundeb_local.total",
    )
    application = _require_amount_count(
        _line_in_section(text, "DESPESAS LIQUIDAS", "TOTAL", max_lookahead=35),
        6,
        "fundeb_local.local_monitoring_application_total",
    )
    professionals = _require_amount_count(
        _line_in_section(
            text,
            "DESPESAS LIQUIDAS",
            "PROFISSIONAIS DA EDUCACAO BASICA* - exceto Complementacao da Uniao VAAR",
            max_lookahead=35,
        ),
        6,
        "fundeb_local.local_monitoring_professionals",
    )
    return {
        "family": "FUNDEB_LOCAL",
        "authority": "LOCAL_MONITORING_NO_OFFICIAL_RREO_PERIOD_MATCH",
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


def normalize_f02_local_monitoring_document(contract: F02SourceContract, text: str) -> dict:
    observed = classify_f02_text(text)
    if observed != contract.family:
        raise F02IngestStop(
            f"STOP_F02_LOCAL_CLASSIFIER_CONTRACT_MISMATCH: expected={contract.family};observed={observed}"
        )
    parser = parse_fundeb_local_monitoring if observed == "FUNDEB_LOCAL" else parse_mde_25_local
    result = parser(text)
    result["source_id"] = contract.source_id
    result["source_role"] = contract.role
    result["drive_file_id"] = contract.drive_file_id
    return result


def reconcile_f02_local_monitoring(records: list[dict]) -> dict:
    by_family = {}
    for record in records:
        family = record.get("family")
        if family in by_family:
            raise F02IngestStop(f"STOP_F02_LOCAL_RECONCILIATION_DUPLICATE_FAMILY: {family}")
        by_family[family] = record
    if set(by_family) != set(LOCAL_FAMILIES):
        raise F02IngestStop("STOP_F02_LOCAL_RECONCILIATION_EXACT_LOCAL_FAMILY_SET_REQUIRED")
    periods = {(record["period_start"], record["period_end"]) for record in records}
    if len(periods) != 1:
        raise F02IngestStop("STOP_F02_LOCAL_RECONCILIATION_PERIOD_MISMATCH")

    fundeb = by_family["FUNDEB_LOCAL"]
    mde25 = by_family["MDE_25_LOCAL"]
    left = Decimal(fundeb["metrics"]["fundeb_retained"])
    right = Decimal(mde25["metrics"]["fundeb_retained"])
    if left != right:
        raise F02IngestStop(
            "STOP_F02_LOCAL_RECONCILIATION_RETENTION_MISMATCH: "
            + json.dumps({"fundeb_local": str(left), "mde25_local": str(right)}, sort_keys=True)
        )

    return {
        "status": "PASS_F02_LOCAL_MONITORING_RECONCILIATION_NO_RREO_PERIOD_MATCH",
        "period_start": fundeb["period_start"],
        "period_end": fundeb["period_end"],
        "exact_checks": {"fundeb_retained_local_reports": True},
        "observed_local_metrics": {
            "fundeb_total_received": fundeb["metrics"]["fundeb_total_received"],
            "fundeb_professionals_liquidated": fundeb["metrics"]["fundeb_professionals_liquidated"],
            "fundeb_professionals_liquidated_percent_local": fundeb["metrics"]["fundeb_professionals_liquidated_percent_local"],
            "mde_tax_revenue_realized": mde25["metrics"]["tax_revenue_realized"],
            "mde_education_expense_liquidated": mde25["metrics"]["education_expense_liquidated"],
            "mde_education_expense_liquidated_percent_local": mde25["metrics"]["education_expense_liquidated_percent"],
        },
        "authority_policy": {
            "rreo_mde_same_period_present": False,
            "official_mde_claim_authorized": False,
            "annual_compliance_claim_authorized": False,
            "interpretation": "LOCAL_MONITORING_ONLY_NOT_OFFICIAL_MDE_SUBSTITUTION",
        },
        "promotion": {
            "gold_authorized": False,
            "serving_authorized": False,
            "publication_authorized": False,
        },
    }

"""Sanitized structural evidence helpers for the T0 SIOPE 2025 runner."""

from __future__ import annotations

import hashlib
import json

METRIC_IDS = (
    "receita_realizada_sobre_previsao_atualizada_pct",
    "despesa_paga_sobre_dotacao_atualizada_pct",
    "despesa_educacao_paga_sobre_dotacao_atualizada_educacao_pct",
    "participacao_educacao_na_despesa_empenhada_pct",
    "participacao_educacao_na_despesa_liquidada_pct",
    "participacao_educacao_na_despesa_paga_pct",
    "despesa_total_paga_por_habitante",
    "despesa_educacao_paga_por_habitante",
)


def _hash_names(names: list[str]) -> str:
    raw = json.dumps(names, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def summarize_schema(phase_b: dict, *, required_fields: list[str]) -> dict:
    performed = phase_b.get("performed") is True
    fields = phase_b.get("schema_fields", []) if performed else []
    if not isinstance(fields, list):
        fields = []
    names = sorted(str(field) for field in fields)
    field_set = set(names)
    status = {
        field: ("PRESENT" if field in field_set else "ABSENT") if performed else "NOT_OBSERVED"
        for field in required_fields
    }
    return {
        "performed": performed,
        "observed_field_count": len(names),
        "observed_fields": names,
        "observed_fields_sha256": _hash_names(names),
        "required_gold_input_status": status,
        "all_required_gold_inputs_present": all(value == "PRESENT" for value in status.values()) if performed else None,
        "missing_required_gold_input_fields": [field for field, value in status.items() if value == "ABSENT"],
    }


def _transport_summary(observation: dict, *, ordinal: int, phase: str, period: int) -> dict:
    records = observation.get("records", [])
    cardinality = len(records) if isinstance(records, list) else None
    return {
        "ordinal": ordinal,
        "phase": phase,
        "period": period,
        "response_status": observation.get("response_status"),
        "content_type": observation.get("content_type"),
        "response_byte_count": observation.get("response_byte_count"),
        "cardinality": cardinality,
        "redirect_followed": observation.get("redirect_followed"),
        "nextlink_present": observation.get("nextlink_present"),
        "retry_performed": observation.get("retry_performed"),
    }


def build_sanitized_observation_evidence(
    *,
    probes: list[dict],
    phase_b: dict,
    required_fields: list[str],
    outcome: str,
    observed_periods: list[int],
) -> dict:
    transport = [
        _transport_summary(probe, ordinal=index, phase="PERIOD_AVAILABILITY", period=index)
        for index, probe in enumerate(probes, start=1)
    ]
    if phase_b.get("performed") is True:
        transport.append(_transport_summary(phase_b, ordinal=7, phase="CONDITIONAL_SCHEMA", period=6))
    metric_statuses = {metric_id: "UNKNOWN" for metric_id in METRIC_IDS}
    return {
        "outcome": outcome,
        "observed_periods": list(observed_periods),
        "transport": transport,
        "schema": summarize_schema(phase_b, required_fields=required_fields),
        "metric_statuses": metric_statuses,
        "any_metric_proven": False,
        "annual_closure_status": "UNKNOWN",
        "promote_2025_to_proven": False,
        "source_get_count": 0,
        "drive_read_count": 0,
        "drive_write_count": 0,
        "publication": False,
        "network_called": False,
        "response_body_persisted": False,
        "record_values_persisted": False,
        "query_values_persisted": False,
        "tokens_persisted": False,
        "cookies_persisted": False,
        "sensitive_headers_persisted": False,
    }

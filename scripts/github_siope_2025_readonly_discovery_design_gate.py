#!/usr/bin/env python3
"""Validate TASK 002's SIOPE 2025 read-only design without network access."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "config" / "siope_2025_readonly_discovery_design.v1.json"
REGIMES = ROOT / "config" / "siope_historical_regimes.v1.json"
POLICY = ROOT / "config" / "automation_policy.v1.json"
PASS = "PASS_SIOPE_2025_READONLY_DISCOVERY_DESIGN_T0"


class Siope2025DesignError(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Siope2025DesignError(f"STOP_SIOPE_2025_READONLY_DESIGN_{code}")


def _load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise Siope2025DesignError(f"STOP_SIOPE_2025_READONLY_DESIGN_UNREADABLE_{path.name}") from exc
    _require(isinstance(value, dict), f"OBJECT_{path.name}")
    return value


def validate(design_path: Path = DESIGN, regimes_path: Path = REGIMES, policy_path: Path = POLICY) -> dict:
    design, regime_map, policy = _load(design_path), _load(regimes_path), _load(policy_path)
    _require(design.get("schema") == "SIOPE_2025_READONLY_DISCOVERY_DESIGN_V1", "SCHEMA")
    _require(design.get("design_tier") == "T0_OFFLINE", "DESIGN_TIER")
    _require(design.get("proposed_runtime_tier") == "T1_REMOTE_READONLY", "RUNTIME_TIER")
    _require(design.get("future_batch_execution_authorized") is False, "FUTURE_BATCH")
    _require(policy.get("policy_invariants", {}).get("agent_may_authorize_remote_execution") is False, "POLICY_AGENT_AUTHORITY")
    _require(policy.get("policy_invariants", {}).get("future_batch_execution_authorized") is False, "POLICY_FUTURE_BATCH")

    # TASK 002 is a frozen pre-live design artifact. Its target must continue to
    # describe the uncertainty that existed before TASK 004C produced evidence.
    target = design.get("target", {})
    _require(target == {
        "year": 2025, "state": "SP", "municipality_code": 352690, "municipality_name": "Limeira",
        "resource_candidate": "Dados_Gerais_Siope", "resource_status": "UNPROVEN_FOR_2025",
        "annual_period_candidate": 6, "annual_period_status": "CANDIDATE_NOT_PROVEN",
        "annual_closure_status": "UNKNOWN", "closed_series_eligibility": "UNKNOWN",
    }, "TARGET")

    runtime = design.get("proposed_runtime", {})
    expected_closed = {
        "runtime_execution_authorized_by_this_design": False, "source_get_authorized_by_this_design": False,
        "follow_redirects": False, "follow_odata_nextlink": False, "retry_authorized": False,
        "pagination_authorized": False, "drive_access_authorized": False, "persistence_authorized": False,
        "publication_authorized": False, "bronze_silver_gold_creation_authorized": False,
        "batch_expansion_authorized": False, "recurrence_authorized": False, "schedule_enabled": False,
    }
    for key, expected in expected_closed.items():
        _require(runtime.get(key) is expected, f"RUNTIME_{key.upper()}")
    _require(runtime.get("human_authorization_required") is True, "HUMAN_AUTHORIZATION")
    _require(runtime.get("allowed_method") == "GET", "METHOD")
    _require(runtime.get("allowed_host") == "www.fnde.gov.br", "HOST")
    _require(runtime.get("period_probe_values") == [1, 2, 3, 4, 5, 6], "PERIOD_PROBES")
    _require(runtime.get("period_probe_request_count") == 6, "PERIOD_REQUEST_COUNT")
    _require(runtime.get("conditional_schema_request_count") == 1, "SCHEMA_REQUEST_COUNT")
    _require(runtime.get("maximum_total_request_count") == 7, "TOTAL_REQUEST_BOUND")
    _require(runtime.get("maximum_requests_per_period") == 1, "PER_PERIOD_BOUND")
    _require(runtime.get("max_attempts") == 1, "ATTEMPTS")
    _require(runtime.get("secrets_required") == [] and runtime.get("authentication_required") is False, "CREDENTIALS")

    phase_a = design.get("phase_a_period_availability", {})
    _require(phase_a.get("selected_fields") == ["COD_MUNI", "NOM_MUNI", "NUM_ANO", "NUM_PERI", "SIG_UF"], "IDENTITY_FIELDS")
    _require(phase_a.get("more_than_one_record_means") == "STOP_DUPLICATE", "DUPLICATE")
    _require(phase_a.get("schema_or_metric_promotion_authorized") is False, "PHASE_A_PROMOTION")
    _require(phase_a.get("annual_closure_inference_authorized") is False, "PHASE_A_CLOSURE")

    phase_b = design.get("phase_b_conditional_schema", {})
    _require(phase_b.get("precondition") == "PHASE_A_PERIOD_6_OBSERVED_EXACT_IDENTITY", "SCHEMA_PRECONDITION")
    _require(phase_b.get("period") == 6 and phase_b.get("period_semantics") == "CANDIDATE_ONLY", "P6_NOT_PROVEN_IN_FROZEN_DESIGN")
    _require(phase_b.get("expected_selected_schema_key_count") == 52, "SCHEMA_COUNT")
    _require(len(phase_b.get("required_gold_input_fields", [])) == 11, "GOLD_INPUT_FIELDS")
    _require(phase_b.get("allowed_aliases") == {}, "ALIASES")
    for key in ("response_body_persistence_authorized", "record_value_persistence_authorized", "gold_calculation_authorized", "semantic_comparability_inference_authorized", "annual_closure_inference_authorized"):
        _require(phase_b.get(key) is False, f"PHASE_B_{key.upper()}")

    promotion = design.get("promotion_contract", {})
    for key in ("promote_regime_map_by_this_design", "promote_2025_to_proven", "join_closed_annual_series", "automatic_compliance_claims_authorized"):
        _require(promotion.get(key) is False, f"PROMOTION_{key.upper()}")
    _require(promotion.get("requires_separate_pinned_live_evidence_review") is True, "PINNED_REVIEW")
    _require(promotion.get("requires_separate_annual_closure_decision") is True, "CLOSURE_DECISION")

    offline = design.get("offline_validation", {})
    _require(offline.get("validator") == "robo_dados_publicos/sources/siope_2025_readonly_discovery_offline.py", "OFFLINE_VALIDATOR")
    _require(offline.get("gate") == "scripts/github_siope_2025_readonly_discovery_offline_fixtures_gate.py", "OFFLINE_GATE")
    _require(offline.get("fixtures_directory") == "tests/fixtures/siope_2025_readonly_discovery", "OFFLINE_FIXTURES")
    _require(offline.get("fixture_count") == 10, "OFFLINE_FIXTURE_COUNT")
    _require(offline.get("synthetic_only") is True, "OFFLINE_SYNTHETIC")
    _require(offline.get("financial_values_allowed") is False, "OFFLINE_FINANCIAL_VALUES")
    _require(offline.get("live_evidence_claim_allowed") is False, "OFFLINE_LIVE_EVIDENCE")
    schema_fields = offline.get("expected_schema_fields")
    _require(isinstance(schema_fields, list) and len(schema_fields) == 52, "OFFLINE_SCHEMA_COUNT")
    _require(len(schema_fields) == len(set(schema_fields)), "OFFLINE_SCHEMA_DUPLICATE")
    for relative in (offline["validator"], offline["gate"], offline["fixtures_directory"]):
        _require((ROOT / relative).exists(), "OFFLINE_VALIDATION_PATH")

    # The canonical map may now reflect a later, separately reviewed promotion.
    # That promotion must remain structural only; it cannot rewrite TASK 002 or
    # silently imply annual closure, Gold comparability or closed-series entry.
    regime_2025 = next((item for item in regime_map.get("regimes", []) if item.get("years") == [2025]), None)
    _require(regime_2025 is not None, "REGIME_2025_MISSING")
    _require(regime_2025.get("id") == "STRUCTURALLY_PROVEN_2025", "REGIME_2025_ID")
    _require(regime_2025.get("status") == "PROVEN_STRUCTURAL_RECENT", "REGIME_2025_STATUS")
    _require(regime_2025.get("period") == {"value": 6, "status": "PROVEN_AVAILABLE_CLOSURE_UNKNOWN"}, "REGIME_2025_PERIOD")
    _require(regime_2025.get("schema") == {"status": "PROVEN_2025_P6_SCHEMA", "name": "DADOS_GERAIS_SIOPE_52_FIELDS"}, "REGIME_2025_SCHEMA")
    _require(regime_2025.get("annual_closure_status") == "UNKNOWN", "REGIME_2025_CLOSURE")
    _require(regime_2025.get("semantic_comparability_status") == "UNKNOWN", "REGIME_2025_COMPARABILITY")
    _require(regime_2025.get("closed_series_eligible") is False, "REGIME_2025_CLOSED_SERIES")
    _require(regime_2025.get("gold_metrics_status") == "UNKNOWN", "REGIME_2025_GOLD")
    _require(regime_map.get("closed_annual_series") == {"first_year": 2016, "last_year": 2024}, "CLOSED_SERIES_BOUNDARY")

    return {
        "status": PASS,
        "tier": "T0_OFFLINE",
        "network_called": False,
        "drive_called": False,
        "secrets_used": False,
        "runtime_execution_authorized": False,
        "maximum_future_request_count": 7,
        "frozen_design_target_status": "UNPROVEN_FOR_2025",
        "canonical_2025_status": "PROVEN_STRUCTURAL_RECENT",
        "annual_closure_status": "UNKNOWN",
    }


def main() -> int:
    try:
        result = validate()
    except Siope2025DesignError as exc:
        print(exc)
        return 13
    print(PASS)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

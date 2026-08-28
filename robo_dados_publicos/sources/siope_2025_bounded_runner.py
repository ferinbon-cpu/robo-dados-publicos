"""Bounded SIOPE 2025 runner restricted to injected fake transport."""

from __future__ import annotations

from robo_dados_publicos.sources.siope_2025_evidence import (
    METRIC_IDS,
    build_sanitized_observation_evidence,
)
from robo_dados_publicos.sources.siope_2025_fake_transport import FakeSiope2025Transport
from robo_dados_publicos.sources.siope_2025_readonly_discovery_offline import (
    Siope2025OfflineFixtureError,
    validate_fixture,
    validate_period_observation,
)
from robo_dados_publicos.sources.siope_2025_request_plan import (
    PHASE_B_PRECONDITION,
    RequestExecutionLedger,
    materialize_request_plan,
    sanitized_plan_evidence,
)

STOP_LIVE_NOT_AUTHORIZED = "STOP_LIVE_NOT_AUTHORIZED"
ERROR = "STOP_SIOPE_2025_BOUNDED_RUNNER"
PASS = "PASS_SIOPE_2025_BOUNDED_RUNNER_T0"


class Siope2025BoundedRunnerError(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Siope2025BoundedRunnerError(code if code == STOP_LIVE_NOT_AUTHORIZED else f"{ERROR}_{code}")


def validate_semantic_state(
    *,
    year: int,
    state: str,
    municipality_code: int,
    annual_closure_status: str,
    promote_2025_to_proven: bool,
    metric_statuses: dict[str, str],
) -> None:
    _stop(year == 2025, "SEMANTIC_YEAR")
    _stop(state == "SP", "SEMANTIC_STATE")
    _stop(municipality_code == 352690, "SEMANTIC_MUNICIPALITY")
    _stop(annual_closure_status == "UNKNOWN", "ANNUAL_CLOSURE_PROMOTION")
    _stop(promote_2025_to_proven is False, "REGIME_PROMOTION")
    _stop(set(metric_statuses) == set(METRIC_IDS), "METRIC_SET")
    _stop(all(status == "UNKNOWN" for status in metric_statuses.values()), "METRIC_PROMOTION")


def run_bounded(
    *,
    runner_config: dict,
    design: dict,
    transport: FakeSiope2025Transport | None = None,
) -> dict:
    """Execute the bounded plan only against the concrete in-memory fake transport."""
    _validate_contract(runner_config, design)
    if type(transport) is not FakeSiope2025Transport:
        raise Siope2025BoundedRunnerError(STOP_LIVE_NOT_AUTHORIZED)

    plan = materialize_request_plan(design)
    ledger = RequestExecutionLedger(plan)
    schema_fields = tuple(design["offline_validation"]["expected_schema_fields"])
    required_fields = list(design["phase_b_conditional_schema"]["required_gold_input_fields"])
    probes: list[dict] = []
    executed_ordinals: list[int] = []

    for spec in plan[:6]:
        ledger.consume(spec)
        observation = transport.request(spec)
        executed_ordinals.append(spec.ordinal)
        try:
            validate_period_observation(observation, period=spec.period)
        except Siope2025OfflineFixtureError as exc:
            raise Siope2025BoundedRunnerError(str(exc)) from None
        probes.append(observation)

    p6 = probes[5]
    records = p6.get("records")
    _stop(isinstance(records, list), "P6_RECORDS")
    _stop(len(records) <= 1, "P6_DUPLICATE")
    if records:
        _stop(plan[6].precondition == PHASE_B_PRECONDITION, "PHASE_B_PRECONDITION")
        _stop(
            records[0].get("COD_MUNI") == 352690
            and records[0].get("NOM_MUNI") == "Limeira"
            and records[0].get("NUM_ANO") == 2025
            and records[0].get("NUM_PERI") == 6
            and records[0].get("SIG_UF") == "SP",
            "PHASE_B_IDENTITY_PRECONDITION",
        )
        ledger.consume(plan[6])
        phase_b = transport.request(plan[6])
        executed_ordinals.append(7)
    else:
        phase_b = {
            "performed": False,
            "period": None,
            "schema_fields": [],
            "field_semantics_status": "NOT_EVALUATED",
        }

    synthetic = {
        "schema": "SIOPE_2025_READONLY_DISCOVERY_OFFLINE_FIXTURE_V1",
        "case_id": "BOUNDED_RUNNER_SYNTHETIC",
        "synthetic": True,
        "contains_financial_values": False,
        "network_called": False,
        "drive_called": False,
        "declared_request_count": ledger.count,
        "phase_a_period_probes": probes,
        "phase_b_schema_probe": phase_b,
        "expected_outcome": _expected_outcome(probes, phase_b),
    }
    try:
        validated = validate_fixture(synthetic, expected_schema_fields=schema_fields)
    except Siope2025OfflineFixtureError as exc:
        raise Siope2025BoundedRunnerError(str(exc)) from None

    metric_statuses = {metric_id: "UNKNOWN" for metric_id in METRIC_IDS}
    validate_semantic_state(
        year=2025,
        state="SP",
        municipality_code=352690,
        annual_closure_status="UNKNOWN",
        promote_2025_to_proven=False,
        metric_statuses=metric_statuses,
    )
    plan_evidence = sanitized_plan_evidence(plan, executed_ordinals=executed_ordinals)
    observation_evidence = build_sanitized_observation_evidence(
        probes=probes,
        phase_b=phase_b,
        required_fields=required_fields,
        outcome=validated["outcome"],
        observed_periods=validated["observed_periods"],
    )
    result = {
        "status": PASS,
        "outcome": validated["outcome"],
        "observed_periods": validated["observed_periods"],
        "fake_request_count": ledger.count,
        "source_get_count": 0,
        "schema_exact": validated["schema_exact"],
        "annual_closure_status": "UNKNOWN",
        "promote_2025_to_proven": False,
        "metric_statuses": metric_statuses,
        "network_called": False,
        "drive_called": False,
        "response_persisted": False,
        "live_execution_authorized": False,
        "drive_read_count": 0,
        "drive_write_count": 0,
        "publication": False,
        "request_plan_evidence": plan_evidence,
        "observation_evidence": observation_evidence,
    }
    _stop(set(result) == set(runner_config["allowed_result_fields"]), "RESULT_FIELDS")
    return result


def _expected_outcome(probes: list[dict], phase_b: dict) -> str:
    observed = [probe["period"] for probe in probes if probe.get("records")]
    if phase_b.get("performed") is True:
        return "2025_P6_SCHEMA_EXACT_SEMANTICS_AND_CLOSURE_UNKNOWN"
    return "2025_PERIODS_OBSERVED_SCHEMA_UNKNOWN" if observed else "2025_NOT_OBSERVED"


def _validate_contract(config: dict, design: dict) -> None:
    _stop(config.get("schema") == "SIOPE_2025_BOUNDED_RUNNER_V1", "CONFIG_SCHEMA")
    _stop(config.get("tier") == "T0_OFFLINE", "CONFIG_TIER")
    components = config.get("components", {})
    _stop(components.get("live_transport") is None, "LIVE_COMPONENT")
    _stop(components.get("request_plan") == "robo_dados_publicos/sources/siope_2025_request_plan.py", "PLAN_COMPONENT")
    _stop(components.get("fake_transport") == "robo_dados_publicos/sources/siope_2025_fake_transport.py", "FAKE_COMPONENT")
    _stop(components.get("evidence") == "robo_dados_publicos/sources/siope_2025_evidence.py", "EVIDENCE_COMPONENT")

    target = config.get("target", {})
    _stop(target == {"year": 2025, "state": "SP", "municipality_code": 352690, "municipality_name": "Limeira"}, "TARGET")
    execution = config.get("execution", {})
    expected_execution = {
        "fake_transport_required": True,
        "live_transport_authorized": False,
        "stop_without_fake_transport": STOP_LIVE_NOT_AUTHORIZED,
        "periods": [1, 2, 3, 4, 5, 6],
        "phase_a_request_count": 6,
        "phase_b_period": 6,
        "phase_b_request_count_max": 1,
        "maximum_request_count": 7,
        "maximum_requests_per_period": 1,
        "timeout_seconds": 60,
        "max_response_bytes": 262144,
        "max_attempts": 1,
        "retry_authorized": False,
        "pagination_authorized": False,
        "follow_redirects": False,
        "follow_nextlink": False,
        "phase_b_precondition": PHASE_B_PRECONDITION,
    }
    _stop(execution == expected_execution, "EXECUTION_CONTRACT")

    semantic = config.get("semantic_guards", {})
    _stop(semantic.get("annual_closure_status_required") == "UNKNOWN", "SEMANTIC_CLOSURE")
    _stop(semantic.get("promote_2025_to_proven") is False, "SEMANTIC_PROMOTION")
    _stop(semantic.get("include_2026_authorized") is False, "SEMANTIC_2026")
    _stop(semantic.get("metric_status_required") == "UNKNOWN", "SEMANTIC_METRIC_STATUS")
    _stop(tuple(semantic.get("metric_ids", [])) == METRIC_IDS, "SEMANTIC_METRICS")

    effects = config.get("effects", {})
    _stop(effects and all(value is False for value in effects.values()), "EFFECTS")
    _stop(design.get("design_tier") == "T0_OFFLINE", "DESIGN_TIER")
    _stop(design.get("target", {}).get("year") == 2025, "DESIGN_YEAR")
    _stop(design.get("target", {}).get("resource_status") == "UNPROVEN_FOR_2025", "DESIGN_RESOURCE_STATUS")
    _stop(design.get("target", {}).get("annual_period_status") == "CANDIDATE_NOT_PROVEN", "DESIGN_PERIOD_STATUS")
    _stop(design.get("target", {}).get("annual_closure_status") == "UNKNOWN", "DESIGN_CLOSURE")
    _stop(design.get("promotion_contract", {}).get("promote_2025_to_proven") is False, "DESIGN_PROMOTION")
    _stop(design.get("future_batch_execution_authorized") is False, "DESIGN_BATCH")
    _stop(design.get("proposed_runtime", {}).get("runtime_execution_authorized_by_this_design") is False, "DESIGN_RUNTIME")

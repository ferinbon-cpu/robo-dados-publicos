"""Bounded first-live SIOPE 2025 discovery runtime.

The module can execute only with a validated AuthorizationGrant. TASK 004A does
not create such a grant in the repository, therefore source GET remains blocked.
"""

from __future__ import annotations

from robo_dados_publicos.sources.siope_2025_bounded_runner import (
    _expected_outcome,
    _validate_period_observation,
    validate_semantic_state,
)
from robo_dados_publicos.sources.siope_2025_evidence import (
    METRIC_IDS,
    build_sanitized_observation_evidence,
)
from robo_dados_publicos.sources.siope_2025_readonly_discovery_offline import (
    Siope2025OfflineFixtureError,
    validate_fixture,
)
from robo_dados_publicos.sources.siope_2025_request_plan import (
    PHASE_B_PRECONDITION,
    RequestExecutionLedger,
    materialize_request_plan,
    sanitized_plan_evidence,
)
from robo_dados_publicos.sources.siope_2025_t1_authorization import AuthorizationGrant
from robo_dados_publicos.sources.siope_2025_t1_transport import (
    Siope2025T1HttpTransport,
    Siope2025T1TransportError,
)

ERROR = "STOP_SIOPE_2025_T1_DISCOVERY"
PASS = "PASS_SIOPE_2025_T1_FIRST_LIVE_BOUNDED"


class Siope2025T1DiscoveryError(RuntimeError):
    def __init__(self, message: str, *, source_get_count: int = 0):
        super().__init__(message)
        self.source_get_count = source_get_count


def _stop(condition: bool, code: str, *, source_get_count: int = 0) -> None:
    if not condition:
        raise Siope2025T1DiscoveryError(f"{ERROR}_{code}", source_get_count=source_get_count)


def execute_authorized_discovery(
    *,
    grant: AuthorizationGrant,
    design: dict,
    transport: Siope2025T1HttpTransport,
) -> dict:
    """Execute the exact P1-P6 + conditional P6-schema plan once."""
    _stop(type(grant) is AuthorizationGrant, "AUTHORIZATION_GRANT_REQUIRED")
    _stop(type(transport) is Siope2025T1HttpTransport, "TRANSPORT_TYPE")
    _stop(transport.grant == grant, "GRANT_TRANSPORT_MISMATCH")

    plan = materialize_request_plan(design)
    ledger = RequestExecutionLedger(plan)
    expected_schema_fields = tuple(design["offline_validation"]["expected_schema_fields"])
    required_fields = list(design["phase_b_conditional_schema"]["required_gold_input_fields"])
    probes: list[dict] = []
    executed_ordinals: list[int] = []

    try:
        for spec in plan[:6]:
            ledger.consume(spec)
            observation = transport.request(spec)
            executed_ordinals.append(spec.ordinal)
            _validate_period_observation(observation, period=spec.period)
            probes.append(observation)

        p6_records = probes[5].get("records")
        _stop(isinstance(p6_records, list), "P6_RECORDS", source_get_count=transport.source_get_count)
        _stop(len(p6_records) <= 1, "P6_DUPLICATE", source_get_count=transport.source_get_count)
        if p6_records:
            _stop(plan[6].precondition == PHASE_B_PRECONDITION, "PHASE_B_PRECONDITION", source_get_count=transport.source_get_count)
            record = p6_records[0]
            _stop(
                isinstance(record, dict)
                and record.get("COD_MUNI") == 352690
                and record.get("NOM_MUNI") == "Limeira"
                and record.get("NUM_ANO") == 2025
                and record.get("NUM_PERI") == 6
                and record.get("SIG_UF") == "SP",
                "PHASE_B_IDENTITY_PRECONDITION",
                source_get_count=transport.source_get_count,
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
    except Siope2025T1TransportError as exc:
        raise Siope2025T1DiscoveryError(str(exc), source_get_count=exc.source_get_count) from None
    except Exception as exc:
        if isinstance(exc, Siope2025T1DiscoveryError):
            raise
        raise Siope2025T1DiscoveryError(str(exc), source_get_count=transport.source_get_count) from None

    _stop(transport.source_get_count == ledger.count, "SOURCE_GET_LEDGER_MISMATCH", source_get_count=transport.source_get_count)
    _stop(transport.source_get_count <= 7, "SOURCE_GET_BUDGET", source_get_count=transport.source_get_count)

    synthetic = {
        "schema": "SIOPE_2025_READONLY_DISCOVERY_OFFLINE_FIXTURE_V1",
        "case_id": "T1_FIRST_LIVE_TRANSIENT",
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
        validated = validate_fixture(synthetic, expected_schema_fields=expected_schema_fields)
    except Siope2025OfflineFixtureError as exc:
        raise Siope2025T1DiscoveryError(str(exc), source_get_count=transport.source_get_count) from None

    metric_statuses = {metric_id: "UNKNOWN" for metric_id in METRIC_IDS}
    validate_semantic_state(
        year=2025,
        state="SP",
        municipality_code=352690,
        annual_closure_status="UNKNOWN",
        promote_2025_to_proven=False,
        metric_statuses=metric_statuses,
    )
    observation_evidence = build_sanitized_observation_evidence(
        probes=probes,
        phase_b=phase_b,
        required_fields=required_fields,
        outcome=validated["outcome"],
        observed_periods=validated["observed_periods"],
    )
    observation_evidence["source_get_count"] = transport.source_get_count
    observation_evidence["network_called"] = transport.source_get_count > 0
    observation_evidence["authorization_id"] = grant.authorization_id

    return {
        "status": PASS,
        "authorization_id": grant.authorization_id,
        "outcome": validated["outcome"],
        "observed_periods": validated["observed_periods"],
        "source_get_count": transport.source_get_count,
        "schema_exact": validated["schema_exact"],
        "annual_closure_status": "UNKNOWN",
        "promote_2025_to_proven": False,
        "metric_statuses": metric_statuses,
        "drive_read_count": 0,
        "drive_write_count": 0,
        "publication": False,
        "response_persisted": False,
        "request_plan_evidence": sanitized_plan_evidence(plan, executed_ordinals=executed_ordinals),
        "observation_evidence": observation_evidence,
    }

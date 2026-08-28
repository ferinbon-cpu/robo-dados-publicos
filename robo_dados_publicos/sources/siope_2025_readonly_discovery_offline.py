"""Pure offline validation for sanitized SIOPE 2025 discovery fixtures."""

from __future__ import annotations

from collections.abc import Iterable

ERROR = "STOP_SIOPE_2025_OFFLINE_FIXTURE"


class Siope2025OfflineFixtureError(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Siope2025OfflineFixtureError(f"{ERROR}_{code}")


def validate_fixture(fixture: dict, *, expected_schema_fields: Iterable[str]) -> dict:
    """Validate one synthetic/sanitized fixture without performing I/O."""
    _stop(isinstance(fixture, dict), "OBJECT")
    _stop(fixture.get("schema") == "SIOPE_2025_READONLY_DISCOVERY_OFFLINE_FIXTURE_V1", "SCHEMA")
    _stop(fixture.get("synthetic") is True, "SYNTHETIC_REQUIRED")
    _stop(fixture.get("contains_financial_values") is False, "FINANCIAL_VALUES")
    _stop(fixture.get("network_called") is False, "NETWORK")
    _stop(fixture.get("drive_called") is False, "DRIVE")

    probes = fixture.get("phase_a_period_probes")
    _stop(isinstance(probes, list) and len(probes) == 6, "PROBE_COUNT")
    _stop([probe.get("period") for probe in probes] == [1, 2, 3, 4, 5, 6], "PROBE_PERIODS")
    observed = []
    request_count = 0
    expected_identity = {
        "COD_MUNI": 352690,
        "NOM_MUNI": "Limeira",
        "NUM_ANO": 2025,
        "SIG_UF": "SP",
    }
    for probe in probes:
        period = probe["period"]
        _validate_transport(probe, f"P{period}")
        request_count += probe["request_count"]
        records = probe.get("records")
        _stop(isinstance(records, list), f"RECORDS_P{period}")
        _stop(len(records) <= 1, f"DUPLICATE_P{period}")
        if records:
            record = records[0]
            _stop(isinstance(record, dict), f"RECORD_OBJECT_P{period}")
            _stop(set(record) == {*expected_identity, "NUM_PERI"}, f"IDENTITY_SCHEMA_P{period}")
            _stop(all(record.get(key) == value for key, value in expected_identity.items()), f"IDENTITY_P{period}")
            _stop(record.get("NUM_PERI") == period, f"IDENTITY_PERIOD_P{period}")
            observed.append(period)

    phase_b = fixture.get("phase_b_schema_probe")
    _stop(isinstance(phase_b, dict), "PHASE_B")
    performed = phase_b.get("performed")
    _stop(isinstance(performed, bool), "PHASE_B_PERFORMED")
    expected_fields = frozenset(expected_schema_fields)
    _stop(len(expected_fields) == 52, "EXPECTED_SCHEMA_COUNT")
    if 6 in observed:
        _stop(performed is True, "PHASE_B_REQUIRED")
        _validate_transport(phase_b, "PHASE_B")
        request_count += phase_b["request_count"]
        _stop(phase_b.get("period") == 6, "PHASE_B_PERIOD")
        fields = phase_b.get("schema_fields")
        _stop(isinstance(fields, list), "PHASE_B_FIELDS")
        _stop(len(fields) == len(set(fields)), "PHASE_B_DUPLICATE_FIELD")
        _stop(frozenset(fields) == expected_fields, "PHASE_B_SCHEMA_DRIFT")
        _stop(phase_b.get("field_semantics_status") == "NOT_PROVEN_SCHEMA_ONLY", "PHASE_B_SEMANTICS")
        outcome = "2025_P6_SCHEMA_EXACT_SEMANTICS_AND_CLOSURE_UNKNOWN"
    else:
        _stop(performed is False, "PHASE_B_NOT_AUTHORIZED")
        _stop(
            phase_b == {
                "performed": False,
                "period": None,
                "schema_fields": [],
                "field_semantics_status": "NOT_EVALUATED",
            },
            "PHASE_B_EMPTY",
        )
        outcome = "2025_PERIODS_OBSERVED_SCHEMA_UNKNOWN" if observed else "2025_NOT_OBSERVED"

    declared_request_count = fixture.get("declared_request_count")
    _stop(isinstance(declared_request_count, int) and declared_request_count <= 7, "REQUEST_BUDGET")
    _stop(declared_request_count == request_count, "REQUEST_COUNT_DECLARATION")
    _stop(fixture.get("expected_outcome") == outcome, "EXPECTED_OUTCOME")
    return {
        "status": "PASS_SIOPE_2025_OFFLINE_FIXTURE",
        "case_id": fixture.get("case_id"),
        "observed_periods": observed,
        "outcome": outcome,
        "schema_exact": outcome == "2025_P6_SCHEMA_EXACT_SEMANTICS_AND_CLOSURE_UNKNOWN",
        "annual_closure_status": "UNKNOWN",
        "promote_2025_to_proven": False,
        "network_called": False,
        "drive_called": False,
        "request_count": request_count,
    }


def _validate_transport(observation: dict, label: str) -> None:
    """Fail closed on transport metadata before interpreting records/schema."""
    _stop(observation.get("request_count") == 1, f"REQUEST_COUNT_{label}")
    _stop(observation.get("method") == "GET", f"METHOD_{label}")
    _stop(observation.get("response_status") == 200, f"HTTP_STATUS_{label}")
    _stop(
        observation.get("content_type") in {"application/json", "application/odata+json"},
        f"CONTENT_TYPE_{label}",
    )
    byte_count = observation.get("response_byte_count")
    _stop(isinstance(byte_count, int) and 0 <= byte_count <= 262144, f"RESPONSE_LIMIT_{label}")
    _stop(observation.get("redirect_followed") is False, f"REDIRECT_{label}")
    _stop(observation.get("nextlink_present") is False, f"NEXTLINK_{label}")
    _stop(observation.get("retry_performed") is False, f"RETRY_{label}")

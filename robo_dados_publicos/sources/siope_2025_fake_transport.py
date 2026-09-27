"""In-memory fake transport for T0 SIOPE 2025 runner tests and gates."""

from __future__ import annotations

from copy import deepcopy

from robo_dados_publicos.sources.siope_2025_request_plan import PlannedRequest

ERROR = "STOP_SIOPE_2025_FAKE_TRANSPORT"


class Siope2025FakeTransportError(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Siope2025FakeTransportError(f"{ERROR}_{code}")


class FakeSiope2025Transport:
    """Returns fixture copies and cannot perform network or filesystem I/O."""

    def __init__(self, fixture: dict):
        self._fixture = deepcopy(fixture)
        self.requests: list[PlannedRequest] = []

    def request(self, spec: PlannedRequest) -> dict:
        self.requests.append(spec)
        if spec.phase == "PERIOD_AVAILABILITY":
            probes = self._fixture.get("phase_a_period_probes", [])
            matches = [probe for probe in probes if probe.get("period") == spec.period]
            _stop(len(matches) == 1, f"PERIOD_RESPONSE_{spec.period}")
            return deepcopy(matches[0])
        _stop(spec.phase == "CONDITIONAL_SCHEMA" and spec.period == 6, "REQUEST_SPEC")
        phase_b = self._fixture.get("phase_b_schema_probe")
        _stop(isinstance(phase_b, dict) and phase_b.get("performed") is True, "SCHEMA_RESPONSE")
        return deepcopy(phase_b)

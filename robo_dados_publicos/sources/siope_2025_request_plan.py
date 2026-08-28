"""Pure request-plan materialization for the bounded SIOPE 2025 runner."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

ERROR = "STOP_SIOPE_2025_REQUEST_PLAN"
EXPECTED_PATH = "/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata/Dados_Gerais_Siope(Ano_Consulta=@Ano_Consulta,Num_Peri=@Num_Peri,Sig_UF=@Sig_UF)"
PHASE_B_PRECONDITION = "PHASE_A_PERIOD_6_OBSERVED_EXACT_IDENTITY"


class Siope2025RequestPlanError(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Siope2025RequestPlanError(f"{ERROR}_{code}")


@dataclass(frozen=True)
class PlannedRequest:
    ordinal: int
    phase: str
    method: str
    host: str
    path: str
    year: int
    period: int
    state: str
    municipality_code: int
    selected_fields: tuple[str, ...]
    timeout_seconds: int
    max_response_bytes: int
    max_attempts: int
    retry_authorized: bool
    follow_redirects: bool
    pagination_authorized: bool
    follow_nextlink: bool
    precondition: str | None

    def sanitized_shape(self) -> dict:
        return {
            "ordinal": self.ordinal,
            "phase": self.phase,
            "method": self.method,
            "host": self.host,
            "path": self.path,
            "timeout_seconds": self.timeout_seconds,
            "max_response_bytes": self.max_response_bytes,
            "max_attempts": self.max_attempts,
            "retry_authorized": self.retry_authorized,
            "follow_redirects": self.follow_redirects,
            "pagination_authorized": self.pagination_authorized,
            "follow_nextlink": self.follow_nextlink,
            "precondition": self.precondition,
            "query_keys": ["Ano_Consulta", "Num_Peri", "Sig_UF", "$filter", "$select", "$format"],
            "selected_field_count": len(self.selected_fields),
        }


@dataclass
class RequestExecutionLedger:
    plan: tuple[PlannedRequest, ...]
    _next_index: int = 0
    _seen_phase_period: set[tuple[str, int]] = field(default_factory=set)

    def __post_init__(self) -> None:
        validate_request_plan(self.plan)

    @property
    def count(self) -> int:
        return self._next_index

    def consume(self, spec: PlannedRequest) -> None:
        _stop(self._next_index < len(self.plan), "REQUEST_BUDGET")
        key = (spec.phase, spec.period)
        _stop(key not in self._seen_phase_period, "DUPLICATE_PHASE_PERIOD")
        _stop(spec == self.plan[self._next_index], "UNPLANNED_OR_OUT_OF_ORDER")
        self._seen_phase_period.add(key)
        self._next_index += 1


def _runtime_limits(design: dict) -> dict:
    runtime = design.get("proposed_runtime", {})
    target = design.get("target", {})
    _stop(target.get("year") == 2025, "YEAR")
    _stop(target.get("state") == "SP", "STATE")
    _stop(target.get("municipality_code") == 352690, "MUNICIPALITY")
    _stop(target.get("municipality_name") == "Limeira", "MUNICIPALITY_NAME")
    _stop(runtime.get("allowed_method") == "GET", "METHOD")
    _stop(runtime.get("allowed_host") == "www.fnde.gov.br", "HOST")
    _stop(runtime.get("allowed_path") == EXPECTED_PATH, "PATH")
    _stop(runtime.get("period_probe_values") == [1, 2, 3, 4, 5, 6], "PERIODS")
    _stop(runtime.get("maximum_total_request_count") == 7, "REQUEST_BOUND")
    _stop(runtime.get("maximum_requests_per_period") == 1, "REQUESTS_PER_PERIOD")
    _stop(runtime.get("timeout_seconds") == 60, "TIMEOUT")
    _stop(runtime.get("max_attempts") == 1, "ATTEMPTS")
    _stop(runtime.get("max_response_bytes_per_request") == 262144, "RESPONSE_LIMIT")
    _stop(runtime.get("follow_redirects") is False, "REDIRECT_POLICY")
    _stop(runtime.get("follow_odata_nextlink") is False, "NEXTLINK_POLICY")
    _stop(runtime.get("retry_authorized") is False, "RETRY_POLICY")
    _stop(runtime.get("pagination_authorized") is False, "PAGINATION_POLICY")
    _stop(design.get("phase_b_conditional_schema", {}).get("precondition") == PHASE_B_PRECONDITION, "PHASE_B_PRECONDITION")
    return runtime


def materialize_request_plan(design: dict) -> tuple[PlannedRequest, ...]:
    runtime = _runtime_limits(design)
    identity_fields = tuple(design.get("phase_a_period_availability", {}).get("selected_fields", []))
    schema_fields = tuple(design.get("offline_validation", {}).get("expected_schema_fields", []))
    _stop(len(identity_fields) == 5 and len(set(identity_fields)) == 5, "IDENTITY_FIELDS")
    _stop(len(schema_fields) == 52 and len(set(schema_fields)) == 52, "SCHEMA_FIELDS")

    common = {
        "method": "GET",
        "host": "www.fnde.gov.br",
        "path": EXPECTED_PATH,
        "year": 2025,
        "state": "SP",
        "municipality_code": 352690,
        "timeout_seconds": 60,
        "max_response_bytes": 262144,
        "max_attempts": 1,
        "retry_authorized": False,
        "follow_redirects": False,
        "pagination_authorized": False,
        "follow_nextlink": False,
    }
    plan = [
        PlannedRequest(
            ordinal=period,
            phase="PERIOD_AVAILABILITY",
            period=period,
            selected_fields=identity_fields,
            precondition=None,
            **common,
        )
        for period in range(1, 7)
    ]
    plan.append(
        PlannedRequest(
            ordinal=7,
            phase="CONDITIONAL_SCHEMA",
            period=6,
            selected_fields=schema_fields,
            precondition=PHASE_B_PRECONDITION,
            **common,
        )
    )
    result = tuple(plan)
    validate_request_plan(result)
    return result


def validate_request_plan(plan: tuple[PlannedRequest, ...]) -> None:
    _stop(len(plan) == 7, "COUNT")
    _stop([item.ordinal for item in plan] == list(range(1, 8)), "ORDINALS")
    _stop([item.period for item in plan] == [1, 2, 3, 4, 5, 6, 6], "PERIOD_ORDER")
    _stop(all(item.phase == "PERIOD_AVAILABILITY" for item in plan[:6]), "PHASE_A")
    _stop(plan[6].phase == "CONDITIONAL_SCHEMA", "PHASE_B")
    _stop(all(item.method == "GET" for item in plan), "METHOD_DRIFT")
    _stop(all(item.host == "www.fnde.gov.br" for item in plan), "HOST_DRIFT")
    _stop(all(item.path == EXPECTED_PATH for item in plan), "PATH_DRIFT")
    _stop(all(item.year == 2025 and item.state == "SP" and item.municipality_code == 352690 for item in plan), "TARGET_DRIFT")
    _stop(all(item.timeout_seconds == 60 for item in plan), "TIMEOUT_DRIFT")
    _stop(all(item.max_response_bytes == 262144 for item in plan), "RESPONSE_LIMIT_DRIFT")
    _stop(all(item.max_attempts == 1 for item in plan), "ATTEMPT_DRIFT")
    _stop(all(item.retry_authorized is False for item in plan), "RETRY_DRIFT")
    _stop(all(item.follow_redirects is False for item in plan), "REDIRECT_DRIFT")
    _stop(all(item.pagination_authorized is False for item in plan), "PAGINATION_DRIFT")
    _stop(all(item.follow_nextlink is False for item in plan), "NEXTLINK_DRIFT")
    _stop(all(item.precondition is None for item in plan[:6]), "PHASE_A_PRECONDITION")
    _stop(plan[6].precondition == PHASE_B_PRECONDITION, "PHASE_B_PRECONDITION_DRIFT")
    _stop(all(len(item.selected_fields) == 5 for item in plan[:6]), "PHASE_A_SELECT")
    _stop(len(plan[6].selected_fields) == 52, "PHASE_B_SELECT")
    _stop(len({(item.phase, item.period) for item in plan}) == 7, "DUPLICATE_PHASE_PERIOD")


def sanitized_plan_evidence(plan: tuple[PlannedRequest, ...], *, executed_ordinals: list[int]) -> dict:
    validate_request_plan(plan)
    allowed = ([], [1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 6, 7])
    _stop(executed_ordinals in allowed, "EXECUTED_ORDINALS")
    shapes = [item.sanitized_shape() for item in plan if item.ordinal in executed_ordinals]
    raw = json.dumps(shapes, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return {
        "request_shape_count": len(shapes),
        "request_shapes": shapes,
        "request_shapes_sha256": hashlib.sha256(raw).hexdigest(),
        "query_values_persisted": False,
        "response_values_persisted": False,
    }

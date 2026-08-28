"""Strict read-only HTTP adapter for the future authorized SIOPE 2025 T1 run.

This module has no import-time network effects. Construction of the default live
client is only allowed after an AuthorizationGrant has been produced by the
separate authorization gate.
"""

from __future__ import annotations

from dataclasses import dataclass

from robo_dados_publicos.sources.siope_2025_request_plan import (
    EXPECTED_PATH,
    PlannedRequest,
)
from robo_dados_publicos.sources.siope_2025_t1_authorization import AuthorizationGrant
from robo_dados_publicos.sources.siope_client import (
    SiopeClient,
    SiopeClientError,
    SiopeClientPolicy,
)

ERROR = "STOP_SIOPE_2025_T1_TRANSPORT"


class Siope2025T1TransportError(RuntimeError):
    def __init__(self, message: str, *, source_get_count: int = 0):
        super().__init__(message)
        self.source_get_count = source_get_count


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Siope2025T1TransportError(f"{ERROR}_{code}")


@dataclass(frozen=True)
class T1TransportPolicy:
    timeout_seconds: int = 60
    max_response_bytes: int = 262144
    max_attempts: int = 1
    retry_authorized: bool = False
    follow_redirects: bool = False
    pagination_authorized: bool = False
    follow_nextlink: bool = False

    def validate(self) -> None:
        _stop(self.timeout_seconds == 60, "TIMEOUT")
        _stop(self.max_response_bytes == 262144, "RESPONSE_LIMIT")
        _stop(self.max_attempts == 1, "ATTEMPTS")
        _stop(self.retry_authorized is False, "RETRY")
        _stop(self.follow_redirects is False, "REDIRECT")
        _stop(self.pagination_authorized is False, "PAGINATION")
        _stop(self.follow_nextlink is False, "NEXTLINK")


class Siope2025T1HttpTransport:
    """Adapter around the already proven SiopeClient with stricter 2025 limits."""

    def __init__(
        self,
        *,
        grant: AuthorizationGrant,
        client: SiopeClient,
        policy: T1TransportPolicy | None = None,
    ):
        _stop(type(grant) is AuthorizationGrant, "AUTHORIZATION_GRANT_REQUIRED")
        self.grant = grant
        self.policy = policy or T1TransportPolicy()
        self.policy.validate()
        _stop(client.policy.timeout_seconds == 60, "CLIENT_TIMEOUT")
        _stop(client.policy.max_response_bytes == 262144, "CLIENT_RESPONSE_LIMIT")
        _stop(client.policy.max_attempts == 1, "CLIENT_ATTEMPTS")
        _stop(client.policy.follow_redirects is False, "CLIENT_REDIRECT")
        _stop(client.policy.follow_nextlink is False, "CLIENT_NEXTLINK")
        self.client = client
        self._seen_phase_period: set[tuple[str, int]] = set()
        self.source_get_count = 0

    @classmethod
    def build_live(cls, *, grant: AuthorizationGrant) -> "Siope2025T1HttpTransport":
        policy = T1TransportPolicy()
        policy.validate()
        client = SiopeClient(
            policy=SiopeClientPolicy(
                timeout_seconds=policy.timeout_seconds,
                max_response_bytes=policy.max_response_bytes,
                max_attempts=policy.max_attempts,
                follow_redirects=policy.follow_redirects,
                follow_nextlink=policy.follow_nextlink,
            )
        )
        return cls(grant=grant, client=client, policy=policy)

    def request(self, spec: PlannedRequest) -> dict:
        self._validate_spec(spec)
        key = (spec.phase, spec.period)
        _stop(key not in self._seen_phase_period, "DUPLICATE_PHASE_PERIOD")
        self._seen_phase_period.add(key)
        try:
            page = self.client.get_dados_gerais_page(
                ano=spec.year,
                periodo=spec.period,
                uf=spec.state,
                municipality_code=spec.municipality_code,
                select_fields=spec.selected_fields,
            )
            self.source_get_count += page.request_count
        except SiopeClientError as exc:
            self.source_get_count += int(getattr(exc, "request_count", 0) or 0)
            raise Siope2025T1TransportError(
                f"{ERROR}_CLIENT_{exc}",
                source_get_count=self.source_get_count,
            ) from None

        common = {
            "period": spec.period,
            "request_count": page.request_count,
            "method": "GET",
            "response_status": page.status,
            "content_type": page.content_type,
            "response_byte_count": page.response_byte_count,
            "redirect_followed": False,
            "nextlink_present": page.nextlink_present,
            "retry_performed": False,
            "records": page.records,
        }
        if spec.phase == "CONDITIONAL_SCHEMA":
            fields = list(page.records[0].keys()) if len(page.records) == 1 else []
            return {
                **common,
                "performed": True,
                "schema_fields": fields,
                "field_semantics_status": "NOT_PROVEN_SCHEMA_ONLY",
            }
        return common

    @staticmethod
    def _validate_spec(spec: PlannedRequest) -> None:
        _stop(type(spec) is PlannedRequest, "SPEC_TYPE")
        _stop(spec.method == "GET", "METHOD")
        _stop(spec.host == "www.fnde.gov.br", "HOST")
        _stop(spec.path == EXPECTED_PATH, "PATH")
        _stop(spec.year == 2025, "YEAR")
        _stop(spec.state == "SP", "STATE")
        _stop(spec.municipality_code == 352690, "MUNICIPALITY")
        _stop(spec.period in {1, 2, 3, 4, 5, 6}, "PERIOD")
        _stop(spec.timeout_seconds == 60, "TIMEOUT_SPEC")
        _stop(spec.max_response_bytes == 262144, "RESPONSE_LIMIT_SPEC")
        _stop(spec.max_attempts == 1, "ATTEMPTS_SPEC")
        _stop(spec.retry_authorized is False, "RETRY_SPEC")
        _stop(spec.follow_redirects is False, "REDIRECT_SPEC")
        _stop(spec.pagination_authorized is False, "PAGINATION_SPEC")
        _stop(spec.follow_nextlink is False, "NEXTLINK_SPEC")

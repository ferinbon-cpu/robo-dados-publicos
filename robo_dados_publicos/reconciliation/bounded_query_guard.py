from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse


class BoundedQueryGuardError(RuntimeError):
    """Fail-closed violation of a bounded public-source query contract."""


@dataclass
class BoundedQueryGuard:
    """Pure request-budget/origin guard for bounded read-only source queries.

    This class performs no network I/O. Call ``authorize`` immediately before a
    transport request; only a returned observation is eligible to be sent.
    """

    allowed_host: str
    max_requests: int
    allowed_methods: frozenset[str] = frozenset({"GET", "POST"})
    request_log: list[dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.allowed_host = self.allowed_host.strip().lower()
        if not self.allowed_host:
            raise BoundedQueryGuardError("STOP_BOUNDED_QUERY_ALLOWED_HOST_MISSING")
        if not isinstance(self.max_requests, int) or self.max_requests < 1:
            raise BoundedQueryGuardError("STOP_BOUNDED_QUERY_REQUEST_BUDGET_INVALID")

    def authorize(self, url: str, *, method: str = "GET", params: dict | None = None) -> dict:
        if len(self.request_log) >= self.max_requests:
            raise BoundedQueryGuardError("STOP_BOUNDED_QUERY_HTTP_BUDGET_EXCEEDED")

        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if host != self.allowed_host:
            raise BoundedQueryGuardError("STOP_BOUNDED_QUERY_ORIGIN_OUTSIDE_ALLOWLIST")

        normalized_method = method.upper()
        if normalized_method not in self.allowed_methods:
            raise BoundedQueryGuardError("STOP_BOUNDED_QUERY_METHOD_NOT_ALLOWED")

        observation = {
            "ordinal": len(self.request_log) + 1,
            "method": normalized_method,
            "host": host,
            "path": parsed.path,
            "submitted_field_names": sorted((params or {}).keys()),
        }
        self.request_log.append(observation)
        return observation


def validate_resolver_status(status: str, allowed_statuses: set[str] | frozenset[str]) -> str:
    if status not in allowed_statuses:
        raise BoundedQueryGuardError("STOP_BOUNDED_QUERY_UNEXPECTED_RESOLVER_STATUS")
    return status

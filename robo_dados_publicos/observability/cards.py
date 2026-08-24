from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


def _required_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _iso8601(value: str) -> datetime:
    _required_text("timestamp", value)
    normalized = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return dt.astimezone(timezone.utc)


@dataclass(frozen=True)
class SourceCard:
    source_id: str
    institution: str
    source_url: str
    formats: tuple[str, ...]
    periodicity: str
    scope: str
    expected_update_interval_hours: float | None = None
    fields: tuple[str, ...] = ()
    license: str = ""
    risks: tuple[str, ...] = ()
    owner: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        for name in ("source_id", "institution", "source_url", "periodicity", "scope"):
            _required_text(name, getattr(self, name))
        if not self.formats:
            raise ValueError("formats must not be empty")
        if self.expected_update_interval_hours is not None and self.expected_update_interval_hours <= 0:
            raise ValueError("expected_update_interval_hours must be positive")

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "SourceCard":
        payload = dict(data)
        for key in ("formats", "fields", "risks"):
            if key in payload:
                payload[key] = tuple(payload[key])
        return cls(**payload)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RunCard:
    run_id: str
    source_id: str
    software_version: str
    started_at: str
    finished_at: str
    status: str
    artifacts: tuple[str, ...] = ()
    records_in: int | None = None
    records_out: int | None = None
    warnings: tuple[str, ...] = ()
    failure_reason: str = ""
    expected_absence: bool = False

    def __post_init__(self) -> None:
        for name in ("run_id", "source_id", "software_version", "started_at", "finished_at", "status"):
            _required_text(name, getattr(self, name))
        start = _iso8601(self.started_at)
        finish = _iso8601(self.finished_at)
        if finish < start:
            raise ValueError("finished_at must not be before started_at")
        for name in ("records_in", "records_out"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.expected_absence and self.status != "EXPECTED_ABSENCE":
            raise ValueError("expected_absence requires status EXPECTED_ABSENCE")

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "RunCard":
        payload = dict(data)
        for key in ("artifacts", "warnings"):
            if key in payload:
                payload[key] = tuple(payload[key])
        return cls(**payload)

    @property
    def latency_seconds(self) -> float:
        return (_iso8601(self.finished_at) - _iso8601(self.started_at)).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["latency_seconds"] = self.latency_seconds
        return payload


@dataclass(frozen=True)
class MetricCard:
    metric_id: str
    name: str
    definition: str
    formula: str
    unit: str
    source_fields: tuple[str, ...]
    null_semantics: str
    limitations: tuple[str, ...] = ()
    example: str = ""

    def __post_init__(self) -> None:
        for field_name in (
            "metric_id",
            "name",
            "definition",
            "formula",
            "unit",
            "null_semantics",
        ):
            _required_text(field_name, getattr(self, field_name))
        if not self.source_fields:
            raise ValueError("source_fields must not be empty")

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "MetricCard":
        payload = dict(data)
        for key in ("source_fields", "limitations"):
            if key in payload:
                payload[key] = tuple(payload[key])
        return cls(**payload)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

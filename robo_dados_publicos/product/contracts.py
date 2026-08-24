from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime


_ALLOWED_STATUSES = {
    "READY",
    "READY_WITH_CAUTION",
    "EVIDENCIA_INSUFICIENTE",
    "NO_DATA",
}


@dataclass(frozen=True)
class ReportCard:
    """Human-facing report contract.

    The card describes the output without claiming that a presentation layer is
    evidence. Numeric or documentary truth must remain in the underlying
    AnswerContract rows and their sources.
    """

    report_id: str
    title: str
    scope: str
    software_version: str
    generated_at: str
    status: str
    row_count: int
    formats: tuple[str, ...]
    limitations: tuple[str, ...] = ()
    notes: str = ""

    def __post_init__(self):
        for name in ("report_id", "title", "scope", "software_version", "generated_at", "status"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name.upper()}_REQUIRED")
        try:
            parsed = datetime.fromisoformat(self.generated_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("GENERATED_AT_INVALID_ISO8601") from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("GENERATED_AT_TIMEZONE_REQUIRED")
        if self.status not in _ALLOWED_STATUSES:
            raise ValueError("REPORT_STATUS_INVALID")
        if self.row_count < 0:
            raise ValueError("ROW_COUNT_NEGATIVE")
        if not self.formats:
            raise ValueError("REPORT_FORMATS_REQUIRED")
        if len(set(self.formats)) != len(self.formats):
            raise ValueError("REPORT_FORMATS_DUPLICATED")

    def to_dict(self) -> dict:
        data = asdict(self)
        data["formats"] = list(self.formats)
        data["limitations"] = list(self.limitations)
        return data

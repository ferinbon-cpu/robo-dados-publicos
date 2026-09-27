from __future__ import annotations

from dataclasses import asdict, dataclass, field


STAGES = (
    "PREFLIGHT", "SOURCE_SELECTION", "ACQUISITION_OR_REUSE", "PROCESSING",
    "RECONCILIATION", "OBSERVABILITY", "PRODUCT_BUILD", "OPERATIONAL_SUMMARY",
)
STATUSES = {
    "PASS", "SKIPPED_ALREADY_PROVEN", "NO_NEW_DATA", "EVIDENCIA_INSUFICIENTE",
    "STOP_CONTRACT_UNPROVEN", "STOP_SCHEMA_UNKNOWN", "STOP_AUTHORIZATION_REQUIRED",
    "STOP_DEPENDENCY", "FAILED",
}
SOURCE_AUTHORIZATION_STATES = {
    "PINNED_REUSE", "LIVE_READONLY_AUTHORIZED", "LIVE_CREATE_ONLY_AUTHORIZED",
    "BLOCKED_AUTHORIZATION_REQUIRED", "BLOCKED_CONTRACT_UNPROVEN",
}


@dataclass(frozen=True)
class StageResult:
    stage: str
    status: str
    executed: bool
    input_identity: list[str] = field(default_factory=list)
    output_identity: list[str] = field(default_factory=list)
    evidence_references: list[str] = field(default_factory=list)
    warnings_stops: list[str] = field(default_factory=list)
    remote_reads: int = 0
    remote_writes: int = 0

    def __post_init__(self):
        if self.stage not in STAGES or self.status not in STATUSES:
            raise ValueError("UNKNOWN_OPERATIONAL_STAGE_OR_STATUS")
        if self.remote_reads or self.remote_writes:
            raise ValueError("TASK_017_REMOTE_EFFECT_PROHIBITED")

    def to_dict(self) -> dict:
        return asdict(self)

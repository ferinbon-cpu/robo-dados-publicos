from dataclasses import dataclass, asdict
from typing import Any

@dataclass(frozen=True)
class GateResult:
    gate: str
    passed: bool
    status: str
    message: str = ""
    payload: dict[str, Any] | None = None

    def to_dict(self):
        return asdict(self)

@dataclass(frozen=True)
class IngestDecision:
    decision: str
    sha256: str
    reason: str

@dataclass(frozen=True)
class AnswerContract:
    status: str
    dado: str = ""
    calculo: str = ""
    correspondencia: str = ""
    interpretacao: str = ""
    cautela: str = ""
    fontes: tuple[str, ...] = ()

from dataclasses import dataclass
from pathlib import Path
import json

@dataclass(frozen=True)
class Config:
    state_db: str = "runtime/robot_state.sqlite"
    supported_extensions: tuple[str, ...] = (".csv", ".xlsx", ".json", ".pdf", ".zip")
    bronze_immutable: bool = True
    unknown_schema_action: str = "STOP_QUARANTINE"
    llm_numeric_truth_engine: bool = False

    @classmethod
    def from_json(cls, path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if "supported_extensions" in data:
            data["supported_extensions"] = tuple(data["supported_extensions"])
        return cls(**data)

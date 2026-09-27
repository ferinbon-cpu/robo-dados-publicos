from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from robo_dados_publicos.analytics.task202_equity_missingness_aware_gate import (
    current_answerability_config_v4,
    current_question_answerability_v4,
)

ROOT = Path(__file__).resolve().parents[2]
POINTER = ROOT / "config/observatory_current_answerability_pointer.v1.json"


class CurrentAnswerabilityStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise CurrentAnswerabilityStop(code)


def load_pointer(path: str | Path = POINTER) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "OBSERVATORY_CURRENT_ANSWERABILITY_POINTER_V1", "CURRENT_ANSWERABILITY_SCHEMA")
    _stop(obj.get("canonical_version") == 4, "CURRENT_ANSWERABILITY_VERSION")
    _stop(obj.get("base_config") == "config/observatory_semantic_answerability.v3.json", "CURRENT_ANSWERABILITY_BASE")
    _stop(obj.get("overlay") == "config/observatory_semantic_answerability.v4.overlay.json", "CURRENT_ANSWERABILITY_OVERLAY")
    _stop(
        obj.get("evaluator_function") == "current_question_answerability",
        "CURRENT_ANSWERABILITY_FUNCTION",
    )
    _stop(all(v is False for v in obj["remote_effects"].values()), "CURRENT_ANSWERABILITY_REMOTE")
    return obj


def current_answerability_config() -> dict[str, Any]:
    load_pointer()
    return current_answerability_config_v4()


def current_question_answerability(
    products: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    pointer = load_pointer()
    report = current_question_answerability_v4(products)
    _stop(report["status_counts"] == pointer["expected_status_counts"], "CURRENT_ANSWERABILITY_EXPECTED_COUNTS")
    return report

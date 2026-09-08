from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from robo_dados_publicos.analytics.current_observatory_bundle import (
    build_current_products,
)
from robo_dados_publicos.productization.human_answer_renderer import (
    build_answer_card,
    render_answer_card_markdown,
)


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "config/task206_offline_answer_cli_qa.v1.json"


class Task206QaStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task206QaStop(code)


def load_contract(path: str | Path = CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK206_OFFLINE_ANSWER_CLI_QA_V1", "TASK206_QA_SCHEMA")
    _stop(obj.get("issue") == 656, "TASK206_QA_ISSUE")
    _stop(len(obj.get("representative_qa") or []) == 6, "TASK206_QA_CASES")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK206_QA_REMOTE")
    return obj


def _facts(card: Mapping[str, Any]) -> str:
    return "\n".join(str(row.get("text") or "") for row in card["NUMBER_OR_FACT"])


def _markdown(card: Mapping[str, Any]) -> str:
    return render_answer_card_markdown(card)["markdown"]


def _common(card: Mapping[str, Any]) -> None:
    _stop(bool(card["NUMBER_OR_FACT"]), "TASK206_QA_FACT")
    _stop(bool(card["TIME_REFERENCE"]), "TASK206_QA_TIME")
    _stop(bool(card["SOURCE_AND_PROVENANCE"]), "TASK206_QA_PROVENANCE")
    _stop(bool(card["CAUTION_OR_LIMIT"]), "TASK206_QA_CAUTION")
    _stop(card["llm_used"] is False, "TASK206_QA_LLM")
    _stop(card["numeric_invention_performed"] is False, "TASK206_QA_NUMERIC")
    _stop(card["causal_effect_created"] is False, "TASK206_QA_CAUSAL")


def representative_qa(
    products: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    contract = load_contract()
    results: list[dict[str, Any]] = []

    for spec in contract["representative_qa"]:
        qid = spec["question_id"]
        card = build_answer_card(qid, products)
        _common(card)
        facts = _facts(card)
        markdown = _markdown(card)

        if qid == "ACC_Q1":
            _stop("368762412.07" in facts, "TASK206_QA_ACC_COMMITTED")
            _stop("262452288.06" in facts, "TASK206_QA_ACC_LIQUIDATED")
            _stop("227797802.44" in facts, "TASK206_QA_ACC_PAID")
            _stop(
                "COMMITMENT_NE_LIQUIDATION_NE_PAYMENT" in card["CAUTION_OR_LIMIT"],
                "TASK206_QA_ACC_STAGE_GUARD",
            )

        elif qid == "FIN_Q3":
            _stop("118066203.65" in facts, "TASK206_QA_FIN_FUNDEB")
            _stop("3692142.87" in facts, "TASK206_QA_FIN_ETI")
            _stop(
                "REVENUE_NE_EXPENDITURE" in card["CAUTION_OR_LIMIT"],
                "TASK206_QA_FIN_GUARD",
            )

        elif qid == "PLAN_Q1":
            _stop("PLANNING_NE_EXECUTION" in card["CAUTION_OR_LIMIT"], "TASK206_QA_PLAN_GUARD")
            _stop(
                "Planejamento e autorização não provam, por si só, execução." in markdown,
                "TASK206_QA_PLAN_EXPLANATION",
            )

        elif qid == "NORMS_Q1":
            _stop("NORM_NE_IMPLEMENTATION" in card["CAUTION_OR_LIMIT"], "TASK206_QA_NORM_GUARD")
            _stop(
                "A existência de uma norma não prova implementação ou resultado." in markdown,
                "TASK206_QA_NORM_EXPLANATION",
            )

        elif qid == "TEACH_Q2":
            _stop("1280" in facts, "TASK206_QA_TEACH_COUNT")
            for token in ("681", "291", "400"):
                _stop(token in facts, f"TASK206_QA_TEACH_BOND_{token}")
            _stop(
                "PERSONNEL_EVENT_FLOW_NE_WORKFORCE_STOCK" in card["CAUTION_OR_LIMIT"],
                "TASK206_QA_TEACH_FLOW_GUARD",
            )
            _stop("vínculo" in facts.casefold(), "TASK206_QA_TEACH_BOND_LABEL")

        elif qid == "EQUITY_Q1":
            _stop("64/69" in facts, "TASK206_QA_EQUITY_COVERAGE")
            _stop("5 escolas permanecem HELD" in facts, "TASK206_QA_EQUITY_HELD")
            _stop(
                "TERRITORY_COVERAGE_64_OF_69_5_HELD_NE_FULL_NETWORK"
                in card["CAUTION_OR_LIMIT"],
                "TASK206_QA_EQUITY_GUARD",
            )
            _stop(
                "Contexto do território da escola não é perfil socioeconômico individual dos estudantes."
                in markdown,
                "TASK206_QA_EQUITY_EXPLANATION",
            )

        else:
            raise Task206QaStop("TASK206_QA_UNKNOWN_CASE")

        rendered = render_answer_card_markdown(card)
        results.append(
            {
                "question_id": qid,
                "focus": spec["focus"],
                "answer_card_sha256": card["answer_card_sha256"],
                "markdown_sha256": rendered["markdown_sha256"],
                "fact_count": len(card["NUMBER_OR_FACT"]),
                "time_reference_count": len(card["TIME_REFERENCE"]),
                "provenance_count": len(card["SOURCE_AND_PROVENANCE"]),
                "caution_count": len(card["CAUTION_OR_LIMIT"]),
                "status": "PASS",
            }
        )

    _stop(len(results) == 6, "TASK206_QA_RESULT_COUNT")
    return {
        "schema": "TASK206_REPRESENTATIVE_HUMAN_ANSWER_QA_V1",
        "status": "PASS",
        "case_count": 6,
        "cases": results,
        "presentation_repairs_verified": {
            "teacher_bond_context_visible": True,
            "equity_territory_missingness_visible": True,
        },
        "llm_used": False,
        "remote_effects": dict(contract["remote_effects"]),
    }


def build_current_representative_qa() -> dict[str, Any]:
    contract = load_contract()
    products = build_current_products(
        generated_at=contract["default_generated_at"],
        software_version=contract["default_software_version"],
    )
    return representative_qa(products)

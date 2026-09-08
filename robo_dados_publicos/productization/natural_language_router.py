from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from typing import Any, Mapping

from robo_dados_publicos.analytics.current_observatory_answerability import (
    current_answerability_config,
)
from robo_dados_publicos.analytics.current_observatory_bundle import (
    build_current_products,
)
from robo_dados_publicos.productization.human_answer_renderer import (
    build_answer_card,
    render_answer_card_markdown,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task207_natural_language_router.v1.json"
TASK206_CONTRACT = ROOT / "config/task206_offline_answer_cli_qa.v1.json"


class Task207RouteStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task207RouteStop(code)


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def normalize_text(value: str) -> str:
    _stop(isinstance(value, str), "TASK207_TEXT_TYPE")
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.casefold()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _contains(normalized_text: str, normalized_marker: str) -> bool:
    marker = normalize_text(normalized_marker)
    if not marker:
        return False
    padded_text = f" {normalized_text} "
    padded_marker = f" {marker} "
    return padded_marker in padded_text


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK207_NATURAL_LANGUAGE_ROUTER_V1", "TASK207_SCHEMA")
    _stop(obj.get("issue") == 658, "TASK207_ISSUE")
    _stop(
        obj.get("base_main_sha") == "143c11cb22cf38c801ab4595e112d02f972aa306",
        "TASK207_BASE",
    )
    _stop(
        obj.get("mode") == "T0_OFFLINE_DETERMINISTIC_TEXT_TO_CANONICAL_QUESTION_ROUTER",
        "TASK207_MODE",
    )
    _stop(set(obj.get("route_states") or []) == {"ROUTED", "AMBIGUOUS", "LOW_CONFIDENCE_STOP"}, "TASK207_STATES")
    _stop(len(obj.get("question_routes") or {}) == 38, "TASK207_ROUTE_COUNT")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK207_REMOTE")
    return obj


def _current_questions() -> list[dict[str, str]]:
    cfg = current_answerability_config()
    rows = [
        {
            "question_id": str(row["id"]),
            "domain_id": str(row["domain_id"]),
            "text": str(row["text"]),
        }
        for row in cfg["questions"]
    ]
    rows.sort(key=lambda x: x["question_id"])
    _stop(len(rows) == 38, "TASK207_CURRENT_QUESTION_COUNT")
    _stop(len({x["question_id"] for x in rows}) == 38, "TASK207_CURRENT_QUESTION_DUPLICATE")
    return rows


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(path)
    current = _current_questions()
    ids = {x["question_id"] for x in current}
    route_ids = set(obj["question_routes"])
    _stop(ids == route_ids, "TASK207_ROUTE_ID_DRIFT")

    for qid, spec in obj["question_routes"].items():
        _stop(spec.get("domain_id") in {x["domain_id"] for x in current if x["question_id"] == qid}, "TASK207_DOMAIN_DRIFT")
        _stop(isinstance(spec.get("phrases"), list) and spec["phrases"], "TASK207_PHRASES")
        _stop(isinstance(spec.get("terms"), list) and spec["terms"], "TASK207_TERMS")
        _stop(isinstance(spec.get("negative_terms"), list), "TASK207_NEGATIVE_TERMS")

    scoring = obj["scoring"]
    _stop(scoring["exact_canonical_question_score"] == 100, "TASK207_EXACT_SCORE")
    _stop(scoring["phrase_weight"] > scoring["term_weight"] > 0, "TASK207_WEIGHTS")
    _stop(scoring["single_route_min_score"] > scoring["low_confidence_min_score"], "TASK207_THRESHOLDS")
    _stop(scoring["ambiguity_candidate_min_score"] > 0, "TASK207_AMBIGUITY_MIN")
    return {
        "schema": "TASK207_NATURAL_LANGUAGE_ROUTER_VALIDATION_V1",
        "status": "PASS",
        "question_count": 38,
        "route_id_drift": False,
        "network": False,
        "drive_write": False,
        "llm": False,
    }


def _score_question(
    normalized_query: str,
    qid: str,
    spec: Mapping[str, Any],
    *,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    scoring = contract["scoring"]
    matched_phrases = [
        phrase
        for phrase in spec["phrases"]
        if _contains(normalized_query, phrase)
    ]
    matched_terms = [
        term
        for term in spec["terms"]
        if _contains(normalized_query, term)
    ]
    matched_negative = [
        term
        for term in spec["negative_terms"]
        if _contains(normalized_query, term)
    ]
    score = (
        len(matched_phrases) * int(scoring["phrase_weight"])
        + len(matched_terms) * int(scoring["term_weight"])
        - len(matched_negative) * int(scoring["negative_term_penalty"])
    )
    score = max(0, score)
    return {
        "question_id": qid,
        "domain_id": str(spec["domain_id"]),
        "score": score,
        "matched_phrases": sorted(matched_phrases),
        "matched_terms": sorted(matched_terms),
        "matched_negative_terms": sorted(matched_negative),
    }


def _confidence(score: int, margin: int, contract: Mapping[str, Any]) -> float:
    scoring = contract["scoring"]
    score_component = min(1.0, score / float(scoring["confidence_score_divisor"]))
    margin_component = min(1.0, max(0, margin) / float(scoring["confidence_margin_divisor"]))
    return round(0.75 * score_component + 0.25 * margin_component, 4)


def route_natural_language(
    text: str,
    *,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    validate_contract(contract_path)
    normalized = normalize_text(text)
    _stop(bool(normalized), "TASK207_EMPTY_TEXT")

    current = _current_questions()
    current_by_id = {x["question_id"]: x for x in current}

    for row in current:
        if normalized == normalize_text(row["text"]):
            material = {
                "normalized_text": normalized,
                "state": "ROUTED",
                "route_mode": "EXACT_CANONICAL_TEXT",
                "selected_question_ids": [row["question_id"]],
                "top_score": contract["scoring"]["exact_canonical_question_score"],
                "second_score": 0,
                "margin": contract["scoring"]["exact_canonical_question_score"],
                "confidence": 1.0,
            }
            return {
                "schema": "TASK207_NATURAL_LANGUAGE_ROUTE_RESULT_V1",
                **material,
                "input_text": text,
                "selected_questions": [current_by_id[row["question_id"]]],
                "candidates": [
                    {
                        "question_id": row["question_id"],
                        "domain_id": row["domain_id"],
                        "score": contract["scoring"]["exact_canonical_question_score"],
                        "matched_phrases": ["EXACT_CANONICAL_TEXT"],
                        "matched_terms": [],
                        "matched_negative_terms": [],
                    }
                ],
                "text_is_truth_source": False,
                "llm_used": False,
                "numeric_truth_created": False,
                "route_result_sha256": _sha(material),
                "remote_effects": deepcopy(contract["remote_effects"]),
            }

    candidates = [
        _score_question(
            normalized,
            qid,
            spec,
            contract=contract,
        )
        for qid, spec in contract["question_routes"].items()
    ]
    candidates.sort(key=lambda x: (-x["score"], x["question_id"]))
    top = candidates[0]
    second = candidates[1]
    top_score = int(top["score"])
    second_score = int(second["score"])
    margin = top_score - second_score
    scoring = contract["scoring"]

    normalized_padded = f" {normalized} "
    compound_marker_present = any(
        marker in normalized_padded
        for marker in contract["compound_markers"]
    )
    compound_clear = (
        compound_marker_present
        and top_score >= int(scoring["compound_route_min_score_each"])
        and second_score >= int(scoring["compound_route_min_score_each"])
        and (
            not scoring["compound_requires_phrase_match_each"]
            or (bool(top["matched_phrases"]) and bool(second["matched_phrases"]))
        )
    )

    if compound_clear:
        selected = [top["question_id"], second["question_id"]][: int(scoring["max_compound_routes"])]
        state = "ROUTED"
        route_mode = "COMPOUND"
    elif (
        top_score >= int(scoring["single_route_min_score"])
        and margin >= int(scoring["single_route_min_margin"])
    ):
        selected = [top["question_id"]]
        state = "ROUTED"
        route_mode = "SINGLE"
    elif (
        top_score >= int(scoring["ambiguity_candidate_min_score"])
        and second_score >= int(scoring["ambiguity_candidate_min_score"])
        and margin < int(scoring["ambiguity_margin_lt"])
    ):
        selected = []
        state = "AMBIGUOUS"
        route_mode = "NO_SELECTION"
    else:
        selected = []
        state = "LOW_CONFIDENCE_STOP"
        route_mode = "NO_SELECTION"

    conf = _confidence(top_score, margin, contract) if state == "ROUTED" else 0.0
    material = {
        "normalized_text": normalized,
        "state": state,
        "route_mode": route_mode,
        "selected_question_ids": selected,
        "top_score": top_score,
        "second_score": second_score,
        "margin": margin,
        "confidence": conf,
    }
    return {
        "schema": "TASK207_NATURAL_LANGUAGE_ROUTE_RESULT_V1",
        **material,
        "input_text": text,
        "selected_questions": [current_by_id[qid] for qid in selected],
        "candidates": candidates[:5],
        "text_is_truth_source": False,
        "llm_used": False,
        "numeric_truth_created": False,
        "route_result_sha256": _sha(material),
        "remote_effects": deepcopy(contract["remote_effects"]),
    }


def _task206_runtime() -> tuple[str, str]:
    obj = json.loads(TASK206_CONTRACT.read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK206_OFFLINE_ANSWER_CLI_QA_V1", "TASK207_TASK206_SCHEMA")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK207_TASK206_REMOTE")
    return str(obj["default_generated_at"]), str(obj["default_software_version"])


def route_and_render(
    text: str,
    *,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    route = route_natural_language(text, contract_path=contract_path)
    _stop(route["state"] == "ROUTED", f"TASK207_ROUTE_NOT_RENDERABLE:{route['state']}")
    generated_at, software_version = _task206_runtime()
    products = build_current_products(
        generated_at=generated_at,
        software_version=software_version,
    )
    answers = []
    for qid in route["selected_question_ids"]:
        card = build_answer_card(qid, products)
        rendered = render_answer_card_markdown(card)
        answers.append(
            {
                "question_id": qid,
                "answer_card_sha256": card["answer_card_sha256"],
                "markdown_sha256": rendered["markdown_sha256"],
                "markdown": rendered["markdown"],
            }
        )
    _stop(1 <= len(answers) <= 2, "TASK207_RENDER_COUNT")
    material = {
        "route_result_sha256": route["route_result_sha256"],
        "answers": [
            {
                "question_id": x["question_id"],
                "answer_card_sha256": x["answer_card_sha256"],
                "markdown_sha256": x["markdown_sha256"],
            }
            for x in answers
        ],
    }
    return {
        "schema": "TASK207_NATURAL_LANGUAGE_ROUTED_ANSWER_V1",
        "route": route,
        "answer_count": len(answers),
        "answers": answers,
        "result_sha256": _sha(material),
        "text_is_truth_source": False,
        "llm_used": False,
        "numeric_truth_created_by_router": False,
        "remote_effects": deepcopy(contract["remote_effects"]),
    }

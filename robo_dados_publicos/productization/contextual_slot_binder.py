from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any, Mapping

from robo_dados_publicos.analytics.school_indicator_library_seed import (
    read_wide_fixture,
)
from robo_dados_publicos.productization.natural_language_router import (
    route_and_render,
    route_natural_language,
    normalize_text,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task208_contextual_slot_binder.v1.json"


class Task208ContextStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task208ContextStop(code)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _contains(normalized_text: str, phrase: str) -> bool:
    needle = normalize_text(phrase)
    return f" {needle} " in f" {normalized_text} "


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(
        obj.get("schema") == "TASK208_CONTEXTUAL_SLOT_BINDER_V1",
        "TASK208_CONTRACT_SCHEMA",
    )
    _stop(
        obj.get("mode") == "T0_OFFLINE_DETERMINISTIC_CONTEXT_BINDING",
        "TASK208_CONTRACT_MODE",
    )
    _stop(
        obj["school_identity"]["expected_school_count"] == 40,
        "TASK208_SCHOOL_COUNT_CONTRACT",
    )
    _stop(
        obj["school_identity"]["fuzzy_matching_creates_identity"] is False,
        "TASK208_FUZZY_IDENTITY_GUARD",
    )
    _stop(
        obj["relative_time"]["implicit_clock_allowed"] is False,
        "TASK208_CLOCK_GUARD",
    )
    _stop(
        obj["render_guard"]["never_silently_drop_context"] is True,
        "TASK208_RENDER_DROP_GUARD",
    )
    _stop(
        all(v is False for v in obj["remote_effects"].values()),
        "TASK208_REMOTE_EFFECT",
    )
    return obj


def _school_rows() -> list[dict[str, str]]:
    rows = read_wide_fixture()
    result = []
    for row in rows:
        code = str(row["codigo_inep"]).strip()
        name = " ".join(str(row["unidade"]).split())
        result.append({"school_code": code, "school_name": name})
    result.sort(key=lambda x: x["school_code"])
    _stop(len(result) == 40, "TASK208_SCHOOL_COUNT_RUNTIME")
    _stop(len({x["school_code"] for x in result}) == 40, "TASK208_SCHOOL_CODE_UNIQUE")
    return result


def _strip_school_prefix(normalized_name: str) -> str:
    prefixes = (
        "ceief ",
        "emeief ",
        "emei ",
        "emef ",
        "escola municipal ",
    )
    for prefix in prefixes:
        if normalized_name.startswith(prefix):
            return normalized_name[len(prefix) :].strip()
    return normalized_name


def _school_aliases(raw_name: str) -> list[str]:
    variants = {normalize_text(raw_name)}
    head = raw_name.split(",", 1)[0].split("(", 1)[0].strip()
    if head:
        variants.add(normalize_text(head))
    expanded = set(variants)
    for variant in list(variants):
        stripped = _strip_school_prefix(variant)
        if stripped:
            expanded.add(stripped)
    aliases = sorted(
        x
        for x in expanded
        if len(x) >= 5 and len(x.split()) >= 2
    )
    return aliases


def school_roster() -> list[dict[str, Any]]:
    return [
        {
            **row,
            "aliases": _school_aliases(row["school_name"]),
        }
        for row in _school_rows()
    ]


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    contract = load_contract(path)
    roster = school_roster()
    _stop(
        len(roster) == contract["school_identity"]["expected_school_count"],
        "TASK208_SCHOOL_COUNT_VALIDATION",
    )
    _stop(
        all(len(x["school_code"]) == 8 and x["school_code"].isdigit() for x in roster),
        "TASK208_INEP_CODE_VALIDATION",
    )
    _stop(
        all(x["aliases"] for x in roster),
        "TASK208_ALIAS_VALIDATION",
    )
    return {
        "schema": "TASK208_CONTEXTUAL_SLOT_BINDER_VALIDATION_V1",
        "status": "PASS",
        "school_count": len(roster),
        "network": False,
        "drive_read": False,
        "drive_write": False,
        "serving": False,
        "publication": False,
        "llm": False,
    }


def _resolve_context_school(
    context_school_code: str | None,
    roster_by_code: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any] | None:
    if context_school_code is None:
        return None
    code = str(context_school_code).strip()
    row = roster_by_code.get(code)
    if row is None:
        return {
            "status": "UNRESOLVED",
            "origin": "CALLER_CONTEXT",
            "requested_code": code,
        }
    return {
        "status": "RESOLVED",
        "origin": "CALLER_CONTEXT",
        "school_code": row["school_code"],
        "school_name": row["school_name"],
        "matched_alias": None,
    }


def resolve_school(
    text: str,
    *,
    context_school_code: str | None = None,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    normalized = normalize_text(text)
    roster = school_roster()
    by_code = {x["school_code"]: x for x in roster}

    personal_reference = any(
        _contains(normalized, marker)
        for marker in contract["personal_school_markers"]
    )
    context_resolution = _resolve_context_school(context_school_code, by_code)
    if personal_reference:
        if context_resolution is None:
            return {
                "status": "NEEDS_CONTEXT",
                "origin": "PERSONAL_REFERENCE",
                "personal_reference": True,
                "candidates": [],
            }
        return {
            **context_resolution,
            "personal_reference": True,
            "candidates": (
                [context_resolution["school_code"]]
                if context_resolution["status"] == "RESOLVED"
                else []
            ),
        }

    code_tokens = sorted(set(re.findall(r"\b\d{8}\b", normalized)))
    if len(code_tokens) > 1:
        return {
            "status": "AMBIGUOUS",
            "origin": "INEP_CODE",
            "personal_reference": False,
            "candidates": code_tokens,
        }
    if len(code_tokens) == 1:
        code = code_tokens[0]
        row = by_code.get(code)
        if row is None:
            return {
                "status": "UNRESOLVED",
                "origin": "INEP_CODE",
                "personal_reference": False,
                "requested_code": code,
                "candidates": [],
            }
        return {
            "status": "RESOLVED",
            "origin": "INEP_CODE",
            "personal_reference": False,
            "school_code": row["school_code"],
            "school_name": row["school_name"],
            "matched_alias": code,
            "candidates": [code],
        }

    matched: list[tuple[str, str, str]] = []
    for row in roster:
        for alias in row["aliases"]:
            if _contains(normalized, alias):
                matched.append((row["school_code"], row["school_name"], alias))
                break

    unique_codes = sorted({x[0] for x in matched})
    if len(unique_codes) > 1:
        return {
            "status": "AMBIGUOUS",
            "origin": "CANONICAL_ALIAS",
            "personal_reference": False,
            "candidates": unique_codes,
        }
    if len(unique_codes) == 1:
        code = unique_codes[0]
        code_matches = [x for x in matched if x[0] == code]
        best = sorted(code_matches, key=lambda x: (-len(x[2]), x[2]))[0]
        return {
            "status": "RESOLVED",
            "origin": "CANONICAL_ALIAS",
            "personal_reference": False,
            "school_code": best[0],
            "school_name": best[1],
            "matched_alias": best[2],
            "candidates": [best[0]],
        }

    likely_school_reference = any(
        _contains(normalized, marker)
        for marker in contract["school_type_markers"]
    )
    if likely_school_reference:
        return {
            "status": "UNRESOLVED",
            "origin": "SCHOOL_TEXT",
            "personal_reference": False,
            "candidates": [],
        }

    return {
        "status": "NOT_REQUESTED",
        "origin": None,
        "personal_reference": False,
        "candidates": [],
    }


def _parse_reference_date(value: str | None) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise Task208ContextStop("TASK208_REFERENCE_DATE_INVALID") from exc


def extract_period(
    text: str,
    *,
    reference_date: str | None = None,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    normalized = normalize_text(text)
    reference = _parse_reference_date(reference_date)
    years = sorted({int(x) for x in re.findall(r"\b20\d{2}\b", normalized)})

    relative_year = any(
        _contains(normalized, marker)
        for marker in contract["relative_time"]["relative_year_markers"]
    )
    if len(years) > 1:
        return {
            "status": "AMBIGUOUS",
            "mode": None,
            "years": years,
        }

    resolved_year: int | None = years[0] if years else None
    if relative_year:
        if reference is None:
            return {
                "status": "REFERENCE_REQUIRED",
                "mode": None,
                "years": years,
            }
        if resolved_year is not None and resolved_year != reference.year:
            return {
                "status": "AMBIGUOUS",
                "mode": None,
                "years": sorted({resolved_year, reference.year}),
            }
        resolved_year = reference.year

    months = sorted(
        {
            int(month_number)
            for month_name, month_number in contract["months"].items()
            if _contains(normalized, month_name)
        }
    )
    if len(months) > 1:
        return {
            "status": "AMBIGUOUS",
            "mode": None,
            "year": resolved_year,
            "months": months,
        }

    month = months[0] if months else None
    if month is not None and resolved_year is None:
        if reference is None:
            return {
                "status": "REFERENCE_REQUIRED",
                "mode": None,
                "month": month,
            }
        resolved_year = reference.year

    if resolved_year is None and month is None:
        return {
            "status": "NOT_REQUESTED",
            "mode": None,
        }

    through_marker = any(
        _contains(normalized, marker)
        for marker in ("ate", "até")
    )
    if month is not None and through_marker:
        return {
            "status": "RESOLVED",
            "mode": "YEAR_TO_MONTH",
            "year": resolved_year,
            "start_month": 1,
            "end_month": month,
            "reference_date": reference.isoformat() if reference else None,
        }
    if month is not None:
        return {
            "status": "RESOLVED",
            "mode": "MONTH",
            "year": resolved_year,
            "month": month,
            "reference_date": reference.isoformat() if reference else None,
        }
    return {
        "status": "RESOLVED",
        "mode": "YEAR",
        "year": resolved_year,
        "reference_date": reference.isoformat() if reference else None,
    }


def extract_policy_service_facets(
    text: str,
    *,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> list[str]:
    contract = load_contract(contract_path)
    normalized = normalize_text(text)
    facets = []
    for facet, phrases in contract["policy_service_facets"].items():
        if any(_contains(normalized, phrase) for phrase in phrases):
            facets.append(facet)
    return sorted(facets)


def _task207_route_with_school_bridge(
    text: str,
    school: Mapping[str, Any],
    *,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    route = route_natural_language(text)
    if route["state"] == "ROUTED":
        return {
            "origin": "TASK207",
            "state": "ROUTED",
            "selected_question_ids": list(route["selected_question_ids"]),
            "task207": route,
        }

    broad_profile = (
        school.get("status") == "RESOLVED"
        and any(
            _contains(normalize_text(text), phrase)
            for phrase in contract["broad_school_profile"]["phrases"]
        )
    )
    if broad_profile:
        return {
            "origin": "TASK208_SCHOOL_PROFILE_BRIDGE",
            "state": "ROUTED",
            "selected_question_ids": [
                contract["broad_school_profile"]["default_question_id"]
            ],
            "task207": route,
        }

    return {
        "origin": "TASK207",
        "state": route["state"],
        "selected_question_ids": [],
        "task207": route,
    }


def _granularity(
    text: str,
    school: Mapping[str, Any],
    route: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    normalized = normalize_text(text)
    has_comparison = any(
        _contains(normalized, marker)
        for marker in contract["comparison_markers"]
    )
    has_network = any(
        _contains(normalized, marker)
        for marker in contract["network_markers"]
    )
    if route["origin"] == "TASK208_SCHOOL_PROFILE_BRIDGE":
        return {
            "value": contract["broad_school_profile"]["default_granularity"],
            "explicit": False,
        }
    if school.get("status") == "RESOLVED" and (has_comparison or has_network):
        return {"value": "SCHOOL_VS_NETWORK", "explicit": True}
    if school.get("status") == "RESOLVED":
        return {"value": "SCHOOL", "explicit": True}
    if has_network:
        return {"value": "NETWORK", "explicit": True}

    qids = set(route.get("selected_question_ids") or [])
    document_prefixes = ("NORMS_", "POLICY_", "JOM_", "PROC_", "PERS_")
    if any(qid.startswith(document_prefixes) for qid in qids):
        return {"value": "DOCUMENT_EVENT", "explicit": False}
    return {"value": "MUNICIPALITY", "explicit": False}


def bind_context(
    text: str,
    *,
    reference_date: str | None = None,
    context_school_code: str | None = None,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    validate_contract(contract_path)
    normalized = normalize_text(text)
    _stop(bool(normalized), "TASK208_EMPTY_TEXT")

    school = resolve_school(
        text,
        context_school_code=context_school_code,
        contract_path=contract_path,
    )
    period = extract_period(
        text,
        reference_date=reference_date,
        contract_path=contract_path,
    )
    facets = extract_policy_service_facets(text, contract_path=contract_path)

    if school["status"] == "NEEDS_CONTEXT":
        state = "NEEDS_SCHOOL_CONTEXT"
        route = {
            "origin": "NOT_EVALUATED",
            "state": "NO_SELECTION",
            "selected_question_ids": [],
            "task207": None,
        }
    elif school["status"] == "UNRESOLVED":
        state = "SCHOOL_UNRESOLVED"
        route = {
            "origin": "NOT_EVALUATED",
            "state": "NO_SELECTION",
            "selected_question_ids": [],
            "task207": None,
        }
    elif school["status"] == "AMBIGUOUS":
        state = "SCHOOL_AMBIGUOUS"
        route = {
            "origin": "NOT_EVALUATED",
            "state": "NO_SELECTION",
            "selected_question_ids": [],
            "task207": None,
        }
    elif period["status"] == "AMBIGUOUS":
        state = "PERIOD_AMBIGUOUS"
        route = {
            "origin": "NOT_EVALUATED",
            "state": "NO_SELECTION",
            "selected_question_ids": [],
            "task207": None,
        }
    elif period["status"] == "REFERENCE_REQUIRED":
        state = "PERIOD_REFERENCE_REQUIRED"
        route = {
            "origin": "NOT_EVALUATED",
            "state": "NO_SELECTION",
            "selected_question_ids": [],
            "task207": None,
        }
    else:
        route = _task207_route_with_school_bridge(
            text,
            school,
            contract=contract,
        )
        state = (
            "CONTEXT_BOUND"
            if route["state"] == "ROUTED"
            else "ROUTE_STOP_PROPAGATED"
        )

    granularity = _granularity(text, school, route, contract)

    has_school_filter = school.get("status") == "RESOLVED"
    has_period_filter = period.get("status") == "RESOLVED"
    render_safe = (
        state == "CONTEXT_BOUND"
        and not has_school_filter
        and not has_period_filter
    )
    render_state = (
        "TASK207_RENDER_SAFE"
        if render_safe
        else (
            "CONTEXT_UNSUPPORTED_FOR_RENDER"
            if state == "CONTEXT_BOUND"
            else "NOT_RENDERABLE"
        )
    )

    material = {
        "normalized_text": normalized,
        "state": state,
        "selected_question_ids": list(route.get("selected_question_ids") or []),
        "school": school,
        "period": period,
        "policy_service_facets": facets,
        "granularity": granularity,
        "render_state": render_state,
    }
    return {
        "schema": "TASK208_CONTEXT_BIND_RESULT_V1",
        **material,
        "input_text": text,
        "route": route,
        "text_is_truth_source": False,
        "school_text_creates_identity": False,
        "relative_time_uses_implicit_clock": False,
        "numeric_truth_created": False,
        "llm_used": False,
        "context_result_sha256": _sha(material),
        "remote_effects": deepcopy(contract["remote_effects"]),
    }


def bind_and_render(
    text: str,
    *,
    reference_date: str | None = None,
    context_school_code: str | None = None,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    result = bind_context(
        text,
        reference_date=reference_date,
        context_school_code=context_school_code,
        contract_path=contract_path,
    )
    _stop(
        result["state"] == "CONTEXT_BOUND",
        f"TASK208_CONTEXT_NOT_BOUND:{result['state']}",
    )
    _stop(
        result["render_state"] == "TASK207_RENDER_SAFE",
        "TASK208_CONTEXT_UNSUPPORTED_FOR_RENDER",
    )
    rendered = route_and_render(text)
    return {
        "schema": "TASK208_CONTEXT_BOUND_RENDER_V1",
        "context": result,
        "task207_render": rendered,
        "context_dropped": False,
        "remote_effects": deepcopy(result["remote_effects"]),
    }

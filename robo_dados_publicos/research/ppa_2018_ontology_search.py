from __future__ import annotations

import json
from pathlib import Path
from typing import Any

class Task113Stop(RuntimeError):
    pass

def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task113Stop(code)

def validate_task113_contract(data: dict[str, Any]) -> dict[str, Any]:
    _require(data.get("schema") == "TASK113_PPA2018_ONTOLOGY_LEXICAL_CONTRACT_V1", "TASK113_SCHEMA")
    _require(data.get("mode") == "T0_OFFLINE_ONTOLOGY_A_B_C_ONLY", "TASK113_MODE")
    source = data.get("source_identity") or {}
    _require(source.get("sha256") == "685a621a2f5fa8859e4b7f8518627c1523a2fbc5f3402ff48d4aa7573300113d", "TASK113_SOURCE_SHA")
    _require(source.get("page_count") == 80, "TASK113_PAGE_COUNT")
    families = data.get("families") or {}
    expected = {
        "A_CANONICAL_POLICY_IDENTIFIERS",
        "B_LOCAL_PLANNING_AND_NORMATIVE_ALIASES",
        "C_OPERATIONAL_OFFER_AND_JOURNEY_SIGNALS",
    }
    _require(set(families) == expected, "TASK113_FAMILY_SET")
    for family, entries in families.items():
        _require(isinstance(entries, list) and entries, f"TASK113_{family}_ENTRIES")
        for entry in entries:
            _require(bool(str(entry.get("term") or "").strip()), "TASK113_TERM")
            _require(entry.get("strength") in {
                "STRONG","CONTEXTUAL","WEAK","WEAK_SHORT_FORM",
                "STRONG_OPERATIONAL","WEAK_NUMERIC"
            }, "TASK113_STRENGTH")
            _require(isinstance(entry.get("requires_companion"), bool), "TASK113_COMPANION_FLAG")
    _require(set(data.get("forbidden_families") or []) == {
        "D_FINANCING_AND_INDUCTION_SIGNALS",
        "E_ACCOUNTING_AND_PLANNING_LINKAGE_KEYS",
    }, "TASK113_FORBIDDEN_FAMILIES")
    _require(data.get("exact_normalized_match_only") is True, "TASK113_EXACT_MATCH")
    _require(data.get("fuzzy_edit_distance") is False, "TASK113_NO_FUZZY")
    promotion = data.get("promotion") or {}
    _require(promotion and all(value is False for value in promotion.values()), "TASK113_PROMOTION")
    live = data.get("future_live_gate") or {}
    _require(live.get("authorized_now") is False, "TASK113_LIVE_NOT_AUTHORIZED")
    _require(live.get("max_http_requests_total") == 1, "TASK113_LIVE_REQUEST_MAX")
    _require(live.get("pages_to_ocr") == 80, "TASK113_LIVE_PAGE_COUNT")
    remote = data.get("remote_effects") or {}
    _require(remote and all(value is False for value in remote.values()), "TASK113_REMOTE_EFFECT")
    return {
        "status":"PASS_TASK113_ONTOLOGY_LEXICAL_CONTRACT",
        "family_count":3,
        "term_count":sum(len(v) for v in families.values()),
        "source_sha_pinned":True,
        "live_authorized":False,
        "remote_effects":0,
    }

def load_and_validate_task113_contract(path: str | Path) -> dict[str, Any]:
    try:
        data=json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise Task113Stop("TASK113_INPUT_MISSING") from exc
    except json.JSONDecodeError as exc:
        raise Task113Stop("TASK113_INPUT_JSON") from exc
    return validate_task113_contract(data)

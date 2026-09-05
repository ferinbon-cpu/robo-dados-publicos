from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "config/direct_json_first_source_discovery_policy.v1.json"
EVIDENCE = ROOT / "docs/evidence/TASK_165_DIRECT_JSON_FIRST_SOURCE_DISCOVERY_0.8.0.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise AssertionError(code)


def validate() -> dict:
    p = _load(POLICY)
    e = _load(EVIDENCE)

    _require(p["schema"] == "DIRECT_JSON_FIRST_SOURCE_DISCOVERY_POLICY_V1", "TASK165_SCHEMA")
    _require(p["issue"] == 542 and e["issue"] == 542, "TASK165_ISSUE")
    _require(p["base_sha"] == e["base_sha"], "TASK165_BASE")

    order = [x["strategy"] for x in sorted(p["strategy_order"], key=lambda x: x["rank"])]
    _require(order[0] == "DIRECT_OFFICIAL_JSON_OR_API_GET", "TASK165_JSON_FIRST")
    _require(order[-1] == "HTML_DOM_JS_PATH_REVERSE_ENGINEERING_FALLBACK", "TASK165_REVERSE_LAST")

    pref = p["direct_json_preference"]
    _require("html_scraping" in pref["prefer_over"], "TASK165_HTML")
    _require("javascript_asset_inspection" in pref["prefer_over"], "TASK165_JS")
    _require("owner_authorization_scope" in pref["does_not_override"], "TASK165_AUTH_BOUNDARY")
    _require("access_control" in pref["does_not_override"], "TASK165_ACCESS_BOUNDARY")

    a = p["authorization_reuse"]
    _require("page_number" in a["typical_reusable_variations"], "TASK165_PAGE_REUSE")
    _require("method_changes_to_write_or_mutation" in a["new_authorization_required_when_any"], "TASK165_MUTATION_AUTH")
    _require("new_host_outside_scope" in a["new_authorization_required_when_any"], "TASK165_HOST_AUTH")
    _require(a["preferred_authorization_shape_for_future_sources"].startswith("SOURCE_SCOPE_READ_ONLY"), "TASK165_AUTH_SHAPE")

    rv = p["response_validation"]
    _require(rv["transport_failure_action"] == "SOURCE_TRANSPORT_UNAVAILABLE", "TASK165_TRANSPORT")
    _require(rv["transport_failure_is_no_match"] is False, "TASK165_NO_MATCH")

    pag = p["pagination"]
    _require(pag["direct_json_pagination_preferred"] is True, "TASK165_PAGINATION")
    _require(pag["exhaustive_negative_requires_complete_pagination"] is True, "TASK165_EXHAUSTIVE")
    _require(pag["partial_result_can_create_exhaustive_no_match"] is False, "TASK165_PARTIAL")

    ref = p["reference_example"]
    _require(ref["source"] == "PNCP", "TASK165_REFERENCE")
    _require(ref["authorization_metering"] == "UNMETERED_WITHIN_PNCP_SCOPE_UNTIL_REVOKED_OR_SUPERSEDED", "TASK165_PNCP_REUSE")

    result = e["policy_result"]
    _require(result["direct_json_first"] is True, "TASK165_RESULT_JSON")
    _require(result["reverse_engineering_is_fallback"] is True, "TASK165_RESULT_FALLBACK")
    _require(result["per_page_authorization_required_inside_reusable_scope"] is False, "TASK165_RESULT_AUTH")

    hard = e["hard_boundaries"]
    _require(all(v is False for v in hard.values()), "TASK165_HARD_BOUNDARIES")

    return {
        "task": p["task"],
        "schema": p["schema"],
        "first_strategy": order[0],
        "fallback_strategy": order[-1],
        "pncp_reference": ref["source"],
        "status": "VALID"
    }


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, sort_keys=True))

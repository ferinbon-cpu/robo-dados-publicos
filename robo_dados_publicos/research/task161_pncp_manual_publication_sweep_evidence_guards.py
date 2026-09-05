from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config/task161_pncp_manual_publication_sweep_evidence_guards.v1.json"
EVIDENCE = ROOT / "docs/evidence/TASK_161_PNCP_MANUAL_PUBLICATION_SWEEP_EVIDENCE_GUARDS_0.8.0.json"


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise AssertionError(code)


def validate() -> dict:
    c = json.loads(CONFIG.read_text(encoding="utf-8"))
    e = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    _require(c["issue"] == 534 and e["issue"] == 534, "TASK161_ISSUE")
    _require(c["base_sha"] == e["base_sha"], "TASK161_BASE_SHA")

    a = c["authorization"]
    _require(a["owner_instruction_exact"] == "Autorizado pn p irrestrito", "TASK161_AUTH_TEXT")
    _require(a["issued_after_task_160_closure"] is True, "TASK161_AUTH_FRESH")
    _require(a["scope"] == "PNCP_LIVE_READ_DISCOVERY_ONLY", "TASK161_AUTH_SCOPE")
    _require(a["mutations_allowed"] is False, "TASK161_NO_MUTATIONS")
    _require(a["drive_writes_allowed"] is False, "TASK161_NO_DRIVE")
    _require(a["non_pncp_live_sources_allowed"] is False, "TASK161_NO_OTHER_LIVE")

    s = c["source_scope"]
    _require(s["expected_cnpj"] == "45132495000140", "TASK161_CNPJ")
    _require(s["expected_municipio"] == "Limeira", "TASK161_MUNICIPIO")
    _require(s["expected_uf"] == "SP", "TASK161_UF")
    _require(s["page_size"] == 50, "TASK161_PAGE_SIZE")
    _require(s["date_axis"] == "dataPublicacaoPncp", "TASK161_DATE_AXIS")

    relay = c["manual_owner_relay"]
    _require(relay["raw_json_git"] is False, "TASK161_RAW_GIT")
    _require(relay["raw_json_drive"] is False, "TASK161_RAW_DRIVE")
    _require(relay["sanitized_summary_git"] is True, "TASK161_SANITIZED_ONLY")

    complete = {x["modality_id"]: x for x in c["complete_scopes"]}
    _require(set(complete) == {6, 8, 12}, "TASK161_COMPLETE_MODALITIES")
    _require((complete[6]["total_records"], complete[6]["total_pages"]) == (181, 4), "TASK161_M6")
    _require((complete[8]["total_records"], complete[8]["total_pages"]) == (434, 9), "TASK161_M8")
    _require((complete[12]["total_records"], complete[12]["total_pages"]) == (5, 1), "TASK161_M12")
    for item in complete.values():
        _require(item["pages_observed"] == item["total_pages"], "TASK161_ALL_PAGES")
        _require(item["exhaustive_within_exact_scope"] is True, "TASK161_EXHAUSTIVE_SCOPE")
        _require(item["explicit_eiti_match_count"] == 0, "TASK161_EXPLICIT_EITI")

    incomplete = {x["modality_id"]: x for x in c["incomplete_scopes"]}
    _require(incomplete[9]["exhaustive_within_exact_scope"] is False, "TASK161_M9_NOT_EXHAUSTIVE")
    _require(incomplete[9]["pncp_no_match_allowed"] is False, "TASK161_M9_NO_NO_MATCH")
    _require(incomplete[9]["stable_pncp_id_status"] == "NOT_YET_RECOVERED", "TASK161_M9_ID")

    tiers = c["evidence_ladder"]
    _require(tiers == ["GENERAL", "EDUCATION_RELEVANT", "EITI_CANDIDATE", "EITI_CORROBORATED", "EITI_PROVEN"], "TASK161_LADDER")
    p = c["promotion_rules"]
    _require(p["education_relevant_is_not_eiti_proven"] is True, "TASK161_EDU_NE_EITI")
    _require(p["stable_administrative_id_required_before_correlated_promotion"] is True, "TASK161_STABLE_ID")

    i = c["identity_guard"]
    _require(i["platform_or_domain_match_is_insufficient"] is True, "TASK161_DOMAIN_INSUFFICIENT")
    _require(i["wrong_municipality_action"] == "REJECT_SOURCE_WITH_ENTITY_IDENTITY_MISMATCH", "TASK161_IDENTITY_REJECT")
    _require(i["known_rejected_example"]["actual_municipality"] == "Itupeva", "TASK161_ITUP_EVIDENCE")
    _require(i["known_rejected_example"]["must_not_enter_limeira_evidence_graph"] is True, "TASK161_ITUP_REJECT")

    pg = c["pagination_guard"]
    _require(pg["exhaustive_requires_all_pages_observed"] is True, "TASK161_PAGINATION")
    _require(pg["indexed_search_cannot_create_exhaustive_no_match"] is True, "TASK161_INDEX_NOT_EXHAUSTIVE")

    t = c["transport_guard"]
    _require(t["tool_layer_failure_is_not_source_no_match"] is True, "TASK161_TOOL_FAILURE")
    _require(t["dns_failure_is_not_source_no_match"] is True, "TASK161_DNS_FAILURE")
    _require(t["required_failure_semantics"] == "SOURCE_TRANSPORT_UNAVAILABLE", "TASK161_TRANSPORT_SEM")

    anomaly = c["anomaly_policy"]
    _require(anomaly["preserve_raw_source_values"] is True, "TASK161_RAW_PRESERVE")
    _require(anomaly["silent_repair_forbidden"] is True, "TASK161_NO_SILENT_REPAIR")

    g = c["global_epistemic_state"]
    _require(g["explicit_eiti_match_in_complete_modalities_6_8_12"] is False, "TASK161_NO_EXPLICIT_EITI")
    _require(g["global_pncp_no_match_created"] is False, "TASK161_NO_GLOBAL_NEGATIVE")
    _require(g["eiti_financial_identity_proven"] is False, "TASK161_NO_FIN_ID")

    ee = e["epistemic_closure"]
    _require(ee["education_relevant_equals_eiti_proven"] is False, "TASK161_EVIDENCE_EDU_NE_EITI")
    _require(ee["complete_scope_negative_is_global_negative"] is False, "TASK161_SCOPE_NEGATIVE")
    _require(ee["indexed_discovery_is_exhaustive"] is False, "TASK161_INDEXED")
    _require(ee["transport_failure_is_no_match"] is False, "TASK161_TRANSPORT")
    _require(ee["global_pncp_no_match_created"] is False, "TASK161_EVIDENCE_NO_GLOBAL_NEGATIVE")

    return {
        "task": c["task"],
        "complete_modalities": sorted(complete),
        "explicit_eiti_match": False,
        "modality_9_exhaustive": False,
        "identity_guard": "FAIL_CLOSED",
        "transport_guard": "FAIL_CLOSED",
    }


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, sort_keys=True))

#!/usr/bin/env python3
"""TASK 009E T0 gate for bounded official documentary discovery design."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "config" / "siope_2025_official_alias_documentary_discovery_design.v1.json"
TASK007 = ROOT / "config" / "siope_2025_official_documentary_proof.v1.json"
TASK008 = ROOT / "config" / "siope_2025_alias_finality_audit.v1.json"
TASK009D = ROOT / "config" / "siope_2025_route_dead_end_consolidation.v1.json"
SIOPE_CLIENT = ROOT / "robo_dados_publicos" / "sources" / "siope_client.py"


class DocumentaryDiscoveryDesignError(ValueError):
    pass


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise DocumentaryDiscoveryDesignError(reason)


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"OBJECT_REQUIRED:{path.name}")
    return value


def validate_design(design: dict, task007: dict, task008: dict, task009d: dict, siope_client_text: str) -> None:
    _require(design.get("schema") == "SIOPE_2025_OFFICIAL_ALIAS_DOCUMENTARY_DISCOVERY_DESIGN_V1", "DESIGN_SCHEMA")
    _require(design.get("task") == "TASK_009E", "TASK_ID")
    _require(design.get("issue") == 221, "ISSUE_ID")
    _require(design.get("tier") == "T0_OFFLINE", "T0_OFFLINE_REQUIRED")
    _require(design.get("starting_main_sha") == "9c20f078b68891334aac7abe8b3074c54a374149", "STARTING_MAIN_SHA")

    effects = design.get("current_effects", {})
    _require(effects == {
        "source_get_count": 0,
        "drive_read_count": 0,
        "drive_write_count": 0,
        "persistence": False,
        "publication": False,
        "remote_execution_authorized": False,
        "live_workflow_added": False,
    }, "CURRENT_EFFECTS_MUST_BE_ZERO_OFFLINE")

    gate_b = task007.get("gate_b_field_semantics", {})
    _require(gate_b.get("historical_primary_definition_coverage") == "10_OF_11_FINANCIAL_INPUT_CONCEPTS_HAVE_OFFICIAL_DICTIONARY_COUNTERPARTS", "TASK007_10_OF_11_REQUIRED")
    _require(gate_b.get("current_2025_alias_bridge_status") == "NOT_PROVEN", "TASK007_ALIAS_BRIDGE_UNPROVEN")
    _require(gate_b.get("population_denominator_status") == "NOT_PROVEN_OFFICIAL_PRIMARY_DEFINITION", "TASK007_NUM_POPU_UNPROVEN")
    field_assessment = gate_b.get("field_assessment")
    _require(isinstance(field_assessment, list) and len(field_assessment) == 11, "TASK007_11_FIELDS_REQUIRED")
    _require(sum(1 for row in field_assessment if row.get("historical_definition_found") is True) == 10, "TASK007_EXACTLY_10_HISTORICAL_DEFINITIONS")
    _require(sum(1 for row in field_assessment if row.get("2025_alias_identity_proven") is True) == 0, "TASK007_ZERO_2025_ALIAS_IDENTITIES")
    pop = [row for row in field_assessment if row.get("odata_field") == "NUM_POPU"]
    _require(len(pop) == 1 and pop[0].get("historical_definition_found") is False, "TASK007_NUM_POPU_MISSING")

    alias_gate = task008.get("gate_a_alias_metadata", {})
    _require(alias_gate.get("official_2025_municipal_metadata_package_status") == "PROVEN_PUBLISHED_BY_FNDE", "TASK008_PACKAGE_PUBLISHED")
    _require(alias_gate.get("package_content_inspection_status") == "NOT_INSPECTED_CURRENT_CONNECTOR_BINARY_UNAVAILABLE", "TASK008_PACKAGE_NOT_INSPECTED")
    _require(alias_gate.get("current_2025_alias_bridge_status") == "NOT_PROVEN", "TASK008_ALIAS_BRIDGE_UNPROVEN")
    _require(alias_gate.get("population_denominator_status") == "NOT_PROVEN_OFFICIAL_PRIMARY_DEFINITION_AND_VINTAGE", "TASK008_NUM_POPU_VINTAGE_UNPROVEN")
    _require(alias_gate.get("field_level_identity_proven_count") == 0, "TASK008_ZERO_IDENTITIES")
    _require(alias_gate.get("field_level_identity_required_count") == 11, "TASK008_11_REQUIRED")

    _require(task009d.get("decision") == "KEEP_BLOCKED_UNTIL_NEW_OFFICIAL_EVIDENCE_CLASS_IS_PINNED", "TASK009D_KEEP_BLOCKED")
    dead_routes = task009d.get("route_inventory", [])
    _require(len(dead_routes) == 3, "TASK009D_ROUTE_INVENTORY")
    _require(all(item.get("repeat_probe_authorized") is False for item in dead_routes), "TASK009D_NO_REPEAT")
    _require(any(item.get("status") == "OBSERVED_HTTP_401_NOT_PUBLIC_ANONYMOUSLY_PROVEN" for item in dead_routes), "TASK009D_HTTP401_PIN")
    _require(any(item.get("status") == "PUBLIC_METADATA_VERIFIED_AUTH_BOUNDARY_BEFORE_ARTIFACT_ROUTE" for item in dead_routes), "TASK009D_AUTH_BOUNDARY_PIN")

    _require('"NUM_POPU"' in siope_client_text, "SIOPE_CLIENT_NUM_POPU_SCHEMA_REQUIRED")
    _require('PROVEN_DADOS_GERAIS_FIELDS' in siope_client_text, "SIOPE_CLIENT_SCHEMA_ALLOWLIST_REQUIRED")

    baseline = design.get("repo_resident_baseline", {})
    expected_baseline = {
        "historical_dictionary_definition_coverage": "10_OF_11_FINANCIAL_INPUT_CONCEPTS",
        "current_2025_alias_identity_proven_count": 0,
        "current_2025_alias_identity_required_count": 11,
        "num_popu_definition_status": "NOT_PROVEN_OFFICIAL_PRIMARY_DEFINITION_AND_VINTAGE",
        "official_2025_metadata_package_status": "PROVEN_PUBLISHED_BY_FNDE",
        "official_2025_metadata_package_content_status": "NOT_INSPECTED",
        "sharepoint_resolved_route_status": "OBSERVED_HTTP_401_NOT_PUBLIC_ANONYMOUSLY_PROVEN",
        "antonieta_artifact_route_status": "UNPROVEN_BEYOND_AUTHENTICATION_BOUNDARY",
    }
    _require(baseline == expected_baseline, "BASELINE_DRIFT")

    questions = design.get("discovery_questions")
    _require(isinstance(questions, list) and [q.get("id") for q in questions] == ["S1_NUM_POPU", "S2_FINANCIAL_ALIAS_BRIDGE"], "EXACT_DISCOVERY_QUESTIONS_REQUIRED")
    s2_aliases = questions[1].get("required_aliases")
    _require(s2_aliases == [
        "VAL_RECE_PREV_ATUA",
        "VAL_RECE_REAL",
        "VAL_DESP_DOTA_ATUA",
        "VAL_DESP_EMPE",
        "VAL_DESP_LIQU",
        "VAL_DESP_PAGA",
        "VL_DESP_DOTA_ATUA_EDU",
        "VL_DESP_EMPE_EDU",
        "VL_DESP_LIQU_EDU",
        "VL_DESP_PAGA_EDU",
    ], "FINANCIAL_ALIAS_SET_DRIFT")

    t1 = design.get("future_t1_template", {})
    _require(t1.get("authorized") is False, "FUTURE_T1_MUST_NOT_BE_AUTHORIZED")
    _require(t1.get("execution_model") == "HUMAN_OR_ASSISTANT_BOUNDED_DOCUMENTARY_DISCOVERY_ONLY_AFTER_EXPLICIT_OWNER_AUTHORIZATION", "EXECUTION_MODEL")
    _require(t1.get("allowed_authorities") == ["FNDE"], "FNDE_ONLY")
    _require(set(t1.get("allowed_hosts", [])) == {"www.gov.br", "gov.br", "www.fnde.gov.br", "fnde.gov.br"}, "OFFICIAL_HOST_ALLOWLIST")
    _require(t1.get("allowed_methods") == ["GET"], "GET_ONLY")
    _require(t1.get("maximum_official_document_opens") == 12, "DOCUMENT_OPEN_BUDGET")
    _require(t1.get("maximum_distinct_official_urls") == 12, "URL_BUDGET")
    _require(t1.get("maximum_attempts_per_url") == 1, "ONE_ATTEMPT_PER_URL")
    for key in (
        "retry_authorized",
        "authentication_authorized",
        "cookies_authorized",
        "oauth_authorized",
        "credential_use_authorized",
        "sharepoint_401_route_reuse_authorized",
        "antonieta_login_authorized",
        "limeira_financial_data_query_authorized",
        "municipality_parameter_authorized",
        "year_period_data_parameter_authorized",
        "binary_package_download_authorized",
        "source_data_collection_authorized",
        "gold_computation_authorized",
        "semantic_promotion_in_same_execution_authorized",
        "closure_promotion_in_same_execution_authorized",
        "publication_authorized",
        "drive_access_authorized",
    ):
        _require(t1.get(key) is False, f"T1_TEMPLATE_MUST_BE_FALSE:{key}")

    admissible = design.get("admissible_evidence", {})
    _require(admissible.get("authority_required") == "FNDE_OFFICIAL_PRIMARY", "OFFICIAL_PRIMARY_REQUIRED")
    _require("SEARCH_RESULT_SNIPPET_WITHOUT_OFFICIAL_SOURCE_OPEN" in admissible.get("not_sufficient_alone", []), "SEARCH_SNIPPET_NOT_SUFFICIENT")
    _require("HISTORICAL_2019_DEFINITION_WITHOUT_CURRENT_BRIDGE" in admissible.get("not_sufficient_alone", []), "2019_ALONE_NOT_SUFFICIENT")
    _require("CURRENT_52_FIELD_SCHEMA_PRESENCE_WITHOUT_DEFINITION" in admissible.get("not_sufficient_alone", []), "SCHEMA_ALONE_NOT_SUFFICIENT")

    blocked = set(design.get("blocked_targets_and_actions", []))
    required_blocked = {
        "https://fnde.sharepoint.com/sites/SIOPE/Documentos%20Compartilhados/Metadados_Mun_2025.zip",
        "AUTOMATE_GOV_BR_LOGIN",
        "USE_OR_CAPTURE_CREDENTIALS_COOKIES_OAUTH_SESSION",
        "SYNTHESIZE_DOWNLOAD_URL",
        "RETRY_ALREADY_NEGATIVE_SHAREPOINT_ROUTE",
        "QUERY_LIMEIRA_FINANCIAL_RECORDS",
        "PROMOTE_ALIAS_IDENTITY_FROM_NAME_SIMILARITY",
        "PROMOTE_NUM_POPU_WITHOUT_SOURCE_AND_VINTAGE",
        "PROMOTE_2025_SEMANTIC_COMPARABILITY",
        "PROMOTE_2025_ANNUAL_CLOSURE",
        "COMPUTE_OR_PERSIST_GOLD_2025",
        "EXPAND_CLOSED_ANNUAL_SERIES_TO_2025",
        "PROMOTE_2026",
    }
    _require(blocked == required_blocked, "BLOCKED_SET_DRIFT")

    semantics = design.get("semantic_guards", {})
    _require(semantics.get("year_2025_status") == "PROVEN_STRUCTURAL_RECENT", "YEAR_2025_STATUS")
    for key in ("annual_closure_status", "semantic_comparability_status", "gold_metrics_status"):
        _require(semantics.get(key) == "UNKNOWN", f"UNKNOWN_REQUIRED:{key}")
    _require(semantics.get("closed_annual_series_first_year") == 2016, "CLOSED_SERIES_START")
    _require(semantics.get("closed_annual_series_last_year") == 2024, "CLOSED_SERIES_END")
    _require(semantics.get("year_2026_status") == "UNPROVEN_CURRENT_YEAR", "YEAR_2026_STATUS")

    _require(design.get("decision") == "DESIGN_READY_REMOTE_DISCOVERY_NOT_AUTHORIZED", "DECISION")
    _require(design.get("next_gate") == "TASK_009E_L_SEPARATE_OWNER_AUTHORIZATION_FOR_BOUNDED_OFFICIAL_DOCUMENTARY_DISCOVERY", "NEXT_GATE")


def main() -> int:
    try:
        validate_design(
            _load(DESIGN),
            _load(TASK007),
            _load(TASK008),
            _load(TASK009D),
            SIOPE_CLIENT.read_text(encoding="utf-8"),
        )
    except (OSError, json.JSONDecodeError, DocumentaryDiscoveryDesignError) as exc:
        print(str(exc))
        return 13
    print(json.dumps({
        "status": "PASS_TASK009E_OFFICIAL_ALIAS_DOCUMENTARY_DISCOVERY_DESIGN_T0",
        "source_get_count": 0,
        "remote_execution_authorized": False,
        "questions": ["S1_NUM_POPU", "S2_FINANCIAL_ALIAS_BRIDGE"],
        "future_document_open_budget": 12,
        "gold_2025": "UNKNOWN",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

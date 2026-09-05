from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATTERN = ROOT / "config/methodology_json_engineering_pattern.v1.json"
REGISTRY = ROOT / "config/methodology_domain_registry.v1.json"
EVIDENCE = ROOT / "docs/evidence/TASK_164_GENERAL_METHODOLOGY_JSON_PATTERN_0.8.0.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise AssertionError(code)


def validate() -> dict:
    p = _load(PATTERN)
    r = _load(REGISTRY)
    e = _load(EVIDENCE)

    _require(p["schema"] == "METHODOLOGY_JSON_ENGINEERING_PATTERN_V1", "TASK164_PATTERN_SCHEMA")
    _require(r["schema"] == "METHODOLOGY_DOMAIN_REGISTRY_V1", "TASK164_REGISTRY_SCHEMA")
    _require(r["pattern"] == p["schema"], "TASK164_PATTERN_LINK")
    _require(p["issue"] == 540 and e["issue"] == 540, "TASK164_ISSUE")
    _require(p["base_sha"] == e["base_sha"], "TASK164_BASE")

    components = {x["id"]: x for x in p["required_components"]}
    expected = {
        "DOMAIN_METHODOLOGY",
        "OBSERVATION_CONTRACT",
        "QUESTION_SOURCE_ROUTER",
        "VALIDATOR",
        "TESTS",
        "SANITIZED_EVIDENCE",
    }
    _require(expected == set(components), "TASK164_COMPONENTS")
    _require(all(x["required"] for x in components.values()), "TASK164_REQUIRED_COMPONENTS")

    layers = set(p["knowledge_layer_contract"]["required_layers_when_applicable"])
    _require({"METHODOLOGICAL_ACADEMIC", "NORMATIVE_OFFICIAL", "EMPIRICAL_PRIMARY"} <= layers, "TASK164_LAYERS")

    _require(p["ontology_contract"]["unknown_default"] == "UNKNOWN_NOT_INFERRED", "TASK164_UNKNOWN")
    _require(p["ontology_contract"]["silent_completion_forbidden"] is True, "TASK164_NO_SILENT_COMPLETION")

    forbidden = set(p["inference_contract"]["general_forbidden_promotions"])
    for item in [
        "THEMATIC_SIMILARITY_TO_IDENTITY",
        "CHRONOLOGY_TO_IDENTITY",
        "SEARCH_SNIPPET_TO_EXHAUSTIVE_EVIDENCE",
        "TRANSPORT_FAILURE_TO_SOURCE_NO_MATCH",
        "ACADEMIC_REFERENCE_TO_CURRENT_NORMATIVE_FACT",
        "MISSING_FIELD_TO_GUESSED_VALUE",
    ]:
        _require(item in forbidden, f"TASK164_FORBIDDEN_{item}")

    _require(p["routing_contract"]["default_fallback"] == "EVIDENCIA_INSUFICIENTE", "TASK164_FALLBACK")
    _require(p["integration_contract"]["domain_adapters_should_emit_observation_contract_packets"] is True, "TASK164_ADAPTERS")
    _require(p["integration_contract"]["research_queries_should_use_router_before_claim_promotion"] is True, "TASK164_ROUTER")
    _require(p["integration_contract"]["validators_should_run_offline_in_ci"] is True, "TASK164_CI")
    _require(p["integration_contract"]["domain_implementation_must_register_itself"] is True, "TASK164_REGISTRATION")

    domains = {x["domain_id"]: x for x in r["domains"]}
    _require("PUBLIC_BUDGET" in domains, "TASK164_PUBLIC_BUDGET")
    budget = domains["PUBLIC_BUDGET"]
    _require(budget["status"] == "CONFORMING", "TASK164_BUDGET_STATUS")
    for key in [
        "methodology_path",
        "observation_contract_path",
        "router_path",
        "validator_path",
        "test_path",
        "evidence_path",
    ]:
        _require((ROOT / budget[key]).exists(), f"TASK164_BUDGET_PATH_{key}")

    hard = e["hard_boundaries"]
    _require(all(v is False for v in hard.values()), "TASK164_HARD_BOUNDARIES")

    return {
        "task": p["task"],
        "pattern": p["schema"],
        "registered_domains": sorted(domains),
        "first_reference_implementation": p["first_reference_implementation"]["domain_id"],
        "status": "VALID",
    }


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, sort_keys=True))

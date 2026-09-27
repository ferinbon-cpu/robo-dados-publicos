from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
METHODOLOGY = ROOT / "config/public_budget_methodology.v1.json"
OBSERVATION = ROOT / "config/public_budget_observation_contract.v1.json"
ROUTER = ROOT / "config/public_budget_question_router.v1.json"
EVIDENCE = ROOT / "docs/evidence/TASK_163_PUBLIC_BUDGET_METHODOLOGY_JSON_BRAIN_0.8.0.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise AssertionError(code)


def validate() -> dict:
    m = _load(METHODOLOGY)
    o = _load(OBSERVATION)
    r = _load(ROUTER)
    e = _load(EVIDENCE)

    _require(m["schema"] == "PUBLIC_BUDGET_METHODOLOGY_V1", "TASK163_M_SCHEMA")
    _require(o["schema"] == "PUBLIC_BUDGET_OBSERVATION_CONTRACT_V1", "TASK163_O_SCHEMA")
    _require(r["schema"] == "PUBLIC_BUDGET_QUESTION_ROUTER_V1", "TASK163_R_SCHEMA")
    _require(e["issue"] == 538, "TASK163_ISSUE")
    _require(m["base_sha"] == e["base_sha"], "TASK163_BASE")

    ref = m["methodological_reference"]
    _require(ref["author"] == "James Giacomoni", "TASK163_AUTHOR")
    _require(ref["edition"] == 18, "TASK163_EDITION")
    _require(ref["source_role"] == "ACADEMIC_METHOD_REFERENCE", "TASK163_METHOD_ROLE")
    _require(ref["copyright_boundary"]["full_text_persistence"] is False, "TASK163_NO_FULLTEXT")
    _require(ref["copyright_boundary"]["paraphrased_concept_digest_only"] is True, "TASK163_PARAPHRASE")

    layers = {x["id"]: x for x in m["knowledge_layers"]}
    _require(set(layers) == {"METHODOLOGICAL_ACADEMIC", "NORMATIVE_OFFICIAL", "EMPIRICAL_PRIMARY"}, "TASK163_LAYERS")
    _require("current_legal_rule" in layers["METHODOLOGICAL_ACADEMIC"]["cannot_prove"], "TASK163_METHOD_NE_LAW")
    _require("municipal_empirical_fact" in layers["METHODOLOGICAL_ACADEMIC"]["cannot_prove"], "TASK163_METHOD_NE_FACT")

    stages = {x["id"] for x in m["evidence_stages"]}
    required_stages = {
        "PLANNING_INTENT",
        "ANNUAL_BUDGET_GUIDANCE",
        "BUDGET_AUTHORIZATION_INITIAL",
        "BUDGET_AUTHORIZATION_UPDATED",
        "PROCUREMENT",
        "CONTRACT",
        "COMMITMENT",
        "LIQUIDATION",
        "PAYMENT",
        "RESTOS_A_PAGAR",
        "AGGREGATED_REPORTING",
    }
    _require(required_stages <= stages, "TASK163_STAGES")

    rules = {x["id"]: x["rule"] for x in m["interpretation_rules"]}
    for rid in [
        "R01_PLANNING_NE_EXECUTION",
        "R02_LOA_NE_EXECUTION",
        "R03_PROCUREMENT_NE_PAYMENT",
        "R04_EXECUTION_STAGES_DISTINCT",
        "R05_PROGRAM_NE_POLICY_IDENTITY",
        "R08_NOMINAL_NE_REAL_CHANGE",
        "R12_CURRENT_LAW_FRESHNESS",
        "R13_STABLE_JOIN_KEYS",
    ]:
        _require(rid in rules, f"TASK163_RULE_{rid}")

    forbidden = set(m["forbidden_promotions"])
    _require("PPA_VALUE_TO_EXECUTION" in forbidden, "TASK163_FORBID_PPA")
    _require("LOA_APPROPRIATION_TO_PAYMENT" in forbidden, "TASK163_FORBID_LOA")
    _require("PNCP_PROCUREMENT_TO_PAYMENT" in forbidden, "TASK163_FORBID_PNCP")
    _require("ACADEMIC_REFERENCE_TO_CURRENT_LAW" in forbidden, "TASK163_FORBID_METHOD_LAW")
    _require("SPENDING_GROWTH_TO_POLICY_EFFECT" in forbidden, "TASK163_FORBID_CAUSAL")

    req = set(o["required_top_level"])
    _require({"source", "scope", "evidence_stage", "amounts", "classifications", "stable_keys", "policy_linkage", "provenance", "quality"} <= req, "TASK163_OBS_REQUIRED")
    _require("ACADEMIC_METHOD_REFERENCE" in o["field_contract"]["source"]["allowed_source_roles"], "TASK163_OBS_METHOD_ROLE")
    _require(o["field_contract"]["classifications"]["missing_value"] == "UNKNOWN_NOT_INFERRED", "TASK163_NO_INFERRED_CLASS")

    capabilities = {x["source_family"]: x for x in r["source_capabilities"]}
    _require("PPA" in capabilities and "LOA" in capabilities and "PNCP" in capabilities, "TASK163_SOURCE_CAP")
    _require("payment" in capabilities["PNCP"]["cannot_answer_alone"], "TASK163_PNCP_NE_PAYMENT")
    _require("commitment" in capabilities["LOA"]["cannot_answer_alone"], "TASK163_LOA_NE_COMMITMENT")
    _require("current_law" in capabilities["ACADEMIC_METHOD"]["cannot_answer_alone"], "TASK163_ACADEMIC_NE_CURRENT_LAW")

    routes = {x["id"]: x for x in r["question_routes"]}
    _require(routes["Q_EXECUTED"]["required_semantic_split"] == ["COMMITTED_VALUE", "LIQUIDATED_VALUE", "PAID_VALUE"], "TASK163_EXEC_SPLIT")
    _require(routes["Q_POLICY_FINANCIAL_IDENTITY"]["fallback"] == "EVIDENCIA_INSUFICIENTE", "TASK163_POLICY_FALLBACK")
    _require(routes["Q_EFFECT"]["fallback"] == "CAUSAL_INFERENCE_NOT_AUTHORIZED", "TASK163_CAUSAL_FALLBACK")

    pipeline = r["research_pipeline"]
    _require(pipeline[0] == "1_IDENTITY_VALIDATE_ENTITY_PERIOD_SOURCE", "TASK163_PIPELINE_IDENTITY_FIRST")
    _require(pipeline[-1] == "13_NAME_NEXT_SOURCE_NEEDED_TO_CLOSE_GAP", "TASK163_PIPELINE_GAP_SOURCE")

    hard = e["hard_boundaries"]
    _require(all(v is False for v in hard.values()), "TASK163_EVIDENCE_BOUNDARIES")

    return {
        "task": m["task"],
        "schemas": [m["schema"], o["schema"], r["schema"]],
        "method_reference": "James Giacomoni, 18th edition",
        "knowledge_layers": sorted(layers),
        "evidence_stage_count": len(stages),
        "interpretation_rule_count": len(rules),
        "question_route_count": len(routes),
        "status": "VALID",
    }


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, sort_keys=True))

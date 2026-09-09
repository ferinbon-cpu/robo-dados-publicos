from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/task219e_pncp_transport_incident_canonization.v1.json"


class Task219EError(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task219EError(code)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def git_blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    payload = b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    return hashlib.sha1(payload).hexdigest()


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    cfg = _load(Path(path))
    _stop(cfg.get("schema") == "TASK219E_PNCP_TRANSPORT_INCIDENT_CANONIZATION_V1", "TASK219E_SCHEMA")
    _stop(cfg.get("task") == "TASK_219E" and cfg.get("issue") == 699, "TASK219E_TASK")
    _stop(cfg.get("parent_issue") == 691, "TASK219E_PARENT")
    semantics = cfg["absence_semantics"]
    required_false = [
        "timeout_can_prove_no_match",
        "zero_bytes_can_prove_no_match",
        "http_502_can_prove_no_match",
        "http_503_can_prove_no_match",
        "http_504_can_prove_no_match",
        "incomplete_pagination_can_prove_no_match",
        "portal_visibility_can_replace_api_primary_proof",
        "secondary_evidence_can_create_procurement_identity",
    ]
    _stop(all(semantics[k] is False for k in required_false), "TASK219E_ABSENCE_GUARDS")
    _stop(semantics["no_match_requires_complete_exact_scope"] is True, "TASK219E_COMPLETE_SCOPE")
    _stop(semantics["no_match_requires_all_required_responses_successful"] is True, "TASK219E_SUCCESS_SCOPE")
    _stop(not any(cfg["remote_effects"].values()), "TASK219E_REMOTE_EFFECTS")
    future = cfg["future_controlled_probe"]
    _stop(future["implemented"] is False and future["executed"] is False, "TASK219E_FUTURE_PROBE_INERT")
    _stop(future["fresh_owner_authorization_required"] is True, "TASK219E_FUTURE_AUTH")
    _stop(future["authorization_reuse_allowed"] is False, "TASK219E_AUTH_REUSE")
    _stop(future["proxy_or_mirror_may_be_primary_evidence"] is False, "TASK219E_PROXY")
    return cfg


def classify_response(
    *,
    http_status: int | None,
    bytes_received: int,
    json_valid: bool,
    transport_error: str | None = None,
    cfg: Mapping[str, Any] | None = None,
) -> str:
    c = dict(cfg or load_config())
    rules = c["classification"]

    if transport_error:
        return "TRANSPORT_OR_EDGE_UNAVAILABLE"
    if http_status is None:
        return "TRANSPORT_OR_EDGE_UNAVAILABLE"
    if int(http_status) in set(rules["transport_or_edge_statuses"]):
        return "TRANSPORT_OR_EDGE_UNAVAILABLE"
    if int(http_status) in set(rules["confirmed_empty_statuses"]):
        return "CONFIRMED_EMPTY_RESPONSE"
    if (
        int(http_status) == int(rules["valid_json_status"])
        and int(bytes_received) > 0
        and bool(json_valid)
    ):
        return "VALID_JSON_RESPONSE"
    return "INVALID_OR_INSUFFICIENT_RESPONSE"


def no_match_allowed(
    responses: Iterable[Mapping[str, Any]],
    *,
    exact_scope_complete: bool,
    cfg: Mapping[str, Any] | None = None,
) -> bool:
    c = dict(cfg or load_config())
    if not exact_scope_complete:
        return False
    accepted = {"VALID_JSON_RESPONSE", "CONFIRMED_EMPTY_RESPONSE"}
    states = [
        classify_response(
            http_status=r.get("http_status"),
            bytes_received=int(r.get("bytes_received") or 0),
            json_valid=bool(r.get("json_valid")),
            transport_error=r.get("transport_error"),
            cfg=c,
        )
        for r in responses
    ]
    return bool(states) and all(state in accepted for state in states)


def _validate_blob(root: Path, spec: Mapping[str, Any]) -> dict[str, Any]:
    path = root / str(spec["path"])
    _stop(path.is_file(), "TASK219E_UPSTREAM_FILE_MISSING")
    if spec.get("git_blob_sha"):
        _stop(git_blob_sha(path) == spec["git_blob_sha"], "TASK219E_UPSTREAM_BLOB_SHA")
    return _load(path)


def build_evidence(root: Path = ROOT) -> dict[str, Any]:
    cfg = load_config(root / "config/task219e_pncp_transport_incident_canonization.v1.json")
    upstream = cfg["upstream_evidence"]

    t168 = _validate_blob(root, upstream["task168b"])
    req168 = t168["requests"]
    exp168 = upstream["task168b"]["expected"]
    _stop([r["http_status"] for r in req168] == exp168["http_statuses"], "TASK219E_168_STATUS")
    _stop(t168["pagination"]["totalRegistros"] == exp168["total_records"], "TASK219E_168_RECORDS")
    _stop(t168["pagination"]["exhaustive_within_exact_scope"] is exp168["complete"], "TASK219E_168_COMPLETE")

    t216 = _validate_blob(root, upstream["task216"])
    exp216 = upstream["task216"]["expected"]
    a1 = t216["runtime_attempt_1"]
    a2 = t216["runtime_attempt_2"]
    _stop(a1["page_statuses"] == exp216["attempt1_page_statuses"], "TASK219E_216_A1_STATUS")
    _stop(a1["complete_pagination"] is exp216["attempt1_complete"], "TASK219E_216_A1_COMPLETE")
    _stop(a1["scientific_effect"] == exp216["attempt1_scientific_effect"], "TASK219E_216_A1_SCIENCE")
    _stop(a2["total_records"] == exp216["attempt2_total_records"], "TASK219E_216_A2_RECORDS")
    _stop(sum(a2["partition_pages"].values()) == exp216["attempt2_total_gets"], "TASK219E_216_A2_GETS")
    _stop(a2["complete_all_partitions"] is exp216["attempt2_complete"], "TASK219E_216_A2_COMPLETE")

    t219c = _validate_blob(root, upstream["task219c"])
    exp219c = upstream["task219c"]["expected"]
    _stop(t219c["prior_pncp_complete_scope"]["run_id"] == exp219c["prior_complete_run_id"], "TASK219E_219C_RUN")
    _stop(t219c["prior_pncp_complete_scope"]["total_records"] == exp219c["prior_complete_total_records"], "TASK219E_219C_RECORDS")
    _stop(t219c["scientific_state"]["contextual_paths_after_carrier"] == exp219c["contextual_paths"], "TASK219E_219C_PATHS")

    t219c2 = _validate_blob(root, upstream["task219c2"])
    exp219c2 = upstream["task219c2"]["expected"]
    failed = t219c2["failed_runtime"]
    _stop(failed["run_id"] == exp219c2["failed_run_id"], "TASK219E_219C2_RUN")
    _stop(failed["request_count"] == exp219c2["request_count"], "TASK219E_219C2_REQUESTS")
    _stop(failed["bytes_received"] == exp219c2["bytes_received"], "TASK219E_219C2_BYTES")
    _stop(failed["status"] == exp219c2["status"], "TASK219E_219C2_STATUS")
    _stop(failed["scientific_effect"] == exp219c2["scientific_effect"], "TASK219E_219C2_SCIENCE")
    _stop(failed["absence_inference"] is exp219c2["absence_inference"], "TASK219E_219C2_ABSENCE")

    t219d = _validate_blob(root, upstream["task219d"])
    exp219d = upstream["task219d"]["expected"]
    counts = t219d["counts"]
    _stop(counts["combined_unique_identities"] == exp219d["combined_unique_identities"], "TASK219E_219D_IDENTITIES")
    _stop(counts["combined_edital_identity_keys"] == exp219d["combined_edital_identity_keys"], "TASK219E_219D_EDITALS")
    _stop(counts["combined_daily_search_seed_count"] == exp219d["combined_daily_search_seed_count"], "TASK219E_219D_SEEDS")
    _stop(t219d["scientific_adjudication"]["contextual_paths_after"] == exp219d["contextual_paths"], "TASK219E_219D_PATHS")

    historical_168 = [
        {
            "http_status": r["http_status"],
            "bytes_received": r["bytes_received"],
            "json_valid": r["content_type"] == "application/json" and bool(r.get("source_sha256")),
        }
        for r in req168
    ]
    historical_216_a1 = [
        {
            "http_status": status,
            "bytes_received": 1 if status == 200 else 0,
            "json_valid": status == 200,
        }
        for status in a1["page_statuses"]
    ]
    timeout_219c = [{
        "http_status": None,
        "bytes_received": failed["bytes_received"],
        "json_valid": False,
        "transport_error": failed["transport_error"],
    }]

    observations = [
        {
            "id": "TASK168B_COMPLETE_759",
            "endpoint": t168["exact_scope"]["endpoint"],
            "response_states": [
                classify_response(cfg=cfg, **row) for row in historical_168
            ],
            "exact_scope_complete": True,
            "no_match_semantically_eligible": no_match_allowed(
                historical_168, exact_scope_complete=True, cfg=cfg
            ),
            "meaning": "A bounded negative result can be scientific because all required pages were valid and the exact scope was exhaustive.",
        },
        {
            "id": "TASK216_ATTEMPT1_200_200_200_502",
            "endpoint": a2["overall_scope"]["endpoint"],
            "response_states": [
                classify_response(cfg=cfg, **row) for row in historical_216_a1
            ],
            "exact_scope_complete": False,
            "no_match_semantically_eligible": no_match_allowed(
                historical_216_a1, exact_scope_complete=False, cfg=cfg
            ),
            "meaning": "The final 502 makes the attempt incomplete and scientifically incapable of proving absence.",
        },
        {
            "id": "TASK216B_COMPLETE_1933",
            "endpoint": a2["overall_scope"]["endpoint"],
            "total_records": a2["total_records"],
            "total_gets": sum(a2["partition_pages"].values()),
            "exact_scope_complete": True,
            "meaning": "The same endpoint family completed successfully under a partitioned transport shape one day before the later zero-byte timeout.",
        },
        {
            "id": "TASK219C_ZERO_BYTE_TIMEOUT",
            "endpoint": cfg["source_family"]["consulta_contracts_endpoint"],
            "response_states": [
                classify_response(cfg=cfg, **row) for row in timeout_219c
            ],
            "exact_scope_complete": False,
            "no_match_semantically_eligible": no_match_allowed(
                timeout_219c, exact_scope_complete=False, cfg=cfg
            ),
            "bytes_received": failed["bytes_received"],
            "scientific_effect": failed["scientific_effect"],
            "absence_inference": failed["absence_inference"],
            "meaning": "A zero-byte timeout is transport evidence only, never data absence.",
        },
    ]

    operator = []
    for item in cfg["supporting_operator_observations"]:
        operator.append({
            **item,
            "classified_states": [
                classify_response(
                    http_status=int(status),
                    bytes_received=0,
                    json_valid=False,
                    cfg=cfg,
                )
                for status in item["observed_status_family"]
            ],
            "can_prove_absence": False,
        })

    return {
        "task": "TASK_219E_PNCP_TRANSPORT_INCIDENT_CANONIZATION",
        "issue": 699,
        "parent_issue": 691,
        "canonical_date": cfg["canonical_date"],
        "canonical_transport_label": cfg["scientific_state"]["canonical_transport_label"],
        "historical_observations": observations,
        "supporting_operator_observations": operator,
        "external_diagnostic_leads": cfg["external_diagnostic_leads"],
        "adjudication": {
            "same_endpoint_has_recent_success_and_failure": True,
            "endpoint_deprecation_proven": False,
            "rate_limit_proven": False,
            "waf_or_asn_filtering_proven": False,
            "backend_outage_proven": False,
            "current_transport_or_edge_unavailability_proven_by_canonical_runtime": True,
            "transport_failure_can_be_reinterpreted_as_no_match": False,
            "secondary_or_portal_evidence_can_replace_primary_identity_proof": False,
            "question_promotion_performed": False,
            "contextual_paths_before": 34,
            "contextual_paths_after": 34,
            "canonical_questions_total": 38,
            "remaining_blockers": cfg["scientific_state"]["remaining_blockers"],
        },
        "future_controlled_probe": cfg["future_controlled_probe"],
        "next_action": "PRIMARY_MUNICIPAL_OR_TCE_IDENTITY_ROUTE_NOW; CONTROLLED_MULTI_ORIGIN_PNCP_PROBE_ONLY_LATER_WITH_FRESH_AUTHORIZATION",
        "remote_effects": cfg["remote_effects"],
    }


def materialize(root: Path = ROOT) -> dict[str, Any]:
    evidence = build_evidence(root)
    cfg = load_config(root / "config/task219e_pncp_transport_incident_canonization.v1.json")
    path = root / cfg["outputs"]["evidence"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return evidence


def main() -> int:
    result = materialize()
    print("TASK219E_STATUS=PASS_PNCP_TRANSPORT_INCIDENT_CANONIZATION")
    print("TASK219E_LABEL=" + result["canonical_transport_label"])
    print("TASK219E_CONTEXTUAL_PATHS=" + str(result["adjudication"]["contextual_paths_after"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

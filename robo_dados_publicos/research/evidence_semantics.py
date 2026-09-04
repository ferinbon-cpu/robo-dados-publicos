from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
from typing import Any


SOURCE_ROLES = (
    "DOCTRINAL_SOURCE",
    "ACADEMIC_RESEARCH",
    "NORMATIVE_PRIMARY",
    "PLANNING_PRIMARY",
    "BUDGET_PRIMARY",
    "ACCOUNTING_EXECUTION_PRIMARY",
    "ADMINISTRATIVE_PRIMARY",
    "STATISTICAL_PRIMARY",
    "SECONDARY_AGGREGATOR",
)

CLAIM_DOMAINS = (
    "CONCEPTUAL_INTERPRETATION",
    "ACADEMIC_FINDING",
    "LEGAL_NORM",
    "PLANNING_INTENT",
    "BUDGET_AUTHORIZATION",
    "ACCOUNTING_EXECUTION",
    "ADMINISTRATIVE_EVENT",
    "STATISTICAL_OBSERVATION",
    "POLICY_LINKAGE",
    "SEARCH_RESULT",
    "CAUSAL_EFFECT",
)

EVIDENCE_KINDS = (
    "DIRECT_EXPLICIT",
    "DETERMINISTIC_DERIVATION",
    "ANALYTICAL_INFERENCE",
    "NEGATIVE_SEARCH_OBSERVATION",
)

STATUS_ORDER = ("UNKNOWN", "CANDIDATE", "CORROBORATED", "PROVEN")
_STATUS_RANK = {status: index for index, status in enumerate(STATUS_ORDER)}
_TYPED_ID_RE = re.compile(r"^[A-Z_]+:[A-Za-z0-9][A-Za-z0-9._:-]{0,199}$")

SOURCE_DOMAIN_POLICY = {
    "DOCTRINAL_SOURCE": {
        "direct": {"CONCEPTUAL_INTERPRETATION"},
        "corroborate": {"ACADEMIC_FINDING", "POLICY_LINKAGE"},
    },
    "ACADEMIC_RESEARCH": {
        "direct": {"ACADEMIC_FINDING", "CONCEPTUAL_INTERPRETATION"},
        "corroborate": {"POLICY_LINKAGE", "STATISTICAL_OBSERVATION"},
    },
    "NORMATIVE_PRIMARY": {
        "direct": {"LEGAL_NORM"},
        "corroborate": {"PLANNING_INTENT", "POLICY_LINKAGE", "ADMINISTRATIVE_EVENT"},
    },
    "PLANNING_PRIMARY": {
        "direct": {"PLANNING_INTENT"},
        "corroborate": {"BUDGET_AUTHORIZATION", "POLICY_LINKAGE"},
    },
    "BUDGET_PRIMARY": {
        "direct": {"BUDGET_AUTHORIZATION"},
        "corroborate": {"PLANNING_INTENT", "POLICY_LINKAGE"},
    },
    "ACCOUNTING_EXECUTION_PRIMARY": {
        "direct": {"ACCOUNTING_EXECUTION"},
        "corroborate": {"BUDGET_AUTHORIZATION", "POLICY_LINKAGE", "ADMINISTRATIVE_EVENT"},
    },
    "ADMINISTRATIVE_PRIMARY": {
        "direct": {"ADMINISTRATIVE_EVENT"},
        "corroborate": {"POLICY_LINKAGE", "ACCOUNTING_EXECUTION"},
    },
    "STATISTICAL_PRIMARY": {
        "direct": {"STATISTICAL_OBSERVATION"},
        "corroborate": set(),
    },
    "SECONDARY_AGGREGATOR": {
        "direct": set(),
        "corroborate": {
            "STATISTICAL_OBSERVATION",
            "ACCOUNTING_EXECUTION",
            "BUDGET_AUTHORIZATION",
            "ADMINISTRATIVE_EVENT",
            "POLICY_LINKAGE",
        },
    },
}


class EvidenceSemanticsStop(RuntimeError):
    """Fail-closed epistemic/source-role validation error."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise EvidenceSemanticsStop(code)


def _typed_id(value: object, *, prefix: str, code: str) -> str:
    text = str(value or "")
    _require(bool(_TYPED_ID_RE.fullmatch(text)), code)
    _require(text.startswith(prefix + ":"), code)
    return text


def source_role_max_status(source_role: str, claim_domain: str) -> str:
    _require(source_role in SOURCE_ROLES, "TASK095_SOURCE_ROLE")
    _require(claim_domain in CLAIM_DOMAINS, "TASK095_CLAIM_DOMAIN")
    if claim_domain == "CAUSAL_EFFECT":
        return "CANDIDATE"
    policy = SOURCE_DOMAIN_POLICY[source_role]
    if claim_domain in policy["direct"]:
        return "PROVEN"
    if claim_domain in policy["corroborate"]:
        return "CORROBORATED"
    return "CANDIDATE"


def evidence_kind_max_status(kind: str, *, claim_domain: str) -> str:
    _require(kind in EVIDENCE_KINDS, "TASK095_EVIDENCE_KIND")
    _require(claim_domain in CLAIM_DOMAINS, "TASK095_CLAIM_DOMAIN")
    if claim_domain == "CAUSAL_EFFECT":
        return "CANDIDATE"
    if kind == "DIRECT_EXPLICIT":
        return "PROVEN"
    if kind == "DETERMINISTIC_DERIVATION":
        return "PROVEN"
    if kind == "ANALYTICAL_INFERENCE":
        return "CANDIDATE"
    if kind == "NEGATIVE_SEARCH_OBSERVATION":
        return "PROVEN" if claim_domain == "SEARCH_RESULT" else "CANDIDATE"
    raise EvidenceSemanticsStop("TASK095_UNREACHABLE_EVIDENCE_KIND")


def allowed_evidence_status(source_role: str, claim_domain: str, kind: str) -> str:
    source_max = source_role_max_status(source_role, claim_domain)
    kind_max = evidence_kind_max_status(kind, claim_domain=claim_domain)
    return min((source_max, kind_max), key=lambda value: _STATUS_RANK[value])


def validate_semantic_evidence(record: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(record, dict), "TASK095_EVIDENCE_OBJECT")
    evidence_id = _typed_id(
        record.get("evidence_id"),
        prefix="EVIDENCE",
        code="TASK095_EVIDENCE_ID",
    )
    source_document_id = _typed_id(
        record.get("source_document_id"),
        prefix="DOC",
        code="TASK095_SOURCE_DOCUMENT_ID",
    )
    source_role = str(record.get("source_role") or "")
    claim_domain = str(record.get("claim_domain") or "")
    evidence_kind = str(record.get("evidence_kind") or "")
    _require(source_role in SOURCE_ROLES, "TASK095_SOURCE_ROLE")
    _require(claim_domain in CLAIM_DOMAINS, "TASK095_CLAIM_DOMAIN")
    _require(evidence_kind in EVIDENCE_KINDS, "TASK095_EVIDENCE_KIND")

    locator = record.get("locator")
    _require(isinstance(locator, dict) and locator, "TASK095_LOCATOR")
    requested_status = str(record.get("requested_status") or "")
    _require(requested_status in STATUS_ORDER, "TASK095_REQUESTED_STATUS")
    maximum = allowed_evidence_status(source_role, claim_domain, evidence_kind)
    _require(
        _STATUS_RANK[requested_status] <= _STATUS_RANK[maximum],
        "TASK095_STATUS_EXCEEDS_SOURCE_OR_KIND_CAPABILITY",
    )

    input_evidence_ids = record.get("input_evidence_ids", [])
    _require(isinstance(input_evidence_ids, list), "TASK095_INPUT_EVIDENCE_IDS")
    normalized_inputs: list[str] = []
    for value in input_evidence_ids:
        item = _typed_id(value, prefix="EVIDENCE", code="TASK095_INPUT_EVIDENCE_ID")
        _require(item != evidence_id, "TASK095_SELF_DERIVATION")
        _require(item not in normalized_inputs, "TASK095_DUPLICATE_INPUT_EVIDENCE")
        normalized_inputs.append(item)

    if evidence_kind == "DETERMINISTIC_DERIVATION":
        _require(bool(normalized_inputs), "TASK095_DERIVATION_INPUT_REQUIRED")
        _require(record.get("reproducible") is True, "TASK095_DERIVATION_REPRODUCIBILITY_REQUIRED")
    else:
        _require(record.get("reproducible") in {None, False}, "TASK095_REPRODUCIBLE_ONLY_FOR_DERIVATION")

    if evidence_kind == "NEGATIVE_SEARCH_OBSERVATION":
        _require(claim_domain == "SEARCH_RESULT", "TASK095_NEGATIVE_OBSERVATION_DOMAIN")
        _require(record.get("negative_search_id") is not None, "TASK095_NEGATIVE_SEARCH_ID_REQUIRED")

    note = str(record.get("note") or "")
    return {
        "evidence_id": evidence_id,
        "source_document_id": source_document_id,
        "source_role": source_role,
        "claim_domain": claim_domain,
        "evidence_kind": evidence_kind,
        "locator": deepcopy(locator),
        "requested_status": requested_status,
        "maximum_allowed_status": maximum,
        "input_evidence_ids": normalized_inputs,
        "reproducible": record.get("reproducible") is True,
        "negative_search_id": record.get("negative_search_id"),
        "note": note,
    }


def validate_negative_evidence(record: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(record, dict), "TASK095_NEGATIVE_OBJECT")
    search_id = _typed_id(
        record.get("search_id"),
        prefix="SEARCH",
        code="TASK095_NEGATIVE_SEARCH_ID",
    )
    target = str(record.get("target") or "").strip()
    _require(target != "", "TASK095_NEGATIVE_TARGET")
    scope = record.get("scope")
    method = record.get("method")
    coverage = record.get("coverage")
    for value, code in (
        (scope, "TASK095_NEGATIVE_SCOPE"),
        (method, "TASK095_NEGATIVE_METHOD"),
        (coverage, "TASK095_NEGATIVE_COVERAGE"),
    ):
        _require(isinstance(value, dict) and value, code)

    result = str(record.get("result") or "")
    _require(result in {"NO_MATCH", "PARTIAL_MATCH", "MATCH"}, "TASK095_NEGATIVE_RESULT")
    exhaustive = record.get("exhaustive")
    _require(isinstance(exhaustive, bool), "TASK095_NEGATIVE_EXHAUSTIVE")

    if result == "NO_MATCH":
        interpretation = "ABSENCE_OBSERVED_WITHIN_DECLARED_SEARCH_SCOPE_ONLY"
        proves_nonexistence = False
    elif result == "PARTIAL_MATCH":
        interpretation = "PARTIAL_MATCH_WITHIN_DECLARED_SEARCH_SCOPE_ONLY"
        proves_nonexistence = False
    else:
        interpretation = "MATCH_OBSERVED_WITHIN_DECLARED_SEARCH_SCOPE"
        proves_nonexistence = False

    return {
        "search_id": search_id,
        "target": target,
        "scope": deepcopy(scope),
        "method": deepcopy(method),
        "coverage": deepcopy(coverage),
        "result": result,
        "exhaustive": exhaustive,
        "interpretation": interpretation,
        "proves_nonexistence": proves_nonexistence,
    }


def can_evidence_support_status(
    evidence: dict[str, Any],
    desired_status: str,
) -> bool:
    normalized = validate_semantic_evidence(evidence)
    _require(desired_status in STATUS_ORDER, "TASK095_DESIRED_STATUS")
    return _STATUS_RANK[desired_status] <= _STATUS_RANK[normalized["maximum_allowed_status"]]


def load_source_role_contract(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    _require(
        data.get("schema") == "SOURCE_ROLE_EVIDENCE_SEMANTICS_V1",
        "TASK095_CONTRACT_SCHEMA",
    )
    _require(tuple(data.get("source_roles") or ()) == SOURCE_ROLES, "TASK095_CONTRACT_SOURCE_ROLES")
    _require(tuple(data.get("claim_domains") or ()) == CLAIM_DOMAINS, "TASK095_CONTRACT_CLAIM_DOMAINS")
    _require(tuple(data.get("evidence_kinds") or ()) == EVIDENCE_KINDS, "TASK095_CONTRACT_EVIDENCE_KINDS")
    _require(tuple(data.get("status_order") or ()) == STATUS_ORDER, "TASK095_CONTRACT_STATUS_ORDER")

    raw_policy = data.get("source_domain_policy") or {}
    _require(set(raw_policy) == set(SOURCE_ROLES), "TASK095_CONTRACT_SOURCE_POLICY_SET")
    for role in SOURCE_ROLES:
        expected = SOURCE_DOMAIN_POLICY[role]
        observed = raw_policy.get(role) or {}
        _require(
            set(observed.get("direct") or []) == expected["direct"],
            f"TASK095_CONTRACT_DIRECT_{role}",
        )
        _require(
            set(observed.get("corroborate") or []) == expected["corroborate"],
            f"TASK095_CONTRACT_CORROBORATE_{role}",
        )

    neg = data.get("negative_evidence") or {}
    _require(neg.get("proves_nonexistence") is False, "TASK095_CONTRACT_NEGATIVE_OVERREACH")
    _require(
        neg.get("no_match_semantics") == "ABSENCE_OBSERVED_WITHIN_DECLARED_SEARCH_SCOPE_ONLY",
        "TASK095_CONTRACT_NO_MATCH_SEMANTICS",
    )
    remote = data.get("remote_effects") or {}
    _require(
        remote and all(value is False for value in remote.values()),
        "TASK095_CONTRACT_REMOTE_EFFECT",
    )
    return data

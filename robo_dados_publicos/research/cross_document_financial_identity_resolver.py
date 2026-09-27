from __future__ import annotations

from copy import deepcopy
from hashlib import sha1, sha256
import json
from pathlib import Path
from typing import Any, Iterable

from robo_dados_publicos.research.ppa_research_digest_adapter import (
    build_ppa_research_packets,
    load_adapter_contract as load_ppa_adapter_contract,
)
from robo_dados_publicos.research.loa_research_digest_adapter import (
    build_loa_research_packet,
    load_adapter_contract as load_loa_adapter_contract,
)
from robo_dados_publicos.research.siope_fundeb_research_digest_adapter import (
    build_siope_fundeb_research_packet,
    load_adapter_contract as load_siope_adapter_contract,
)


class CrossDocumentFinancialIdentityResolverStop(RuntimeError):
    """Fail-closed cross-document identity resolution error."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise CrossDocumentFinancialIdentityResolverStop(code)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _git_blob_sha(raw: bytes) -> str:
    return sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def _load_pinned_json(root: Path, meta: dict[str, Any], *, code: str) -> dict[str, Any]:
    path = root / str(meta.get("path") or "")
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise CrossDocumentFinancialIdentityResolverStop(code) from exc
    _require(_git_blob_sha(raw) == meta.get("git_blob_sha"), code)
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CrossDocumentFinancialIdentityResolverStop(code) from exc
    _require(isinstance(data, dict), code)
    return data


def validate_contract(contract: dict[str, Any], *, root: str | Path) -> dict[str, Any]:
    _require(
        contract.get("schema") == "EITI_CROSS_DOCUMENT_FINANCIAL_IDENTITY_RESOLVER_V1",
        "TASK122_SCHEMA",
    )
    _require(
        contract.get("mode") == "T0_OFFLINE_CROSS_DOCUMENT_IDENTITY_RESOLUTION",
        "TASK122_MODE",
    )
    remote = contract.get("remote_effects") or {}
    _require(remote and all(value is False for value in remote.values()), "TASK122_REMOTE_EFFECT")

    rules = contract.get("join_rules") or {}
    _require(rules.get("compare_only_same_key_type_and_value") is True, "TASK122_SAME_DIMENSION_RULE")
    _require(rules.get("same_value_different_key_type_is_match") is False, "TASK122_CROSS_DIMENSION_RULE")
    _require(rules.get("shared_key_automatically_policy_specific") is False, "TASK122_SHARED_KEY_RULE")
    for key in (
        "program_2001_sufficient",
        "generic_action_2690_sufficient",
        "generic_action_2720_sufficient",
        "text_similarity_allowed",
        "amount_equality_allowed",
        "reporting_bucket_is_transaction_identity",
    ):
        _require(rules.get(key) is False, f"TASK122_RULE_{key.upper()}")

    promotion = contract.get("promotion") or {}
    for key in (
        "current_financial_identity",
        "current_transaction_identity",
        "automatic_promotion",
        "causal_inference",
    ):
        _require(promotion.get(key) is False, f"TASK122_PROMOTION_{key.upper()}")

    clue = (contract.get("legacy_clues") or {}).get("2607004") or {}
    _require(
        clue.get("status") == "HYPOTHESIS_ONLY_NOT_ADMISSIBLE_AS_PROVEN_KEY",
        "TASK122_2607004_STATUS",
    )
    _require(clue.get("can_create_policy_identity") is False, "TASK122_2607004_POLICY")
    _require(clue.get("can_create_transaction_identity") is False, "TASK122_2607004_TRANSACTION")

    expected = contract.get("expected_current_resolution") or {}
    _require(
        expected.get("resolution_status")
        == "STOP_NO_STABLE_POLICY_TO_ACCOUNTING_EXECUTION_KEY",
        "TASK122_EXPECTED_STATUS",
    )
    _require(expected.get("cross_document_financial_identity_candidates") == 0, "TASK122_EXPECTED_CANDIDATES")
    _require(expected.get("transaction_identity") == "UNKNOWN", "TASK122_EXPECTED_TRANSACTION")

    root = Path(root)
    inputs = contract.get("inputs") or {}
    _require(
        set(inputs) == {"ppa_adapter", "loa_adapter", "siope_adapter", "task051_guard", "task049_guard"},
        "TASK122_INPUT_SET",
    )
    for name, meta in inputs.items():
        _load_pinned_json(root, meta, code=f"TASK122_{name.upper()}_BLOB")

    task051 = _load_pinned_json(root, inputs["task051_guard"], code="TASK122_TASK051_BLOB")
    _require(
        task051.get("result") == "PASS_TASK051_GRANULAR_EXECUTION_SOURCE_SELECTION_DESIGNED_NO_REMOTE_EFFECT",
        "TASK122_TASK051_STATUS",
    )
    closed = task051.get("closed_paths") or {}
    for key in (
        "repeat_program_2001_action_label_search",
        "attribute_program_2001_total_to_eiti",
        "attribute_generic_action_2690_to_eiti",
        "attribute_generic_action_2720_to_eiti",
        "infer_identity_from_ppa_loa_amount_alignment",
    ):
        _require(closed.get(key) is False, f"TASK122_TASK051_CLOSED_{key.upper()}")

    stopping = set(task051.get("stopping_rules") or [])
    for required in (
        "NO_EXPLICIT_OR_STABLY_PROVEN_POLICY_TO_ACCOUNTING_KEY_LINK_MEANS_IDENTITY_REMAINS_INSUFFICIENT",
        "DO_NOT_FALL_BACK_TO_PROGRAM_2001_TOTAL",
        "DO_NOT_FALL_BACK_TO_2690_OR_2720_GENERIC_ATTRIBUTION",
        "DO_NOT_USE_DESCRIPTION_SIMILARITY_OR_AMOUNT_EQUALITY_AS_FINANCIAL_IDENTITY",
    ):
        _require(required in stopping, "TASK122_TASK051_STOPPING_RULE")

    task049 = _load_pinned_json(root, inputs["task049_guard"], code="TASK122_TASK049_BLOB")
    conclusion = task049.get("conclusion") or {}
    _require(
        conclusion.get("program_to_explicit_eiti_action_linkage") == "NOT_PROVEN",
        "TASK122_TASK049_LINKAGE",
    )
    _require(
        conclusion.get("program_or_generic_action_financial_attribution_to_eiti") == "FORBIDDEN",
        "TASK122_TASK049_ATTRIBUTION",
    )

    acquisition = contract.get("acquisition_packet") or {}
    _require(
        acquisition.get("priority_order")
        == [item["source_class"] for item in task051.get("candidate_source_classes") or []],
        "TASK122_ACQUISITION_PRIORITY_DRIFT",
    )
    for required in (
        "EXPLICIT_EITI_OR_EQUIVALENT_POLICY_MARKER",
        "STABLE_ACCOUNTING_IDENTIFIER",
        "SOURCE_PROVENANCE",
    ):
        _require(required in set(acquisition.get("immediate_unlock_requirements") or []), "TASK122_UNLOCK_REQUIREMENT")
    return contract


def _key_pairs(group: dict[str, Any]) -> set[tuple[str, str]]:
    keys = group.get("stable_accounting_keys") or []
    out: set[tuple[str, str]] = set()
    for key in keys:
        key_type = str(key.get("key_type") or "")
        value = str(key.get("value") or "")
        _require(key_type != "" and value != "", "TASK122_KEY_SHAPE")
        out.add((key_type, value))
    return out


def _all_pairs(groups: Iterable[dict[str, Any]]) -> set[tuple[str, str]]:
    out: set[tuple[str, str]] = set()
    for group in groups:
        out |= _key_pairs(group)
    return out


def _same_dimension_intersection(
    left: Iterable[dict[str, Any]],
    right: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    pairs = _all_pairs(left) & _all_pairs(right)
    return [
        {"key_type": key_type, "value": value}
        for key_type, value in sorted(pairs)
    ]


def _same_value_cross_dimension(
    left: Iterable[dict[str, Any]],
    right: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    left_pairs = _all_pairs(left)
    right_pairs = _all_pairs(right)
    out: set[tuple[str, str, str]] = set()
    for left_type, left_value in left_pairs:
        for right_type, right_value in right_pairs:
            if left_value == right_value and left_type != right_type:
                out.add((left_value, left_type, right_type))
    return [
        {
            "value": value,
            "left_key_type": left_type,
            "right_key_type": right_type,
            "match_status": "REJECTED_DIFFERENT_IDENTITY_DIMENSION",
        }
        for value, left_type, right_type in sorted(out)
    ]


def _policy_groups(digest: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        deepcopy(group)
        for group in digest.get("context_groups") or []
        if group.get("qualified_policy_signal") is True
    ]


def _all_groups(digest: dict[str, Any]) -> list[dict[str, Any]]:
    return [deepcopy(group) for group in digest.get("context_groups") or []]


def resolve_eiti_cross_document_identity(
    contract: dict[str, Any],
    *,
    root: str | Path,
) -> dict[str, Any]:
    contract = validate_contract(contract, root=root)
    root = Path(root)

    ppa_contract = load_ppa_adapter_contract(
        root / contract["inputs"]["ppa_adapter"]["path"],
        root=root,
    )
    loa_contract = load_loa_adapter_contract(
        root / contract["inputs"]["loa_adapter"]["path"],
        root=root,
    )
    siope_contract = load_siope_adapter_contract(
        root / contract["inputs"]["siope_adapter"]["path"],
        root=root,
    )

    ppa = build_ppa_research_packets(ppa_contract, root=root)
    loa = build_loa_research_packet(loa_contract, root=root)
    siope = build_siope_fundeb_research_packet(siope_contract, root=root)

    _require(ppa.get("status") == "PASS_TASK117_PPA_REPOSITORY_EVIDENCE_ADAPTER", "TASK122_PPA_STATUS")
    _require(loa.get("status") == "PASS_TASK119_LOA_REPOSITORY_EVIDENCE_ADAPTER", "TASK122_LOA_STATUS")
    _require(siope.get("status") == "PASS_TASK121_SIOPE_FUNDEB_REPOSITORY_EVIDENCE_ADAPTER", "TASK122_SIOPE_STATUS")

    ppa_2026 = [
        digest
        for digest in ppa["research_digests"]
        if digest["source"]["document_id"] == "DOC:PPA_7213_2025"
    ]
    _require(len(ppa_2026) == 1, "TASK122_PPA2026_DIGEST")
    ppa_policy_groups = _policy_groups(ppa_2026[0])
    _require(bool(ppa_policy_groups), "TASK122_PPA_POLICY_ANCHOR")

    loa_groups = _all_groups(loa["research_digest"])
    _require(bool(loa_groups), "TASK122_LOA_GROUPS")
    _require(not _policy_groups(loa["research_digest"]), "TASK122_LOA_POLICY_SIGNAL_UNEXPECTED")

    siope_policy_groups = _policy_groups(siope["research_digest"])
    _require(bool(siope_policy_groups), "TASK122_SIOPE_POLICY_ANCHOR")
    _require(all(not _key_pairs(group) for group in siope_policy_groups), "TASK122_SIOPE_KEY_UNEXPECTED")

    ppa_loa = _same_dimension_intersection(ppa_policy_groups, loa_groups)
    ppa_siope = _same_dimension_intersection(ppa_policy_groups, siope_policy_groups)
    loa_siope = _same_dimension_intersection(loa_groups, siope_policy_groups)

    expected = contract["expected_current_resolution"]
    _require(ppa_loa == expected["ppa_loa_same_dimension_shared_keys"], "TASK122_PPA_LOA_INTERSECTION")
    _require(ppa_siope == expected["ppa_siope_same_dimension_shared_keys"], "TASK122_PPA_SIOPE_INTERSECTION")
    _require(loa_siope == expected["loa_siope_same_dimension_shared_keys"], "TASK122_LOA_SIOPE_INTERSECTION")

    cross_dimension = {
        "ppa_loa": _same_value_cross_dimension(ppa_policy_groups, loa_groups),
        "ppa_siope": _same_value_cross_dimension(ppa_policy_groups, siope_policy_groups),
        "loa_siope": _same_value_cross_dimension(loa_groups, siope_policy_groups),
    }

    rejected: list[dict[str, Any]] = []
    for key in ppa_loa:
        if key == {"key_type": "program", "value": "2001"}:
            rejected.append({
                **key,
                "status": "REJECTED_NON_SPECIFIC_POLICY_BRIDGE",
                "reason": "GENERIC_PROGRAM_NOT_EITI_SPECIFIC",
                "task049_program_to_explicit_eiti_action_linkage": "NOT_PROVEN",
                "task051_program_total_fallback_allowed": False,
            })
        else:
            rejected.append({
                **key,
                "status": "REJECTED_UNADJUDICATED_SHARED_KEY",
                "reason": "SHARED_KEY_NOT_PROVEN_POLICY_SPECIFIC",
            })

    _require(
        [
            {"key_type": item["key_type"], "value": item["value"], "reason": item["reason"]}
            for item in rejected
        ]
        == expected["rejected_shared_keys"],
        "TASK122_REJECTED_SHARED_KEYS",
    )

    candidates: list[dict[str, Any]] = []
    # Current evidence has no admissible bridge:
    # - PPA<->LOA overlap is generic Program 2001 only;
    # - SIOPE has policy-specific reporting but no stable accounting key.
    _require(len(candidates) == expected["cross_document_financial_identity_candidates"], "TASK122_CANDIDATE_COUNT")

    task051 = _load_pinned_json(root, contract["inputs"]["task051_guard"], code="TASK122_TASK051_BLOB")
    acquisition = contract["acquisition_packet"]

    resolution_core = {
        "schema": "EITI_CROSS_DOCUMENT_FINANCIAL_IDENTITY_RESOLUTION_V1",
        "mode": contract["mode"],
        "policy_id": "POLICY:EITI_LIMEIRA",
        "anchors": {
            "planning_policy": {
                "source_document_id": ppa_2026[0]["source"]["document_id"],
                "source_role": ppa_2026[0]["source"]["source_role"],
                "qualified_policy_group_count": len(ppa_policy_groups),
                "stable_key_pairs": [
                    {"key_type": key_type, "value": value}
                    for key_type, value in sorted(_all_pairs(ppa_policy_groups))
                ],
            },
            "budget_authorization": {
                "source_document_id": loa["research_digest"]["source"]["document_id"],
                "source_role": loa["research_digest"]["source"]["source_role"],
                "segment_count": len(loa_groups),
                "stable_key_pair_count": len(_all_pairs(loa_groups)),
                "authorization_observation_count": loa["authorization_observation_count"],
            },
            "policy_finance_reporting": {
                "source_document_id": siope["research_digest"]["source"]["document_id"],
                "source_role": siope["research_digest"]["source"]["source_role"],
                "qualified_policy_group_count": len(siope_policy_groups),
                "reporting_identity": siope["reporting_identity"]["status"],
                "stable_accounting_key_found": False,
            },
        },
        "same_dimension_shared_keys": {
            "ppa_loa": ppa_loa,
            "ppa_siope": ppa_siope,
            "loa_siope": loa_siope,
        },
        "same_value_different_dimension_observations": cross_dimension,
        "rejected_shared_keys": rejected,
        "cross_document_financial_identity_candidates": candidates,
        "financial_identity": {
            "status": "UNKNOWN",
            "promotion_performed": False,
            "reason": "NO_ADMISSIBLE_POLICY_SPECIFIC_STABLE_ACCOUNTING_BRIDGE",
        },
        "transaction_identity": {
            "status": expected["transaction_identity"],
            "promotion_performed": False,
            "reason": "NO_POLICY_SPECIFIC_STABLE_ACCOUNTING_KEY_AND_NO_EVENT_LEVEL_EXECUTION_CHAIN",
        },
        "legacy_clues": deepcopy(contract["legacy_clues"]),
        "acquisition_packet": {
            "priority_order": deepcopy(acquisition["priority_order"]),
            "immediate_unlock_requirements": deepcopy(acquisition["immediate_unlock_requirements"]),
            "transaction_chain_requirements": deepcopy(acquisition["transaction_chain_requirements"]),
            "desirable_identity_dimensions": deepcopy(acquisition["desirable_identity_dimensions"]),
            "accepted_policy_markers": deepcopy(acquisition["accepted_policy_markers"]),
            "task051_identity_minimum_fields": deepcopy(task051["identity_minimum_fields"]),
            "next_gate_objective": "FIND_PRIMARY_GRANULAR_RECORD_BINDING_POLICY_MARKER_TO_STABLE_ACCOUNTING_IDENTIFIER_AND_EXECUTION_EVENT",
        },
        "forbidden_fallbacks": [
            "PROGRAM_2001_TOTAL",
            "GENERIC_ACTION_2690",
            "GENERIC_ACTION_2720",
            "TEXT_SIMILARITY",
            "AMOUNT_EQUALITY",
            "FOMENTO_ETI_REPORTING_BUCKET_AS_TRANSACTION_IDENTITY",
            "LEGACY_2607004_WITHOUT_PRIMARY_POLICY_AND_EVENT_BINDING",
        ],
        "resolution_status": expected["resolution_status"],
        "persistence_authorized": False,
        "effects": {key: 0 for key in contract["remote_effects"]},
    }
    return {
        **resolution_core,
        "resolution_sha256": sha256(_canonical_bytes(resolution_core)).hexdigest(),
    }


def load_resolver_contract(path: str | Path, *, root: str | Path) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CrossDocumentFinancialIdentityResolverStop("TASK122_CONTRACT_MISSING") from exc
    except json.JSONDecodeError as exc:
        raise CrossDocumentFinancialIdentityResolverStop("TASK122_CONTRACT_JSON") from exc
    _require(isinstance(data, dict), "TASK122_CONTRACT_OBJECT")
    return validate_contract(data, root=root)

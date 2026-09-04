from __future__ import annotations

from copy import deepcopy
from hashlib import sha1, sha256
import json
from pathlib import Path
from typing import Any

from robo_dados_publicos.research.research_ephemeral_digest import (
    digest_research_segments,
    load_contract as load_research_digest_contract,
)


class LoaResearchDigestAdapterStop(RuntimeError):
    """Fail-closed T0 LOA adapter error."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise LoaResearchDigestAdapterStop(code)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _git_blob_sha(raw: bytes) -> str:
    return sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def _load_pinned(path: Path, expected_blob: str, *, code: str) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise LoaResearchDigestAdapterStop(code) from exc
    _require(_git_blob_sha(raw) == expected_blob, code)
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LoaResearchDigestAdapterStop(code) from exc
    _require(isinstance(data, dict), code)
    return data


def validate_contract(contract: dict[str, Any], *, root: str | Path) -> dict[str, Any]:
    _require(contract.get("schema") == "LOA_RESEARCH_DIGEST_ADAPTER_V1", "TASK119_SCHEMA")
    _require(contract.get("mode") == "T0_OFFLINE_VERSIONED_LOA_EVIDENCE_ADAPTER", "TASK119_MODE")
    _require(all(value is False for value in (contract.get("remote_effects") or {}).values()), "TASK119_REMOTE_EFFECT")

    source = contract.get("source") or {}
    _require(source.get("document_id") == "DOC:LOA_7223_2025", "TASK119_DOCUMENT")
    _require(source.get("source_role") == "BUDGET_PRIMARY", "TASK119_SOURCE_ROLE")
    _require(source.get("source_family") == "LOA", "TASK119_SOURCE_FAMILY")
    _require(source.get("required_source_sha256") == "37ea54d85cc5428622b296881a279a17e1aeefd7574576e7a3414443bbee64c4", "TASK119_SOURCE_SHA")

    expected = contract.get("expected") or {}
    _require(expected.get("validated_action_records") == 2, "TASK119_ACTION_COUNT")
    _require(expected.get("total_segments") == 10, "TASK119_SEGMENT_COUNT")
    _require(expected.get("financial_identity_candidates") == 0, "TASK119_FINANCIAL_CANDIDATE_EXPECTATION")

    monetary = contract.get("monetary_semantics") or {}
    _require(monetary.get("appropriation_maps_to") == "AUTHORIZATION", "TASK119_APPROPRIATION_STAGE")
    _require(monetary.get("expense_group_component_maps_to") == "AUTHORIZATION", "TASK119_EXPENSE_GROUP_STAGE")
    _require(monetary.get("funding_source_component_maps_to") == "AUTHORIZATION", "TASK119_FUNDING_STAGE")
    for key in ("commitment_allowed","liquidation_allowed","payment_allowed","amount_equality_creates_policy_identity"):
        _require(monetary.get(key) is False, f"TASK119_MONETARY_{key.upper()}")

    identity = contract.get("identity_semantics") or {}
    _require(identity.get("program_2001_is_eiti") is False, "TASK119_PROGRAM_IDENTITY")
    _require(identity.get("generic_action_2690_is_eiti") is False, "TASK119_ACTION2690_IDENTITY")
    _require(identity.get("generic_action_2720_is_eiti") is False, "TASK119_ACTION2720_IDENTITY")
    _require(identity.get("generic_action_or_program_total_attribution") == "FORBIDDEN", "TASK119_GENERIC_ATTRIBUTION")

    divergence = contract.get("divergence_guard") or {}
    _require(divergence.get("required") is True, "TASK119_DIVERGENCE_REQUIRED")
    _require(divergence.get("pages") == [173, 174], "TASK119_DIVERGENCE_PAGES")
    _require(divergence.get("text_layer_amount_brl") == 29000000, "TASK119_DIVERGENCE_TEXT")
    _require(divergence.get("visual_source_amount_brl") == divergence.get("canonical_selected_amount_brl") == 28000000, "TASK119_DIVERGENCE_VISUAL")
    _require(divergence.get("silent_repair") is False, "TASK119_DIVERGENCE_SILENT_REPAIR")

    root = Path(root)
    research = contract.get("research_digest_contract") or {}
    research_path = root / str(research.get("path") or "")
    research_raw = research_path.read_bytes()
    _require(_git_blob_sha(research_raw) == research.get("git_blob_sha"), "TASK119_RESEARCH_CONTRACT_BLOB")
    research_contract = load_research_digest_contract(research_path, root=root)
    _require(research.get("policy_profile") in research_contract["policy_profiles"], "TASK119_PROFILE")

    input_meta = contract.get("input") or {}
    _load_pinned(
        root / str(input_meta.get("task048_path") or ""),
        str(input_meta.get("task048_git_blob_sha") or ""),
        code="TASK119_TASK048_BLOB",
    )
    return contract


def _base_keys(action: dict[str, Any]) -> list[dict[str, str]]:
    parts = str(action.get("action_code") or "").split(".")
    _require(len(parts) == 4, "TASK119_ACTION_CODE_SHAPE")
    function, subfunction, program, action_code = parts
    _require(function == str(action.get("function")), "TASK119_ACTION_FUNCTION")
    _require(subfunction == str(action.get("subfunction")), "TASK119_ACTION_SUBFUNCTION")
    _require(program == str(action.get("program_code")), "TASK119_ACTION_PROGRAM")
    return [
        {"key_type":"org","value":str(action["organ_code"]),"stability":"EXPLICIT_SOURCE_FIELD"},
        {"key_type":"unit","value":str(action["unit_code"]),"stability":"EXPLICIT_SOURCE_FIELD"},
        {"key_type":"function","value":function,"stability":"EXPLICIT_SOURCE_FIELD"},
        {"key_type":"subfunction","value":subfunction,"stability":"EXPLICIT_SOURCE_FIELD"},
        {"key_type":"program","value":program,"stability":"EXPLICIT_SOURCE_FIELD"},
        {"key_type":"action","value":action_code,"stability":"EXPLICIT_SOURCE_FIELD"},
    ]


def _segment(
    *,
    segment_id: str,
    text: str,
    pages: list[int],
    source_sha256: str,
    representation_level: str,
    keys: list[dict[str, str]],
    amount: int,
    validation: str,
) -> dict[str, Any]:
    _require(isinstance(amount, int) and not isinstance(amount, bool) and amount >= 0, "TASK119_AMOUNT")
    return {
        "segment_id": segment_id,
        "text": text,
        "locator": {
            "task": "TASK_048",
            "coordinate_system": "JOURNAL_EDITION_PDF_PAGE",
            "pages": list(pages),
            "source_sha256": source_sha256,
            "representation": "DETERMINISTIC_SERIALIZATION_OF_DIRECTLY_VALIDATED_PRIMARY_FIELDS",
            "representation_level": representation_level,
            "validation": validation,
        },
        "structured": {
            "accounting_keys": deepcopy(keys),
            "amounts": [
                {
                    "amount_brl": str(amount),
                    "execution_stage": "AUTHORIZATION",
                }
            ],
        },
    }


def build_loa_research_packet(
    contract: dict[str, Any],
    *,
    root: str | Path,
) -> dict[str, Any]:
    contract = validate_contract(contract, root=root)
    root = Path(root)
    research_path = root / contract["research_digest_contract"]["path"]
    research_contract = load_research_digest_contract(research_path, root=root)
    input_meta = contract["input"]
    task048 = _load_pinned(
        root / input_meta["task048_path"],
        input_meta["task048_git_blob_sha"],
        code="TASK119_TASK048_BLOB",
    )

    _require(task048.get("result") == "PASS_TASK048_LOA_SCOPED_SILVER_V2_CANDIDATE_READY_NO_WRITE", "TASK119_TASK048_STATUS")
    payload = task048.get("candidate_payload") or {}
    source = payload.get("source") or {}
    _require(source.get("sha256") == contract["source"]["required_source_sha256"], "TASK119_TASK048_SOURCE_SHA")
    _require((payload.get("legal_instrument") or {}).get("exercise") == 2026, "TASK119_EXERCISE")

    linkage = task048.get("eiti_linkage_assessment") or {}
    _require(linkage.get("program_to_explicit_eiti_action_or_subaction") == "NOT_PROVEN", "TASK119_LINKAGE")
    _require(linkage.get("selected_action_2690_eiti_specific") is False, "TASK119_2690")
    _require(linkage.get("selected_action_2720_eiti_specific") is False, "TASK119_2720")
    _require(linkage.get("generic_action_or_program_total_attribution_to_eiti") == "FORBIDDEN", "TASK119_GENERIC_FORBIDDEN")

    divergence = payload.get("material_text_visual_divergence") or {}
    expected_divergence = contract["divergence_guard"]
    _require(divergence.get("observed") is True, "TASK119_DIVERGENCE_OBSERVED")
    _require(divergence.get("pages") == expected_divergence["pages"], "TASK119_DIVERGENCE_SOURCE_PAGES")
    _require(divergence.get("text_layer_amount_brl") == expected_divergence["text_layer_amount_brl"], "TASK119_DIVERGENCE_SOURCE_TEXT")
    _require(divergence.get("visual_source_amount_brl") == expected_divergence["visual_source_amount_brl"], "TASK119_DIVERGENCE_SOURCE_VISUAL")
    _require(divergence.get("silent_repair") is False, "TASK119_DIVERGENCE_SOURCE_REPAIR")

    actions = payload.get("validated_action_records") or []
    _require(len(actions) == contract["expected"]["validated_action_records"], "TASK119_ACTION_RECORDS")
    segments: list[dict[str, Any]] = []
    action_total_count = 0
    expense_group_count = 0
    funding_source_count = 0

    for action in actions:
        _require(action.get("eiti_specific") is False, "TASK119_ACTION_EITI_SPECIFIC")
        _require(str(action.get("validation") or "").startswith("DIRECT_PRIMARY_JOM_VISUAL_SOURCE"), "TASK119_ACTION_VALIDATION")
        _require(action.get("execution_stage") == "NOT_APPLICABLE_TO_LOA_ENACTMENT_READ", "TASK119_SOURCE_EXECUTION_STAGE")
        base_keys = _base_keys(action)
        action_short = str(action["action_code"]).split(".")[-1]
        pages = list(action["context_pages"])
        total = action["appropriation_brl"]

        segments.append(
            _segment(
                segment_id=f"SEG:LOA2026_ACTION_{action_short}_TOTAL",
                text=" ".join([
                    str(action["label"]),
                    str(action["organ_name"]),
                    str(action["unit_name"]),
                    str(action["sphere"]),
                ]),
                pages=pages,
                source_sha256=source["sha256"],
                representation_level="ACTION_TOTAL",
                keys=base_keys,
                amount=total,
                validation=action["validation"],
            )
        )
        action_total_count += 1

        groups = action.get("expense_group_breakdown_brl") or {}
        _require(groups and sum(groups.values()) == total, "TASK119_EXPENSE_GROUP_SUM")
        for index, (group, amount) in enumerate(sorted(groups.items()), start=1):
            segments.append(
                _segment(
                    segment_id=f"SEG:LOA2026_ACTION_{action_short}_GROUP_{index:02d}",
                    text=" ".join([str(action["label"]), str(group)]),
                    pages=pages,
                    source_sha256=source["sha256"],
                    representation_level="EXPENSE_GROUP_COMPONENT",
                    keys=base_keys + [
                        {"key_type":"expense_group","value":str(group),"stability":"EXPLICIT_SOURCE_FIELD"}
                    ],
                    amount=amount,
                    validation=action["validation"],
                )
            )
            expense_group_count += 1

        sources = action.get("funding_sources_brl") or {}
        _require(sources and sum(sources.values()) == total, "TASK119_FUNDING_SOURCE_SUM")
        for index, (funding, amount) in enumerate(sorted(sources.items()), start=1):
            segments.append(
                _segment(
                    segment_id=f"SEG:LOA2026_ACTION_{action_short}_FUND_{index:02d}",
                    text=" ".join([str(action["label"]), str(funding)]),
                    pages=pages,
                    source_sha256=source["sha256"],
                    representation_level="FUNDING_SOURCE_COMPONENT",
                    keys=base_keys + [
                        {"key_type":"funding_source","value":str(funding),"stability":"EXPLICIT_SOURCE_FIELD"}
                    ],
                    amount=amount,
                    validation=action["validation"],
                )
            )
            funding_source_count += 1

    _require(action_total_count == contract["expected"]["action_total_segments"], "TASK119_ACTION_TOTAL_COUNT")
    _require(expense_group_count == contract["expected"]["expense_group_segments"], "TASK119_GROUP_COUNT")
    _require(funding_source_count == contract["expected"]["funding_source_segments"], "TASK119_FUND_COUNT")
    _require(len(segments) == contract["expected"]["total_segments"], "TASK119_TOTAL_SEGMENTS")

    packet = {
        "schema": "RESEARCH_EPHEMERAL_DIGEST_INPUT_V1",
        "policy_profile": contract["research_digest_contract"]["policy_profile"],
        "source": {
            "document_id": contract["source"]["document_id"],
            "source_role": contract["source"]["source_role"],
            "source_family": contract["source"]["source_family"],
            "source_sha256": source["sha256"],
            "adapter_contract": contract["schema"],
        },
        "segments": segments,
        "remote_effects_authorized": {
            key: False for key in research_contract["remote_effects"]
        },
    }
    digest = digest_research_segments(packet, research_contract, root=root)
    _require(
        len(digest["financial_identity_candidates"])
        == contract["expected"]["financial_identity_candidates"],
        "TASK119_UNEXPECTED_FINANCIAL_CANDIDATE",
    )
    _require("QUALIFIED_POLICY_SIGNAL_NOT_OBSERVED" in digest["evidence_gaps"], "TASK119_POLICY_GAP_MISSING")

    core = {
        "schema": "LOA_RESEARCH_DIGEST_ADAPTER_RESULT_V1",
        "mode": contract["mode"],
        "packet": packet,
        "research_digest": digest,
        "authorization_observation_count": len(segments),
        "action_total_count": action_total_count,
        "expense_group_component_count": expense_group_count,
        "funding_source_component_count": funding_source_count,
        "material_text_visual_divergence": deepcopy(divergence),
        "canonical_action_2720_appropriation_brl": expected_divergence["canonical_selected_amount_brl"],
        "financial_identity_promoted": False,
        "persistence_authorized": False,
        "effects": {key: 0 for key in contract["remote_effects"]},
        "status": "PASS_TASK119_LOA_REPOSITORY_EVIDENCE_ADAPTER",
    }
    return {
        **core,
        "result_sha256": sha256(_canonical_bytes(core)).hexdigest(),
    }


def load_adapter_contract(path: str | Path, *, root: str | Path) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LoaResearchDigestAdapterStop("TASK119_CONTRACT_MISSING") from exc
    except json.JSONDecodeError as exc:
        raise LoaResearchDigestAdapterStop("TASK119_CONTRACT_JSON") from exc
    _require(isinstance(data, dict), "TASK119_CONTRACT_OBJECT")
    return validate_contract(data, root=root)

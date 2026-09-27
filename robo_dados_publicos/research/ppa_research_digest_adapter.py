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


class PpaResearchDigestAdapterStop(RuntimeError):
    """Fail-closed T0 adapter error."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise PpaResearchDigestAdapterStop(code)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _git_blob_sha(raw: bytes) -> str:
    return sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def _load_pinned(root: Path, meta: dict[str, Any], *, code: str) -> dict[str, Any]:
    path = root / str(meta.get("path") or "")
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise PpaResearchDigestAdapterStop(code) from exc
    _require(_git_blob_sha(raw) == meta.get("git_blob_sha"), code)
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PpaResearchDigestAdapterStop(code) from exc
    _require(isinstance(data, dict), code)
    return data


def validate_contract(contract: dict[str, Any], *, root: str | Path) -> dict[str, Any]:
    _require(contract.get("schema") == "PPA_RESEARCH_DIGEST_ADAPTER_V1", "TASK117_SCHEMA")
    _require(contract.get("mode") == "T0_OFFLINE_VERSIONED_PPA_EVIDENCE_ADAPTER", "TASK117_MODE")
    _require(set(contract.get("periods") or {}) == {"2022-2025", "2026-2029"}, "TASK117_PERIOD_SET")
    _require((contract.get("output") or {}).get("expected_packet_count") == 2, "TASK117_PACKET_COUNT")
    _require((contract.get("output") or {}).get("persistence_authorized") is False, "TASK117_PERSISTENCE")
    _require((contract.get("output") or {}).get("automatic_financial_identity_promotion") is False, "TASK117_AUTO_PROMOTION")
    _require(all(value is False for value in (contract.get("remote_effects") or {}).values()), "TASK117_REMOTE_EFFECT")

    monetary = contract.get("monetary_semantics") or {}
    for key in (
        "ppa_projected_values_are_execution_amounts",
        "ppa_projected_values_are_loa_authorization_amounts",
        "emit_task116_amount_observations",
    ):
        _require(monetary.get(key) is False, f"TASK117_MONETARY_{key.upper()}")

    root = Path(root)
    research_meta = contract.get("research_digest_contract") or {}
    path = root / str(research_meta.get("path") or "")
    raw = path.read_bytes()
    _require(_git_blob_sha(raw) == research_meta.get("git_blob_sha"), "TASK117_RESEARCH_CONTRACT_BLOB")
    research_contract = load_research_digest_contract(path, root=root)
    _require(research_meta.get("policy_profile") in research_contract["policy_profiles"], "TASK117_POLICY_PROFILE")

    inputs = contract.get("inputs") or {}
    _require(set(inputs) == {"task107", "task041", "task049"}, "TASK117_INPUT_SET")
    for name in ("task107", "task041", "task049"):
        _load_pinned(root, inputs[name], code=f"TASK117_{name.upper()}_BLOB")
    return contract


def _remote_effect_packet(research_contract: dict[str, Any]) -> dict[str, bool]:
    return {key: False for key in research_contract["remote_effects"]}


def build_ppa_research_packets(
    contract: dict[str, Any],
    *,
    root: str | Path,
) -> dict[str, Any]:
    contract = validate_contract(contract, root=root)
    root = Path(root)
    research_path = root / contract["research_digest_contract"]["path"]
    research_contract = load_research_digest_contract(research_path, root=root)

    task107 = _load_pinned(root, contract["inputs"]["task107"], code="TASK117_TASK107_BLOB")
    task041 = _load_pinned(root, contract["inputs"]["task041"], code="TASK117_TASK041_BLOB")
    task049 = _load_pinned(root, contract["inputs"]["task049"], code="TASK117_TASK049_BLOB")

    _require(task107.get("overall_status") == "PARTIAL_TASK107_ONE_PRIMARY_PPA_MATCH", "TASK117_TASK107_STATUS")
    period22 = [
        item for item in (task107.get("period_results") or [])
        if item.get("period") == "2022-2025"
    ]
    _require(len(period22) == 1 and period22[0].get("status") == "PRIMARY_MATCH", "TASK117_2022_PRIMARY")
    p22 = period22[0]
    expected22 = contract["periods"]["2022-2025"]
    _require(p22.get("source_sha256") == expected22["required_source_sha256"], "TASK117_2022_SHA")
    _require((p22.get("locator") or {}).get("page") == expected22["required_page"], "TASK117_2022_PAGE")
    excerpt = str(p22.get("direct_evidence_excerpt") or "")
    _require(excerpt.strip() != "", "TASK117_2022_EXCERPT")

    packet22 = {
        "schema": "RESEARCH_EPHEMERAL_DIGEST_INPUT_V1",
        "policy_profile": contract["research_digest_contract"]["policy_profile"],
        "source": {
            "document_id": expected22["document_id"],
            "source_role": expected22["source_role"],
            "source_family": expected22["source_family"],
            "source_sha256": p22["source_sha256"],
            "adapter_contract": contract["schema"],
        },
        "segments": [
            {
                "segment_id": "SEG:PPA_2022_2025_PAGE_23",
                "text": excerpt,
                "locator": {
                    "task": "TASK_107",
                    "coordinate_system": p22["locator"]["coordinate_system"],
                    "page": p22["locator"]["page"],
                    "page_text_sha256": p22["locator"]["page_text_sha256"],
                    "representation": expected22["representation"],
                },
                "structured": {
                    "accounting_keys": [],
                    "amounts": [],
                },
            }
        ],
        "remote_effects_authorized": _remote_effect_packet(research_contract),
    }

    ppa = task041.get("ppa_candidate") or {}
    source = ppa.get("source") or {}
    program = ppa.get("program_2001") or {}
    indicator = program.get("indicator") or {}
    expected26 = contract["periods"]["2026-2029"]
    _require(source.get("sha256") == expected26["required_source_sha256"], "TASK117_2026_SHA")
    _require(program.get("program_code") == "2001", "TASK117_2026_PROGRAM")
    _require(indicator.get("source_page") == expected26["indicator_page"], "TASK117_2026_INDICATOR_PAGE")
    _require(indicator.get("validation") == "DIRECT_PRIMARY_JOM_VISUAL_SOURCE_VERIFICATION", "TASK117_2026_INDICATOR_VALIDATION")

    indicator_text = " ".join(
        [
            str(program.get("program_name") or ""),
            str(program.get("responsible_unit_name") or ""),
            str(indicator.get("name") or ""),
            str(indicator.get("unit") or ""),
        ]
    ).strip()
    _require(indicator_text != "", "TASK117_2026_INDICATOR_TEXT")

    indicator_segment = {
        "segment_id": "SEG:PPA_2026_2029_PROGRAM_2001_INDICATOR",
        "text": indicator_text,
        "locator": {
            "task": "TASK_041",
            "coordinate_system": "JOURNAL_EDITION_PDF_PAGE",
            "page": indicator["source_page"],
            "source_sha256": source["sha256"],
            "representation": expected26["representation"],
            "validation": indicator["validation"],
        },
        "structured": {
            "accounting_keys": [
                {
                    "key_type": "program",
                    "value": str(program["program_code"]),
                    "stability": "EXPLICIT_SOURCE_FIELD",
                },
                {
                    "key_type": "unit",
                    "value": str(program["responsible_unit_code"]),
                    "stability": "EXPLICIT_SOURCE_FIELD",
                },
            ],
            "amounts": [],
        },
    }

    selected = program.get("selected_actions") or []
    _require(len(selected) == expected26["selected_action_count"], "TASK117_2026_ACTION_COUNT")
    action_segments: list[dict[str, Any]] = []
    for index, action in enumerate(selected, start=1):
        _require(action.get("validation") == "DIRECT_PRIMARY_JOM_VISUAL_SOURCE_VERIFICATION", "TASK117_2026_ACTION_VALIDATION")
        _require(action.get("eiti_specific") is False, "TASK117_2026_ACTION_EITI_FLAG")
        action_segments.append(
            {
                "segment_id": f"SEG:PPA_2026_2029_ACTION_{index:02d}",
                "text": " ".join(
                    [
                        str(action.get("label") or ""),
                        str(action.get("education_level") or ""),
                    ]
                ).strip(),
                "locator": {
                    "task": "TASK_041",
                    "coordinate_system": "JOURNAL_EDITION_PDF_PAGE",
                    "page": action["page"],
                    "source_sha256": source["sha256"],
                    "representation": expected26["representation"],
                    "validation": action["validation"],
                    "eiti_specific": False,
                },
                "structured": {
                    "accounting_keys": [
                        {"key_type": "program", "value": "2001", "stability": "EXPLICIT_SOURCE_FIELD"},
                        {"key_type": "action", "value": str(action["action_code"]), "stability": "EXPLICIT_SOURCE_FIELD"},
                        {"key_type": "function", "value": str(action["function"]), "stability": "EXPLICIT_SOURCE_FIELD"},
                        {"key_type": "subfunction", "value": str(action["subfunction"]), "stability": "EXPLICIT_SOURCE_FIELD"},
                    ],
                    "amounts": [],
                },
            }
        )

    packet26 = {
        "schema": "RESEARCH_EPHEMERAL_DIGEST_INPUT_V1",
        "policy_profile": contract["research_digest_contract"]["policy_profile"],
        "source": {
            "document_id": expected26["document_id"],
            "source_role": expected26["source_role"],
            "source_family": expected26["source_family"],
            "source_sha256": source["sha256"],
            "adapter_contract": contract["schema"],
        },
        "segments": [indicator_segment, *action_segments],
        "remote_effects_authorized": _remote_effect_packet(research_contract),
    }

    _require((task049.get("scope") or {}).get("source_sha256") == source["sha256"], "TASK117_TASK049_SOURCE")
    _require((task049.get("explicit_eiti_action_label_matches") or []) == [], "TASK117_TASK049_MATCHES")
    conclusion = task049.get("conclusion") or {}
    boundary = task049.get("interpretation_boundary") or {}
    _require(conclusion.get("program_to_explicit_eiti_action_linkage") == "NOT_PROVEN", "TASK117_TASK049_LINK")
    _require(conclusion.get("program_or_generic_action_financial_attribution_to_eiti") == "FORBIDDEN", "TASK117_TASK049_FINANCIAL")
    _require(boundary.get("does_not_prove_no_eiti_spending_exists") is True, "TASK117_TASK049_NO_ABSENCE")

    negative = {
        "search_id": "SEARCH:PPA2001_EITI_ACTION_LABELS",
        "scope": deepcopy(task049["scope"]),
        "terms_checked": deepcopy(task049["terms_checked_in_action_labels"]),
        "rows_checked": len(task049["action_rows"]),
        "result": "NO_MATCH",
        "exhaustive_within_declared_action_table_scope": True,
        "proves_no_eiti_spending": False,
        "financial_attribution_to_generic_actions": "FORBIDDEN",
    }

    packets = [packet22, packet26]
    digests = [
        digest_research_segments(packet, research_contract, root=root)
        for packet in packets
    ]
    _require(all(result["financial_identity_candidates"] == [] for result in digests), "TASK117_UNEXPECTED_FINANCIAL_CANDIDATE")

    core = {
        "schema": "PPA_RESEARCH_DIGEST_ADAPTER_RESULT_V1",
        "mode": contract["mode"],
        "packet_count": len(packets),
        "packets": packets,
        "research_digests": digests,
        "negative_action_label_search": negative,
        "planned_values_emitted_as_execution_amounts": False,
        "persistence_authorized": False,
        "financial_identity_promoted": False,
        "effects": {key: 0 for key in contract["remote_effects"]},
        "status": "PASS_TASK117_PPA_REPOSITORY_EVIDENCE_ADAPTER",
    }
    return {
        **core,
        "result_sha256": sha256(_canonical_bytes(core)).hexdigest(),
    }


def load_adapter_contract(path: str | Path, *, root: str | Path) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PpaResearchDigestAdapterStop("TASK117_CONTRACT_MISSING") from exc
    except json.JSONDecodeError as exc:
        raise PpaResearchDigestAdapterStop("TASK117_CONTRACT_JSON") from exc
    _require(isinstance(data, dict), "TASK117_CONTRACT_OBJECT")
    return validate_contract(data, root=root)

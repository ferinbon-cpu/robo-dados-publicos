from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, InvalidOperation
from hashlib import sha1, sha256
import json
from pathlib import Path
import re
from typing import Any
import unicodedata

from robo_dados_publicos.research.budget_ledger import IDENTITY_DIMENSIONS
from robo_dados_publicos.research.evidence_semantics import SOURCE_ROLES, source_role_max_status


class ResearchEphemeralDigestStop(RuntimeError):
    """Fail-closed validation error for the T0 research digest."""


_SEGMENT_ID_RE = re.compile(r"^SEG:[A-Za-z0-9][A-Za-z0-9._:-]{0,199}$")
_DOC_ID_RE = re.compile(r"^DOC:[A-Za-z0-9][A-Za-z0-9._:-]{0,199}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_MONEY_RE = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]{1,2})?$")

ABC_FAMILIES = (
    "A_CANONICAL_POLICY_IDENTIFIERS",
    "B_LOCAL_PLANNING_AND_NORMATIVE_ALIASES",
    "C_OPERATIONAL_OFFER_AND_JOURNEY_SIGNALS",
)
D_FAMILY = "D_FINANCING_AND_INDUCTION_SIGNALS"
E_FAMILY = "E_ACCOUNTING_AND_PLANNING_LINKAGE_KEYS"
ALL_FAMILIES = ABC_FAMILIES + (D_FAMILY, E_FAMILY)


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ResearchEphemeralDigestStop(code)


def _canonical_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _git_blob_sha(raw: bytes) -> str:
    return sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def normalize_research_text(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^A-Za-z0-9]+", " ", text.upper())
    return " ".join(text.split())


def _money(value: object, *, code: str) -> str:
    _require(not isinstance(value, (bool, float)), code)
    text = str(value or "")
    _require(bool(_MONEY_RE.fullmatch(text)), code)
    try:
        amount = Decimal(text)
    except InvalidOperation as exc:
        raise ResearchEphemeralDigestStop(code) from exc
    _require(amount >= Decimal("0"), code)
    return f"{amount.quantize(Decimal('0.01')):.2f}"


def _load_json(path: str | Path, *, code: str) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ResearchEphemeralDigestStop(code) from exc
    except json.JSONDecodeError as exc:
        raise ResearchEphemeralDigestStop(code) from exc
    _require(isinstance(data, dict), code)
    return data


def validate_contract(
    contract: dict[str, Any],
    *,
    root: str | Path,
) -> dict[str, Any]:
    _require(contract.get("schema") == "RESEARCH_EPHEMERAL_DIGEST_CONTRACT_V1", "TASK116_CONTRACT_SCHEMA")
    _require(contract.get("mode") == "T0_OFFLINE_RESEARCH_EPHEMERAL_DIGEST", "TASK116_CONTRACT_MODE")
    remote = contract.get("remote_effects") or {}
    _require(remote and all(value is False for value in remote.values()), "TASK116_REMOTE_EFFECT")

    limits = contract.get("limits") or {}
    expected_limits = {
        "max_segments": (1, 400),
        "max_segment_chars": (1, 12000),
        "max_total_chars": (1, 1000000),
        "max_hits_per_segment": (1, 128),
        "max_accounting_keys_per_segment": (1, 32),
        "max_amount_observations_per_segment": (1, 32),
    }
    for key, (low, high) in expected_limits.items():
        value = limits.get(key)
        _require(isinstance(value, int) and not isinstance(value, bool) and low <= value <= high, f"TASK116_LIMIT_{key.upper()}")

    root = Path(root)
    profiles = contract.get("policy_profiles") or {}
    _require(set(profiles) == {"EITI_LIMEIRA"}, "TASK116_PROFILE_SET")
    profile = profiles["EITI_LIMEIRA"]
    _require(profile.get("policy_id") == "POLICY:EITI_LIMEIRA", "TASK116_POLICY_ID")

    pinned = (
        ("task055a_path", "task055a_git_blob_sha", "TASK116_TASK055A_BLOB"),
        ("task113_abc_path", "task113_abc_git_blob_sha", "TASK116_TASK113_BLOB"),
    )
    loaded: dict[str, dict[str, Any]] = {}
    for path_key, sha_key, code in pinned:
        path = root / str(profile.get(path_key) or "")
        raw = path.read_bytes()
        _require(_git_blob_sha(raw) == profile.get(sha_key), code)
        loaded[path_key] = json.loads(raw.decode("utf-8"))

    registry_path = root / str(contract.get("source_family_registry") or "")
    registry_raw = registry_path.read_bytes()
    _require(_git_blob_sha(registry_raw) == contract.get("source_family_registry_git_blob_sha"), "TASK116_FAMILY_REGISTRY_BLOB")
    registry = json.loads(registry_raw.decode("utf-8"))
    _require(isinstance(registry.get("families"), dict) and registry["families"], "TASK116_FAMILY_REGISTRY")

    ledger_path = root / str(contract.get("accounting_identity_contract") or "")
    ledger_raw = ledger_path.read_bytes()
    _require(_git_blob_sha(ledger_raw) == contract.get("accounting_identity_contract_git_blob_sha"), "TASK116_LEDGER_BLOB")
    ledger = json.loads(ledger_raw.decode("utf-8"))
    _require(tuple(ledger.get("identity_dimensions") or ()) == IDENTITY_DIMENSIONS, "TASK116_LEDGER_IDENTITY_DIMENSIONS")

    task055a = loaded["task055a_path"]
    task113 = loaded["task113_abc_path"]
    ontology = task055a.get("ontology") or {}
    _require(set(ontology) == set(ALL_FAMILIES), "TASK116_ONTOLOGY_FAMILIES")
    counts = {family: len(ontology.get(family) or []) for family in ALL_FAMILIES}
    _require(counts == profile.get("expected_family_counts"), "TASK116_ONTOLOGY_COUNTS")
    _require(sum(counts.values()) == profile.get("expected_total_terms") == 63, "TASK116_ONTOLOGY_TOTAL")

    abc = task113.get("families") or {}
    _require(set(abc) == set(ABC_FAMILIES), "TASK116_TASK113_ABC_SET")
    for family in ABC_FAMILIES:
        observed = [str(item.get("term") or "") for item in abc[family]]
        _require(observed == ontology[family], f"TASK116_TASK113_TERM_DRIFT_{family}")

    key_types = tuple(contract.get("accounting_key_types") or ())
    _require(bool(key_types) and len(key_types) == len(set(key_types)), "TASK116_ACCOUNTING_KEY_TYPES")
    _require(set(key_types).issubset(set(IDENTITY_DIMENSIONS) - {"entity", "fiscal_year"}), "TASK116_ACCOUNTING_KEY_TYPE_UNKNOWN")
    _require(set(contract.get("accounting_key_stability") or ()) == {"EXPLICIT_SOURCE_FIELD", "ADAPTER_PROVEN_STABLE"}, "TASK116_ACCOUNTING_STABILITY")
    _require(set(contract.get("execution_stages") or ()) == {"AUTHORIZATION", "COMMITMENT", "LIQUIDATION", "PAYMENT", "REPORTING_BUCKET"}, "TASK116_EXECUTION_STAGES")

    matching = contract.get("matching_rules") or {}
    _require(matching.get("d_terms_alone_create_policy_signal") is False, "TASK116_D_POLICY_GUARD")
    _require(matching.get("e_terms_alone_create_policy_signal") is False, "TASK116_E_POLICY_GUARD")
    _require(matching.get("accounting_key_alone_creates_policy_identity") is False, "TASK116_KEY_POLICY_GUARD")
    _require(matching.get("amount_equality_alone_creates_policy_identity") is False, "TASK116_AMOUNT_POLICY_GUARD")
    _require(matching.get("candidate_financial_bridge_scope") == "SAME_SEGMENT_ONLY", "TASK116_BRIDGE_SCOPE")
    _require(matching.get("candidate_bridge_status") == "CANDIDATE", "TASK116_BRIDGE_STATUS")
    _require(matching.get("automatic_promotion") is False, "TASK116_AUTO_PROMOTION")
    _require(matching.get("causal_inference") is False, "TASK116_CAUSAL_GUARD")
    return contract


def _ontology_entries(task055a: dict[str, Any], task113: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    ontology = task055a["ontology"]
    out: dict[str, list[dict[str, Any]]] = {}
    for family in ABC_FAMILIES:
        out[family] = [
            {
                "term": item["term"],
                "strength": item["strength"],
                "requires_companion": item["requires_companion"],
            }
            for item in task113["families"][family]
        ]
    out[D_FAMILY] = [
        {"term": term, "strength": "FINANCING_SIGNAL", "requires_companion": False}
        for term in ontology[D_FAMILY]
    ]
    out[E_FAMILY] = [
        {"term": term, "strength": "ACCOUNTING_LINKAGE_TERM", "requires_companion": False}
        for term in ontology[E_FAMILY]
    ]
    return out


def _validate_input(
    packet: dict[str, Any],
    *,
    contract: dict[str, Any],
    family_registry: dict[str, Any],
) -> list[dict[str, Any]]:
    _require(isinstance(packet, dict), "TASK116_INPUT_OBJECT")
    _require(packet.get("schema") == "RESEARCH_EPHEMERAL_DIGEST_INPUT_V1", "TASK116_INPUT_SCHEMA")
    profile = str(packet.get("policy_profile") or "")
    _require(profile in contract["policy_profiles"], "TASK116_INPUT_PROFILE")

    source = packet.get("source")
    _require(isinstance(source, dict), "TASK116_SOURCE")
    document_id = str(source.get("document_id") or "")
    _require(bool(_DOC_ID_RE.fullmatch(document_id)), "TASK116_SOURCE_DOCUMENT_ID")
    role = str(source.get("source_role") or "")
    _require(role in SOURCE_ROLES, "TASK116_SOURCE_ROLE")
    family = str(source.get("source_family") or "")
    _require(family in (family_registry.get("families") or {}), "TASK116_SOURCE_FAMILY")
    digest = str(source.get("source_sha256") or "")
    _require(bool(_SHA256_RE.fullmatch(digest)), "TASK116_SOURCE_SHA256")
    _require(bool(str(source.get("adapter_contract") or "").strip()), "TASK116_ADAPTER_CONTRACT")

    effects = packet.get("remote_effects_authorized")
    _require(isinstance(effects, dict) and set(effects) == set(contract["remote_effects"]), "TASK116_INPUT_EFFECT_SET")
    _require(all(value is False for value in effects.values()), "TASK116_INPUT_REMOTE_EFFECT")

    segments = packet.get("segments")
    _require(isinstance(segments, list) and 1 <= len(segments) <= contract["limits"]["max_segments"], "TASK116_SEGMENT_COUNT")
    seen: set[str] = set()
    total_chars = 0
    normalized: list[dict[str, Any]] = []
    for segment in segments:
        _require(isinstance(segment, dict), "TASK116_SEGMENT_OBJECT")
        segment_id = str(segment.get("segment_id") or "")
        _require(bool(_SEGMENT_ID_RE.fullmatch(segment_id)), "TASK116_SEGMENT_ID")
        _require(segment_id not in seen, "TASK116_DUPLICATE_SEGMENT_ID")
        seen.add(segment_id)
        text = segment.get("text")
        _require(isinstance(text, str) and text.strip() != "", "TASK116_SEGMENT_TEXT")
        _require(len(text) <= contract["limits"]["max_segment_chars"], "TASK116_SEGMENT_TOO_LARGE")
        total_chars += len(text)
        _require(total_chars <= contract["limits"]["max_total_chars"], "TASK116_TOTAL_TEXT_TOO_LARGE")
        locator = segment.get("locator")
        _require(isinstance(locator, dict) and locator, "TASK116_SEGMENT_LOCATOR")

        structured = segment.get("structured", {})
        _require(isinstance(structured, dict), "TASK116_STRUCTURED")
        keys = structured.get("accounting_keys", [])
        amounts = structured.get("amounts", [])
        _require(isinstance(keys, list) and len(keys) <= contract["limits"]["max_accounting_keys_per_segment"], "TASK116_ACCOUNTING_KEYS")
        _require(isinstance(amounts, list) and len(amounts) <= contract["limits"]["max_amount_observations_per_segment"], "TASK116_AMOUNTS")

        normalized_keys: list[dict[str, str]] = []
        seen_key_pairs: set[tuple[str, str]] = set()
        for key in keys:
            _require(isinstance(key, dict), "TASK116_ACCOUNTING_KEY_OBJECT")
            key_type = str(key.get("key_type") or "")
            value = str(key.get("value") or "").strip()
            stability = str(key.get("stability") or "")
            _require(key_type in contract["accounting_key_types"], "TASK116_ACCOUNTING_KEY_TYPE")
            _require(value != "" and len(value) <= 200, "TASK116_ACCOUNTING_KEY_VALUE")
            _require(stability in contract["accounting_key_stability"], "TASK116_ACCOUNTING_KEY_STABILITY")
            pair = (key_type, value)
            _require(pair not in seen_key_pairs, "TASK116_DUPLICATE_ACCOUNTING_KEY")
            seen_key_pairs.add(pair)
            normalized_keys.append({"key_type": key_type, "value": value, "stability": stability})

        normalized_amounts: list[dict[str, str]] = []
        for amount in amounts:
            _require(isinstance(amount, dict), "TASK116_AMOUNT_OBJECT")
            stage = str(amount.get("execution_stage") or "")
            _require(stage in contract["execution_stages"], "TASK116_EXECUTION_STAGE")
            normalized_amounts.append({
                "amount_brl": _money(amount.get("amount_brl"), code="TASK116_AMOUNT_BRL"),
                "execution_stage": stage,
            })

        normalized.append({
            "segment_id": segment_id,
            "text": text,
            "locator": deepcopy(locator),
            "structured": {
                "accounting_keys": normalized_keys,
                "amounts": normalized_amounts,
            },
        })
    return normalized


def digest_research_segments(
    packet: dict[str, Any],
    contract: dict[str, Any],
    *,
    root: str | Path,
) -> dict[str, Any]:
    contract = validate_contract(contract, root=root)
    root = Path(root)
    profile_name = str(packet.get("policy_profile") or "")
    _require(profile_name in contract["policy_profiles"], "TASK116_INPUT_PROFILE")
    profile = contract["policy_profiles"][profile_name]

    task055a = _load_json(root / profile["task055a_path"], code="TASK116_TASK055A_JSON")
    task113 = _load_json(root / profile["task113_abc_path"], code="TASK116_TASK113_JSON")
    registry = _load_json(root / contract["source_family_registry"], code="TASK116_FAMILY_REGISTRY_JSON")
    segments = _validate_input(packet, contract=contract, family_registry=registry)
    entries = _ontology_entries(task055a, task113)
    companions = [normalize_research_text(x) for x in (task113.get("companion_context_terms") or [])]

    hits: list[dict[str, Any]] = []
    contexts: list[dict[str, Any]] = []
    bridges: list[dict[str, Any]] = []
    policy_signal_segments: set[str] = set()
    stable_key_segments: set[str] = set()
    amount_segments: set[str] = set()

    for segment in segments:
        normalized_text = normalize_research_text(segment["text"])
        companion_hits = [term for term in companions if term and term in normalized_text]
        segment_hits: list[dict[str, Any]] = []
        qualified_policy_hits: list[dict[str, Any]] = []

        for family in ALL_FAMILIES:
            for entry in entries[family]:
                normalized_term = normalize_research_text(entry["term"])
                if not normalized_term or normalized_term not in normalized_text:
                    continue
                qualified = not entry["requires_companion"] or bool(companion_hits)
                hit = {
                    "segment_id": segment["segment_id"],
                    "family": family,
                    "term": entry["term"],
                    "normalized_term": normalized_term,
                    "strength": entry["strength"],
                    "requires_companion": entry["requires_companion"],
                    "qualified": qualified,
                    "companion_hits": companion_hits[:10] if entry["requires_companion"] else [],
                    "locator": deepcopy(segment["locator"]),
                }
                segment_hits.append(hit)
                if family in ABC_FAMILIES and qualified:
                    qualified_policy_hits.append(hit)

        _require(len(segment_hits) <= contract["limits"]["max_hits_per_segment"], "TASK116_HIT_LIMIT")
        hits.extend(segment_hits)

        keys = segment["structured"]["accounting_keys"]
        amounts = segment["structured"]["amounts"]
        stable_keys = [
            key for key in keys
            if key["stability"] in {"EXPLICIT_SOURCE_FIELD", "ADAPTER_PROVEN_STABLE"}
        ]
        if qualified_policy_hits:
            policy_signal_segments.add(segment["segment_id"])
        if stable_keys:
            stable_key_segments.add(segment["segment_id"])
        if amounts:
            amount_segments.add(segment["segment_id"])

        family_counts = {
            family: sum(1 for hit in segment_hits if hit["family"] == family)
            for family in ALL_FAMILIES
        }
        contexts.append({
            "segment_id": segment["segment_id"],
            "locator": deepcopy(segment["locator"]),
            "family_hit_counts": family_counts,
            "qualified_policy_signal": bool(qualified_policy_hits),
            "qualified_policy_terms": [hit["term"] for hit in qualified_policy_hits],
            "financing_signal_terms": [hit["term"] for hit in segment_hits if hit["family"] == D_FAMILY],
            "accounting_linkage_terms": [hit["term"] for hit in segment_hits if hit["family"] == E_FAMILY],
            "stable_accounting_keys": deepcopy(stable_keys),
            "amount_observations": deepcopy(amounts),
        })

        if qualified_policy_hits and stable_keys and amounts:
            for amount in amounts:
                core = {
                    "segment_id": segment["segment_id"],
                    "policy_id": profile["policy_id"],
                    "status": "CANDIDATE",
                    "binding_scope": "SAME_SEGMENT_ONLY",
                    "policy_signal_terms": [hit["term"] for hit in qualified_policy_hits],
                    "stable_accounting_keys": deepcopy(stable_keys),
                    "amount_brl": amount["amount_brl"],
                    "execution_stage": amount["execution_stage"],
                    "locator": deepcopy(segment["locator"]),
                    "automatic_promotion": False,
                }
                bridges.append({
                    **core,
                    "candidate_bridge_sha256": sha256(_canonical_bytes(core)).hexdigest(),
                })

    hits.sort(key=lambda x: (x["segment_id"], ALL_FAMILIES.index(x["family"]), x["normalized_term"], x["term"]))
    contexts.sort(key=lambda x: x["segment_id"])
    bridges.sort(key=lambda x: (x["segment_id"], x["execution_stage"], x["amount_brl"], x["candidate_bridge_sha256"]))

    gaps: list[str] = []
    if not policy_signal_segments:
        gaps.append("QUALIFIED_POLICY_SIGNAL_NOT_OBSERVED")
    else:
        if not stable_key_segments:
            gaps.append("STABLE_ACCOUNTING_LINKAGE_KEY_NOT_OBSERVED")
        if not amount_segments:
            gaps.append("AMOUNT_AND_EXECUTION_STAGE_NOT_OBSERVED")
        if not bridges:
            gaps.append("SAME_SEGMENT_FINANCIAL_BRIDGE_NOT_OBSERVED")

    source = packet["source"]
    source_role = source["source_role"]
    result_core = {
        "schema": "RESEARCH_EPHEMERAL_DIGEST_RESULT_V1",
        "mode": contract["mode"],
        "policy_profile": profile_name,
        "policy_id": profile["policy_id"],
        "source": {
            "document_id": source["document_id"],
            "source_role": source_role,
            "source_family": source["source_family"],
            "source_sha256": source["source_sha256"],
            "adapter_contract": source["adapter_contract"],
        },
        "source_role_boundary": {
            "policy_linkage_max_status": source_role_max_status(source_role, "POLICY_LINKAGE"),
            "digest_output_status_cap": "CANDIDATE",
            "source_role_does_not_override_candidate_only_rule": True,
        },
        "segment_count": len(segments),
        "ontology_term_count": sum(profile["expected_family_counts"].values()),
        "ontology_hits": hits,
        "context_groups": contexts,
        "financial_identity_candidates": bridges,
        "evidence_gaps": gaps,
        "promotion_performed": False,
        "persistence_authorized": False,
        "causal_inference_performed": False,
        "effects": {key: 0 for key in contract["remote_effects"]},
        "status": "PASS_RESEARCH_EPHEMERAL_DIGEST_CANDIDATES_ONLY",
    }
    return {
        **result_core,
        "result_sha256": sha256(_canonical_bytes(result_core)).hexdigest(),
    }


def load_contract(path: str | Path, *, root: str | Path) -> dict[str, Any]:
    contract = _load_json(path, code="TASK116_CONTRACT_JSON")
    return validate_contract(contract, root=root)

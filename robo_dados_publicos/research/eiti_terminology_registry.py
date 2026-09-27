from __future__ import annotations

from hashlib import sha1
import json
from pathlib import Path
from typing import Any


class EitiTerminologyRegistryStop(RuntimeError):
    """Fail-closed terminology registry validation error."""


BASE_FAMILIES = (
    "A_CANONICAL_POLICY_IDENTIFIERS",
    "B_LOCAL_PLANNING_AND_NORMATIVE_ALIASES",
    "C_OPERATIONAL_OFFER_AND_JOURNEY_SIGNALS",
    "D_FINANCING_AND_INDUCTION_SIGNALS",
    "E_ACCOUNTING_AND_PLANNING_LINKAGE_KEYS",
)


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise EitiTerminologyRegistryStop(code)


def _git_blob_sha(raw: bytes) -> str:
    return sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def _read_json(path: Path, *, code: str) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise EitiTerminologyRegistryStop(code) from exc
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EitiTerminologyRegistryStop(code) from exc
    _require(isinstance(data, dict), code)
    return data


def validate_terminology_registry(
    registry: dict[str, Any],
    *,
    root: str | Path,
) -> dict[str, Any]:
    _require(registry.get("schema") == "EITI_RESEARCH_TERMINOLOGY_REGISTRY_V2", "TASK118_SCHEMA")
    _require(registry.get("mode") == "T0_OFFLINE_VERSIONED_TERMINOLOGY_REGISTRY", "TASK118_MODE")
    _require(registry.get("policy_profile") == "EITI_LIMEIRA", "TASK118_PROFILE")
    _require(registry.get("policy_id") == "POLICY:EITI_LIMEIRA", "TASK118_POLICY")
    _require(all(value is False for value in (registry.get("remote_effects") or {}).values()), "TASK118_REMOTE_EFFECT")

    root = Path(root)
    base = registry.get("base_ontology") or {}
    base_path = root / str(base.get("path") or "")
    raw = base_path.read_bytes()
    _require(_git_blob_sha(raw) == base.get("git_blob_sha"), "TASK118_BASE_BLOB")
    task055a = json.loads(raw.decode("utf-8"))
    ontology = task055a.get("ontology") or {}
    _require(tuple(ontology) == BASE_FAMILIES, "TASK118_BASE_FAMILY_ORDER")
    observed_counts = {family: len(ontology.get(family) or []) for family in BASE_FAMILIES}
    _require(observed_counts == base.get("family_counts"), "TASK118_BASE_COUNTS")
    base_terms = [term for family in BASE_FAMILIES for term in ontology[family]]
    _require(len(base_terms) == 63, "TASK118_BASE_TOTAL")
    _require(len(set(base_terms)) == 63, "TASK118_BASE_DUPLICATE_TERM")
    _require(base.get("distinct_term_count") == 63, "TASK118_BASE_DECLARED_TOTAL")
    _require(base.get("immutable_historical_evidence") is True, "TASK118_BASE_IMMUTABILITY")

    aliases = registry.get("discovered_aliases")
    _require(isinstance(aliases, list) and len(aliases) == 1, "TASK118_ALIAS_COUNT")
    alias = aliases[0]
    _require(alias.get("alias_id") == "ALIAS:FOMENTO_ETI", "TASK118_ALIAS_ID")
    _require(alias.get("term") == "FOMENTO ETI", "TASK118_ALIAS_TERM")
    _require(alias.get("term") not in set(base_terms), "TASK118_ALIAS_ALREADY_BASE")
    _require(alias.get("classification") == "STRONG_POLICY_FINANCE_REPORTING_ALIAS", "TASK118_ALIAS_CLASS")
    _require(set(alias.get("semantic_roles") or []) == {"POLICY_SIGNAL", "FINANCING_SIGNAL", "REPORTING_BUCKET_ALIAS"}, "TASK118_ALIAS_ROLES")
    _require(alias.get("requires_companion") is False, "TASK118_ALIAS_COMPANION")
    _require(alias.get("policy_signal_scope") == "FINANCIAL_REPORTING_ONLY", "TASK118_ALIAS_SCOPE")
    _require(alias.get("source_role_scope") == "ACCOUNTING_EXECUTION_PRIMARY", "TASK118_ALIAS_SOURCE_ROLE")
    for key in ("transaction_identity", "generic_policy_financial_identity", "amount_alone_sufficient"):
        _require(alias.get(key) is False, f"TASK118_ALIAS_{key.upper()}")
    _require(alias.get("stable_accounting_key_still_required_for_transaction_bridge") is True, "TASK118_ALIAS_STABLE_KEY")

    provenance = alias.get("provenance") or {}
    source_path = root / str(provenance.get("path") or "")
    source_raw = source_path.read_bytes()
    _require(_git_blob_sha(source_raw) == provenance.get("git_blob_sha"), "TASK118_ALIAS_SOURCE_BLOB")
    source = json.loads(source_raw.decode("utf-8"))
    discovered = ((source.get("ontology_scan") or {}).get("new_alias_discovered") or {})
    _require(discovered.get("term") == alias["term"], "TASK118_SOURCE_ALIAS_TERM")
    _require(discovered.get("classification") == alias["classification"], "TASK118_SOURCE_ALIAS_CLASS")
    _require(discovered.get("must_be_added_to_future_matching") is True, "TASK118_SOURCE_PROPAGATION")
    findings = source.get("fomento_eti_reporting_findings") or {}
    _require(findings.get("dedicated_reporting_bucket_found") is True, "TASK118_SOURCE_BUCKET")
    _require(findings.get("transaction_level_eiti_financial_identity_proven") is False, "TASK118_SOURCE_TRANSACTION_BOUNDARY")

    _require(registry.get("discovered_alias_count") == 1, "TASK118_DECLARED_ALIAS_COUNT")
    _require(registry.get("active_distinct_term_count") == 64, "TASK118_ACTIVE_TOTAL")
    _require(len(set(base_terms + [alias["term"]])) == 64, "TASK118_ACTIVE_DISTINCT")

    invariants = set(registry.get("invariants") or [])
    for required in (
        "FOMENTO_ETI_DOES_NOT_PROVE_TRANSACTION_IDENTITY",
        "STABLE_ACCOUNTING_KEY_REMAINS_REQUIRED_FOR_TRANSACTION_BRIDGE",
        "DISCOVERED_ALIAS_DOES_NOT_RECLASSIFY_GENERIC_PROGRAM_OR_ACTION_AS_EITI",
    ):
        _require(required in invariants, "TASK118_INVARIANT")
    return {
        "status": "PASS_TASK118_TERMINOLOGY_REGISTRY_V2",
        "base_term_count": 63,
        "discovered_alias_count": 1,
        "active_distinct_term_count": 64,
        "alias": alias["term"],
        "remote_effects": 0,
    }


def load_terminology_registry(path: str | Path, *, root: str | Path) -> dict[str, Any]:
    data = _read_json(Path(path), code="TASK118_REGISTRY_JSON")
    validate_terminology_registry(data, root=root)
    return data

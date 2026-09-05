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


class SiopeFundebResearchDigestAdapterStop(RuntimeError):
    """Fail-closed T0 SIOPE/FUNDEB adapter error."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise SiopeFundebResearchDigestAdapterStop(code)


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
        raise SiopeFundebResearchDigestAdapterStop(code) from exc
    _require(_git_blob_sha(raw) == meta.get("git_blob_sha"), code)
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SiopeFundebResearchDigestAdapterStop(code) from exc
    _require(isinstance(data, dict), code)
    return data


def validate_contract(contract: dict[str, Any], *, root: str | Path) -> dict[str, Any]:
    _require(contract.get("schema") == "SIOPE_FUNDEB_RESEARCH_DIGEST_ADAPTER_V1", "TASK121_SCHEMA")
    _require(contract.get("mode") == "T0_OFFLINE_VERSIONED_SIOPE_FUNDEB_EVIDENCE_ADAPTER", "TASK121_MODE")
    _require(all(value is False for value in (contract.get("remote_effects") or {}).values()), "TASK121_REMOTE_EFFECT")

    source = contract.get("source") or {}
    _require(source.get("document_id") == "DOC:SIOPE_MAVS_2026_B1", "TASK121_DOCUMENT")
    _require(source.get("source_role") == "ACCOUNTING_EXECUTION_PRIMARY", "TASK121_SOURCE_ROLE")
    _require(source.get("source_family") == "SIOPE", "TASK121_SOURCE_FAMILY")
    _require(source.get("expected_sha256") == "d2b7f7638222bc9788f6d42df11126d2e3aa57cb4204450914c98d9400bf0bbe", "TASK121_SOURCE_SHA")
    _require(source.get("expected_bytes") == 360070, "TASK121_SOURCE_BYTES")

    segments = contract.get("segments") or {}
    _require(segments.get("expected_count") == 3, "TASK121_SEGMENT_COUNT")
    _require(segments.get("execution_stage") == "REPORTING_BUCKET", "TASK121_STAGE")
    _require(segments.get("stable_accounting_keys_expected") == 0, "TASK121_STABLE_KEYS")
    _require(segments.get("transaction_event_claims_allowed") is False, "TASK121_TRANSACTION_EVENT_GUARD")

    expected = contract.get("expected") or {}
    _require(expected.get("active_ontology_terms") == 64, "TASK121_ONTOLOGY_TOTAL")
    _require(expected.get("composite_alias") == "FOMENTO ETI", "TASK121_ALIAS")
    _require(expected.get("composite_alias_qualified") is True, "TASK121_ALIAS_QUALIFICATION")
    _require(expected.get("financial_identity_candidates") == 0, "TASK121_FINANCIAL_CANDIDATE_EXPECTATION")
    _require(set(expected.get("required_gaps") or []) == {
        "STABLE_ACCOUNTING_LINKAGE_KEY_NOT_OBSERVED",
        "SAME_SEGMENT_FINANCIAL_BRIDGE_NOT_OBSERVED",
    }, "TASK121_GAPS")

    boundary = contract.get("semantic_boundary") or {}
    _require(boundary.get("dedicated_policy_finance_reporting_identity") == "PROVEN_SCOPED", "TASK121_REPORTING_IDENTITY")
    _require(boundary.get("transaction_level_financial_identity") == "UNKNOWN", "TASK121_TRANSACTION_IDENTITY")
    for key in ("zero_bucket_value_generalizes_to_all_eiti_spending","reporting_bucket_is_transaction_identity"):
        _require(boundary.get(key) is False, f"TASK121_{key.upper()}")
    _require(boundary.get("report_column_label_is_not_individual_event_chain") is True, "TASK121_COLUMN_EVENT_GUARD")

    root = Path(root)
    research = contract.get("research_digest_contract") or {}
    research_path = root / str(research.get("path") or "")
    raw = research_path.read_bytes()
    _require(_git_blob_sha(raw) == research.get("git_blob_sha"), "TASK121_RESEARCH_CONTRACT_BLOB")
    digest_contract = load_research_digest_contract(research_path, root=root)
    _require(research.get("policy_profile") in digest_contract["policy_profiles"], "TASK121_PROFILE")
    _require(digest_contract["policy_profiles"]["EITI_LIMEIRA"]["expected_active_total_terms"] == 64, "TASK121_ACTIVE_VOCABULARY")

    inputs = contract.get("inputs") or {}
    _require(set(inputs) == {"task056","task120"}, "TASK121_INPUT_SET")
    _load_pinned(root, inputs["task056"], code="TASK121_TASK056_BLOB")
    _load_pinned(root, inputs["task120"], code="TASK121_TASK120_BLOB")
    return contract


def _segment(
    *,
    segment_id: str,
    text: str,
    line_refs: list[str],
    source_sha256: str,
    amount_brl: str,
) -> dict[str, Any]:
    return {
        "segment_id": segment_id,
        "text": text,
        "locator": {
            "task": "TASK_056",
            "report_lines": list(line_refs),
            "source_sha256": source_sha256,
            "representation": "DETERMINISTIC_SERIALIZATION_OF_VERSIONED_TASK056_FIELDS",
        },
        "structured": {
            "accounting_keys": [],
            "amounts": [
                {
                    "amount_brl": amount_brl,
                    "execution_stage": "REPORTING_BUCKET",
                }
            ],
        },
    }


def build_siope_fundeb_research_packet(
    contract: dict[str, Any],
    *,
    root: str | Path,
) -> dict[str, Any]:
    contract = validate_contract(contract, root=root)
    root = Path(root)
    research_path = root / contract["research_digest_contract"]["path"]
    research_contract = load_research_digest_contract(research_path, root=root)
    task056 = _load_pinned(root, contract["inputs"]["task056"], code="TASK121_TASK056_BLOB")
    task120 = _load_pinned(root, contract["inputs"]["task120"], code="TASK121_TASK120_BLOB")

    _require(task056.get("result") == "PASS_TASK056_MAVS_FOMENTO_ETI_REPORTING_IDENTITY_PARTIAL_NO_TRANSACTION_LINKAGE_NO_PROMOTION", "TASK121_TASK056_STATUS")
    _require(task120.get("status") == "PASS_TASK120_EXACT_SOURCE_BINARY_IDENTITY", "TASK121_TASK120_STATUS")
    source120 = task120.get("source") or {}
    _require(source120.get("sha256") == contract["source"]["expected_sha256"], "TASK121_BINARY_SHA")
    _require(source120.get("raw_media_size_bytes") == contract["source"]["expected_bytes"], "TASK121_BINARY_BYTES")

    observed = task056.get("observed_source") or {}
    _require(observed.get("title") == source120.get("title"), "TASK121_TITLE_BINDING")
    _require(observed.get("period") == contract["source"]["period"], "TASK121_PERIOD")
    _require(observed.get("funding_family") == "FUNDEB", "TASK121_FUNDEB")
    _require(observed.get("source_system_marker") == "SIOPE", "TASK121_SIOPE")
    _require(observed.get("execution_column_marker") == "DESPESA LIQUIDADA/EMPENHADA", "TASK121_COLUMN_MARKER")

    scan = task056.get("ontology_scan") or {}
    alias = scan.get("new_alias_discovered") or {}
    _require(alias.get("term") == "FOMENTO ETI", "TASK121_TASK056_ALIAS")
    _require(alias.get("classification") == "STRONG_POLICY_FINANCE_REPORTING_ALIAS", "TASK121_TASK056_ALIAS_CLASS")
    _require(alias.get("must_be_added_to_future_matching") is True, "TASK121_TASK056_ALIAS_PROPAGATION")
    accounting = scan.get("E_ACCOUNTING_AND_PLANNING_LINKAGE_KEYS") or {}
    _require(accounting.get("program_action_subaction_found") is False, "TASK121_PROGRAM_ACTION_KEY")
    _require(accounting.get("ficha_found") is False, "TASK121_FICHA_KEY")
    _require(accounting.get("centro_de_custo_found") is False, "TASK121_COST_CENTER_KEY")
    _require(accounting.get("transaction_level_stable_key_found") is False, "TASK121_TRANSACTION_KEY")

    findings = task056.get("fomento_eti_reporting_findings") or {}
    _require(findings.get("dedicated_reporting_bucket_found") is True, "TASK121_BUCKET")
    _require(findings.get("period_scope") == "FIRST_BIMESTER_2026_ONLY", "TASK121_PERIOD_SCOPE")
    _require(findings.get("funding_scope") == "FUNDEB_ONLY", "TASK121_FUNDING_SCOPE")
    _require(findings.get("dedicated_policy_finance_reporting_identity_proven") is True, "TASK121_REPORTING_PROOF")
    _require(findings.get("transaction_level_eiti_financial_identity_proven") is False, "TASK121_TRANSACTION_PROOF")

    context = " ".join([
        str(observed["funding_family"]),
        str(observed["source_system_marker"]),
        str(observed["execution_column_marker"]),
        "PAGAMENTOS EFETUADOS",
    ])
    segments = [
        _segment(
            segment_id="SEG:SIOPE_2026_B1_FOMENTO_ETI_APPLIED",
            text=" ".join([str(findings["line_10_1_label"]), context]),
            line_refs=["10.1"],
            source_sha256=source120["sha256"],
            amount_brl=f"{float(findings['line_10_1_applied_amount_brl']):.2f}",
        ),
        _segment(
            segment_id="SEG:SIOPE_2026_B1_FOMENTO_ETI_REQUIRED",
            text=" ".join([str(findings["line_15_label"]), context]),
            line_refs=["15","15.1"],
            source_sha256=source120["sha256"],
            amount_brl=f"{float(findings['line_15_1_required_amount_brl']):.2f}",
        ),
        _segment(
            segment_id="SEG:SIOPE_2026_B1_FOMENTO_ETI_AFTER_DEDUCTIONS",
            text=" ".join([
                str(findings["line_15_label"]),
                "APLICADO APOS DEDUCOES",
                context,
            ]),
            line_refs=["15","15.2"],
            source_sha256=source120["sha256"],
            amount_brl=f"{float(findings['line_15_2_applied_after_deductions_brl']):.2f}",
        ),
    ]
    _require(len(segments) == contract["segments"]["expected_count"], "TASK121_SEGMENT_OUTPUT_COUNT")
    _require(all(segment["structured"]["accounting_keys"] == [] for segment in segments), "TASK121_UNEXPECTED_STABLE_KEY")

    packet = {
        "schema": "RESEARCH_EPHEMERAL_DIGEST_INPUT_V1",
        "policy_profile": contract["research_digest_contract"]["policy_profile"],
        "source": {
            "document_id": contract["source"]["document_id"],
            "source_role": contract["source"]["source_role"],
            "source_family": contract["source"]["source_family"],
            "source_sha256": source120["sha256"],
            "adapter_contract": contract["schema"],
        },
        "segments": segments,
        "remote_effects_authorized": {
            key: False for key in research_contract["remote_effects"]
        },
    }
    digest = digest_research_segments(packet, research_contract, root=root)

    alias_hits = [
        hit for hit in digest["ontology_hits"]
        if hit["term"] == contract["expected"]["composite_alias"]
    ]
    _require(len(alias_hits) == len(segments), "TASK121_ALIAS_HIT_COUNT")
    _require(all(hit["qualified"] is True for hit in alias_hits), "TASK121_ALIAS_NOT_QUALIFIED")
    _require(all(hit["family"] == "X_DISCOVERED_COMPOSITE_ALIASES" for hit in alias_hits), "TASK121_ALIAS_FAMILY")
    _require(digest["ontology_term_count"] == 64, "TASK121_DIGEST_ONTOLOGY_TOTAL")
    _require(digest["financial_identity_candidates"] == [], "TASK121_UNEXPECTED_FINANCIAL_CANDIDATE")
    for gap in contract["expected"]["required_gaps"]:
        _require(gap in digest["evidence_gaps"], "TASK121_REQUIRED_GAP")

    interpretation = task056.get("interpretation") or {}
    _require(interpretation.get("zero_value_must_not_be_generalized_beyond_fundeb_fomento_eti_bucket_and_period") is True, "TASK121_ZERO_GENERALIZATION")
    _require(interpretation.get("reporting_identity_is_not_transaction_identity") is True, "TASK121_REPORTING_TRANSACTION_BOUNDARY")

    core = {
        "schema": "SIOPE_FUNDEB_RESEARCH_DIGEST_ADAPTER_RESULT_V1",
        "mode": contract["mode"],
        "packet": packet,
        "research_digest": digest,
        "reporting_identity": {
            "status": "PROVEN_SCOPED",
            "period_scope": findings["period_scope"],
            "funding_scope": findings["funding_scope"],
            "composite_alias": "FOMENTO ETI",
        },
        "transaction_identity": {
            "status": "UNKNOWN",
            "stable_accounting_key_found": False,
            "program_action_subaction_found": False,
            "ficha_found": False,
            "cost_center_found": False,
        },
        "source_binary_identity_sha256": source120["sha256"],
        "financial_identity_promoted": False,
        "persistence_authorized": False,
        "effects": {key: 0 for key in contract["remote_effects"]},
        "status": "PASS_TASK121_SIOPE_FUNDEB_REPOSITORY_EVIDENCE_ADAPTER",
    }
    return {
        **core,
        "result_sha256": sha256(_canonical_bytes(core)).hexdigest(),
    }


def load_adapter_contract(path: str | Path, *, root: str | Path) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SiopeFundebResearchDigestAdapterStop("TASK121_CONTRACT_MISSING") from exc
    except json.JSONDecodeError as exc:
        raise SiopeFundebResearchDigestAdapterStop("TASK121_CONTRACT_JSON") from exc
    _require(isinstance(data, dict), "TASK121_CONTRACT_OBJECT")
    return validate_contract(data, root=root)

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from robo_dados_publicos.journal.semantic_layers import classify_event

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/task220_direct_jom_procurement_context.v1.json"


class Task220Error(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task220Error(code)


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(cfg["schema"] == "TASK220_DIRECT_JOM_PROCUREMENT_CONTEXT_V1", "TASK220_SCHEMA")
    _stop(cfg["task"] == "TASK_220" and cfg["issue"] == 697, "TASK220_TASK")
    scope = cfg["bounded_scope"]
    _stop(scope["start_date"] == "2026-01-01" and scope["end_date"] == "2026-09-08", "TASK220_SCOPE")
    _stop(scope["official_document_count"] == 99, "TASK220_DOC_COUNT")
    _stop(scope["completed_calendar_year_claim"] is False, "TASK220_YEAR_GUARD")
    src = cfg["sources"]
    _stop(src["legacy_event_count"] == 303 and src["new_event_count"] == 2408, "TASK220_SOURCE_COUNTS")
    filt = cfg["direct_procurement_filter"]
    _stop(filt["require_semantic_evidence_layer"] == "PROCUREMENT_CONTRACT", "TASK220_LAYER")
    _stop(
        set(filt["allowed_event_types"])
        == {"CONTRATO", "ATA_REGISTRO_PRECOS", "EDITAL", "TERMO_ADITIVO_CONTRATO", "APOSTILAMENTO"},
        "TASK220_TYPES",
    )
    bounds = cfg["hard_boundaries"]
    _stop(bounds["jom_publication_ne_payment"] is True, "TASK220_PAYMENT_GUARD")
    _stop(bounds["jom_contract_ne_accounting_execution"] is True, "TASK220_EXECUTION_GUARD")
    _stop(bounds["value_ne_paid_amount"] is True, "TASK220_VALUE_GUARD")
    _stop(bounds["no_cross_source_identity_in_this_task"] is True, "TASK220_CROSS_SOURCE_GUARD")
    _stop(bounds["ctrl_q2_remains_blocked"] is True, "TASK220_CTRL_GUARD")
    _stop(bounds["no_public_source_network"] is True and bounds["no_drive_write"] is True, "TASK220_REMOTE_GUARD")
    return cfg


_TERM_PATTERNS = [
    re.compile(
        r"(?i)\b(?:PRAZO|VIG[ÊE]NCIA)\s*:\s*"
        r"((?:AT[ÉE]\s+)?\d{1,3}\s*(?:\([^)]{1,30}\)\s*)?(?:DIAS?|MESES?|ANOS?))"
    ),
    re.compile(
        r"(?i)\b(?:PRAZO|VIG[ÊE]NCIA)\s+(?:DE|POR)\s+"
        r"((?:AT[ÉE]\s+)?\d{1,3}\s*(?:\([^)]{1,30}\)\s*)?(?:DIAS?|MESES?|ANOS?))"
    ),
]


def extract_term_text(excerpt: str | None) -> str | None:
    text = " ".join(str(excerpt or "").split())
    for pattern in _TERM_PATTERNS:
        match = pattern.search(text)
        if match:
            return " ".join(match.group(1).split())
    return None


def _semantics_for(event: Mapping[str, Any]) -> dict[str, Any]:
    sem = classify_event(dict(event))
    _stop(isinstance(sem, dict), "TASK220_SEMANTIC_OBJECT")
    return sem


def _direct_procurement_event(
    event: Mapping[str, Any],
    sem: Mapping[str, Any],
    cfg: Mapping[str, Any],
) -> bool:
    filt = cfg["direct_procurement_filter"]
    if event.get("event_type") not in set(filt["allowed_event_types"]):
        return False
    if filt["require_semantic_evidence_layer"] not in set(sem.get("evidence_layers") or []):
        return False
    if event.get("event_type") == "EDITAL" and filt["edital_requires_object_and_procurement_identifier"]:
        if not event.get("object_text"):
            return False
        if not any(event.get(field) for field in filt["procurement_identifier_fields"]):
            return False
    return True


def compact_event(
    event: Mapping[str, Any],
    sem: Mapping[str, Any],
    cfg: Mapping[str, Any],
    *,
    source_corpus: str,
) -> dict[str, Any]:
    term = extract_term_text(event.get("excerpt_redacted"))
    event_type = str(event.get("event_type"))
    q1 = event_type in set(cfg["q1"]["event_types"]) and bool(event.get("object_text"))
    q2 = event_type in set(cfg["q2"]["event_types"]) and all(
        (term if field == "term_text" else event.get(field))
        for field in cfg["q2"]["require_fields"]
    )
    q3 = event_type in set(cfg["q3"]["change_event_types"] + cfg["q3"]["new_tender_event_types"])

    capabilities = []
    for name, present in (
        ("OBJECT", event.get("object_text")),
        ("SUPPLIER", event.get("contractor")),
        ("SUPPLIER_CNPJ", event.get("cnpj")),
        ("PUBLISHED_VALUE", event.get("value_brl")),
        ("PUBLISHED_TERM", term),
        ("CONTRACT_ID", event.get("contract_number")),
        ("PROCESS_ID", event.get("process_number")),
        ("BIDDING_ID", event.get("bidding_number") or event.get("edital_number")),
    ):
        if present:
            capabilities.append(name)
    if event_type in set(cfg["q3"]["change_event_types"]):
        capabilities.append("CHANGE_EVENT")
    if event_type in set(cfg["q3"]["new_tender_event_types"]):
        capabilities.append("NEW_TENDER_EVENT")

    keep = (
        "event_id",
        "event_type",
        "edition",
        "publication_date",
        "page_number",
        "source_id",
        "source_sha256",
        "source_url",
        "organ",
        "contract_number",
        "process_number",
        "edital_number",
        "bidding_modality",
        "bidding_number",
        "contractor",
        "cnpj",
        "object_text",
        "value_brl",
        "signature_date",
        "target_act_type",
        "target_act_number",
    )
    row = {key: event.get(key) for key in keep}
    row.update(
        {
            "source_corpus": source_corpus,
            "term_text": term,
            "semantic_evidence_layer": "PROCUREMENT_CONTRACT",
            "direct_claim_capabilities": sorted(set(capabilities)),
            "q1_eligible": q1,
            "q2_eligible": q2,
            "q3_eligible": q3,
            "payment_or_accounting_execution_proven": False,
            "cross_source_identity_proven": False,
        }
    )
    return row


def materialize(artifact_dir: Path, *, root: Path = ROOT) -> dict[str, Any]:
    cfg = load_config(root / "config/task220_direct_jom_procurement_context.v1.json")
    src = cfg["sources"]

    legacy_path = root / src["legacy_fixture"]
    _stop(sha256_path(legacy_path) == src["legacy_fixture_sha256"], "TASK220_LEGACY_SHA")
    legacy = _load_jsonl(legacy_path)
    _stop(len(legacy) == src["legacy_event_count"], "TASK220_LEGACY_ROWS")

    new_events_path = artifact_dir / "task219a_events_gold_sanitized.jsonl"
    new_semantics_path = artifact_dir / "task219a_event_semantics_sanitized.jsonl"
    manifest_path = artifact_dir / "task219a_manifest.json"
    _stop(new_events_path.is_file() and new_semantics_path.is_file() and manifest_path.is_file(), "TASK220_ARTIFACT_FILES")
    _stop(sha256_path(new_events_path) == src["new_events_sha256"], "TASK220_NEW_EVENTS_SHA")
    _stop(sha256_path(new_semantics_path) == src["new_semantics_sha256"], "TASK220_NEW_SEMANTICS_SHA")
    new_events = _load_jsonl(new_events_path)
    new_semantics = _load_jsonl(new_semantics_path)
    _stop(len(new_events) == src["new_event_count"], "TASK220_NEW_EVENT_ROWS")
    _stop(len(new_semantics) == src["new_event_count"], "TASK220_NEW_SEMANTIC_ROWS")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    _stop(manifest["status"] == "PASS_COMPLETE_87_DOCUMENT_GENERAL_EVENT_REDIGEST", "TASK220_SOURCE_STATUS")
    _stop(manifest["complete_scope"] is True and manifest["validated_download_count"] == 87, "TASK220_SOURCE_SCOPE")
    _stop(manifest["counts"]["failure_count"] == 0, "TASK220_SOURCE_FAILURES")

    sem_by_id = {row["event_id"]: row for row in new_semantics}
    _stop(len(sem_by_id) == len(new_semantics), "TASK220_SEMANTIC_ID_UNIQUE")
    _stop({row["event_id"] for row in new_events} == set(sem_by_id), "TASK220_EVENT_SEMANTIC_COVERAGE")

    all_ids = [row["event_id"] for row in legacy] + [row["event_id"] for row in new_events]
    _stop(len(all_ids) == len(set(all_ids)), "TASK220_EVENT_ID_COLLISION")

    selected: list[dict[str, Any]] = []
    semantic_replay_mismatch = 0
    for event in legacy:
        sem = _semantics_for(event)
        if _direct_procurement_event(event, sem, cfg):
            selected.append(compact_event(event, sem, cfg, source_corpus="LEGACY_12_EDITIONS"))
    for event in new_events:
        sem = sem_by_id[event["event_id"]]
        replay = _semantics_for(event)
        if set(replay.get("evidence_layers") or []) != set(sem.get("evidence_layers") or []):
            semantic_replay_mismatch += 1
        if _direct_procurement_event(event, sem, cfg):
            selected.append(compact_event(event, sem, cfg, source_corpus="NEW_87_EDITIONS"))

    _stop(semantic_replay_mismatch == 0, "TASK220_SEMANTIC_REPLAY_MISMATCH")
    selected.sort(
        key=lambda row: (
            str(row.get("publication_date") or ""),
            int(row.get("edition") or 0),
            int(row.get("page_number") or 0),
            str(row.get("event_id") or ""),
        )
    )

    out_path = root / cfg["outputs"]["fixture"]
    evidence_path = root / cfg["outputs"]["materialization_evidence"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in selected),
        encoding="utf-8",
    )

    by_type = Counter(row["event_type"] for row in selected)
    by_corpus = Counter(row["source_corpus"] for row in selected)
    counts = {
        "direct_procurement_event_count": len(selected),
        "event_type_counts": dict(sorted(by_type.items())),
        "source_corpus_counts": dict(sorted(by_corpus.items())),
        "q1_eligible_count": sum(bool(row["q1_eligible"]) for row in selected),
        "q2_eligible_count": sum(bool(row["q2_eligible"]) for row in selected),
        "q3_eligible_count": sum(bool(row["q3_eligible"]) for row in selected),
        "object_text_count": sum(bool(row.get("object_text")) for row in selected),
        "supplier_count": sum(bool(row.get("contractor")) for row in selected),
        "supplier_cnpj_count": sum(bool(row.get("cnpj")) for row in selected),
        "published_value_count": sum(bool(row.get("value_brl")) for row in selected),
        "published_term_count": sum(bool(row.get("term_text")) for row in selected),
        "contract_id_count": sum(bool(row.get("contract_number")) for row in selected),
        "process_id_count": sum(bool(row.get("process_number")) for row in selected),
        "observed_event_bearing_edition_count": len({row["edition"] for row in selected}),
    }

    evidence = {
        "task": "TASK_220_JOM_PROCUREMENT_MATERIALIZATION",
        "issue": cfg["issue"],
        "bounded_scope": cfg["bounded_scope"],
        "sources": {
            "legacy_event_count": len(legacy),
            "new_event_count": len(new_events),
            "new_runtime_run_id": src["new_runtime_run_id"],
            "new_runtime_artifact_id": src["new_runtime_artifact_id"],
            "new_runtime_status": manifest["status"],
            "new_runtime_validated_documents": manifest["validated_download_count"],
        },
        "counts": counts,
        "fixture": {
            "path": cfg["outputs"]["fixture"],
            "sha256": sha256_path(out_path),
            "bytes": out_path.stat().st_size,
        },
        "claim_semantics": {
            "PROC_Q1": cfg["q1"]["claim_semantic"],
            "PROC_Q2": cfg["q2"]["claim_semantic"],
            "PROC_Q3": cfg["q3"]["claim_semantic"],
        },
        "hard_boundaries": cfg["hard_boundaries"],
        "semantic_replay_mismatch_count": semantic_replay_mismatch,
        "contextual_coverage_candidate": {
            "before": 34,
            "candidate_after_if_executor_tests_pass": 37,
            "canonical_questions_total": 38,
            "remaining_candidate_blocker": "CTRL_Q2",
        },
    }
    evidence_path.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return evidence


__all__ = [
    "Task220Error",
    "load_config",
    "extract_term_text",
    "compact_event",
    "materialize",
    "sha256_path",
]

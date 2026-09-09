from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/task219b_jom_strong_identity_canonization.v1.json"

ALLOWED_EVENT_TYPES = {
    "EDITAL",
    "ATA_REGISTRO_PRECOS",
    "CONTRATO",
    "TERMO_ADITIVO_CONTRATO",
}
PROCESS_RE = re.compile(r"^\d{1,3}(?:\.\d{3})*/\d{4}$")
CONTRACT_RE = re.compile(r"^\d+/\d{4}$")


class Task219BError(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task219BError(code)


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_config(path: Path | str = DEFAULT_CONFIG) -> dict[str, Any]:
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(cfg["schema"] == "TASK219B_JOM_STRONG_IDENTITY_CANONIZATION_V1", "TASK219B_SCHEMA")
    _stop(cfg["task"] == "TASK_219B", "TASK219B_TASK")
    guards = cfg["identity_guards"]
    for key in (
        "cnpj_alone_is_identity",
        "amount_similarity_is_identity",
        "date_proximity_is_identity",
        "object_text_is_identity",
        "semantic_similarity_is_identity",
        "end_to_end_chain_proven_by_this_task",
    ):
        _stop(guards[key] is False, "TASK219B_WEAK_IDENTITY_GUARD_" + key.upper())
    _stop(guards["process_identity_may_have_multiple_suppliers"] is True, "TASK219B_PROCESS_MULTI_SUPPLIER")
    _stop(guards["contract_supplier_conflict_blocks_promotion"] is True, "TASK219B_CONTRACT_CONFLICT")
    remote = cfg["remote_effects"]
    _stop(not any(remote.values()), "TASK219B_REMOTE_EFFECTS")
    return cfg


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _normalize_identifier(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"[.,;]+$", "", str(value).strip()).strip()


def _supplier(value: Any) -> str | None:
    digits = re.sub(r"\D", "", str(value or ""))
    return digits if len(digits) == 14 else None


def derive_legacy_anchors(events: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    anchors: list[dict[str, Any]] = []
    for event in events:
        if event.get("event_type") not in ALLOWED_EVENT_TYPES:
            continue
        process = _normalize_identifier(event.get("process_number"))
        contract = _normalize_identifier(event.get("contract_number"))
        base = {
            "event_id": event["event_id"],
            "event_type": event.get("event_type"),
            "publication_date": event.get("publication_date"),
            "supplier_cnpj": _supplier(event.get("cnpj")),
        }
        if PROCESS_RE.fullmatch(process):
            anchors.append({**base, "anchor_type": "PROCESS_IDENTITY", "anchor_value": process})
        if CONTRACT_RE.fullmatch(contract):
            anchors.append({**base, "anchor_type": "CONTRACT_IDENTITY", "anchor_value": contract})
    return sorted(anchors, key=lambda r: (r["event_id"], r["anchor_type"], r["anchor_value"]))


def identity_key(row: Mapping[str, Any]) -> tuple[str, str]:
    return str(row["anchor_type"]), str(row["anchor_value"])


def _validate_new_anchor(row: Mapping[str, Any]) -> None:
    _stop(row.get("anchor_type") in {"PROCESS_IDENTITY", "CONTRACT_IDENTITY"}, "TASK219B_ANCHOR_TYPE")
    value = _normalize_identifier(row.get("anchor_value"))
    pattern = PROCESS_RE if row["anchor_type"] == "PROCESS_IDENTITY" else CONTRACT_RE
    _stop(bool(pattern.fullmatch(value)), "TASK219B_ANCHOR_VALUE")
    _stop(row.get("event_type") in ALLOWED_EVENT_TYPES, "TASK219B_EVENT_TYPE")
    _stop(str(row.get("event_id", "")).startswith("JOEV_"), "TASK219B_EVENT_ID")
    _stop(isinstance(row.get("edition"), int), "TASK219B_EDITION")
    _stop(isinstance(row.get("page_number"), int), "TASK219B_PAGE")
    _stop(bool(re.fullmatch(r"[0-9a-f]{64}", str(row.get("source_sha256", "")))), "TASK219B_SOURCE_SHA")
    supplier = row.get("supplier_cnpj")
    _stop(supplier is None or bool(re.fullmatch(r"\d{14}", str(supplier))), "TASK219B_SUPPLIER_CNPJ")


def validate_runtime_artifact(artifact_dir: Path, cfg: Mapping[str, Any]) -> dict[str, Any]:
    source = cfg["source_runtime"]
    expected_files = source["files"]
    actual_names = {p.name for p in artifact_dir.iterdir() if p.is_file()}
    _stop(actual_names == set(expected_files), "TASK219B_ARTIFACT_FILESET")
    for name, expected_sha in expected_files.items():
        _stop(sha256_path(artifact_dir / name) == expected_sha, "TASK219B_FILE_SHA_" + name.upper().replace(".", "_"))

    manifest = json.loads((artifact_dir / "task219a_manifest.json").read_text(encoding="utf-8"))
    _stop(manifest["status"] == "PASS_COMPLETE_87_DOCUMENT_GENERAL_EVENT_REDIGEST", "TASK219B_SOURCE_STATUS")
    _stop(manifest["complete_scope"] is True, "TASK219B_SOURCE_SCOPE")
    _stop(manifest["target_document_count"] == 87, "TASK219B_SOURCE_TARGETS")
    _stop(manifest["validated_download_count"] == 87, "TASK219B_SOURCE_DOWNLOADS")
    _stop(manifest["counts"]["failure_count"] == 0, "TASK219B_SOURCE_FAILURES")
    _stop(manifest["bundle_sha256"] == source["bundle_sha256"], "TASK219B_BUNDLE_SHA")
    _stop(manifest["strong_anchor_proves_end_to_end_identity_chain"] is False, "TASK219B_CHAIN_GUARD")
    _stop(manifest["absence_inference_allowed"] is False, "TASK219B_ABSENCE_GUARD")
    _stop(manifest["raw_pdf_persisted"] is False, "TASK219B_RAW_PDF")
    _stop(manifest["raw_page_text_persisted"] is False, "TASK219B_RAW_TEXT")
    _stop(manifest["rag_chunks_persisted"] is False, "TASK219B_RAG")
    _stop(manifest["drive_write_count"] == 0, "TASK219B_DRIVE_WRITE")
    _stop(manifest["serving_write_count"] == 0, "TASK219B_SERVING_WRITE")
    _stop(manifest["publication_count"] == 0, "TASK219B_PUBLICATION")
    _stop(manifest["promotion_performed"] is False, "TASK219B_PROMOTION")
    return manifest


def _unique_counts(rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    keys = {identity_key(r) for r in rows}
    return {
        "unique_identities": len(keys),
        "unique_process_identities": sum(1 for t, _ in keys if t == "PROCESS_IDENTITY"),
        "unique_contract_identities": sum(1 for t, _ in keys if t == "CONTRACT_IDENTITY"),
    }


def build_identity_index(
    old_anchors: list[dict[str, Any]],
    new_anchors: list[dict[str, Any]],
) -> dict[str, Any]:
    grouped: dict[tuple[str, str], list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    for row in old_anchors:
        grouped[identity_key(row)].append(("LEGACY_12_EDITIONS", row))
    for row in new_anchors:
        grouped[identity_key(row)].append(("NEW_87_EDITIONS", row))

    identities: list[dict[str, Any]] = []
    process_multi_supplier = 0
    contract_multi_supplier = 0
    for key in sorted(grouped):
        tagged = grouped[key]
        suppliers = sorted({str(r.get("supplier_cnpj")) for _, r in tagged if r.get("supplier_cnpj")})
        corpora = sorted({tag for tag, _ in tagged})
        events = sorted({str(r["event_id"]) for _, r in tagged})
        old_n = sum(1 for tag, _ in tagged if tag == "LEGACY_12_EDITIONS")
        new_n = len(tagged) - old_n
        if len(suppliers) > 1:
            if key[0] == "PROCESS_IDENTITY":
                process_multi_supplier += 1
            else:
                contract_multi_supplier += 1
        identities.append(
            {
                "anchor_type": key[0],
                "anchor_value": key[1],
                "total_occurrence_count": len(tagged),
                "legacy_occurrence_count": old_n,
                "new_87_occurrence_count": new_n,
                "event_count": len(events),
                "supplier_count": len(suppliers),
                "supplier_cnpjs": suppliers,
                "source_corpora": corpora,
                "event_ids": events,
            }
        )
    return {
        "schema": "TASK219B_FULL_99_EDITION_STRONG_IDENTITY_INDEX_V1",
        "identity_grain": "one exact administrative identifier type plus normalized value",
        "identities": identities,
        "audit": {
            "process_identities_with_multiple_suppliers": process_multi_supplier,
            "contract_identities_with_multiple_suppliers": contract_multi_supplier,
            "cnpj_alone_is_identity": False,
            "weak_similarity_identity_allowed": False,
        },
    }


def canonize(artifact_dir: Path, root: Path = ROOT) -> dict[str, Any]:
    cfg = load_config(root / "config/task219b_jom_strong_identity_canonization.v1.json")
    manifest = validate_runtime_artifact(artifact_dir, cfg)

    new_anchors = _load_jsonl(artifact_dir / "task219a_strong_identity_anchors.jsonl")
    for row in new_anchors:
        _validate_new_anchor(row)

    legacy_path = root / cfg["legacy_corpus"]["fixture"]
    legacy_events = _load_jsonl(legacy_path)
    _stop(len(legacy_events) == cfg["legacy_corpus"]["row_count"], "TASK219B_LEGACY_ROWS")
    old_anchors = derive_legacy_anchors(legacy_events)

    exp_old = cfg["legacy_corpus"]
    _stop(len(old_anchors) == exp_old["task216_anchor_rows"], "TASK219B_OLD_ANCHORS")
    _stop(len({r["event_id"] for r in old_anchors}) == exp_old["task216_anchor_events"], "TASK219B_OLD_EVENTS")
    _stop(len({identity_key(r) for r in old_anchors}) == exp_old["task216_unique_identities"], "TASK219B_OLD_IDENTITIES")

    exp_new = cfg["expected_new_runtime_counts"]
    _stop(len(new_anchors) == exp_new["anchor_rows"], "TASK219B_NEW_ANCHORS")
    _stop(len({r["event_id"] for r in new_anchors}) == exp_new["anchor_events"], "TASK219B_NEW_EVENTS")
    new_counts = _unique_counts(new_anchors)
    for key in ("unique_identities", "unique_process_identities", "unique_contract_identities"):
        _stop(new_counts[key] == exp_new[key], "TASK219B_NEW_" + key.upper())

    old_keys = {identity_key(r) for r in old_anchors}
    new_keys = {identity_key(r) for r in new_anchors}
    overlap = old_keys & new_keys
    fresh = new_keys - old_keys
    combined = old_keys | new_keys
    cross = {
        "overlapping_unique_identities": len(overlap),
        "new_unique_identities": len(fresh),
        "new_process_identities": sum(1 for t, _ in fresh if t == "PROCESS_IDENTITY"),
        "new_contract_identities": sum(1 for t, _ in fresh if t == "CONTRACT_IDENTITY"),
        "combined_anchor_rows": len(old_anchors) + len(new_anchors),
        "combined_unique_identities": len(combined),
        "combined_unique_process_identities": sum(1 for t, _ in combined if t == "PROCESS_IDENTITY"),
        "combined_unique_contract_identities": sum(1 for t, _ in combined if t == "CONTRACT_IDENTITY"),
    }
    _stop(cross == cfg["expected_cross_corpus_counts"], "TASK219B_CROSS_COUNTS")

    index = build_identity_index(old_anchors, new_anchors)
    _stop(index["audit"]["contract_identities_with_multiple_suppliers"] == 0, "TASK219B_CONTRACT_SUPPLIER_CONFLICT")

    out_new = root / cfg["outputs"]["new_anchor_fixture"]
    out_index = root / cfg["outputs"]["combined_identity_index"]
    out_evidence = root / cfg["outputs"]["evidence"]
    out_new.parent.mkdir(parents=True, exist_ok=True)
    out_index.parent.mkdir(parents=True, exist_ok=True)
    out_evidence.parent.mkdir(parents=True, exist_ok=True)

    shutil.copyfile(artifact_dir / "task219a_strong_identity_anchors.jsonl", out_new)
    _stop(sha256_path(out_new) == cfg["source_runtime"]["files"]["task219a_strong_identity_anchors.jsonl"], "TASK219B_COPIED_ANCHOR_SHA")

    index_payload = {
        **index,
        "source": {
            "task219a_run_id": cfg["source_runtime"]["run_id"],
            "task219a_artifact_id": cfg["source_runtime"]["artifact_id"],
            "task219a_anchor_sha256": cfg["source_runtime"]["files"]["task219a_strong_identity_anchors.jsonl"],
            "legacy_fixture": cfg["legacy_corpus"]["fixture"],
            "legacy_fixture_sha256": sha256_path(legacy_path),
        },
        "counts": {
            "legacy_anchor_rows": len(old_anchors),
            "new_anchor_rows": len(new_anchors),
            **cross,
        },
    }
    out_index.write_text(json.dumps(index_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    evidence = {
        "task": "TASK_219B_FULL_2026_JOM_STRONG_IDENTITY_CANONIZATION",
        "issue": cfg["issue"],
        "source_runtime": {
            "run_id": cfg["source_runtime"]["run_id"],
            "artifact_id": cfg["source_runtime"]["artifact_id"],
            "artifact_zip_sha256": cfg["source_runtime"]["artifact_zip_sha256"],
            "manifest_sha256": cfg["source_runtime"]["files"]["task219a_manifest.json"],
            "events_sha256": cfg["source_runtime"]["files"]["task219a_events_gold_sanitized.jsonl"],
            "semantics_sha256": cfg["source_runtime"]["files"]["task219a_event_semantics_sanitized.jsonl"],
            "anchors_sha256": cfg["source_runtime"]["files"]["task219a_strong_identity_anchors.jsonl"],
            "bundle_sha256": manifest["bundle_sha256"],
            "complete_87_of_87": True,
            "failure_count": 0,
        },
        "general_event_runtime_counts": manifest["counts"],
        "strong_identity_canonization": {
            "legacy_anchor_rows": len(old_anchors),
            "legacy_anchor_events": len({r["event_id"] for r in old_anchors}),
            "legacy_unique_identities": len(old_keys),
            "new_anchor_rows": len(new_anchors),
            "new_anchor_events": len({r["event_id"] for r in new_anchors}),
            **new_counts,
            **cross,
            "cross_corpus_overlap": [
                {"anchor_type": t, "anchor_value": v} for t, v in sorted(overlap)
            ],
            "process_identities_with_multiple_suppliers": index["audit"]["process_identities_with_multiple_suppliers"],
            "contract_identities_with_multiple_suppliers": index["audit"]["contract_identities_with_multiple_suppliers"],
        },
        "scientific_adjudication": {
            "end_to_end_jom_pncp_tce_chain_proven": False,
            "question_promotion_performed": False,
            "contextual_paths_before": 34,
            "contextual_paths_after": 34,
            "canonical_questions_total": 38,
            "remaining_blockers": ["CTRL_Q2", "PROC_Q1", "PROC_Q2", "PROC_Q3"],
            "next_step": "FRESH_BOUNDED_PNCP_EXACT_IDENTIFIER_BRIDGE_AGAINST_303_UNIQUE_JOM_IDENTITIES",
            "weak_match_promotion_forbidden": True,
            "process_multi_supplier_is_expected_for_multi_lot_or_registry_events": True,
            "contract_multi_supplier_conflict_count": 0,
        },
        "outputs": {
            "new_anchor_fixture": cfg["outputs"]["new_anchor_fixture"],
            "new_anchor_fixture_sha256": sha256_path(out_new),
            "combined_identity_index": cfg["outputs"]["combined_identity_index"],
            "combined_identity_index_sha256": sha256_path(out_index),
        },
        "remote_effects": cfg["remote_effects"],
    }
    out_evidence.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return evidence


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        raise SystemExit("usage: python -m robo_dados_publicos.research.task219b_jom_strong_identity_canonization ARTIFACT_DIR")
    evidence = canonize(Path(args[0]))
    print("TASK219B_STATUS=PASS_CANONICAL_STRONG_IDENTITY_INDEX")
    print("TASK219B_NEW_UNIQUE_IDENTITIES=" + str(evidence["strong_identity_canonization"]["new_unique_identities"]))
    print("TASK219B_COMBINED_UNIQUE_IDENTITIES=" + str(evidence["strong_identity_canonization"]["combined_unique_identities"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/task253_jom_pncp_explicit_control_canonization.v1.json"

PNCP_ID_RE = re.compile(
    r"PNCP\s*ID\s*:\s*([0-9][0-9\s]*)\s*-\s*([0-9]+)\s*-\s*([0-9][0-9\s]*)\s*/\s*(20\d{2})",
    re.IGNORECASE,
)
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
PROCESS_RE = re.compile(r"^\d{1,3}(?:\.\d{3})*/\d{4}$")
CONTRACT_RE = re.compile(r"^\d+/\d{4}$")


class Task253Error(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task253Error(code)


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_config(path: Path | str = DEFAULT_CONFIG) -> dict[str, Any]:
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(cfg.get("schema") == "TASK253_JOM_PNCP_EXPLICIT_CONTROL_CANONIZATION_V1", "TASK253_CONFIG_SCHEMA")
    _stop(cfg.get("task") == "TASK_253", "TASK253_CONFIG_TASK")
    _stop(cfg.get("issue") == 839, "TASK253_CONFIG_ISSUE")
    _stop(cfg.get("mode") == "T0_OFFLINE_CANONIZATION_OF_PINNED_TASK252_SANITIZED_RUNTIME_ARTIFACT", "TASK253_CONFIG_MODE")

    source = cfg.get("source_runtime") or {}
    _stop(source.get("implementation_sha") == cfg.get("base_main_sha"), "TASK253_IMPLEMENTATION_SHA")
    for key in ("implementation_sha", "runtime_head_sha"):
        _stop(bool(re.fullmatch(r"[0-9a-f]{40}", str(source.get(key, "")))), "TASK253_SOURCE_" + key.upper())
    _stop(source.get("run_id") == 35279271730, "TASK253_RUN")
    _stop(source.get("job_id") == 105397199842, "TASK253_JOB")
    _stop(source.get("artifact_id") == 10521364762, "TASK253_ARTIFACT")
    _stop(source.get("artifact_name") == "task-252-jom-7321-7324-general-redigest-sanitized", "TASK253_ARTIFACT_NAME")
    _stop(bool(HEX64_RE.fullmatch(str(source.get("artifact_zip_sha256", "")))), "TASK253_ARTIFACT_ZIP_SHA")
    _stop(bool(HEX64_RE.fullmatch(str(source.get("bundle_sha256", "")))), "TASK253_BUNDLE_SHA")

    expected_files = {
        "task252_manifest.json",
        "task252_events_gold_sanitized.jsonl",
        "task252_event_semantics_sanitized.jsonl",
        "task252_strong_identity_anchors.jsonl",
    }
    _stop(set((source.get("files") or {}).keys()) == expected_files, "TASK253_SOURCE_FILESET")
    _stop(all(HEX64_RE.fullmatch(str(v)) for v in source["files"].values()), "TASK253_SOURCE_FILE_HASH")

    expected = cfg.get("expected_task252") or {}
    _stop(expected.get("status") == "PASS_COMPLETE_4_DOCUMENT_GENERAL_EVENT_REDIGEST", "TASK253_SOURCE_STATUS")
    _stop(expected.get("complete_scope") is True, "TASK253_SOURCE_SCOPE")
    _stop(expected.get("editions") == [7321, 7322, 7323, 7324], "TASK253_SOURCE_EDITIONS")
    _stop(expected.get("document_download_count") == 4, "TASK253_SOURCE_DOWNLOADS")
    _stop(expected.get("aggregate_document_bytes") == 230331629, "TASK253_SOURCE_BYTES")
    _stop(expected.get("event_count") == 677, "TASK253_SOURCE_EVENTS")
    _stop(expected.get("semantic_count") == 677, "TASK253_SOURCE_SEMANTICS")
    _stop(expected.get("strong_anchor_rows") == 20, "TASK253_SOURCE_ANCHORS")
    _stop(expected.get("strong_anchor_events") == 18, "TASK253_SOURCE_ANCHOR_EVENTS")
    _stop(expected.get("sparse_pages") == 0, "TASK253_SOURCE_SPARSE")

    docs = expected.get("documents") or []
    _stop([d.get("edition") for d in docs] == [7321, 7322, 7323, 7324], "TASK253_DOCUMENT_SCOPE")
    _stop(sum(int(d.get("bytes", 0)) for d in docs) == 230331629, "TASK253_DOCUMENT_BYTES")
    _stop(sum(int(d.get("event_count", 0)) for d in docs) == 677, "TASK253_DOCUMENT_EVENTS")
    _stop(sum(int(d.get("semantic_count", 0)) for d in docs) == 677, "TASK253_DOCUMENT_SEMANTICS")
    _stop(sum(int(d.get("strong_anchor_count", 0)) for d in docs) == 20, "TASK253_DOCUMENT_ANCHORS")
    for d in docs:
        _stop(bool(HEX64_RE.fullmatch(str(d.get("sha256", "")))), "TASK253_DOCUMENT_SHA")
        _stop(str(d.get("source_id", "")).startswith("LIMEIRA_JO_"), "TASK253_DOCUMENT_SOURCE_ID")
        _stop(str(d.get("document_url", "")).startswith("https://ecrie.com.br/"), "TASK253_DOCUMENT_URL")

    rule = cfg.get("explicit_pncp_rule") or {}
    _stop(rule.get("limeira_cnpj") == "45132495000140", "TASK253_PNCP_CNPJ")
    _stop(rule.get("control_kind") == "1", "TASK253_PNCP_KIND")
    _stop(rule.get("sequence_width") == 6, "TASK253_PNCP_WIDTH")
    _stop(rule.get("year") == 2026, "TASK253_PNCP_YEAR")
    _stop(rule.get("allowed_event_types") == ["EDITAL"], "TASK253_PNCP_EVENT_TYPES")
    _stop(rule.get("evidence_class") == "EXPLICIT_PNCP_ID_IN_OFFICIAL_JOM_TEXT", "TASK253_PNCP_EVIDENCE_CLASS")
    _stop(rule.get("source_field") == "excerpt_redacted", "TASK253_PNCP_SOURCE_FIELD")
    _stop(rule.get("identity_is_direct_textual_candidate") is True, "TASK253_PNCP_DIRECT")
    for key in ("remote_resolution_proven_by_this_task", "tce_chain_proven_by_this_task", "similarity_identity_allowed", "cnpj_alone_is_identity"):
        _stop(rule.get(key) is False, "TASK253_PNCP_GUARD_" + key.upper())

    remote = cfg.get("remote_effects") or {}
    _stop(remote and all(v is False for v in remote.values()), "TASK253_REMOTE_EFFECTS")
    _stop(cfg.get("next_gate") == "BOUNDED_EXACT_8_PNCP_CONTROL_REMOTE_RESOLUTION_REQUIRES_SEPARATE_AUTHORIZATION", "TASK253_NEXT_GATE")
    return cfg


def normalize_explicit_pncp_controls(text: str, cfg: Mapping[str, Any]) -> list[str]:
    rule = cfg["explicit_pncp_rule"]
    controls: list[str] = []
    for match in PNCP_ID_RE.finditer(text or ""):
        cnpj = re.sub(r"\s+", "", match.group(1))
        kind = match.group(2)
        sequence = re.sub(r"\s+", "", match.group(3))
        year = int(match.group(4))
        _stop(cnpj == rule["limeira_cnpj"], "TASK253_PNCP_FOREIGN_CNPJ")
        _stop(kind == rule["control_kind"], "TASK253_PNCP_UNEXPECTED_KIND")
        _stop(sequence.isdigit() and 1 <= len(sequence) <= rule["sequence_width"], "TASK253_PNCP_SEQUENCE")
        _stop(year == rule["year"], "TASK253_PNCP_YEAR_DRIFT")
        normalized = f"{cnpj}-{kind}-{int(sequence):0{rule['sequence_width']}d}/{year}"
        _stop(bool(re.fullmatch(r"45132495000140-1-\d{6}/2026", normalized)), "TASK253_PNCP_NORMALIZED_FORMAT")
        controls.append(normalized)
    return controls


def build_explicit_pncp_anchors(events: Iterable[Mapping[str, Any]], cfg: Mapping[str, Any]) -> list[dict[str, Any]]:
    rule = cfg["explicit_pncp_rule"]
    documents = {int(d["edition"]): d for d in cfg["expected_task252"]["documents"]}
    anchors: list[dict[str, Any]] = []
    seen_events: set[str] = set()
    for event in events:
        event_id = str(event.get("event_id", ""))
        _stop(event_id.startswith("JOEV_"), "TASK253_EVENT_ID")
        _stop(event_id not in seen_events, "TASK253_DUPLICATE_EVENT")
        seen_events.add(event_id)
        _stop(event.get("event_type") in rule["allowed_event_types"], "TASK253_EVENT_TYPE")
        edition = int(event.get("edition", 0))
        _stop(edition in documents, "TASK253_EVENT_EDITION")
        expected_doc = documents[edition]
        _stop(event.get("source_id") == expected_doc["source_id"], "TASK253_EVENT_SOURCE_ID")
        _stop(event.get("source_sha256") == expected_doc["sha256"], "TASK253_EVENT_SOURCE_SHA")
        _stop(event.get("source_url") == expected_doc["document_url"], "TASK253_EVENT_SOURCE_URL")
        _stop(event.get("publication_date") == expected_doc["publication_date"], "TASK253_EVENT_PUBLICATION_DATE")
        _stop(isinstance(event.get("page_number"), int) and event["page_number"] > 0, "TASK253_EVENT_PAGE")
        excerpt = str(event.get(rule["source_field"], ""))
        _stop(bool(excerpt), "TASK253_EVENT_EXCERPT")
        _stop(event.get("excerpt_sha256") == sha256_text(excerpt), "TASK253_EVENT_EXCERPT_SHA")
        _stop("PNCP" in excerpt.upper(), "TASK253_EVENT_PNCP_LABEL")
        controls = normalize_explicit_pncp_controls(excerpt, cfg)
        _stop(len(controls) == 1, "TASK253_EVENT_EXACTLY_ONE_CONTROL")
        anchors.append(
            {
                "anchor_type": "PNCP_PURCHASE_CONTROL",
                "anchor_value": controls[0],
                "evidence_class": rule["evidence_class"],
                "event_id": event_id,
                "event_type": event["event_type"],
                "edition": edition,
                "page_number": event["page_number"],
                "publication_date": event["publication_date"],
                "source_id": event["source_id"],
                "source_sha256": event["source_sha256"],
                "source_url": event["source_url"],
                "excerpt_sha256": event["excerpt_sha256"],
            }
        )
    return sorted(anchors, key=lambda r: (r["edition"], r["page_number"], r["event_id"], r["anchor_value"]))


def validate_strong_anchors(rows: list[dict[str, Any]], cfg: Mapping[str, Any]) -> dict[str, int]:
    documents = {int(d["edition"]): d for d in cfg["expected_task252"]["documents"]}
    for row in rows:
        _stop(row.get("anchor_type") in {"PROCESS_IDENTITY", "CONTRACT_IDENTITY"}, "TASK253_STRONG_TYPE")
        value = str(row.get("anchor_value", ""))
        if row["anchor_type"] == "PROCESS_IDENTITY":
            _stop(bool(PROCESS_RE.fullmatch(value)), "TASK253_STRONG_PROCESS")
        else:
            _stop(bool(CONTRACT_RE.fullmatch(value)), "TASK253_STRONG_CONTRACT")
        edition = int(row.get("edition", 0))
        _stop(edition in documents, "TASK253_STRONG_EDITION")
        _stop(row.get("source_sha256") == documents[edition]["sha256"], "TASK253_STRONG_SOURCE_SHA")
        _stop(str(row.get("event_id", "")).startswith("JOEV_"), "TASK253_STRONG_EVENT_ID")
        _stop(isinstance(row.get("page_number"), int) and row["page_number"] > 0, "TASK253_STRONG_PAGE")
    identities = {(r["anchor_type"], r["anchor_value"]) for r in rows}
    return {
        "strong_anchor_rows": len(rows),
        "strong_anchor_events": len({r["event_id"] for r in rows}),
        "strong_unique_identities": len(identities),
        "strong_unique_process_identities": sum(1 for t, _ in identities if t == "PROCESS_IDENTITY"),
        "strong_unique_contract_identities": sum(1 for t, _ in identities if t == "CONTRACT_IDENTITY"),
    }


def validate_prior_99_overlap(rows: list[dict[str, Any]], prior_index: Mapping[str, Any], cfg: Mapping[str, Any]) -> dict[str, int]:
    _stop(prior_index.get("schema") == cfg["prior_canonical_index"]["schema"], "TASK253_PRIOR_INDEX_SCHEMA")
    identities = prior_index.get("identities") or []
    prior = {(r["anchor_type"], r["anchor_value"]) for r in identities}
    current = {(r["anchor_type"], r["anchor_value"]) for r in rows}
    overlap = prior & current
    new_only = current - prior
    process_new = sum(1 for t, _ in new_only if t == "PROCESS_IDENTITY")
    contract_new = sum(1 for t, _ in new_only if t == "CONTRACT_IDENTITY")
    return {
        "prior_99_unique_identities": len(prior),
        "strong_overlap_with_prior_99": len(overlap),
        "strong_new_only_vs_prior_99": len(new_only),
        "projected_103_unique_identities": len(prior | current),
        "projected_103_unique_process_identities": sum(1 for t, _ in (prior | current) if t == "PROCESS_IDENTITY"),
        "projected_103_unique_contract_identities": sum(1 for t, _ in (prior | current) if t == "CONTRACT_IDENTITY"),
        "new_process_identities_vs_prior_99": process_new,
        "new_contract_identities_vs_prior_99": contract_new,
    }


def validate_committed_outputs(root: Path = ROOT) -> dict[str, Any]:
    cfg = load_config(root / "config/task253_jom_pncp_explicit_control_canonization.v1.json")
    outputs = cfg["outputs"]
    strong_path = root / outputs["strong_anchors_fixture"]
    event_path = root / outputs["explicit_pncp_source_events_fixture"]
    pncp_path = root / outputs["explicit_pncp_control_anchors_fixture"]
    evidence_path = root / outputs["evidence"]
    prior_path = root / cfg["prior_canonical_index"]["path"]
    for path in (strong_path, event_path, pncp_path, evidence_path, prior_path):
        _stop(path.is_file(), "TASK253_REQUIRED_FILE_" + path.name.upper())

    strong = _load_jsonl(strong_path)
    events = _load_jsonl(event_path)
    committed_pncp = _load_jsonl(pncp_path)
    derived_pncp = build_explicit_pncp_anchors(events, cfg)
    _stop(derived_pncp == committed_pncp, "TASK253_PNCP_REDERIVATION")

    strong_counts = validate_strong_anchors(strong, cfg)
    prior_index = json.loads(prior_path.read_text(encoding="utf-8"))
    overlap_counts = validate_prior_99_overlap(strong, prior_index, cfg)
    expected = cfg["expected_outputs"]
    for key, value in {**strong_counts, **overlap_counts}.items():
        if key in expected:
            _stop(value == expected[key], "TASK253_EXPECTED_" + key.upper())

    _stop(len(events) == expected["explicit_pncp_source_events"], "TASK253_EXPECTED_SOURCE_EVENTS")
    _stop(len(committed_pncp) == expected["explicit_pncp_anchor_rows"], "TASK253_EXPECTED_PNCP_ROWS")
    _stop(len({r["anchor_value"] for r in committed_pncp}) == expected["explicit_pncp_unique_controls"], "TASK253_EXPECTED_PNCP_UNIQUE")

    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    _stop(evidence.get("schema") == "TASK253_JOM_PNCP_EXPLICIT_CONTROL_CANONIZATION_RESULT_V1", "TASK253_EVIDENCE_SCHEMA")
    _stop(evidence.get("status") == "PASS_TASK252_CANONIZED_AND_8_EXPLICIT_PNCP_CONTROLS_MATERIALIZED", "TASK253_EVIDENCE_STATUS")
    materialized = evidence.get("materialized") or {}
    _stop(materialized.get("strong_anchor_fixture_sha256") == sha256_path(strong_path), "TASK253_EVIDENCE_STRONG_SHA")
    _stop(materialized.get("explicit_pncp_source_events_fixture_sha256") == sha256_path(event_path), "TASK253_EVIDENCE_EVENTS_SHA")
    _stop(materialized.get("explicit_pncp_control_anchors_fixture_sha256") == sha256_path(pncp_path), "TASK253_EVIDENCE_PNCP_SHA")
    _stop(materialized.get("explicit_pncp_controls") == [r["anchor_value"] for r in committed_pncp], "TASK253_EVIDENCE_CONTROLS")
    _stop(evidence.get("remote_effects") == cfg["remote_effects"], "TASK253_EVIDENCE_REMOTE_EFFECTS")
    _stop(evidence.get("next_gate") == cfg["next_gate"], "TASK253_EVIDENCE_NEXT_GATE")

    return {
        "status": "PASS_TASK253_JOM_PNCP_EXPLICIT_CONTROL_CANONIZATION",
        "strong_anchor_rows": len(strong),
        "strong_unique_identities": strong_counts["strong_unique_identities"],
        "explicit_pncp_controls": len(committed_pncp),
        "new_strong_identities_vs_prior_99": overlap_counts["strong_new_only_vs_prior_99"],
        "projected_103_unique_identities": overlap_counts["projected_103_unique_identities"],
        "next_gate": cfg["next_gate"],
    }


def validate_runtime_artifact(artifact_dir: Path, cfg: Mapping[str, Any]) -> dict[str, Any]:
    expected_files = cfg["source_runtime"]["files"]
    actual = {p.name for p in artifact_dir.iterdir() if p.is_file()}
    _stop(actual == set(expected_files), "TASK253_ARTIFACT_FILESET")
    for name, digest in expected_files.items():
        _stop(sha256_path(artifact_dir / name) == digest, "TASK253_ARTIFACT_FILE_SHA_" + name.upper().replace(".", "_"))

    manifest = json.loads((artifact_dir / "task252_manifest.json").read_text(encoding="utf-8"))
    result = manifest.get("result") or {}
    expected = cfg["expected_task252"]
    _stop(result.get("status") == expected["status"], "TASK253_ARTIFACT_STATUS")
    _stop(result.get("complete_scope") is True, "TASK253_ARTIFACT_SCOPE")
    _stop(result.get("canonical_binary_scope") == expected["editions"], "TASK253_ARTIFACT_EDITIONS")
    _stop(result.get("document_download_count") == expected["document_download_count"], "TASK253_ARTIFACT_DOWNLOADS")
    _stop(result.get("aggregate_document_bytes") == expected["aggregate_document_bytes"], "TASK253_ARTIFACT_BYTES")
    counts = result.get("counts") or {}
    _stop(counts.get("event_count") == expected["event_count"], "TASK253_ARTIFACT_EVENTS")
    _stop(counts.get("semantic_count") == expected["semantic_count"], "TASK253_ARTIFACT_SEMANTICS")
    _stop(counts.get("strong_anchor_count") == expected["strong_anchor_rows"], "TASK253_ARTIFACT_ANCHORS")
    _stop(counts.get("strong_anchor_event_count") == expected["strong_anchor_events"], "TASK253_ARTIFACT_ANCHOR_EVENTS")
    _stop(manifest.get("bundle_sha256") == cfg["source_runtime"]["bundle_sha256"], "TASK253_ARTIFACT_BUNDLE")
    for key in ("raw_pdf_persisted", "raw_page_text_persisted", "rag_chunks_persisted", "accounting_query_tasks_persisted", "promotion_performed"):
        _stop(result.get(key) is False, "TASK253_ARTIFACT_GUARD_" + key.upper())
    for key in ("drive_write_count", "bronze_created", "silver_created", "gold_created", "serving_write_count", "publication_count"):
        _stop(result.get(key) == 0, "TASK253_ARTIFACT_ZERO_" + key.upper())
    return result

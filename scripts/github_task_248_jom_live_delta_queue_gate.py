from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_248_JOM_LIVE_DELTA_CANONICAL_0.8.0.json"
QUEUE = ROOT / "config/task248_jom_bounded_ingestion_queue.v1.json"
TASK247 = ROOT / "config/task247_jom_rolling_discovery.v1.json"

EXPECTED_RESULT_SHA256 = "28701eb442dee5bc74e34fe9c7c5a21cec27ffcbae680fe0988ef4a64c978b6d"
EXPECTED_EDITIONS = [7321, 7322, 7323, 7324]
EXPECTED_BASELINE = [7316, 7317, 7318, 7319, 7320]


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError(code)


def canonical_result_hash(result: Mapping[str, Any]) -> str:
    payload = dict(result)
    payload.pop("result_sha256", None)
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def validate_payloads(
    evidence: Mapping[str, Any],
    queue: Mapping[str, Any],
    task247: Mapping[str, Any],
) -> dict[str, Any]:
    require(evidence.get("schema") == "TASK248_JOM_LIVE_DELTA_CANONICAL_V1", "TASK248_EVIDENCE_SCHEMA")
    require(evidence.get("task") == "TASK_248", "TASK248_EVIDENCE_TASK")
    require(evidence.get("issue") == 826, "TASK248_EVIDENCE_ISSUE")
    require(evidence.get("status") == "PASS_TASK247_LIVE_DELTA_CANONIZED", "TASK248_EVIDENCE_STATUS")

    provenance = evidence.get("provenance", {})
    expected_provenance = {
        "repository": "ferinbon-cpu/robo-dados-publicos",
        "implementation_sha": "3c3b59606ecafbd48fe634ef850543ac03c72bdc",
        "runtime_branch": "task-247-jom-rolling-discovery-runtime",
        "runtime_sha": "cbaa17bb14a90bf171c10f090e9f596896120368",
        "workflow_run_id": 35151868669,
        "workflow_conclusion": "success",
        "artifact_id": 10469402153,
        "artifact_name": "task-247-jom-rolling-sanitized-discovery",
        "artifact_zip_digest": "sha256:bea443dcec80cd271e6902c3f16cdf0ee65dea0468a90a5d35d14b013ccdbb7f",
        "sanitized_result_sha256": EXPECTED_RESULT_SHA256,
    }
    require(provenance == expected_provenance, "TASK248_PROVENANCE_DRIFT")

    live = evidence.get("live_result", {})
    require(live.get("schema") == "TASK247_JOM_ROLLING_DISCOVERY_RESULT_V1", "TASK248_LIVE_SCHEMA")
    require(live.get("status") == "PASS_JOM_ROLLING_DELTA_DISCOVERY", "TASK248_LIVE_STATUS")
    require(live.get("baseline_verified") is True, "TASK248_BASELINE_NOT_VERIFIED")
    require(live.get("observed_window_complete") is True, "TASK248_WINDOW_NOT_COMPLETE")
    require(live.get("absence_inference_allowed") is False, "TASK248_ABSENCE_INFERENCE")
    require(live.get("future_editions_inference_allowed") is False, "TASK248_FUTURE_INFERENCE")
    require(live.get("delta_count") == 4, "TASK248_DELTA_COUNT")
    require(live.get("index_pages_fetched") == 1, "TASK248_INDEX_PAGES")
    require(live.get("estimated_remote_get_count") == 2, "TASK248_REMOTE_GETS")
    for key in ("document_download_count", "drive_write_count", "serving_write_count", "publication_count"):
        require(live.get(key) == 0, f"TASK248_LIVE_{key.upper()}")
    for key in ("promotion_performed", "recurrence_performed", "schedule_performed"):
        require(live.get(key) is False, f"TASK248_LIVE_{key.upper()}")

    scope = live.get("scope", {})
    require(scope == {"end_date": "2026-09-16", "month": 9, "start_date": "2026-09-09", "year": 2026}, "TASK248_SCOPE")
    baseline = live.get("baseline", {})
    require(baseline.get("through_date") == "2026-09-08", "TASK248_BASELINE_DATE")
    require(baseline.get("total_document_count") == 99, "TASK248_BASELINE_TOTAL")
    require(baseline.get("september_editions") == EXPECTED_BASELINE, "TASK248_BASELINE_EDITIONS")

    computed_hash = canonical_result_hash(live)
    require(live.get("result_sha256") == EXPECTED_RESULT_SHA256, "TASK248_LIVE_HASH_FIELD")
    require(provenance.get("sanitized_result_sha256") == EXPECTED_RESULT_SHA256, "TASK248_PROVENANCE_HASH")
    require(computed_hash == EXPECTED_RESULT_SHA256, "TASK248_RESULT_HASH_RECOMPUTE")

    require(task247.get("schema") == "TASK247_JOM_ROLLING_DISCOVERY_V1", "TASK248_TASK247_SCHEMA")
    require(task247.get("issue") == 821, "TASK248_TASK247_ISSUE")
    require(task247.get("scope") == scope, "TASK248_TASK247_SCOPE_DRIFT")
    require(task247.get("baseline", {}).get("september_editions") == EXPECTED_BASELINE, "TASK248_TASK247_BASELINE_DRIFT")
    require(task247.get("source", {}).get("family") == "LIMEIRA_JORNAL_OFICIAL", "TASK248_SOURCE_FAMILY_DRIFT")

    require(queue.get("schema") == "TASK248_JOM_BOUNDED_INGESTION_QUEUE_V1", "TASK248_QUEUE_SCHEMA")
    require(queue.get("task") == "TASK_248", "TASK248_QUEUE_TASK")
    require(queue.get("issue") == 826, "TASK248_QUEUE_ISSUE")
    require(queue.get("status") == "INERT_OFFLINE_QUEUE_READY_FOR_SEPARATE_AUTHORIZATION", "TASK248_QUEUE_STATUS")
    require(queue.get("canonical_live_evidence") == "docs/evidence/TASK_248_JOM_LIVE_DELTA_CANONICAL_0.8.0.json", "TASK248_QUEUE_EVIDENCE_PATH")
    require(queue.get("queue_count") == 4, "TASK248_QUEUE_COUNT")

    items = queue.get("items")
    require(isinstance(items, list) and len(items) == 4, "TASK248_QUEUE_ITEMS")
    require(items == live.get("delta_editions"), "TASK248_QUEUE_NE_LIVE_DELTA")
    editions = [row.get("edition") for row in items]
    require(editions == EXPECTED_EDITIONS, "TASK248_QUEUE_EDITIONS")
    require(len(set(editions)) == len(editions), "TASK248_DUPLICATE_EDITION")
    require(not set(editions).intersection(EXPECTED_BASELINE), "TASK248_BASELINE_OVERLAP")
    require(min(editions) > max(EXPECTED_BASELINE), "TASK248_NON_MONOTONIC_EDITION")

    source_ids = [row.get("source_id") for row in items]
    logical_keys = [row.get("logical_key") for row in items]
    require(len(set(source_ids)) == 4, "TASK248_DUPLICATE_SOURCE_ID")
    require(len(set(logical_keys)) == 4, "TASK248_DUPLICATE_LOGICAL_KEY")

    allowed_hosts = set(queue.get("source", {}).get("allowed_document_hosts", []))
    require(allowed_hosts == {"ecrie.com.br"}, "TASK248_ALLOWED_HOSTS")
    for row in items:
        edition = row["edition"]
        require(row.get("source_id") == f"LIMEIRA_JO_{edition:05d}", "TASK248_SOURCE_ID")
        require(row.get("logical_key") == f"limeira/jornal_oficial/edicao/{edition}", "TASK248_LOGICAL_KEY")
        require("2026-09-09" <= row.get("publication_date", "") <= "2026-09-16", "TASK248_PUBLICATION_DATE")
        parsed = urlparse(str(row.get("document_url") or ""))
        require(parsed.scheme == "https", "TASK248_DOCUMENT_HTTPS")
        require((parsed.hostname or "").lower() in allowed_hosts, "TASK248_DOCUMENT_HOST")

    effects = queue.get("effects", {})
    expected_effect_keys = {
        "source_network", "document_download", "raw_html_persisted", "raw_pdf_persisted",
        "drive_write", "serving_write", "publication", "promotion", "recurrence", "schedule",
    }
    require(set(effects) == expected_effect_keys, "TASK248_EFFECT_KEYS")
    require(all(value is False for value in effects.values()), "TASK248_EFFECT_NOT_INERT")

    interpretation = evidence.get("interpretation", {})
    require(interpretation.get("absence_inference_allowed") is False, "TASK248_INTERPRETATION_ABSENCE")
    require(interpretation.get("future_editions_inference_allowed") is False, "TASK248_INTERPRETATION_FUTURE")
    require(interpretation.get("document_ingestion_authorized") is False, "TASK248_INGESTION_AUTH")
    require(interpretation.get("recurrence_authorized") is False, "TASK248_RECURRENCE_AUTH")
    require(interpretation.get("schedule_authorized") is False, "TASK248_SCHEDULE_AUTH")

    required_guards = {
        "LIVE_RESULT_MUST_MATCH_TASK247_CONTRACT",
        "RUN_AND_ARTIFACT_PROVENANCE_PINNED",
        "RESULT_HASH_MUST_RECOMPUTE",
        "QUEUE_COUNT_EXACTLY_4",
        "QUEUE_IDS_EXACTLY_7321_7322_7323_7324",
        "NO_BASELINE_OVERLAP",
        "NO_ABSENCE_INFERENCE",
        "NO_PDF_DOWNLOAD",
        "NO_SOURCE_NETWORK",
        "NO_DRIVE_WRITE",
        "NO_SERVING_WRITE",
        "NO_PUBLICATION",
        "NO_PROMOTION",
        "NO_SCHEDULE",
        "NO_RECURRENCE",
    }
    require(required_guards.issubset(set(queue.get("guards", []))), "TASK248_GUARDS")

    return {
        "schema": "TASK248_JOM_LIVE_DELTA_QUEUE_GATE_RESULT_V1",
        "status": "PASS",
        "result_sha256": computed_hash,
        "baseline_total": 99,
        "delta_count": 4,
        "delta_editions": EXPECTED_EDITIONS,
        "source_network": False,
        "document_download": False,
        "drive_write": False,
        "serving_write": False,
        "publication": False,
        "promotion": False,
        "recurrence": False,
        "schedule": False,
        "next_gate": queue.get("next_gate"),
    }


def validate_files() -> dict[str, Any]:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    task247 = json.loads(TASK247.read_text(encoding="utf-8"))
    return validate_payloads(evidence, queue, task247)


def main() -> int:
    print(json.dumps(validate_files(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

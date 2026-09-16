#!/usr/bin/env python3
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_248_JOM_LIVE_DELTA_CANONICAL_RESULT_0.8.0.json"

EXPECTED_IMPL = "3c3b59606ecafbd48fe634ef850543ac03c72bdc"
EXPECTED_RUNTIME = "cbaa17bb14a90bf171c10f090e9f596896120368"
EXPECTED_RUN = 35151868669
EXPECTED_RESULT_SHA = "28701eb442dee5bc74e34fe9c7c5a21cec27ffcbae680fe0988ef4a64c978b6d"
EXPECTED_ZIP_SHA = "bea443dcec80cd271e6902c3f16cdf0ee65dea0468a90a5d35d14b013ccdbb7f"
EXPECTED_EDITIONS = [(7321, "2026-09-09"), (7322, "2026-09-10"), (7323, "2026-09-11"), (7324, "2026-09-12")]
PASS = "PASS_TASK248_JOM_LIVE_DELTA_CANONIZED"


def req(ok: bool, code: str) -> None:
    if not ok:
        raise ValueError(code)


def validate(evidence: dict) -> None:
    req(evidence.get("schema") == "TASK248_JOM_LIVE_DELTA_CANONICAL_RESULT_V1", "TASK248_SCHEMA")
    req(evidence.get("task") == "TASK_248" and evidence.get("issue") == 824, "TASK248_IDENTITY")
    req(evidence.get("status") == "PASS_JOM_ROLLING_DELTA_CANONIZED", "TASK248_STATUS")
    req(evidence.get("implementation_sha") == EXPECTED_IMPL, "TASK248_IMPL_SHA")
    req(evidence.get("runtime_head_sha") == EXPECTED_RUNTIME, "TASK248_RUNTIME_SHA")
    req(evidence.get("workflow_run_id") == EXPECTED_RUN and evidence.get("workflow_conclusion") == "success", "TASK248_RUN")

    source = evidence["source_result"]
    req(source.get("status") == "PASS_JOM_ROLLING_DELTA_DISCOVERY", "TASK248_SOURCE_STATUS")
    req(source.get("result_sha256") == EXPECTED_RESULT_SHA, "TASK248_RESULT_SHA")
    req(source.get("artifact_zip_sha256") == EXPECTED_ZIP_SHA, "TASK248_ARTIFACT_SHA")

    baseline = evidence["baseline"]
    req(baseline.get("through_date") == "2026-09-08", "TASK248_BASELINE_DATE")
    req(baseline.get("total_document_count") == 99, "TASK248_BASELINE_COUNT")
    req(baseline.get("september_editions") == [7316, 7317, 7318, 7319, 7320], "TASK248_BASELINE_EDITIONS")
    req(baseline.get("baseline_verified") is True, "TASK248_BASELINE_VERIFY")

    scope = evidence["scope"]
    req(scope.get("start_date") == "2026-09-09" and scope.get("end_date") == "2026-09-16", "TASK248_SCOPE")
    req(scope.get("observed_window_complete") is True, "TASK248_WINDOW")
    req(scope.get("absence_inference_allowed") is False and scope.get("future_editions_inference_allowed") is False, "TASK248_ABSENCE_GUARD")

    rows = evidence["delta_editions"]
    req(evidence.get("delta_count") == 4 and len(rows) == 4, "TASK248_DELTA_COUNT")
    req([(r["edition"], r["publication_date"]) for r in rows] == EXPECTED_EDITIONS, "TASK248_DELTA_IDENTITY")
    req(len({r["source_id"] for r in rows}) == 4 and len({r["logical_key"] for r in rows}) == 4, "TASK248_DUPLICATE")
    for row in rows:
        parsed = urlparse(row["document_url"])
        req(parsed.scheme == "https" and parsed.hostname == "ecrie.com.br" and parsed.path.lower().endswith(".pdf"), "TASK248_DOCUMENT_ROUTE")

    execution = evidence["execution"]
    req(execution.get("index_pages_fetched") == 1 and execution.get("estimated_remote_get_count") == 2, "TASK248_BOUNDED_GETS")
    for key in ("document_download_count", "drive_write_count", "serving_write_count", "publication_count"):
        req(execution.get(key) == 0, "TASK248_SIDE_EFFECT_" + key.upper())
    for key in ("promotion_performed", "recurrence_performed", "schedule_performed"):
        req(execution.get(key) is False, "TASK248_SIDE_EFFECT_" + key.upper())

    boundary = evidence["canonical_boundary"]
    req(boundary.get("metadata_identity_only") is True and boundary.get("pdf_contents_proven") is False, "TASK248_METADATA_ONLY")
    for key in ("document_ingestion_authorized", "recurrence_authorized", "schedule_authorized", "serving_authorized", "release_promotion_authorized"):
        req(boundary.get(key) is False, "TASK248_AUTH_BOUNDARY_" + key.upper())


def main() -> int:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    validate(evidence)
    print(PASS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

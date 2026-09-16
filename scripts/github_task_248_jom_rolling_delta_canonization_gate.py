#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/task248_jom_rolling_delta_canonization.v1.json"
SANITIZED = ROOT / "docs/evidence/TASK_248_JOM_ROLLING_DELTA_SANITIZED_RESULT_0.8.0.json"
CANONICAL = ROOT / "docs/evidence/TASK_248_JOM_ROLLING_DELTA_CANONICAL_RESULT_0.8.0.json"
PRIOR = ROOT / "docs/evidence/TASK_217C_JOM_2026_DISCOVERY_CANONICAL_RESULT_0.8.0.json"
TASK_DOC = ROOT / "docs/tasks/TASK_248_JOM_ROLLING_DELTA_CANONIZATION.md"


def req(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run() -> dict:
    cfg = _load(CONFIG)
    sanitized = _load(SANITIZED)
    canonical = _load(CANONICAL)
    prior = _load(PRIOR)
    task_doc = TASK_DOC.read_text(encoding="utf-8")

    req(cfg.get("schema") == "TASK248_JOM_ROLLING_DELTA_CANONIZATION_V1", "STOP_TASK248_SCHEMA")
    req(cfg.get("task") == "TASK_248" and cfg.get("issue") == 823, "STOP_TASK248_IDENTITY")
    req(cfg.get("base_main_sha") == "3c3b59606ecafbd48fe634ef850543ac03c72bdc", "STOP_TASK248_BASE_MAIN")
    runtime = cfg["runtime"]
    req(runtime["run_id"] == 35151868669, "STOP_TASK248_RUN_ID")
    req(runtime["head_sha"] == "cbaa17bb14a90bf171c10f090e9f596896120368", "STOP_TASK248_RUNTIME_HEAD")
    req(runtime["implementation_sha"] == cfg["base_main_sha"], "STOP_TASK248_IMPLEMENTATION_SHA")
    req(runtime["artifact_id"] == 10469402153, "STOP_TASK248_ARTIFACT_ID")
    req(runtime["artifact_zip_sha256"] == "bea443dcec80cd271e6902c3f16cdf0ee65dea0468a90a5d35d14b013ccdbb7f", "STOP_TASK248_ARTIFACT_ZIP_HASH")
    req(runtime["result_sha256"] == "28701eb442dee5bc74e34fe9c7c5a21cec27ffcbae680fe0988ef4a64c978b6d", "STOP_TASK248_RESULT_HASH_PIN")
    req(runtime["conclusion"] == "success", "STOP_TASK248_RUNTIME_CONCLUSION")

    req(prior.get("status") == "PASS_COMPLETE_DISCOVERY_CANONIZED", "STOP_TASK248_PRIOR_STATUS")
    req(prior.get("scope", {}).get("total_documents") == 99, "STOP_TASK248_PRIOR_COUNT")
    req(cfg["prior_baseline"]["document_count"] == 99, "STOP_TASK248_CONFIG_PRIOR_COUNT")
    req(cfg["prior_baseline"]["through_date"] == "2026-09-08", "STOP_TASK248_PRIOR_DATE")
    req(cfg["prior_baseline"]["september_editions"] == [7316, 7317, 7318, 7319, 7320], "STOP_TASK248_PRIOR_SEPTEMBER")

    req(sanitized.get("schema") == "TASK247_JOM_ROLLING_DISCOVERY_RESULT_V1", "STOP_TASK248_SANITIZED_SCHEMA")
    req(sanitized.get("status") == "PASS_JOM_ROLLING_DELTA_DISCOVERY", "STOP_TASK248_SANITIZED_STATUS")
    req(sanitized.get("baseline_verified") is True, "STOP_TASK248_BASELINE_NOT_VERIFIED")
    req(sanitized.get("delta_count") == 4, "STOP_TASK248_DELTA_COUNT")
    delta = sanitized.get("delta_editions") or []
    req([row.get("edition") for row in delta] == [7321, 7322, 7323, 7324], "STOP_TASK248_DELTA_EDITIONS")
    req([row.get("publication_date") for row in delta] == ["2026-09-09", "2026-09-10", "2026-09-11", "2026-09-12"], "STOP_TASK248_DELTA_DATES")
    req([row.get("source_id") for row in delta] == ["LIMEIRA_JO_07321", "LIMEIRA_JO_07322", "LIMEIRA_JO_07323", "LIMEIRA_JO_07324"], "STOP_TASK248_DELTA_SOURCE_IDS")
    req(all(str(row.get("document_url", "")).startswith("https://ecrie.com.br/") for row in delta), "STOP_TASK248_DOCUMENT_ROUTE")
    req(sanitized.get("index_pages_fetched") == 1, "STOP_TASK248_INDEX_PAGES")
    req(sanitized.get("estimated_remote_get_count") == 2, "STOP_TASK248_REMOTE_GETS")
    req(sanitized.get("document_download_count") == 0, "STOP_TASK248_PDF_DOWNLOAD")
    req(sanitized.get("drive_write_count") == 0 and sanitized.get("serving_write_count") == 0, "STOP_TASK248_WRITES")
    req(sanitized.get("publication_count") == 0, "STOP_TASK248_PUBLICATION")
    req(sanitized.get("promotion_performed") is False, "STOP_TASK248_PROMOTION")
    req(sanitized.get("schedule_performed") is False and sanitized.get("recurrence_performed") is False, "STOP_TASK248_RECURRENCE")
    req(sanitized.get("absence_inference_allowed") is False and sanitized.get("future_editions_inference_allowed") is False, "STOP_TASK248_ABSENCE_INFERENCE")

    payload = dict(sanitized)
    observed_hash = payload.pop("result_sha256", None)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    calculated_hash = hashlib.sha256(encoded).hexdigest()
    req(observed_hash == calculated_hash == runtime["result_sha256"], "STOP_TASK248_SANITIZED_RESULT_HASH")

    state = cfg["canonized_state"]
    req(state["status"] == "PASS_JOM_ROLLING_DELTA_CANONIZED", "STOP_TASK248_CANONIZED_STATUS")
    req(state["known_identity_count"] == 103 == 99 + sanitized["delta_count"], "STOP_TASK248_CANONICAL_COUNT")
    req(state["latest_observed_publication_date"] == "2026-09-12", "STOP_TASK248_LATEST_DATE")
    req(state["observed_window_end"] == "2026-09-16", "STOP_TASK248_WINDOW_END")
    req(state["september_known_editions"] == [7316, 7317, 7318, 7319, 7320, 7321, 7322, 7323, 7324], "STOP_TASK248_SEPTEMBER_STATE")
    req(state["identity_only"] is True and state["document_content_proven"] is False, "STOP_TASK248_IDENTITY_CONTENT_BOUNDARY")
    req(state["absence_inference_allowed"] is False and state["future_editions_inference_allowed"] is False, "STOP_TASK248_STATE_ABSENCE_INFERENCE")

    effects = cfg["remote_effects_of_canonization"]
    req(not any(effects.values()), "STOP_TASK248_REMOTE_EFFECT_ENABLED")
    req(canonical.get("status") == "PASS_JOM_ROLLING_DELTA_CANONIZED", "STOP_TASK248_CANONICAL_EVIDENCE_STATUS")
    req(canonical.get("canonized_identity_state", {}).get("known_identity_count") == 103, "STOP_TASK248_CANONICAL_EVIDENCE_COUNT")
    req(canonical.get("canonized_identity_state", {}).get("pdf_content_materialized") is False, "STOP_TASK248_CANONICAL_PDF_BOUNDARY")
    req(canonical.get("next_scope", {}).get("recurrence_authorized") is False, "STOP_TASK248_CANONICAL_RECURRENCE")
    req("103" in task_doc and "7321" in task_doc and "7324" in task_doc and "recorrência: desabilitada" in task_doc, "STOP_TASK248_TASK_DOC")

    return {
        "status": "PASS_TASK248_JOM_ROLLING_DELTA_CANONIZATION",
        "issue": 823,
        "prior_identity_count": 99,
        "delta_count": 4,
        "canonized_identity_count": 103,
        "latest_observed_publication_date": "2026-09-12",
        "observed_window_end": "2026-09-16",
        "document_downloads": 0,
        "network_during_canonization": False,
        "drive_write": False,
        "serving_write": False,
        "publication": False,
        "promotion": False,
        "schedule": False,
        "recurrence": False,
        "absence_inference_allowed": False,
    }


def main() -> int:
    try:
        print(json.dumps(run(), ensure_ascii=False, sort_keys=True))
    except Exception as exc:
        print(json.dumps({"status": "STOP_TASK248_JOM_ROLLING_DELTA_CANONIZATION", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 48
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

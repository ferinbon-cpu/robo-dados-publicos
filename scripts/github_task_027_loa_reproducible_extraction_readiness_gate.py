#!/usr/bin/env python3
"""Fail-closed offline gate for TASK 027 LOA extraction readiness."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.manual_ingest.loa_extraction import (
    choose_extraction_route,
    load_loa_extraction_contract,
    validate_numeric_candidate,
    validate_ocr_manifest,
)


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def synthetic_manifest() -> list[dict]:
    config_hash = digest("synthetic-engine-config")
    return [
        {
            "page_number": page,
            "page_image_sha256": digest(f"page-image-{page}"),
            "ocr_text_sha256": digest(f"ocr-text-{page}"),
            "ocr_text_chars": 100,
            "blank_page": False,
            "engine_name": "SYNTHETIC_TEST_ENGINE",
            "engine_version": "1.0.0",
            "engine_config_sha256": config_hash,
            "render_dpi": 300,
            "render_tool": "SYNTHETIC_RENDERER",
            "render_tool_version": "1.0.0",
            "critical_numeric_status": "REVIEW_REQUIRED" if page in {124, 127} else "NONE",
        }
        for page in range(1, 467)
    ]


def main() -> int:
    contract = load_loa_extraction_contract(
        ROOT / "config/loa_reproducible_extraction_readiness.v1.json"
    )
    fixture = load("tests/fixtures/task_027_loa_reproducible_extraction_readiness.json")
    evidence = load("docs/evidence/TASK_027_LOA_REPRODUCIBLE_EXTRACTION_READINESS_0.8.0.json")
    ci = (ROOT / ".github/workflows/ci-offline.yml").read_text(encoding="utf-8")

    ocr_plan = choose_extraction_route(contract, fixture["ocr_design"])
    manifest = validate_ocr_manifest(contract, synthetic_manifest())
    numeric = validate_numeric_candidate(contract, fixture["numeric_candidate_unreviewed"])
    effects = evidence.get("effects", {})
    auth = evidence.get("authorization", {})
    discovery = evidence.get("read_only_public_discovery_outside_repository_runtime", {})
    canonical = evidence.get("canonical_loa", {})

    checks = {
        "base_and_mode": evidence.get("base_sha") == "93129206723acbb3f986c88080d2abaec4eab5f8" and evidence.get("mode") == contract.get("mode") == "T0_OFFLINE_DESIGN",
        "canonical_source_pinned": canonical.get("sha256") == contract.get("canonical_source", {}).get("sha256") and canonical.get("pages") == 466 and canonical.get("text_layer") == "ABSENT",
        "official_route_first": contract.get("route_priority", [None])[0] == "OFFICIAL_MACHINE_READABLE_EQUIVALENT",
        "discovery_does_not_claim_absence": discovery.get("status") == "OFFICIAL_MACHINE_READABLE_EQUIVALENT_NOT_PROVEN" and discovery.get("absence_claimed") is False,
        "ocr_only_separate_review": ocr_plan.get("status") == "READY_FOR_SEPARATE_DETERMINISTIC_OCR_AUTHORIZATION_REVIEW" and ocr_plan.get("execution_authorized") is False,
        "manifest_contract": manifest.get("status") == "PASS_LOA_OCR_MANIFEST_STRUCTURE_ONLY" and manifest.get("pages") == 466 and manifest.get("silver_authorized") is False,
        "numeric_fail_closed": numeric.get("status") == "REVIEW_REQUIRED" and numeric.get("automatic_promotion") is False,
        "no_llm_numeric_reconstruction": "NO_LLM_NUMERIC_RECONSTRUCTION" in contract.get("ocr_route", {}).get("determinism_requirements", []),
        "no_silent_correction": "NO_SILENT_TEXT_CORRECTION" in contract.get("ocr_route", {}).get("determinism_requirements", []),
        "zero_runtime_effects": effects and all(value in (0, False) for value in effects.values()),
        "bounded_authorization": auth.get("offline_design") is True and all(auth.get(key) is False for key in ("official_source_live_probe", "ocr_execution", "silver_promotion", "gold_promotion", "serving_promotion", "publication")),
        "release_unchanged": evidence.get("release_boundary", {}).get("0.7.0") == "ACTIVE" and evidence.get("release_boundary", {}).get("0.8.0") == "CANDIDATE" and evidence.get("release_boundary", {}).get("unchanged") is True,
        "ci_gate_present": "python scripts/github_task_027_loa_reproducible_extraction_readiness_gate.py" in ci,
    }

    failed = [name for name, ok in checks.items() if not ok]
    status = "PASS_TASK_027_LOA_REPRODUCIBLE_EXTRACTION_READINESS_OFFLINE" if not failed else "STOP"
    print(json.dumps({"status": status, "checks": checks, "failed_checks": failed}, ensure_ascii=False, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())

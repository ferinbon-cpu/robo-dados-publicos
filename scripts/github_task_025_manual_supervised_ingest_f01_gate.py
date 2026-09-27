#!/usr/bin/env python3
"""Fail-closed offline gate for TASK 025 manual supervised ingest F01."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.manual_ingest.planning_budget import (
    extract_ppa_eiti_program,
    load_manual_ingest_contract,
    parse_ldo_structural_markers,
    validate_financial_identity,
)


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    config = load("config/manual_supervised_ingest_f01.v1.json")
    evidence = load("docs/evidence/TASK_025_MANUAL_SUPERVISED_INGEST_F01_0.8.0.json")
    fixture = load("tests/fixtures/task_025_manual_supervised_ingest_f01.json")
    sources = load_manual_ingest_contract(ROOT / "config/manual_supervised_ingest_f01.v1.json")
    ppa = extract_ppa_eiti_program(fixture["ppa_text"])
    ldo = parse_ldo_structural_markers(fixture["ldo_text"])
    finance = validate_financial_identity(fixture["financial_program_only"])
    ci = (ROOT / ".github/workflows/ci-offline.yml").read_text(encoding="utf-8")
    forbidden_workflows = list((ROOT / ".github/workflows").glob("*task-025*"))

    promotion = config.get("promotion", {})
    effects = evidence.get("this_pr_effects", {})
    authorization = evidence.get("authorization", {})
    custody = evidence.get("external_supervised_custody", {})
    parser_boundary = evidence.get("offline_parser_boundary", {})

    checks = {
        "base_and_mode": evidence.get("base_sha") == "9e27a3fa8596a756b8d25e04b35df84e9cc018f9" and config.get("mode") == "MANUAL_SUPERVISED_INGEST" and evidence.get("mode") == "T0_OFFLINE_IMPLEMENTATION_BOUNDARY",
        "exact_source_set": [source.family for source in sources] == ["PPA", "LDO", "LOA"],
        "exact_pages": [source.expected_pages for source in sources] == [105, 37, 466],
        "exact_hashes": [source.expected_sha256 for source in sources] == [
            "3e5deb53448c2e5eea56217a4e5d7f20f7fc3859eff7fcb93a7de7eb17011c1a",
            "6f28017bb61fe6dbd7db44e2306bd1a48f813d8d40411d87c130fba78fca2406",
            "bc4c8bf4b2b1e8f59e880318c37ec7f7fbd4357a85a8b46c97750444dbf01d4b",
        ],
        "external_custody_explicit": custody.get("status") == "COMPLETE_READBACK_VERIFIED_OUTSIDE_THIS_PR" and all(item.get("readback_verified") is True for item in custody.get("sources", [])),
        "ppa_program_2001": ppa.get("program_code") == "2001" and ppa.get("responsible_unit_code") == "10.00.00",
        "ppa_eiti_targets": [ppa["indicator"][key] for key in ("recent", "2026", "2027", "2028", "2029", "final_ppa")] == [52, 53, 55, 57, 59, 59],
        "ppa_malformed_row_review": ppa.get("known_text_extraction_review") == "PARSER_REVIEW_REQUIRED_TRANSPORTE_ENSINO_MEDIO",
        "ldo_structure": ldo.get("status") == "PASS_LDO_REQUIRED_STRUCTURE" and all(ldo.get("markers", {}).values()),
        "loa_full_parse_blocked": parser_boundary.get("loa", {}).get("full_structured_parse_authorized") is False and parser_boundary.get("loa", {}).get("reason") == "CURRENT_CANONICAL_PDF_HAS_NO_EXTRACTABLE_TEXT_LAYER",
        "financial_identity_fail_closed": finance.get("status") == "EVIDENCIA_INSUFICIENTE" and finance.get("program_level_bridge_is_financial_identity") is False,
        "program_total_not_eiti": config.get("financial_identity_policy", {}).get("program_2001_total_must_not_be_attributed_to_eiti") is True,
        "no_promotion": promotion and all(value is False for value in promotion.values()),
        "zero_pr_effects": all(value in (0, False) for value in effects.values()),
        "authorizations_bounded": authorization.get("manual_source_validation_offline") is True and all(authorization.get(key) is False for key in ("bronze_mutation", "silver_promotion", "gold_promotion", "serving_promotion", "site_mutation")),
        "release_unchanged": evidence.get("release_boundary", {}).get("0.7.0") == "ACTIVE" and evidence.get("release_boundary", {}).get("0.8.0") == "CANDIDATE" and evidence.get("release_boundary", {}).get("unchanged") is True,
        "no_task_specific_live_workflow": not forbidden_workflows,
        "ci_gate_present": "python scripts/github_task_025_manual_supervised_ingest_f01_gate.py" in ci,
    }

    failed = [name for name, passed in checks.items() if not passed]
    status = "PASS_TASK_025_MANUAL_SUPERVISED_INGEST_F01_OFFLINE" if not failed else "STOP"
    print(json.dumps({"status": status, "checks": checks, "failed_checks": failed}, ensure_ascii=False, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    c = json.loads((ROOT / "config/operational_bootstrap.full.v1.json").read_text())
    a = json.loads((ROOT / "docs/evidence/TASK_018_FULL_OPERATIONAL_BOOTSTRAP_OWNER_AUTHORIZATION_0.8.0.json").read_text())
    w = (ROOT / ".github/workflows/task-018-full-operational-bootstrap.yml").read_text()
    classifications = {x["source_family"]: x["classification"] for x in c["eligibility"]}
    ceilings = c["hard_safety_ceilings"]
    required = {"maximum_runtime_seconds", "maximum_total_remote_get_count", "maximum_index_discovery_pages", "maximum_documents", "maximum_bytes_per_document", "maximum_aggregate_source_bytes", "maximum_drive_create_operations", "maximum_live_reconciliation_requests"}
    checks = {
      "drain_not_one": c["batch_semantic"].startswith("DRAIN_ALL") and ceilings["maximum_documents"] > 1,
      "blocked": classifications.get("LIMEIRA_TDA_PORTAL") == "BLOCKED_CONTRACT_UNPROVEN" and classifications.get("SIOPE_2025") == "BLOCKED_SEMANTIC_UNPROVEN",
      "pending": a["authorized"] is False and a["implementation_merge_sha"] is None and a["status"] == "PENDING_OWNER_AUTHORIZATION",
      "create_only": c["mutation_policy"] == {"create_only": True, "overwrite": False, "replace": False, "delete": False},
      "bounded": required <= set(ceilings) and all(isinstance(ceilings[x], int) and ceilings[x] > 0 for x in required),
      "manual": "workflow_dispatch:" in w and all(x not in w for x in ("schedule:", "cron:", "workflow_run:", "repository_dispatch:")),
      "stages": all(x in w for x in ("T1_DISCOVER_AND_COLLECT", "T2_CREATE_ONLY_PERSIST_AND_PROCESS", "T3_CREATE_ONLY_PRODUCT_PUBLICATION")),
      "manifest": c["publication"]["manifest_written_last"] and c["publication"]["final_readback_required"],
      "no_retry": not c["automatic_retry"] and not c["recurrence"] and not c["schedule"],
    }
    print(json.dumps({"gate": "TASK_018_FULL_OPERATIONAL_BOOTSTRAP_DESIGN", "status": "PASS" if all(checks.values()) else "FAIL", "checks": checks}, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__": raise SystemExit(main())

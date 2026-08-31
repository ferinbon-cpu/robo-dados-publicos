#!/usr/bin/env python3
"""Offline structural gate that rejects an unsafe or non-executable TASK 018."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from robo_dados_publicos.operational.bootstrap_batch import (  # noqa: E402
    validate_canonical_projection,
)


def main():
    config = json.loads(
        (ROOT / "config/operational_bootstrap.full.v1.json").read_text(
            encoding="utf-8"
        )
    )
    auth = json.loads(
        (
            ROOT
            / "docs/evidence/TASK_018_FULL_OPERATIONAL_BOOTSTRAP_OWNER_AUTHORIZATION_0.8.0.json"
        ).read_text(encoding="utf-8")
    )
    workflow = (
        ROOT / ".github/workflows/task-018-full-operational-bootstrap.yml"
    ).read_text(encoding="utf-8")
    entry = (
        ROOT / "scripts/github_task_018_full_operational_bootstrap.py"
    ).read_text(encoding="utf-8")
    adapters = (
        ROOT / "robo_dados_publicos/operational/bootstrap_adapters.py"
    ).read_text(encoding="utf-8")
    engine = (
        ROOT / "robo_dados_publicos/operational/bootstrap_batch.py"
    ).read_text(encoding="utf-8")

    ceilings = config["hard_safety_ceilings"]
    required_ceilings = {
        "maximum_runtime_seconds",
        "maximum_total_remote_get_count",
        "maximum_index_discovery_pages",
        "maximum_documents",
        "maximum_bytes_per_document",
        "maximum_aggregate_source_bytes",
        "maximum_drive_create_operations",
        "maximum_live_reconciliation_requests",
    }
    release_keys = {
        "active",
        "active_status",
        "candidate",
        "candidate_status",
        "closed_annual_series",
        "year_2025",
        "S1_NUM_POPU",
        "S2_FINANCIAL_ALIAS_BRIDGE",
        "annual_closure_status",
        "semantic_comparability_status",
        "gold_2025",
        "year_2026",
        "B1",
        "B2",
        "B3",
    }
    canonical_refs = (
        "config/limeira_sources_discovery.json",
        "config/sources.jornal_oficial_7310_gate.json",
        "config/automation_policy.v1.json",
        "config/cloud.json",
        "TASK_011_FNDE_AUTHORITATIVE_REQUESTS_PENDING",
        "TASK_015_M8_R3_PUBLICATION_CLOSURE",
    )
    wrong_secrets = (
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "GOOGLE_REFRESH_TOKEN",
    )

    reserve_pos = workflow.find("T2_RESERVE_ONE_SHOT")
    t1_pos = workflow.find("T1_DISCOVER_AND_COLLECT")
    t2_pos = workflow.find("T2_CREATE_ONLY_PERSIST_AND_PROCESS")
    t3_pos = workflow.find("T3_CREATE_ONLY_PRODUCT_PUBLICATION")

    dedup_pos = entry.find("deduplicate_discovery(rows)")
    get_pos = entry.find("source.get(")

    checks = {
        "drain_not_one": (
            config["batch_semantic"].startswith("DRAIN_ALL")
            and ceilings["maximum_documents"] > 1
        ),
        "canonical_cross_validation": (
            validate_canonical_projection(config)
            and all(x in engine for x in canonical_refs)
            and release_keys <= set(config["release_boundary"])
        ),
        "proven_host_and_narrow_scope": (
            "ecrie.com.br" in json.dumps(config)
            and "DECLARED_LINKS_IN_PROVEN_MODERN_WINDOW_2026_08"
            in json.dumps(config)
            and "LEGACY_DISCOVERY_WINDOWS" not in json.dumps(config)
        ),
        "truthful_discovery_ceiling": ceilings["maximum_index_discovery_pages"]
        == 50,
        "discovery_pass_enforced": (
            'report.get("status") != "PASS_DISCOVERY"' in adapters
            and "STOP_DISCOVERY_CONTRACT_BROKEN" in adapters
        ),
        "dedup_before_document_get": (
            dedup_pos >= 0 and get_pos >= 0 and dedup_pos < get_pos
        ),
        "t1_failures_carried": (
            '"collection_failures"' in entry
            and "initial_items=" in entry
            and "collection_status" in entry
        ),
        "oversize_item_local": (
            "STOP_DOCUMENT_TOO_LARGE" in entry
            and "enforce_per_document=False" in entry
            and "continue" in entry
        ),
        "pre_t1_one_shot": (
            0 <= reserve_pos < t1_pos < t2_pos < t3_pos
            and "reserve_one_shot" in entry
            and "verify_reservation" in entry
            and 'github_run_attempt") or "") != "1"' in entry
        ),
        "pending_one_shot": (
            auth["authorized"] is False
            and auth["implementation_merge_sha"] is None
            and auth["single_batch_authorized"] is False
            and auth["consumed"] is False
            and auth["further_execution_authorized"] is False
            and auth["retry_authorized"] is False
        ),
        "production_adapters": all(
            x in adapters
            for x in (
                "JornalOficialLimeira",
                "JournalPdfProcessor",
                "DriveRESTClient",
                "OAuthCredentials",
                "TokenProvider",
                "CloudLayout",
                "ReconciliationExecutor",
                "LimeiraContractsResolver",
            )
        ),
        "no_live_stub": (
            "STOP_CREDENTIAL_CAPABILITY" not in entry
            and "build_source_adapter" in entry
        ),
        "real_reconciliation": (
            ".reconciler.execute(" in engine
            and "reconciliation_get_count" in engine
            and "financial_identity_auto_promotion" in engine
            and "StateRegistry" in engine
        ),
        "canonical_state_storage": (
            '"reconciliation_tasks.jsonl": "Gold"' in adapters
            and '"reconciliation_tasks.jsonl": "Bancos"' not in adapters
            and 'self.store.create(\n            "Bancos"' in engine
            and "__ROBOT_STATE.sqlite" in engine
        ),
        "real_readback": (
            '.readback("Outputs"' in engine
            and "self.readback(destination, name)" in adapters
        ),
        "real_publication": (
            'self.store.create(\n                "Outputs"' in engine
            and "manifest.json" in engine
            and "PUBLISHED_CREATE_ONLY_READBACK_VERIFIED" in engine
        ),
        "real_telemetry": all(
            x in engine
            for x in (
                "robots_get_count",
                "index_get_count",
                "document_get_count",
                "reconciliation_get_count",
                "total_remote_get_count",
            )
        )
        and "initial_telemetry=" in entry,
        "bounded": (
            required_ceilings <= set(ceilings)
            and all(
                isinstance(ceilings[x], int) and ceilings[x] > 0
                for x in required_ceilings
            )
            and "before_create()" in engine
            and "accept_source_bytes(" in engine
        ),
        "create_only": config["mutation_policy"]
        == {
            "create_only": True,
            "overwrite": False,
            "replace": False,
            "delete": False,
        },
        "manual_one_job_handoff": (
            "workflow_dispatch:" in workflow
            and workflow.count("runs-on:") == 1
            and all(
                x in workflow
                for x in (
                    "T2_RESERVE_ONE_SHOT",
                    "T1_DISCOVER_AND_COLLECT",
                    "T2_CREATE_ONLY_PERSIST_AND_PROCESS",
                    "T3_CREATE_ONLY_PRODUCT_PUBLICATION",
                    "--workspace task-018-workspace",
                )
            )
        ),
        "runtime_installed": (
            "setup-python@" in workflow
            and "pip install --disable-pip-version-check -r requirements.txt"
            in workflow
        ),
        "correct_secrets": (
            all(
                x in workflow
                for x in (
                    "GOOGLE_DRIVE_CLIENT_ID",
                    "GOOGLE_DRIVE_CLIENT_SECRET",
                    "GOOGLE_DRIVE_REFRESH_TOKEN",
                )
            )
            and not any(x in workflow for x in wrong_secrets)
        ),
        "audit_artifact": (
            "task-018-workspace/task-018-audit/" in workflow
            and "task-018-audit" in entry
            and "if: always()" in workflow
        ),
        "manual_no_retry": (
            all(
                x not in workflow
                for x in (
                    "schedule:",
                    "cron:",
                    "workflow_run:",
                    "repository_dispatch:",
                )
            )
            and not config["schedule"]
            and not config["recurrence"]
            and not config["automatic_retry"]
        ),
    }
    payload = {
        "gate": "TASK_018_FULL_OPERATIONAL_BOOTSTRAP_DESIGN",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
    }
    print(json.dumps(payload, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())

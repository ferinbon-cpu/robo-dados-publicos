#!/usr/bin/env python3
"""Production TASK 018 stage runner. Authorization gates precede every effect."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from robo_dados_publicos.operational.bootstrap_adapters import (  # noqa: E402
    DiscoveryContractError,
    JournalProcessorAdapter,
    LimeiraReconcilerAdapter,
    build_drive_store,
    build_source_adapter,
)
from robo_dados_publicos.operational.bootstrap_batch import (  # noqa: E402
    BootstrapBatch,
    Budget,
    deduplicate_discovery,
    reserve_one_shot,
    validate_authorization,
    validate_canonical_projection,
    verify_reservation,
)
from robo_dados_publicos.state.registry import StateRegistry  # noqa: E402

AUTH = (
    ROOT
    / "docs/evidence/TASK_018_FULL_OPERATIONAL_BOOTSTRAP_OWNER_AUTHORIZATION_0.8.0.json"
)
CONFIG = ROOT / "config/operational_bootstrap.full.v1.json"


def execution_context():
    return {
        "github_run_id": os.getenv("GITHUB_RUN_ID"),
        "github_run_attempt": os.getenv("GITHUB_RUN_ATTEMPT"),
        "execution_sha": os.getenv("GITHUB_SHA"),
    }


def load_and_preflight():
    auth = json.loads(AUTH.read_text(encoding="utf-8"))
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    stop = validate_authorization(auth)
    if stop:
        return auth, config, stop

    execution = execution_context()
    if str(execution.get("github_run_attempt") or "") != "1":
        return auth, config, "STOP_BATCH_AUTHORIZATION_CONSUMED"
    if not execution.get("github_run_id"):
        return auth, config, "STOP_OWNER_AUTHORIZATION_REQUIRED"

    implementation = auth.get("implementation_merge_sha")
    if (
        not implementation
        or subprocess.run(
            ["git", "merge-base", "--is-ancestor", implementation, "HEAD"],
            cwd=ROOT,
        ).returncode
    ):
        return auth, config, "STOP_IMPLEMENTATION_SHA_MISMATCH"
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", implementation + "..HEAD"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    if changed != [str(AUTH.relative_to(ROOT))]:
        return auth, config, "STOP_IMPLEMENTATION_SHA_MISMATCH"
    if not validate_canonical_projection(config):
        return auth, config, "STOP_CANONICAL_POLICY_DRIFT"
    return auth, config, None


def stopped(workspace, status, *, detail=None):
    out = workspace / "task-018-output"
    audit = workspace / "task-018-audit"
    out.mkdir(parents=True, exist_ok=True)
    audit.mkdir(parents=True, exist_ok=True)
    result = {
        "status": status,
        "systemic_stop": True,
        "detail": detail or {},
        "effects": {
            "source_gets": 0,
            "drive_reads": 0,
            "drive_writes": 0,
            "publication_writes": 0,
            "live_reconciliation": 0,
        },
        "telemetry": {
            "robots_get_count": 0,
            "index_get_count": 0,
            "document_get_count": 0,
            "reconciliation_get_count": 0,
            "total_remote_get_count": 0,
            "source_bytes": 0,
            "drive_create_operations": 0,
        },
    }
    for root in (out, audit):
        (root / "operational_result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return 2


def reserve(workspace, auth, execution):
    store = build_drive_store(workspace)
    result = reserve_one_shot(store, auth, execution)
    result["drive_reads"] = 1
    result["drive_writes"] = 1 if result.get("created") else 0
    (workspace / "reservation.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    audit = workspace / "task-018-audit"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "reservation.json").write_text(
        json.dumps(
            {k: v for k, v in result.items() if k != "marker_name"},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return result


def _load_canonical_state(store, workspace):
    path = workspace / "canonical-ROBOT_STATE.sqlite"
    loaded = store.load_named_file("Bancos", "ROBOT_STATE.sqlite", path)
    if not loaded:
        return None, []
    with StateRegistry(path) as state:
        rows = state.list_source_states()
    return path, rows


def _proven_remote_source(row, source_states):
    safe_status = {"DOWNLOADED_NEW", "NOT_MODIFIED", "DUPLICATE_HASH"}
    matches = [
        state
        for state in source_states
        if state.get("url") == row.get("url")
        and state.get("last_sha256")
        and state.get("remote_file_id")
        and state.get("last_status") in safe_status
    ]
    if len(matches) != 1:
        return None
    return matches[0]


def t1(workspace, config, auth, execution):
    store = build_drive_store(workspace)
    reservation_stop = verify_reservation(store, auth, execution)
    drive_reads = 1
    if reservation_stop:
        return {
            "status": reservation_stop,
            "systemic_stop": True,
            "drive_reads": drive_reads,
        }

    try:
        state_path, source_states = _load_canonical_state(store, workspace)
        drive_reads += 1
    except RuntimeError as exc:
        return {
            "status": str(exc),
            "systemic_stop": True,
            "drive_reads": drive_reads,
        }

    source = build_source_adapter()
    budget = Budget(config["hard_safety_ceilings"])
    family = next(
        x
        for x in config["eligibility"]
        if x["classification"] == "ELIGIBLE_LIVE_COLLECTION"
    )

    try:
        rows, telemetry = source.discover(
            family, budget.config["maximum_index_discovery_pages"]
        )
    except DiscoveryContractError as exc:
        return {
            "status": "STOP_DISCOVERY_CONTRACT_BROKEN",
            "systemic_stop": True,
            "drive_reads": drive_reads,
            "discovery": exc.report,
        }
    except Exception as exc:
        return {
            "status": "STOP_DISCOVERY_CONTRACT_BROKEN",
            "systemic_stop": True,
            "drive_reads": drive_reads,
            "discovery": {"error_type": type(exc).__name__},
        }

    budget.add_gets("robots_get_count", telemetry["robots_get_count"])
    budget.add_gets("index_get_count", telemetry["index_get_count"])
    accepted, ambiguous = deduplicate_discovery(rows)

    stage = workspace / "t1"
    stage.mkdir(parents=True, exist_ok=False)
    staged = []
    failures = [
        {
            **{k: v for k, v in item.items() if k not in {"bronze_remote_id"}},
            "collection_status": "STOP_DISCOVERY_AMBIGUITY",
        }
        for item in ambiguous
    ]

    partial = False
    remaining_logical_keys = []
    for index, row in enumerate(accepted):
        proven = _proven_remote_source(row, source_states)
        if proven:
            staged.append(
                {
                    **row,
                    "collection_status": "REUSE_ALREADY_PROVEN",
                    "expected_sha256": proven["last_sha256"],
                    "bronze_remote_id": proven["remote_file_id"],
                }
            )
            continue

        try:
            budget.runtime_ok()
            budget.before_document()
        except RuntimeError:
            partial = True
            remaining_logical_keys = [
                item["logical_key"] for item in accepted[index:]
            ]
            break

        try:
            data, meta = source.get(
                row["url"], budget.config["maximum_bytes_per_document"]
            )
        except Exception as exc:
            failures.append(
                {
                    **row,
                    "collection_status": "STOP_DOCUMENT_FETCH",
                    "error_type": type(exc).__name__,
                }
            )
            continue

        try:
            budget.accept_source_bytes(
                len(data), enforce_per_document=False
            )
        except RuntimeError:
            partial = True
            remaining_logical_keys = [
                item["logical_key"] for item in accepted[index:]
            ]
            break

        if len(data) > budget.config["maximum_bytes_per_document"]:
            failures.append(
                {**row, "collection_status": "STOP_DOCUMENT_TOO_LARGE"}
            )
            continue

        host = (meta.get("final_host") or "").lower()
        if not meta.get("https") or host not in row["allowed_hosts"]:
            failures.append(
                {
                    **row,
                    "collection_status": "STOP_DOCUMENT_HOST_UNPROVEN",
                }
            )
            continue

        if (
            meta.get("content_type") != "application/pdf"
            or not data.startswith(b"%PDF")
        ):
            failures.append(
                {**row, "collection_status": "STOP_DOCUMENT_NOT_PDF"}
            )
            continue

        name = hashlib.sha256(row["logical_key"].encode()).hexdigest() + ".pdf"
        (stage / name).write_bytes(data)
        staged.append(
            {
                **row,
                "local_name": name,
                "final_host": host,
                "sha256": hashlib.sha256(data).hexdigest(),
                "byte_count": len(data),
                "collection_status": "STAGED_NEW",
            }
        )

    t1_status = (
        "PARTIAL_BATCH_SAFETY_BUDGET_REACHED" if partial else "PASS_T1_COLLECTION"
    )
    manifest = {
        "status": t1_status,
        "items": staged,
        "collection_failures": failures,
        "telemetry": budget.counts,
        "discovery_status": telemetry["discovery_status"],
        "discovered_count": len(rows),
        "accepted_after_dedup_count": len(accepted),
        "accepted_for_staging_count": len(staged),
        "collection_failure_count": len(failures),
        "remaining_logical_keys": remaining_logical_keys,
        "drive_reads": drive_reads,
        "canonical_state_loaded": state_path is not None,
    }
    (stage / "t1-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


class StagedSource:
    is_staged = True

    def __init__(self, root):
        self.root = Path(root)
        self.manifest = json.loads(
            (self.root / "t1-manifest.json").read_text(encoding="utf-8")
        )

    def discover(self, family, maximum_pages):
        return self.manifest["items"], {
            "robots_get_count": 0,
            "index_get_count": 0,
            "discovery_status": self.manifest.get("discovery_status"),
        }

    def get(self, url, maximum_bytes):
        item = next(
            (
                x
                for x in self.manifest["items"]
                if x["url"] == url and x.get("local_name")
            ),
            None,
        )
        if not item:
            raise RuntimeError("STOP_DOCUMENT_FETCH")
        data = (self.root / item["local_name"]).read_bytes()
        return data, {
            "https": True,
            "final_host": item["final_host"],
            "content_type": "application/pdf",
            "remote_get_count": 0,
        }


def _load_reservation(workspace):
    path = workspace / "reservation.json"
    if not path.exists():
        return {"drive_reads": 0, "drive_writes": 0}
    return json.loads(path.read_text(encoding="utf-8"))


def t2(workspace, config, auth, execution):
    manifest = json.loads(
        (workspace / "t1/t1-manifest.json").read_text(encoding="utf-8")
    )
    if manifest.get("status") not in {
        "PASS_T1_COLLECTION",
        "PARTIAL_BATCH_SAFETY_BUDGET_REACHED",
    }:
        return stopped(workspace, "STOP_DISCOVERY_CONTRACT_BROKEN")

    reservation = _load_reservation(workspace)
    initial_telemetry = dict(manifest["telemetry"])
    initial_telemetry["drive_create_operations"] = int(
        reservation.get("drive_writes", 0) or 0
    )
    initial_effects = {
        "source_gets": int(
            manifest["telemetry"].get("total_remote_get_count", 0) or 0
        ),
        "drive_reads": int(reservation.get("drive_reads", 0) or 0)
        + int(manifest.get("drive_reads", 0) or 0),
        "drive_writes": int(reservation.get("drive_writes", 0) or 0),
        "publication_writes": 0,
        "live_reconciliation": 0,
    }

    store = build_drive_store(workspace)
    state_path = workspace / "canonical-ROBOT_STATE.sqlite"
    if not state_path.exists():
        state_path = workspace / "task-018-state.sqlite"

    batch = BootstrapBatch(
        config,
        StagedSource(workspace / "t1"),
        store,
        JournalProcessorAdapter(),
        reconciler=LimeiraReconcilerAdapter(),
    )
    result = batch.run(
        workspace / "task-018-output",
        auth,
        execution=execution,
        initial_telemetry=initial_telemetry,
        initial_items=[
            {
                **item,
                "status": item.get("collection_status", "QUARANTINED"),
            }
            for item in manifest.get("collection_failures", [])
        ],
        initial_effects=initial_effects,
        discovered_count=manifest.get("discovered_count"),
        state_path=state_path,
        require_reservation=True,
        upstream_partial=(
            manifest.get("status") == "PARTIAL_BATCH_SAFETY_BUDGET_REACHED"
        ),
        upstream_checkpoint=manifest.get("remaining_logical_keys", []),
    )
    return 0 if not result.get("systemic_stop") else 2


def t3(workspace, config, auth, execution):
    store = build_drive_store(workspace)
    reservation_stop = verify_reservation(store, auth, execution)
    if reservation_stop:
        return stopped(workspace, reservation_stop)

    result_path = workspace / "task-018-output/operational_result.json"
    if not result_path.exists():
        return stopped(workspace, "STOP_MANIFEST_INTEGRITY")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result.get("systemic_stop"):
        return stopped(workspace, result.get("status") or "STOP_MANIFEST_INTEGRITY")

    BootstrapBatch(config, None, store, None).publish(
        workspace / "task-018-output", result
    )
    audit = workspace / "task-018-audit"
    audit.mkdir(exist_ok=True)
    for file in (workspace / "task-018-output/product").iterdir():
        shutil.copy2(file, audit / file.name)
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage",
        required=True,
        choices=(
            "T2_RESERVE_ONE_SHOT",
            "T1_DISCOVER_AND_COLLECT",
            "T2_CREATE_ONLY_PERSIST_AND_PROCESS",
            "T3_CREATE_ONLY_PRODUCT_PUBLICATION",
        ),
    )
    parser.add_argument("--workspace", default="task-018-workspace")
    args = parser.parse_args()

    workspace = Path(args.workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    auth, config, stop = load_and_preflight()
    if stop:
        return stopped(workspace, stop)
    execution = execution_context()

    if args.stage == "T2_RESERVE_ONE_SHOT":
        result = reserve(workspace, auth, execution)
        return 0 if result["status"] == "PASS_BATCH_ONE_SHOT_RESERVED" else stopped(
            workspace, result["status"]
        )

    if args.stage == "T1_DISCOVER_AND_COLLECT":
        result = t1(workspace, config, auth, execution)
        if result.get("systemic_stop"):
            return stopped(
                workspace,
                result["status"],
                detail=result.get("discovery") or {},
            )
        return 0

    if args.stage == "T2_CREATE_ONLY_PERSIST_AND_PROCESS":
        return t2(workspace, config, auth, execution)

    return t3(workspace, config, auth, execution)


if __name__ == "__main__":
    raise SystemExit(main())

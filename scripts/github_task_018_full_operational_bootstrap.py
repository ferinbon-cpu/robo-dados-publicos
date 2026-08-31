#!/usr/bin/env python3
"""Production TASK 018 stage runner. Authorization and canonical gates precede effects."""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from robo_dados_publicos.operational.bootstrap_adapters import build_source_adapter, build_drive_store, JournalProcessorAdapter, LimeiraReconcilerAdapter
from robo_dados_publicos.operational.bootstrap_batch import BootstrapBatch, Budget, validate_authorization, validate_canonical_projection

AUTH = ROOT / "docs/evidence/TASK_018_FULL_OPERATIONAL_BOOTSTRAP_OWNER_AUTHORIZATION_0.8.0.json"
CONFIG = ROOT / "config/operational_bootstrap.full.v1.json"

def load_and_preflight():
    auth, config = json.loads(AUTH.read_text()), json.loads(CONFIG.read_text())
    stop = validate_authorization(auth)
    if stop: return auth, config, stop
    implementation = auth.get("implementation_merge_sha")
    if not implementation or subprocess.run(["git", "merge-base", "--is-ancestor", implementation, "HEAD"], cwd=ROOT).returncode: return auth, config, "STOP_IMPLEMENTATION_SHA_MISMATCH"
    changed = subprocess.check_output(["git", "diff", "--name-only", implementation + "..HEAD"], cwd=ROOT, text=True).splitlines()
    if changed != [str(AUTH.relative_to(ROOT))]: return auth, config, "STOP_IMPLEMENTATION_SHA_MISMATCH"
    if not validate_canonical_projection(config): return auth, config, "STOP_CANONICAL_POLICY_DRIFT"
    return auth, config, None

def stopped(workspace, status):
    out = workspace / "task-018-output"; audit = workspace / "task-018-audit"; out.mkdir(parents=True, exist_ok=True); audit.mkdir(parents=True, exist_ok=True)
    result = {"status": status, "effects": {"source_gets": 0, "drive_reads": 0, "drive_writes": 0, "publication_writes": 0, "live_reconciliation": 0}}
    for root in (out, audit): (root / "operational_result.json").write_text(json.dumps(result, indent=2) + "\n")
    return 2

class StagedSource:
    def __init__(self, root): self.root = Path(root); self.manifest = json.loads((self.root / "t1-manifest.json").read_text())
    def discover(self, family, maximum_pages): return self.manifest["items"], {"robots_get_count": self.manifest["telemetry"]["robots_get_count"], "index_get_count": self.manifest["telemetry"]["index_get_count"]}
    def get(self, url, maximum_bytes):
        item = next(x for x in self.manifest["items"] if x["url"] == url); data = (self.root / item["local_name"]).read_bytes()
        return data, {"https": True, "final_host": item["final_host"], "content_type": "application/pdf"}

def t1(workspace, config):
    source, budget = build_source_adapter(), Budget(config["hard_safety_ceilings"]); family = next(x for x in config["eligibility"] if x["classification"] == "ELIGIBLE_LIVE_COLLECTION")
    rows, telemetry = source.discover(family, budget.config["maximum_index_discovery_pages"]); budget.add_gets("robots_get_count", telemetry["robots_get_count"]); budget.add_gets("index_get_count", telemetry["index_get_count"])
    stage = workspace / "t1"; stage.mkdir(parents=True, exist_ok=False); accepted, failures = [], []
    for row in rows:
        budget.before_document(); data, meta = source.get(row["url"], budget.config["maximum_bytes_per_document"]); budget.accept_bytes(len(data))
        if not meta["https"] or meta["final_host"] not in row["allowed_hosts"] or meta["content_type"] != "application/pdf" or not data.startswith(b"%PDF"): failures.append({**row, "collection_status": "STOP_DOCUMENT_NOT_PDF"}); continue
        name = hashlib.sha256(row["logical_key"].encode()).hexdigest() + ".pdf"; (stage / name).write_bytes(data); accepted.append({**row, "local_name": name, "final_host": meta["final_host"], "sha256": hashlib.sha256(data).hexdigest(), "byte_count": len(data)})
    (stage / "t1-manifest.json").write_text(json.dumps({"items": accepted, "collection_failures": failures, "telemetry": budget.counts}, indent=2, sort_keys=True) + "\n")

def main():
    p = argparse.ArgumentParser(); p.add_argument("--stage", required=True, choices=("T1_DISCOVER_AND_COLLECT", "T2_CREATE_ONLY_PERSIST_AND_PROCESS", "T3_CREATE_ONLY_PRODUCT_PUBLICATION")); p.add_argument("--workspace", default="task-018-workspace"); args = p.parse_args(); workspace = Path(args.workspace); workspace.mkdir(parents=True, exist_ok=True)
    auth, config, stop = load_and_preflight()
    if stop: return stopped(workspace, stop)
    if args.stage == "T1_DISCOVER_AND_COLLECT": t1(workspace, config); return 0
    store = build_drive_store(workspace)
    if args.stage == "T2_CREATE_ONLY_PERSIST_AND_PROCESS":
        execution = {"github_run_id": os.getenv("GITHUB_RUN_ID"), "github_run_attempt": os.getenv("GITHUB_RUN_ATTEMPT"), "execution_sha": os.getenv("GITHUB_SHA")}
        batch = BootstrapBatch(config, StagedSource(workspace / "t1"), store, JournalProcessorAdapter(), reconciler=LimeiraReconcilerAdapter())
        result = batch.run(workspace / "task-018-output", auth, execution=execution); return 0 if not result["systemic_stop"] else 2
    result_path = workspace / "task-018-output/operational_result.json"; result = json.loads(result_path.read_text())
    BootstrapBatch(config, None, store, None).publish(workspace / "task-018-output", result)
    audit = workspace / "task-018-audit"; audit.mkdir(exist_ok=True)
    for file in (workspace / "task-018-output/product").iterdir():
        if file.suffix.lower() not in {".pdf"}: shutil.copy2(file, audit / file.name)
    return 0

if __name__ == "__main__": raise SystemExit(main())

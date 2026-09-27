from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import tempfile

from robo_dados_publicos.qa.regression import RegressionSuite
from robo_dados_publicos.state.registry import StateRegistry
from robo_dados_publicos.sources.inventory import load_source_inventory
from robo_dados_publicos.sources.collector import SourceCollector
from robo_dados_publicos.release import (
    ACTIVE_VALIDATED_VERSION,
    CURRENT_CANDIDATE_VERSION,
    METHOD_VERSION,
    NEXT_ACTION,
    RELEASE_STATUS,
    SOFTWARE_VERSION,
)


@dataclass(frozen=True)
class CloudLayout:
    root_id: str
    documentation_id: str
    bronze_id: str
    silver_id: str
    gold_id: str
    documentos_id: str
    rag_id: str
    bancos_id: str
    logs_id: str
    outputs_id: str
    scripts_id: str
    inbox_id: str
    quarantine_id: str
    software_id: str

    @classmethod
    def from_mapping(cls, data: dict):
        return cls(**data)


EXPECTED_ROOT_NAMES = {
    "00_DOCUMENTACAO",
    "01_BRONZE",
    "02_SILVER",
    "03_GOLD",
    "04_DOCUMENTOS",
    "05_RAG",
    "06_BANCOS",
    "07_LOGS",
    "08_OUTPUTS",
    "09_SCRIPTS",
    "10_INBOX",
    "11_QUARENTENA",
    "12_SOFTWARE",
    "START_HERE_ROBO_DADOS_PUBLICOS",
}


class CloudProductionRunner:
    """Unattended runner for the persistent Drive repository.

    The infrastructure-only path remains backward compatible. When an explicit
    source inventory is supplied, M4E adds deterministic acquisition into Bronze
    while preserving QA, state, provenance and STOP semantics.
    """

    def __init__(self, drive, layout: CloudLayout, fixtures_dir: str | Path):
        self.drive = drive
        self.layout = layout
        self.fixtures_dir = Path(fixtures_dir)

    @staticmethod
    def now():
        return datetime.now(timezone.utc).isoformat()

    def preflight(self):
        items = self.drive.list_children(self.layout.root_id)
        names = {x.get("name") for x in items}
        missing = sorted(EXPECTED_ROOT_NAMES - names)
        duplicates = sorted(n for n in EXPECTED_ROOT_NAMES if sum(1 for x in items if x.get("name") == n) > 1)
        status = "PASS" if not missing and not duplicates else "STOP_REPOSITORY_LAYOUT"
        return {
            "status": status,
            "root_id": self.layout.root_id,
            "count": len(items),
            "missing": missing,
            "duplicates": duplicates,
        }

    def _single_remote(self, parent_id, name):
        found = self.drive.find_by_name(parent_id, name)
        if len(found) > 1:
            raise RuntimeError(f"STOP_DUPLICATE_REMOTE_STATE: {name} has {len(found)} copies")
        return found[0] if found else None

    def _load_or_initialize_state(self, local_state: Path, remote_name: str):
        remote = self._single_remote(self.layout.bancos_id, remote_name)
        if remote:
            self.drive.get(remote["id"], local_state)
            source = "REMOTE_EXISTING"
        else:
            with StateRegistry(local_state) as st:
                st.set_meta("PROJECT_PHASE", "SOFTWARE_V01_AUTONOMOUS_RUNTIME_READY")
                st.set_meta("LATEST_METHOD_VERSION", METHOD_VERSION)
                st.set_meta("LATEST_SOFTWARE_VERSION", ACTIVE_VALIDATED_VERSION)
                st.set_meta("LATEST_SOFTWARE_CANDIDATE", CURRENT_CANDIDATE_VERSION)
                st.set_meta("NEXT_ACTION", NEXT_ACTION)
                st.set_blocker(
                    "FOMENTO_ETI_EXECUTION",
                    "STOP_DATA_DEPENDENCY",
                    "V18 metodológica depende de evidência de execução específica do Fomento ETI/2607004.",
                )
            source = "LOCAL_INITIALIZED"
        return remote, source

    def _persist_state(self, local_state: Path, remote, remote_name: str):
        if remote:
            out = self.drive.replace_content(remote["id"], local_state, "application/x-sqlite3")
            return {"mode": "REPLACED", "id": out["id"]}
        out = self.drive.put(local_state, remote_name, self.layout.bancos_id, "application/x-sqlite3")
        return {"mode": "CREATED", "id": out["id"]}

    def _write_log(self, payload: dict, log_name: str):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / log_name
            p.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            out = self.drive.put(p, log_name, self.layout.logs_id, "application/json")
        return {"id": out["id"], "name": log_name, "sha256": digest}

    def run(self, state_name="ROBOT_STATE.sqlite", persist=True, write_log=True, source_config=None, dry_run_sources=False):
        started = self.now()
        preflight = self.preflight()
        if preflight["status"] != "PASS":
            return {
                "status": preflight["status"],
                "started_at": started,
                "finished_at": self.now(),
                "preflight": preflight,
            }

        with tempfile.TemporaryDirectory() as td:
            local_state = Path(td) / state_name
            remote_state, state_source = self._load_or_initialize_state(local_state, state_name)
            with StateRegistry(local_state) as st:
                run_id = st.start_run("RUNNING", {"mode": "M4E" if source_config else "M4C", "state_source": state_source})
                st.set_meta("PROJECT_PHASE", "SOFTWARE_V01_AUTONOMOUS_RUNTIME_READY")
                st.set_meta("LATEST_METHOD_VERSION", METHOD_VERSION)
                st.set_meta("LATEST_SOFTWARE_VERSION", ACTIVE_VALIDATED_VERSION)
                st.set_meta("LATEST_SOFTWARE_CANDIDATE", CURRENT_CANDIDATE_VERSION)
                st.set_meta("NEXT_ACTION", NEXT_ACTION)

            qa = RegressionSuite(self.fixtures_dir).run()
            status = "PASS" if qa["status"] == "PASS" else "STOP_QA_FAILED"
            source_collection = "NOT_CONFIGURED"
            if status == "PASS" and source_config:
                try:
                    inventory = load_source_inventory(source_config)
                    with StateRegistry(local_state) as st:
                        source_collection = SourceCollector(
                            self.drive, self.layout.bronze_id, self.layout.quarantine_id
                        ).collect_inventory(inventory, st, dry_run=dry_run_sources)
                    if source_collection.get("status") == "STOP_SOURCE_COLLECTION":
                        status = "STOP_SOURCE_COLLECTION"
                except Exception as exc:
                    source_collection = {
                        "status": "STOP_SOURCE_CONFIG",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                    status = "STOP_SOURCE_CONFIG"
                    with StateRegistry(local_state) as st:
                        st.event("SOURCE_CONFIG_ERROR", source_collection)

            summary = {
                "status": status,
                "run_id": run_id,
                "started_at": started,
                "finished_at": self.now(),
                "software_version": SOFTWARE_VERSION,
                "release_status": RELEASE_STATUS,
                "method_version": METHOD_VERSION,
                "mode": "SOURCE_COLLECTION_ENABLED" if source_config else "INFRASTRUCTURE_ONLY",
                "preflight": preflight,
                "state_source": state_source,
                "qa": {k: v for k, v in qa.items() if k != "results"},
                "blocker_policy": "PRESERVE_STOP_DATA_DEPENDENCY",
                "source_collection": source_collection,
            }

            with StateRegistry(local_state) as st:
                st.set_meta("LATEST_SOFTWARE_VERSION", ACTIVE_VALIDATED_VERSION)
                st.set_meta("LATEST_SOFTWARE_CANDIDATE", CURRENT_CANDIDATE_VERSION)
                st.set_meta("NEXT_ACTION", NEXT_ACTION)
                st.finish_run(run_id, status, summary)
                st.event("AUTONOMOUS_RUN", summary)

            state_remote = None
            if persist:
                state_remote = self._persist_state(local_state, remote_state, state_name)
                summary["state_remote"] = state_remote

            log_remote = None
            if write_log:
                stamp = started.replace("-", "").replace(":", "").replace("+00:00", "Z").replace(".", "")
                log_name = f"ROBO_RUN_{stamp}_{run_id}.json"
                log_remote = self._write_log(summary, log_name)
                summary["log_remote"] = log_remote

            return summary

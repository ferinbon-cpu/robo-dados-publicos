from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import pypdf

from robo_dados_publicos.journal.gate import load_journal_processing_gate
from robo_dados_publicos.journal.processing import JournalPdfProcessor
from robo_dados_publicos.orchestration.cloud_runner import CloudProductionRunner
from robo_dados_publicos.qa.regression import RegressionSuite
from robo_dados_publicos.release import (
    ACTIVE_VALIDATED_VERSION,
    CURRENT_CANDIDATE_VERSION,
    METHOD_VERSION,
    NEXT_ACTION,
    RELEASE_STATUS,
    SOFTWARE_VERSION,
)
from robo_dados_publicos.state.registry import StateRegistry
from robo_dados_publicos.storage.hashing import sha256_file


class CloudJournalProcessingRunner(CloudProductionRunner):
    """Process one already-collected Bronze PDF without touching its source URL."""

    @staticmethod
    def now():
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict]:
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows

    def _output_specs(self, out_dir: Path, prefix: str) -> list[dict]:
        return [
            {"key": "manifest", "path": out_dir / "edition_manifest.json", "parent": self.layout.documentos_id, "mime": "application/json"},
            {"key": "pages_silver", "path": out_dir / "pages_silver.jsonl", "parent": self.layout.silver_id, "mime": "application/x-ndjson"},
            {"key": "events_gold", "path": out_dir / "events_gold.jsonl", "parent": self.layout.gold_id, "mime": "application/x-ndjson"},
            {"key": "reconciliation_tasks", "path": out_dir / "reconciliation_tasks.jsonl", "parent": self.layout.gold_id, "mime": "application/x-ndjson"},
            {"key": "chunks_rag", "path": out_dir / "chunks_rag.jsonl", "parent": self.layout.rag_id, "mime": "application/x-ndjson"},
        ]

    def _commit_output(self, spec: dict, prefix: str, scratch: Path) -> dict:
        path = spec["path"]
        digest = sha256_file(path)
        suffix = "jsonl" if path.suffix == ".jsonl" else "json"
        remote_name = f"{prefix}__{spec['key']}__{digest[:12]}.{suffix}"
        found = self.drive.find_by_name(spec["parent"], remote_name)
        if len(found) > 1:
            raise RuntimeError(f"STOP_DUPLICATE_PROCESSING_OUTPUT: {spec['key']}")
        if found:
            probe = scratch / f"verify_{spec['key']}.{suffix}"
            got = self.drive.get(found[0]["id"], probe)
            if got["sha256"] != digest or got["bytes"] != path.stat().st_size:
                raise RuntimeError(f"STOP_PROCESSING_OUTPUT_HASH_MISMATCH: {spec['key']}")
            mode = "REUSED_IDENTICAL"
        else:
            self.drive.put(path, remote_name, spec["parent"], spec["mime"])
            mode = "CREATED"
        return {
            "key": spec["key"],
            "mode": mode,
            "sha256": digest,
            "bytes": path.stat().st_size,
            "remote_identifier_exposed": False,
        }

    def run_processing(self, processing_config, *, state_name="ROBOT_STATE.sqlite", persist=True, write_log=True, dry_run=False):
        started = self.now()
        gate = load_journal_processing_gate(processing_config)
        preflight = self.preflight()
        if preflight["status"] != "PASS":
            return {"status": preflight["status"], "preflight": preflight, "secret_values_exposed": False}

        extractor_checks = {
            "extractor_name_match": gate.extractor == "pypdf",
            "extractor_version_match": pypdf.__version__ == gate.extractor_version,
        }
        if not all(extractor_checks.values()):
            return {
                "status": "STOP_PROCESSING_EXTRACTOR_CONTRACT",
                "extractor_checks": extractor_checks,
                "expected_extractor": {"name": gate.extractor, "version": gate.extractor_version},
                "secret_values_exposed": False,
            }

        with tempfile.TemporaryDirectory() as td:
            scratch = Path(td)
            local_state = scratch / state_name
            remote_state, state_source = self._load_or_initialize_state(local_state, state_name)
            with StateRegistry(local_state) as st:
                source_state = st.get_source_state(gate.source_id)

            source_checks = {
                "source_state_present": source_state is not None,
                "source_url_match": bool(source_state and source_state.get("url") == gate.source_url),
                "source_sha256_match": bool(source_state and source_state.get("last_sha256") == gate.source_sha256),
                "source_status_downloaded_new": bool(source_state and source_state.get("last_status") == "DOWNLOADED_NEW"),
                "source_remote_reference_private": bool(source_state and source_state.get("remote_file_id")),
            }
            if not all(source_checks.values()):
                return {
                    "status": "STOP_PROCESSING_SOURCE_STATE",
                    "software_version": SOFTWARE_VERSION,
                    "release_status": RELEASE_STATUS,
                    "source_checks": source_checks,
                    "secret_values_exposed": False,
                }
            if dry_run:
                return {
                    "status": "DRY_RUN",
                    "mode": "BRONZE_PROCESSING_PLANNED",
                    "source_checks": source_checks,
                    "extractor_checks": extractor_checks,
                    "expected_metrics": gate.expected_metrics(),
                    "network_origin_called": False,
                    "drive_source_downloaded": False,
                    "writes": "NONE",
                    "secret_values_exposed": False,
                }

            source_pdf = scratch / f"journal_{gate.edition}.pdf"
            got = self.drive.get(source_state["remote_file_id"], source_pdf)
            artifact_checks = {
                "download_sha256_match": got["sha256"] == gate.source_sha256,
                "download_bytes_match": got["bytes"] == gate.source_bytes,
            }
            if not all(artifact_checks.values()):
                return {
                    "status": "STOP_PROCESSING_BRONZE_CONTRACT",
                    "source_checks": source_checks,
                    "extractor_checks": extractor_checks,
                    "artifact_checks": artifact_checks,
                    "secret_values_exposed": False,
                }

            qa = RegressionSuite(self.fixtures_dir).run()
            if qa["status"] != "PASS":
                return {"status": "STOP_QA_FAILED", "qa": {k: v for k, v in qa.items() if k != "results"}, "secret_values_exposed": False}

            out_dir = scratch / "derived"
            processor = JournalPdfProcessor()
            processed = processor.process(
                source_pdf,
                edition=gate.edition,
                publication_date=gate.publication_date,
                source_url=gate.source_url,
                out_dir=out_dir,
                stage_bronze=False,
                plan_reconciliation=True,
            )
            observed_metrics = {
                "pages": processed.get("text_extraction", {}).get("pages"),
                "total_extracted_chars": processed.get("text_extraction", {}).get("total_extracted_chars"),
                "gold_events": processed.get("gold_events"),
                "rag_chunks": processed.get("rag_chunks"),
                "reconciliation_tasks": processed.get("reconciliation_tasks"),
            }
            processing_checks = {
                "status_pass": processed.get("status") == "PASS_DOCUMENT_PROCESSING",
                "source_sha256_match": processed.get("source_sha256") == gate.source_sha256,
                "metrics_match": observed_metrics == gate.expected_metrics(),
                "bronze_not_recreated": processed.get("bronze") is None,
            }
            if not all(processing_checks.values()):
                return {
                    "status": "STOP_PROCESSING_CONTRACT",
                    "source_checks": source_checks,
                    "extractor_checks": extractor_checks,
                    "artifact_checks": artifact_checks,
                    "processing_checks": processing_checks,
                    "expected_metrics": gate.expected_metrics(),
                    "observed_metrics": observed_metrics,
                    "secret_values_exposed": False,
                }

            outputs = [self._commit_output(spec, gate.output_prefix, scratch) for spec in self._output_specs(out_dir, gate.output_prefix)]
            tasks = self._read_jsonl(out_dir / "reconciliation_tasks.jsonl")
            with StateRegistry(local_state) as st:
                for task in tasks:
                    st.upsert_reconciliation_task(task)
                st.set_meta("LATEST_METHOD_VERSION", METHOD_VERSION)
                st.set_meta("LATEST_SOFTWARE_VERSION", ACTIVE_VALIDATED_VERSION)
                st.set_meta("LATEST_SOFTWARE_CANDIDATE", CURRENT_CANDIDATE_VERSION)
                st.set_meta("NEXT_ACTION", NEXT_ACTION)
                st.set_meta(f"JOURNAL_{gate.edition}_PROCESSING_SHA256", gate.source_sha256)
                st.set_meta(f"JOURNAL_{gate.edition}_PROCESSING_STATUS", "PASS_DOCUMENT_PROCESSING")

            summary = {
                "status": "PASS_CLOUD_JOURNAL_PROCESSING_GATE",
                "software_version": SOFTWARE_VERSION,
                "release_status": RELEASE_STATUS,
                "started_at": started,
                "finished_at": self.now(),
                "state_source": state_source,
                "source_checks": source_checks,
                "extractor_checks": extractor_checks,
                "artifact_checks": artifact_checks,
                "processing_checks": processing_checks,
                "metrics": observed_metrics,
                "outputs": outputs,
                "reconciliation_tasks_persisted": len(tasks),
                "origin_network_called": False,
                "remote_identifiers_exposed": False,
                "secret_values_exposed": False,
            }
            with StateRegistry(local_state) as st:
                st.event("JOURNAL_PROCESSING_GATE", summary)
            if persist:
                state_result = self._persist_state(local_state, remote_state, state_name)
                summary["state_remote"] = {"mode": state_result["mode"], "identifier_exposed": False}
            if write_log:
                stamp = started.replace("-", "").replace(":", "").replace("+00:00", "Z").replace(".", "")
                self._write_log(summary, f"ROBO_PROCESSING_{stamp}_{gate.edition}.json")
                summary["append_only_log"] = {"created": True, "identifier_exposed": False}
            return summary

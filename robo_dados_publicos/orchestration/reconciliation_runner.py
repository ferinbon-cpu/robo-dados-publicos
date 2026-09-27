from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import tempfile

from robo_dados_publicos.orchestration.cloud_runner import CloudProductionRunner
from robo_dados_publicos.qa.regression import RegressionSuite
from robo_dados_publicos.reconciliation.gate import load_reconciliation_execution_gate
from robo_dados_publicos.reconciliation.resolvers import LimeiraContractsResolver, ReconciliationExecutor
from robo_dados_publicos.release import (
    ACTIVE_VALIDATED_VERSION,
    CURRENT_CANDIDATE_VERSION,
    METHOD_VERSION,
    NEXT_ACTION,
    RELEASE_STATUS,
    SOFTWARE_VERSION,
)
from robo_dados_publicos.state.registry import StateRegistry


class CloudReconciliationRunner(CloudProductionRunner):
    """Run one allowlisted reconciliation task and commit state only after PASS."""

    def __init__(self, drive, layout, fixtures_dir, *, executor=None):
        super().__init__(drive, layout, fixtures_dir)
        self.executor = executor or ReconciliationExecutor()

    @staticmethod
    def now():
        return datetime.now(timezone.utc).isoformat()

    def run_reconciliation(
        self,
        reconciliation_config,
        *,
        state_name="ROBOT_STATE.sqlite",
        persist=True,
        write_log=True,
        dry_run=False,
    ):
        gate = load_reconciliation_execution_gate(reconciliation_config)
        started = self.now()
        preflight = self.preflight()
        if preflight["status"] != "PASS":
            return {"status": preflight["status"], "preflight": preflight, "writes": "NONE"}

        with tempfile.TemporaryDirectory() as raw:
            scratch = Path(raw)
            local_state = scratch / state_name
            remote_state = self._single_remote(self.layout.bancos_id, state_name)
            if not remote_state:
                return {
                    "status": "STOP_RECONCILIATION_REMOTE_STATE_MISSING",
                    "state_source": "MISSING",
                    "writes": "NONE",
                    "secret_values_exposed": False,
                }
            self.drive.get(remote_state["id"], local_state)

            qa = RegressionSuite(self.fixtures_dir).run()
            if qa["status"] != "PASS":
                return {
                    "status": "STOP_QA_FAILED",
                    "qa": {k: v for k, v in qa.items() if k != "results"},
                    "writes": "NONE",
                    "secret_values_exposed": False,
                }

            with StateRegistry(local_state) as state:
                all_before = state.list_reconciliation_tasks()
            allowed = set(gate.allowed_targets)
            ready = [
                task for task in all_before
                if task["status"] == gate.initial_status and task["target_source"] in allowed
            ]
            eligible = [task for task in ready if LimeiraContractsResolver.has_minimum_search_key(task)]
            selected = eligible[: gate.limit]
            selected_task_ids = [task["task_id"] for task in selected]
            protected_before = {
                task["task_id"]: task["status"] for task in all_before
                if task["target_source"] not in allowed
            }
            selection_checks = {
                "remote_state_existing": True,
                "one_allowlisted_target": gate.allowed_targets == ("LIMEIRA_CONTRATOS",),
                "one_task_selected": len(selected) == gate.required_selected,
                "selected_initial_status_ready": bool(selected) and all(
                    task["status"] == gate.initial_status for task in selected
                ),
                "selected_minimum_search_key_present": bool(selected) and all(
                    LimeiraContractsResolver.has_minimum_search_key(task) for task in selected
                ),
                "selection_policy_deterministic": gate.selection_policy == "ELIGIBLE_PRIORITY_DESC_TASK_ID_ASC",
                "financial_identity_auto_promotion_prohibited": gate.financial_identity_auto_promotion == "PROHIBITED",
            }
            if dry_run:
                return {
                    "status": "DRY_RUN",
                    "software_version": SOFTWARE_VERSION,
                    "release_status": RELEASE_STATUS,
                    "state_source": "REMOTE_EXISTING",
                    "selection_checks": selection_checks,
                    "selected": len(selected),
                    "ready_allowlisted": len(ready),
                    "eligible_ready": len(eligible),
                    "allowed_targets": list(gate.allowed_targets),
                    "resolver_network_called": False,
                    "remote_writes": "NONE",
                    "task_identifiers_exposed": False,
                    "secret_values_exposed": False,
                }
            if not all(selection_checks.values()):
                return {
                    "status": "STOP_RECONCILIATION_SELECTION_CONTRACT",
                    "selection_checks": selection_checks,
                    "selected": len(selected),
                    "ready_allowlisted": len(ready),
                    "eligible_ready": len(eligible),
                    "remote_writes": "NONE",
                    "task_identifiers_exposed": False,
                    "secret_values_exposed": False,
                }

            execution = self.executor.run_queue(
                local_state,
                work_dir=scratch / "reconciliation",
                limit=gate.limit,
                targets=list(gate.allowed_targets),
                task_ids=selected_task_ids,
                dry_run=False,
            )
            results = execution.get("results") or []
            result_statuses = [str(result.get("status")) for result in results]
            with StateRegistry(local_state) as state:
                all_after = state.list_reconciliation_tasks()
                evidence = [
                    edge
                    for task_id in selected_task_ids
                    for edge in state.list_reconciliation_evidence(task_id)
                ]
            protected_after = {
                task["task_id"]: task["status"] for task in all_after
                if task["target_source"] not in allowed
            }
            financial_edges = [edge for edge in evidence if edge.get("relation") == "financial_identity"]
            candidate_only = [edge for edge in evidence if edge.get("status") != "CANDIDATE_ONLY"]
            execution_checks = {
                "executor_status_pass": execution.get("status") == "PASS_RECONCILIATION_EXECUTION",
                "exactly_one_executed": execution.get("selected") == gate.required_selected and len(results) == 1,
                "selected_task_executed_exactly": (
                    len(results) == len(selected_task_ids)
                    and {result.get("task_id") for result in results} == set(selected_task_ids)
                ),
                "target_scope_respected": bool(results) and all(
                    result.get("target_source") in allowed for result in results
                ),
                "terminal_status_allowlisted": bool(result_statuses) and all(
                    status in gate.allowed_result_statuses for status in result_statuses
                ),
                "protected_targets_unchanged": protected_after == protected_before,
                "candidate_edges_only": not candidate_only,
                "financial_identity_edges_zero": not financial_edges,
            }
            summary = {
                "status": (
                    "PASS_CLOUD_RECONCILIATION_EXECUTION_GATE"
                    if all(execution_checks.values()) else "STOP_RECONCILIATION_EXECUTION_CONTRACT"
                ),
                "software_version": SOFTWARE_VERSION,
                "release_status": RELEASE_STATUS,
                "started_at": started,
                "finished_at": self.now(),
                "state_source": "REMOTE_EXISTING",
                "selection_checks": selection_checks,
                "execution_checks": execution_checks,
                "selected": execution.get("selected"),
                "ready_allowlisted": len(ready),
                "eligible_ready": len(eligible),
                "allowed_targets": list(gate.allowed_targets),
                "result_status_counts": dict(Counter(result_statuses)),
                "candidate_evidence_edges": len(evidence),
                "financial_identity_edges": 0,
                "source_origin_network_called": False,
                "task_identifiers_exposed": False,
                "candidate_payloads_exposed": False,
                "remote_identifiers_exposed": False,
                "secret_values_exposed": False,
            }
            if summary["status"] != "PASS_CLOUD_RECONCILIATION_EXECUTION_GATE":
                summary["remote_writes"] = "NONE"
                return summary

            with StateRegistry(local_state) as state:
                state.set_meta("LATEST_METHOD_VERSION", METHOD_VERSION)
                state.set_meta("LATEST_SOFTWARE_VERSION", ACTIVE_VALIDATED_VERSION)
                state.set_meta("LATEST_SOFTWARE_CANDIDATE", CURRENT_CANDIDATE_VERSION)
                state.set_meta("NEXT_ACTION", NEXT_ACTION)
                state.event("FIRST_RECONCILIATION_EXECUTION_GATE", summary)
            if persist:
                state_result = self._persist_state(local_state, remote_state, state_name)
                summary["state_remote"] = {"mode": state_result["mode"], "identifier_exposed": False}
            if write_log:
                stamp = started.replace("-", "").replace(":", "").replace("+00:00", "Z").replace(".", "")
                self._write_log(summary, f"ROBO_RECONCILIATION_{stamp}.json")
                summary["append_only_log"] = {"created": True, "identifier_exposed": False}
            return summary

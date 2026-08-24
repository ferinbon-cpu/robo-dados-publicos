import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.orchestration.cloud_runner import CloudLayout
from robo_dados_publicos.orchestration.reconciliation_runner import CloudReconciliationRunner
from robo_dados_publicos.reconciliation.gate import load_reconciliation_execution_gate
from robo_dados_publicos.reconciliation.planner import ReconciliationPlanner
from robo_dados_publicos.reconciliation.resolvers import ReconciliationExecutor, ResolutionResult
from robo_dados_publicos.state.registry import StateRegistry


ROOT = Path(__file__).resolve().parent.parent


def layout():
    return CloudLayout(
        root_id="ROOT", documentation_id="D0", bronze_id="D1", silver_id="D2", gold_id="D3",
        documentos_id="D4", rag_id="D5", bancos_id="D6", logs_id="D7", outputs_id="D8",
        scripts_id="D9", inbox_id="D10", quarantine_id="D11", software_id="D12",
    )


class MemoryDrive:
    def __init__(self, cloud_layout):
        self.layout = cloud_layout
        self.files = {}
        self.children = {cloud_layout.root_id: []}
        folders = {
            "00_DOCUMENTACAO": cloud_layout.documentation_id, "01_BRONZE": cloud_layout.bronze_id,
            "02_SILVER": cloud_layout.silver_id, "03_GOLD": cloud_layout.gold_id,
            "04_DOCUMENTOS": cloud_layout.documentos_id, "05_RAG": cloud_layout.rag_id,
            "06_BANCOS": cloud_layout.bancos_id, "07_LOGS": cloud_layout.logs_id,
            "08_OUTPUTS": cloud_layout.outputs_id, "09_SCRIPTS": cloud_layout.scripts_id,
            "10_INBOX": cloud_layout.inbox_id, "11_QUARENTENA": cloud_layout.quarantine_id,
            "12_SOFTWARE": cloud_layout.software_id, "START_HERE_ROBO_DADOS_PUBLICOS": "START",
        }
        for name, file_id in folders.items():
            self.children[cloud_layout.root_id].append({"id": file_id, "name": name})
            self.children.setdefault(file_id, [])
        self.seq = 0

    def list_children(self, parent_id):
        return list(self.children.get(parent_id, []))

    def find_by_name(self, parent_id, name):
        return [item for item in self.list_children(parent_id) if item.get("name") == name]

    def put(self, local_path, remote_name, parent_id=None, mime_type="application/octet-stream"):
        self.seq += 1
        file_id = f"F{self.seq}"
        self.files[file_id] = Path(local_path).read_bytes()
        item = {"id": file_id, "name": remote_name, "mimeType": mime_type, "parents": [parent_id]}
        self.children.setdefault(parent_id, []).append(item)
        return item

    def get(self, file_id, destination):
        data = self.files[file_id]
        path = Path(destination)
        path.write_bytes(data)
        return {
            "file_id": file_id,
            "path": str(path),
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }

    def replace_content(self, file_id, local_path, mime_type="application/octet-stream"):
        self.files[file_id] = Path(local_path).read_bytes()
        for items in self.children.values():
            for item in items:
                if item.get("id") == file_id:
                    return item
        raise KeyError(file_id)


class FakeContractsResolver:
    def __init__(self, *, fail=False):
        self.fail = fail
        self.calls = 0

    def resolve(self, task, work_dir=None):
        self.calls += 1
        if self.fail:
            raise RuntimeError("simulated operational failure")
        return ResolutionResult(
            task_id=task["task_id"],
            target_source="LIMEIRA_CONTRATOS",
            status="MATCH_CANDIDATE",
            checked_at="2026-08-24T00:00:00+00:00",
            candidates=[{
                "contract_number": "51/2025",
                "match_signals": ["CONTRACT_FULL", "CNPJ"],
            }],
            evidence={"mode": "TEST_ONLY"},
            notes=["Correspondência documental candidata; sem promoção financeira."],
        )


def contract_event():
    return {
        "event_id": "JOEV_gate_001",
        "source_id": "LIMEIRA_JO_07310",
        "event_type": "CONTRATO",
        "publication_date": "2026-08-22",
        "contract_number": "51/2025",
        "process_number": "903.586/2025",
        "edital_number": "20/2025",
        "bidding_number": "19/2025",
        "contractor": "Fornecedor de Teste Ltda",
        "cnpj": "61086929000170",
        "object_text": "Serviço de teste controlado",
        "value_brl": "532800.00",
    }


def write_gate(path, **overrides):
    payload = {
        "version": 1,
        "gate": "M4E_FIRST_RECONCILIATION_EXECUTION_GATE",
        "allowed_targets": ["LIMEIRA_CONTRATOS"],
        "limit": 1,
        "required_selected": 1,
        "initial_status": "READY_SEARCH",
        "selection_policy": "PRIORITY_DESC_TASK_ID_ASC",
        "allowed_result_statuses": ["MATCH_CANDIDATE", "NO_MATCH"],
        "financial_identity_auto_promotion": "PROHIBITED",
    }
    payload.update(overrides)
    path.write_text(json.dumps(payload), encoding="utf-8")


def prepare_drive(td):
    cloud_layout = layout()
    drive = MemoryDrive(cloud_layout)
    state_path = td / "state.sqlite"
    tasks = ReconciliationPlanner().plan_event(contract_event())
    with StateRegistry(state_path) as state:
        for task in tasks:
            state.upsert_reconciliation_task(task)
    state_item = drive.put(
        state_path,
        "ROBOT_STATE.sqlite",
        cloud_layout.bancos_id,
        "application/x-sqlite3",
    )
    return cloud_layout, drive, state_item, {task.target_source: task.task_id for task in tasks}


class TestCloudReconciliationGate(unittest.TestCase):
    def test_gate_rejects_expanded_scope_or_limit(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "gate.json"
            write_gate(path, allowed_targets=["LIMEIRA_CONTRATOS", "TCE_SP_DESPESAS"])
            with self.assertRaisesRegex(ValueError, "RECONCILIATION_GATE_TARGET_SCOPE_INVALID"):
                load_reconciliation_execution_gate(path)
            write_gate(path, limit=2)
            with self.assertRaisesRegex(ValueError, "RECONCILIATION_GATE_LIMIT_INVALID"):
                load_reconciliation_execution_gate(path)

    def test_dry_run_selects_one_without_network_or_remote_writes(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            cloud_layout, drive, state_item, _ = prepare_drive(td)
            original = drive.files[state_item["id"]]
            gate_path = td / "gate.json"
            write_gate(gate_path)
            fake = FakeContractsResolver()
            runner = CloudReconciliationRunner(
                drive,
                cloud_layout,
                ROOT / "tests" / "fixtures",
                executor=ReconciliationExecutor(contracts_resolver=fake),
            )
            result = runner.run_reconciliation(gate_path, dry_run=True)
            self.assertEqual("DRY_RUN", result["status"])
            self.assertEqual(1, result["selected"])
            self.assertEqual(0, fake.calls)
            self.assertFalse(result["resolver_network_called"])
            self.assertEqual("NONE", result["remote_writes"])
            self.assertEqual(original, drive.files[state_item["id"]])
            self.assertFalse(drive.list_children(cloud_layout.logs_id))

    def test_pass_replaces_state_and_writes_candidate_only_evidence(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            cloud_layout, drive, state_item, task_ids = prepare_drive(td)
            gate_path = td / "gate.json"
            write_gate(gate_path)
            fake = FakeContractsResolver()
            runner = CloudReconciliationRunner(
                drive,
                cloud_layout,
                ROOT / "tests" / "fixtures",
                executor=ReconciliationExecutor(contracts_resolver=fake),
            )
            result = runner.run_reconciliation(gate_path)
            self.assertEqual("PASS_CLOUD_RECONCILIATION_EXECUTION_GATE", result["status"])
            self.assertEqual(1, fake.calls)
            self.assertEqual(1, result["candidate_evidence_edges"])
            self.assertEqual(0, result["financial_identity_edges"])
            self.assertEqual("REPLACED", result["state_remote"]["mode"])
            self.assertTrue(result["append_only_log"]["created"])
            self.assertFalse(result["task_identifiers_exposed"])
            self.assertFalse(result["candidate_payloads_exposed"])
            self.assertFalse(result["remote_identifiers_exposed"])
            restored = td / "restored.sqlite"
            restored.write_bytes(drive.files[state_item["id"]])
            with StateRegistry(restored) as state:
                statuses = {task["target_source"]: task["status"] for task in state.list_reconciliation_tasks()}
                evidence = state.list_reconciliation_evidence(task_ids["LIMEIRA_CONTRATOS"])
            self.assertEqual("MATCH_CANDIDATE", statuses["LIMEIRA_CONTRATOS"])
            self.assertEqual("READY_SEARCH", statuses["TCE_SP_DESPESAS"])
            self.assertEqual("BLOCKED_CONNECTOR_DISCOVERY", statuses["TDA_LIMEIRA"])
            self.assertEqual(1, len(evidence))
            self.assertEqual("CANDIDATE_ONLY", evidence[0]["status"])
            self.assertEqual("documentary_correspondence_candidate", evidence[0]["relation"])
            self.assertEqual(1, len(drive.list_children(cloud_layout.logs_id)))

    def test_operational_failure_preserves_remote_state_and_writes_no_log(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            cloud_layout, drive, state_item, _ = prepare_drive(td)
            original = drive.files[state_item["id"]]
            gate_path = td / "gate.json"
            write_gate(gate_path)
            fake = FakeContractsResolver(fail=True)
            runner = CloudReconciliationRunner(
                drive,
                cloud_layout,
                ROOT / "tests" / "fixtures",
                executor=ReconciliationExecutor(contracts_resolver=fake),
            )
            result = runner.run_reconciliation(gate_path)
            self.assertEqual("STOP_RECONCILIATION_EXECUTION_CONTRACT", result["status"])
            self.assertEqual("NONE", result["remote_writes"])
            self.assertEqual(original, drive.files[state_item["id"]])
            self.assertFalse(drive.list_children(cloud_layout.logs_id))


if __name__ == "__main__":
    unittest.main()

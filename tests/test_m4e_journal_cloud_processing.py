import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.journal.gate import load_journal_processing_gate
from robo_dados_publicos.orchestration.cloud_runner import CloudLayout
from robo_dados_publicos.orchestration.journal_runner import CloudJournalProcessingRunner
from robo_dados_publicos.state.registry import StateRegistry


ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "jornal_oficial_fixture_2pages.pdf"
SOURCE_ID = "LIMEIRA_JORNAL_OFICIAL_EDICAO_7310"
SOURCE_URL = "https://example.test/jornal.pdf"


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
        return {"file_id": file_id, "path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}

    def replace_content(self, file_id, local_path, mime_type="application/octet-stream"):
        self.files[file_id] = Path(local_path).read_bytes()
        for items in self.children.values():
            for item in items:
                if item.get("id") == file_id:
                    return item
        raise KeyError(file_id)


def write_gate(path: Path, *, source_sha256=None):
    digest = source_sha256 or hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
    payload = {
        "version": 1,
        "gate": "M4E_FIRST_SOURCE_PROCESSING_GATE",
        "source_id": SOURCE_ID,
        "edition": 7310,
        "publication_date": "2026-08-22",
        "source_url": SOURCE_URL,
        "source_sha256": digest,
        "source_bytes": FIXTURE.stat().st_size,
        "extractor": "pypdf",
        "extractor_version": "6.10.0",
        "output_prefix": "LIMEIRA_JO_07310_TEST",
        "expected_pages": 2,
        "expected_total_extracted_chars": 843,
        "expected_gold_events": 2,
        "expected_rag_chunks": 2,
        "expected_reconciliation_tasks": 5,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def prepare_drive(td: Path):
    cloud_layout = layout()
    drive = MemoryDrive(cloud_layout)
    bronze = drive.put(FIXTURE, "source.pdf", cloud_layout.bronze_id, "application/pdf")
    state_path = td / "state.sqlite"
    digest = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
    with StateRegistry(state_path) as state:
        state.upsert_source_state(
            SOURCE_ID,
            SOURCE_URL,
            last_sha256=digest,
            last_status="DOWNLOADED_NEW",
            remote_file_id=bronze["id"],
        )
    drive.put(state_path, "ROBOT_STATE.sqlite", cloud_layout.bancos_id, "application/x-sqlite3")
    return cloud_layout, drive


class TestCloudJournalProcessing(unittest.TestCase):
    def test_gate_rejects_invalid_hash(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "gate.json"
            write_gate(path, source_sha256="bad")
            with self.assertRaisesRegex(ValueError, "PROCESSING_SOURCE_SHA256_INVALID"):
                load_journal_processing_gate(path)

    def test_gate_rejects_unapproved_extractor(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "gate.json"
            write_gate(path)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["extractor"] = "other"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "PROCESSING_EXTRACTOR_INVALID"):
                load_journal_processing_gate(path)

    def test_processing_passes_and_retry_reuses_identical_outputs(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            cloud_layout, drive = prepare_drive(td)
            gate_path = td / "gate.json"
            write_gate(gate_path)
            runner = CloudJournalProcessingRunner(drive, cloud_layout, ROOT / "tests" / "fixtures")
            first = runner.run_processing(gate_path)
            self.assertEqual("PASS_CLOUD_JOURNAL_PROCESSING_GATE", first["status"])
            self.assertEqual(5, len(first["outputs"]))
            self.assertTrue(all(item["mode"] == "CREATED" for item in first["outputs"]))
            self.assertEqual(5, first["reconciliation_tasks_persisted"])
            self.assertFalse(first["origin_network_called"])
            self.assertFalse(first["remote_identifiers_exposed"])
            second = runner.run_processing(gate_path)
            self.assertEqual("PASS_CLOUD_JOURNAL_PROCESSING_GATE", second["status"])
            self.assertTrue(all(item["mode"] == "REUSED_IDENTICAL" for item in second["outputs"]))
            remote_state = drive.find_by_name(cloud_layout.bancos_id, "ROBOT_STATE.sqlite")[0]
            restored = td / "restored.sqlite"
            restored.write_bytes(drive.files[remote_state["id"]])
            with StateRegistry(restored) as state:
                self.assertEqual(5, len(state.list_reconciliation_tasks()))

    def test_bronze_contract_mismatch_stops_before_derived_writes(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            cloud_layout, drive = prepare_drive(td)
            gate_path = td / "gate.json"
            write_gate(gate_path)
            state_item = drive.find_by_name(cloud_layout.bancos_id, "ROBOT_STATE.sqlite")[0]
            state_path = td / "mutated.sqlite"
            state_path.write_bytes(drive.files[state_item["id"]])
            with StateRegistry(state_path) as state:
                current = state.get_source_state(SOURCE_ID)
                state.upsert_source_state(
                    SOURCE_ID,
                    SOURCE_URL,
                    last_sha256="0" * 64,
                    last_status=current["last_status"],
                    remote_file_id=current["remote_file_id"],
                )
            drive.replace_content(state_item["id"], state_path, "application/x-sqlite3")
            out = CloudJournalProcessingRunner(drive, cloud_layout, ROOT / "tests" / "fixtures").run_processing(gate_path)
            self.assertEqual("STOP_PROCESSING_SOURCE_STATE", out["status"])
            self.assertFalse(drive.list_children(cloud_layout.silver_id))
            self.assertFalse(drive.list_children(cloud_layout.gold_id))
            self.assertFalse(drive.list_children(cloud_layout.rag_id))


if __name__ == "__main__":
    unittest.main()

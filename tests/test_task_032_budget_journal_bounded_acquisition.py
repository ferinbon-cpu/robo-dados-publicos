from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from functools import lru_cache
from io import BytesIO
from pathlib import Path

from pypdf import PdfWriter

from robo_dados_publicos.manual_ingest.budget_journal_bounded_acquisition import (
    BudgetJournalAcquisitionStop,
    run_acquisition,
    validate_contract,
    validate_live_authorization,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "budget_laws_journal_bounded_acquisition.v1.json"
SHA = "a" * 40


@lru_cache(maxsize=None)
def pdf_bytes(pages: int) -> bytes:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=72, height=72)
    out = BytesIO()
    writer.write(out)
    return out.getvalue()


class FakeSource:
    network_capable = False

    def __init__(self, *, content_type="application/pdf", page_delta=0, redirect=False, fail_on_call=None):
        self.content_type = content_type
        self.page_delta = page_delta
        self.redirect = redirect
        self.fail_on_call = fail_on_call
        self.calls = 0

    def fetch(self, *, url: str, destination: Path):
        self.calls += 1
        if self.fail_on_call == self.calls:
            raise RuntimeError("synthetic source failure")
        expected = 79 if "07072025191855" in url else 107 if "14112025171148" in url else 631
        body = pdf_bytes(expected + self.page_delta)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(body)
        return {
            "http_status": 200,
            "requested_url": url,
            "final_url": url + "?redirected=1" if self.redirect else url,
            "content_type": self.content_type,
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "path": str(destination),
        }


class FakeStore:
    network_capable = False

    def __init__(self, *, collisions=None, next_page_token=None, fail_create_on=None, corrupt_readback_on=None):
        self.collisions = set(collisions or [])
        self.next_page_token = next_page_token
        self.fail_create_on = fail_create_on
        self.corrupt_readback_on = corrupt_readback_on
        self.inventory_calls = 0
        self.create_calls = 0
        self.readback_calls = 0
        self.created = {}

    def inventory(self, *, parent_id: str):
        self.inventory_calls += 1
        return {
            "items": [{"name": x} for x in sorted(self.collisions)],
            "next_page_token": self.next_page_token,
        }

    def create(self, *, local_path: Path, remote_name: str, parent_id: str):
        self.create_calls += 1
        if self.fail_create_on == self.create_calls:
            raise RuntimeError("synthetic create failure")
        file_id = f"id-{self.create_calls}"
        self.created[file_id] = local_path.read_bytes()
        return {"id": file_id, "name": remote_name, "mimeType": "application/pdf", "parents": [parent_id]}

    def readback(self, *, file_id: str, destination: Path):
        self.readback_calls += 1
        body = self.created[file_id]
        if self.corrupt_readback_on == self.readback_calls:
            body = body + b"corruption"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(body)
        return {
            "file_id": file_id,
            "path": str(destination),
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
        }


class Task032Tests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.auth = {"synthetic_test_only": True}

    def run_fake(self, source=None, store=None):
        with tempfile.TemporaryDirectory() as td:
            return run_acquisition(
                contract=self.contract,
                source=source or FakeSource(),
                store=store or FakeStore(),
                authorization=self.auth,
                expected_sha=SHA,
                work_dir=td,
                offline_test_mode=True,
            )

    def test_contract_is_exact_and_live_disabled(self):
        self.assertEqual(validate_contract(self.contract)["status"], "PASS_TASK_032_CONTRACT")
        self.assertFalse(self.contract["authorization"]["embedded_live_authorization"])
        self.assertEqual(self.contract["limits"]["source_gets"], 3)
        self.assertEqual(self.contract["limits"]["drive_creates"], 3)

    def test_offline_success_proves_exact_three_custody_readbacks(self):
        source = FakeSource()
        store = FakeStore()
        result = self.run_fake(source, store)
        self.assertEqual(result["status"], "PASS_TASK_032_JOM_EXACT_3_SOURCE_CUSTODY_READBACK_VERIFIED")
        self.assertEqual(source.calls, 3)
        self.assertEqual(store.inventory_calls, 1)
        self.assertEqual(store.create_calls, 3)
        self.assertEqual(store.readback_calls, 3)
        self.assertEqual([x["edition"] for x in result["custody"]], [7024, 7119, 7127])
        self.assertEqual([x["pages"] for x in result["custody"]], [79, 107, 631])
        self.assertFalse(result["parser_executed"])
        self.assertEqual(result["bronze_created"], 0)
        self.assertEqual(result["silver_created"], 0)
        self.assertEqual(result["gold_created"], 0)

    def test_missing_live_authorization_blocks_before_any_remote_dependency(self):
        source = FakeSource()
        store = FakeStore()
        with tempfile.TemporaryDirectory() as td:
            result = run_acquisition(
                contract=self.contract,
                source=source,
                store=store,
                authorization=None,
                expected_sha=SHA,
                work_dir=td,
                offline_test_mode=False,
            )
        self.assertEqual(result["status"], "STOP_TASK_032_LIVE_NOT_AUTHORIZED")
        self.assertEqual(source.calls, 0)
        self.assertEqual(store.inventory_calls, 0)
        self.assertEqual(store.create_calls, 0)

    def test_live_authorization_must_match_exact_implementation_sha(self):
        authorization = {
            "task": "TASK_032_BUDGET_JOURNAL_BOUNDED_ACQUISITION",
            "repository": "ferinbon-cpu/robo-dados-publicos",
            "branch": "main",
            "implementation_sha": "b" * 40,
            "source": "LIMEIRA_JORNAL_OFICIAL",
            "operation": "EXACT_3_JOM_PDF_GETS_CREATE_ONLY_CUSTODY_READBACK",
            "target_folder_id": "1CdL4T1CVIPqNph3f5xHbiU8KgxgPpkl5",
            "max_source_gets": 3,
            "max_drive_inventory_requests": 1,
            "max_drive_creates": 3,
            "max_drive_readbacks": 3,
            "automatic_retry": False,
            "overwrite": False,
            "replace": False,
            "delete": False,
            "cleanup": False,
            "ocr": False,
            "parser": False,
            "bronze": False,
            "silver": False,
            "gold": False,
            "serving": False,
            "publication": False,
            "schedule": False,
            "recurrence": False,
            "owner_authorized": True,
            "consumed": False,
        }
        self.assertEqual(
            validate_live_authorization(authorization, expected_sha=SHA)["status"],
            "STOP_TASK_032_AUTHORIZATION_CONTRACT_MISMATCH",
        )

    def test_network_capable_dependency_is_rejected_in_offline_mode(self):
        source = FakeSource()
        source.network_capable = True
        store = FakeStore()
        result = self.run_fake(source, store)
        self.assertEqual(result["status"], "STOP_TASK_032_OFFLINE_NETWORK_CAPABLE_DEPENDENCY")
        self.assertEqual(source.calls, 0)
        self.assertEqual(store.create_calls, 0)

    def test_non_pdf_content_type_stops_before_drive(self):
        source = FakeSource(content_type="text/html")
        store = FakeStore()
        result = self.run_fake(source, store)
        self.assertEqual(result["status"], "STOP_TASK_032_SOURCE_CONTENT_TYPE_NOT_PDF")
        self.assertEqual(store.inventory_calls, 0)
        self.assertEqual(store.create_calls, 0)

    def test_redirect_or_url_drift_stops_before_drive(self):
        source = FakeSource(redirect=True)
        store = FakeStore()
        result = self.run_fake(source, store)
        self.assertEqual(result["status"], "STOP_TASK_032_SOURCE_URL_REDIRECT_OR_DRIFT")
        self.assertEqual(store.create_calls, 0)

    def test_page_count_drift_stops_before_drive(self):
        source = FakeSource(page_delta=1)
        store = FakeStore()
        result = self.run_fake(source, store)
        self.assertEqual(result["status"], "STOP_TASK_032_SOURCE_PAGE_COUNT_MISMATCH")
        self.assertEqual(store.inventory_calls, 0)
        self.assertEqual(store.create_calls, 0)

    def test_any_target_collision_stops_before_first_write(self):
        source = FakeSource()
        name = self.contract["documents"][2]["target_filename"]
        store = FakeStore(collisions={name})
        result = self.run_fake(source, store)
        self.assertEqual(result["status"], "STOP_TASK_032_DRIVE_TARGET_NAME_COLLISION")
        self.assertEqual(source.calls, 3)
        self.assertEqual(store.inventory_calls, 1)
        self.assertEqual(store.create_calls, 0)

    def test_inventory_pagination_is_fail_closed(self):
        store = FakeStore(next_page_token="more")
        result = self.run_fake(FakeSource(), store)
        self.assertEqual(result["status"], "STOP_TASK_032_DRIVE_INVENTORY_PAGINATION_NOT_ALLOWED")
        self.assertEqual(store.create_calls, 0)

    def test_partial_create_failure_never_cleans_up_or_retries(self):
        store = FakeStore(fail_create_on=2)
        result = self.run_fake(FakeSource(), store)
        self.assertEqual(result["status"], "STOP_TASK_032_DRIVE_REMOTE_OPERATION_FAILED")
        self.assertEqual(result["drive_creates"], 1)
        self.assertTrue(result["partial_custody"])
        self.assertTrue(result["owner_decision_required"])
        self.assertFalse(result["cleanup_performed"])
        self.assertFalse(result["retry_performed"])

    def test_readback_mismatch_is_partial_custody_stop(self):
        store = FakeStore(corrupt_readback_on=1)
        result = self.run_fake(FakeSource(), store)
        self.assertEqual(result["status"], "STOP_TASK_032_DRIVE_READBACK_BYTES_MISMATCH")
        self.assertEqual(result["drive_creates"], 1)
        self.assertTrue(result["owner_decision_required"])
        self.assertFalse(result["cleanup_performed"])

    def test_weakening_any_prohibition_invalidates_contract(self):
        data = copy.deepcopy(self.contract)
        data["prohibited"]["parser"] = False
        with self.assertRaises(BudgetJournalAcquisitionStop):
            validate_contract(data)


if __name__ == "__main__":
    unittest.main()

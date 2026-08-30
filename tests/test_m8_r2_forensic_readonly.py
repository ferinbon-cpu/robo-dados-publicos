from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path
import unittest

from robo_dados_publicos.automation.policy import evaluate_gate, load_policy
from robo_dados_publicos.product.publication import GOOGLE_SHEETS_MIME, PublicationNames
from robo_dados_publicos.product.m8_r2_forensic_readonly import (
    ForensicReadonlyAdapter, PASS, STOP_BOUNDED, classify_matrix, run_forensic_readonly,
)
from robo_dados_publicos.product.siope_historical_corrective_publication import (
    EXPECTED_COLUMNS, EXPECTED_ROWS, REMOTE_BASENAME, SEMANTIC_READBACK_RANGE,
)

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/m8-siope-historical-r2-forensic-readonly.yml"


def canonical():
    return [[f"r{r}c{c}" for c in range(EXPECTED_COLUMNS)] for r in range(EXPECTED_ROWS)]


class SimulatedHTTPError(RuntimeError):
    def __init__(self, status, secret):
        super().__init__(f"opaque body spreadsheet-id-123 Authorization: Bearer {secret}")
        self.code = status
        self.response_body = f'{{"token":"{secret}","folder":"folder-id-456"}}'


class FakeReadonly:
    def __init__(self, *, matrix=None, sheet_count=1, pdf=0, manifest=0, token=None,
                 inventory_error=False, read_error=False, worksheets=None,
                 worksheet_metadata=None, inventory_exception=None,
                 metadata_exception=None, values_exception=None):
        names = PublicationNames.from_basename(REMOTE_BASENAME)
        self.files = ([{"id": f"sheet-{i}", "name": names.sheet, "mimeType": GOOGLE_SHEETS_MIME}
                       for i in range(sheet_count)]
                      + [{"id": "pdf", "name": names.pdf, "mimeType": "application/pdf"} for _ in range(pdf)]
                      + [{"id": "manifest", "name": names.manifest, "mimeType": "application/json"} for _ in range(manifest)])
        self.matrix = canonical() if matrix is None else matrix
        self.token = token
        self.inventory_error = inventory_error
        self.read_error = read_error
        self.worksheet_metadata = worksheet_metadata
        self.inventory_exception = inventory_exception
        self.metadata_exception = metadata_exception
        self.values_exception = values_exception
        self.worksheets = ([{"properties": {
            "sheetId": 0, "title": "Sheet 1", "index": 0, "sheetType": "GRID",
        }}] if worksheets is None else worksheets)
        self.inventory_calls = 0
        self.metadata_calls = 0
        self.sheet_calls = 0
        self.ranges = []
        self.events = []

    def list_children_single_page(self, parent, page_size=1000):
        self.inventory_calls += 1
        if self.inventory_exception:
            raise self.inventory_exception
        if self.inventory_error:
            raise RuntimeError("opaque remote failure with possible id")
        return {"files": self.files, "next_page_token": self.token}

    def sheets_values_get(self, spreadsheet_id, range_a1):
        self.events.append("values")
        self.sheet_calls += 1
        self.ranges.append(range_a1)
        if self.values_exception:
            raise self.values_exception
        if self.read_error:
            raise RuntimeError("opaque sheet failure with possible id")
        return {"values": copy.deepcopy(self.matrix)}

    def spreadsheet_metadata_get(self, spreadsheet_id):
        self.events.append("metadata")
        self.metadata_calls += 1
        if self.metadata_exception:
            raise self.metadata_exception
        if self.worksheet_metadata is not None:
            return copy.deepcopy(self.worksheet_metadata)
        return {"sheets": copy.deepcopy(self.worksheets)}


class M8R2ForensicReadonlyTests(unittest.TestCase):
    def run_case(self, **kwargs):
        adapter = FakeReadonly(**kwargs)
        result, code = run_forensic_readonly(adapter, parent_id="never-persisted", canonical_matrix=canonical())
        return adapter, result, code

    def test_one_sheet_pdf_manifest_absent_and_exact_canonical(self):
        adapter, result, code = self.run_case()
        self.assertEqual(0, code)
        self.assertEqual(PASS, result["status"])
        self.assertEqual((1, 0, 0), tuple(result["inventory"][key] for key in (
            "r2_sheet_exact_name_count", "r2_pdf_exact_name_count", "r2_manifest_exact_name_count")))
        forensic = result["sheet_forensics"]
        self.assertEqual("SHEET_EXACT_CANONICAL_9X7", forensic["state"])
        self.assertTrue(forensic["header_match"] and forensic["canonical_matrix_match"])
        self.assertEqual((9, 7), (forensic["observed_row_count"], forensic["observed_max_column_count"]))
        self.assertEqual(["'Sheet 1'!" + SEMANTIC_READBACK_RANGE], adapter.ranges)
        self.assertEqual(["metadata", "values"], adapter.events)
        self.assertEqual("EXACTLY_ONE_WORKSHEET_EXPLICITLY_QUALIFIED", forensic["worksheet_selection"])
        self.assertEqual("FORENSIC_R2_SHEET_EXACT_CANONICAL_PDF_MANIFEST_ABSENT", result["forensic_conclusion"])

    def test_empty_sheet(self):
        _, result, _ = self.run_case(matrix=[])
        self.assertEqual("SHEET_EMPTY", result["sheet_forensics"]["state"])
        self.assertEqual("FORENSIC_R2_SHEET_EMPTY_PDF_MANIFEST_ABSENT", result["forensic_conclusion"])

    def test_partial_sheet(self):
        _, result, _ = self.run_case(matrix=canonical()[:4])
        self.assertEqual("SHEET_PARTIAL", result["sheet_forensics"]["state"])
        self.assertEqual("FORENSIC_R2_SHEET_PARTIAL_PDF_MANIFEST_ABSENT", result["forensic_conclusion"])

    def test_malformed_header_and_wrong_canonical_cell(self):
        for row, column in ((0, 0), (5, 4)):
            with self.subTest(row=row, column=column):
                matrix = canonical(); matrix[row][column] = "WRONG"
                _, result, _ = self.run_case(matrix=matrix)
                self.assertEqual("SHEET_MALFORMED", result["sheet_forensics"]["state"])
                self.assertFalse(result["sheet_forensics"]["canonical_matrix_match"])
                if row == 0:
                    self.assertFalse(result["sheet_forensics"]["header_match"])

    def test_h1_and_a10_are_extra_populated_cells(self):
        matrices = []
        h1 = canonical(); h1[0].append("EXTRA"); matrices.append(h1)
        a10 = canonical(); a10.append(["EXTRA"]); matrices.append(a10)
        for matrix in matrices:
            with self.subTest(rows=len(matrix), columns=max(map(len, matrix))):
                _, result, _ = self.run_case(matrix=matrix)
                self.assertEqual("SHEET_EXTRA_POPULATED_CELLS", result["sheet_forensics"]["state"])
                self.assertTrue(result["sheet_forensics"]["extra_populated_cells"])

    def test_duplicate_and_missing_sheet_never_trigger_sheet_read(self):
        for count, state in ((0, "SHEET_NOT_FOUND"), (2, "SHEET_DUPLICATE")):
            adapter, result, code = self.run_case(sheet_count=count)
            self.assertEqual(state, result["sheet_forensics"]["state"])
            self.assertEqual(0, adapter.sheet_calls)
            self.assertNotEqual(0, code)

    def test_unexpected_pdf_and_manifest_are_remote_state_unexpected(self):
        for kwargs in ({"pdf": 1}, {"manifest": 1}):
            _, result, _ = self.run_case(**kwargs)
            self.assertEqual("FORENSIC_R2_REMOTE_STATE_UNEXPECTED", result["forensic_conclusion"])

    def test_next_page_token_stops_without_second_request(self):
        adapter, result, code = self.run_case(token="redacted-token")
        self.assertEqual(STOP_BOUNDED, result["status"])
        self.assertNotEqual(0, code)
        self.assertEqual(1, adapter.inventory_calls)
        self.assertEqual(0, adapter.sheet_calls)
        self.assertTrue(result["inventory"]["pagination_observed"])
        self.assertNotIn("redacted-token", json.dumps(result))

    def test_inventory_and_sheet_read_fail_closed_and_sanitized(self):
        adapter, result, code = self.run_case(inventory_error=True)
        self.assertEqual(1, adapter.inventory_calls); self.assertNotEqual(0, code)
        self.assertEqual("FORENSIC_R2_READ_FAILED", result["forensic_conclusion"])
        adapter, result, code = self.run_case(read_error=True)
        self.assertEqual(1, adapter.sheet_calls); self.assertNotEqual(0, code)
        self.assertEqual("SHEET_READ_FAILED", result["sheet_forensics"]["state"])
        self.assertNotIn("opaque", json.dumps(result))

    def test_remote_http_failures_report_only_safe_stage_status_and_type(self):
        cases = (
            ({"inventory_exception": SimulatedHTTPError(403, "inventory-secret")},
             "REMOTE_STAGE_DRIVE_INVENTORY", "DRIVE_READONLY", 403),
            ({"metadata_exception": SimulatedHTTPError(403, "metadata-secret")},
             "REMOTE_STAGE_SHEET_METADATA_GET", "SHEETS_READONLY", 403),
            ({"values_exception": SimulatedHTTPError(403, "values-secret")},
             "REMOTE_STAGE_SHEET_VALUES_GET", "SHEETS_READONLY", 403),
            ({"metadata_exception": SimulatedHTTPError(404, "not-found-secret")},
             "REMOTE_STAGE_SHEET_METADATA_GET", "SHEETS_READONLY", 404),
        )
        forbidden = ("opaque body", "spreadsheet-id-123", "folder-id-456",
                     "Authorization", "Bearer", "inventory-secret",
                     "metadata-secret", "values-secret", "not-found-secret")
        for kwargs, stage, operation_class, status in cases:
            with self.subTest(stage=stage, status=status):
                _, result, code = self.run_case(**kwargs)
                serialized = json.dumps(result)
                self.assertNotEqual(0, code)
                self.assertEqual(stage, result["remote_stage"])
                self.assertEqual(operation_class, result["remote_operation_class"])
                self.assertEqual("SimulatedHTTPError", result["error_type"])
                self.assertEqual(status, result["http_status_if_safe"])
                self.assertFalse(result["retryable"])
                for value in forbidden:
                    self.assertNotIn(value, serialized)

    def test_non_http_failure_has_type_without_guessed_status_or_exception_text(self):
        _, result, code = self.run_case(metadata_exception=ValueError(
            "opaque spreadsheet-id-789 Authorization: Bearer token-789"))
        self.assertNotEqual(0, code)
        self.assertEqual("REMOTE_STAGE_SHEET_METADATA_GET", result["remote_stage"])
        self.assertEqual("ValueError", result["error_type"])
        self.assertIsNone(result["http_status_if_safe"])
        serialized = json.dumps(result)
        self.assertNotIn("spreadsheet-id-789", serialized)
        self.assertNotIn("token-789", serialized)

    def test_zero_worksheets_fails_closed_before_values_read(self):
        adapter, result, code = self.run_case(worksheets=[])
        self.assertNotEqual(0, code)
        self.assertEqual("SHEET_WORKSHEET_NOT_FOUND", result["sheet_forensics"]["state"])
        self.assertEqual(1, adapter.metadata_calls)
        self.assertEqual(0, adapter.sheet_calls)
        self.assertEqual("FORENSIC_R2_READ_FAILED", result["forensic_conclusion"])

    def test_ambiguous_worksheet_metadata_fails_closed_before_values_read(self):
        adapter, result, code = self.run_case(worksheet_metadata={"sheets": [{"properties": {}}]})
        self.assertNotEqual(0, code)
        self.assertEqual("SHEET_WORKSHEET_METADATA_AMBIGUOUS", result["sheet_forensics"]["state"])
        self.assertEqual(1, adapter.metadata_calls)
        self.assertEqual(0, adapter.sheet_calls)

    def test_multiple_worksheets_fail_closed_before_values_read(self):
        worksheets = [
            {"properties": {"sheetId": 0, "title": "First", "index": 0, "sheetType": "GRID"}},
            {"properties": {"sheetId": 1, "title": "Second", "index": 1, "sheetType": "GRID"}},
        ]
        adapter, result, code = self.run_case(worksheets=worksheets)
        self.assertNotEqual(0, code)
        self.assertEqual("SHEET_WORKSHEET_AMBIGUOUS", result["sheet_forensics"]["state"])
        self.assertEqual(1, adapter.metadata_calls)
        self.assertEqual(0, adapter.sheet_calls)

    def test_single_worksheet_title_is_a1_escaped_and_explicitly_qualified(self):
        worksheets = [{"properties": {
            "sheetId": 7, "title": "Owner's evidence", "index": 0, "sheetType": "GRID",
        }}]
        adapter, result, code = self.run_case(worksheets=worksheets)
        self.assertEqual(0, code)
        self.assertEqual(["'Owner''s evidence'!A:Z"], adapter.ranges)
        self.assertEqual(1, result["sheet_forensics"]["worksheet_count"])

    def test_result_proves_zero_mutation_retry_cleanup_repair_and_promotions(self):
        _, result, _ = self.run_case()
        expected = {
            "readonly": True, "remote_mutations_performed": 0, "retry_performed": False,
            "cleanup_performed": False, "repair_performed": False,
            "source_recollection_performed": False, "include_2025": False,
            "release_promotion_performed": False,
            "historically_recorded_failure_stage": "UNKNOWN_REMOTE_OPERATION",
            "retryable": False,
        }
        for key, value in expected.items(): self.assertEqual(value, result[key])

    def test_adapter_has_only_get_requests_and_no_mutation_surface(self):
        source = inspect.getsource(ForensicReadonlyAdapter)
        self.assertIn('method="GET"', source)
        forbidden_methods = (
            "create", "update", "delete", "trash", "copy", "move", "put", "patch",
            "values_update", "batch_update", "batchUpdate", "clear", "replace",
        )
        for name in forbidden_methods:
            with self.subTest(name=name):
                self.assertFalse(hasattr(ForensicReadonlyAdapter, name))
        for verb in ('method="POST"', 'method="PUT"', 'method="PATCH"', 'method="DELETE"'):
            self.assertNotIn(verb, source)

    def test_workflow_is_manual_exact_readonly_bounded_and_uploads_always(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        for trigger in ("schedule:", "push:", "pull_request:", "workflow_run:", "workflow_call:"):
            self.assertNotIn(trigger, text)
        self.assertIn("ref: ${{ github.sha }}", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("github_m8_readonly_credential_capability_gate.py", text)
        self.assertIn("GOOGLE_DRIVE_READONLY_REFRESH_TOKEN", text)
        self.assertIn("if: ${{ always() }}", text)
        self.assertNotIn("GOOGLE_DRIVE_REFRESH_TOKEN: ${{ secrets.GOOGLE_DRIVE_REFRESH_TOKEN }}", text)

    def test_policy_is_t1_manual_readonly_and_default_blocked(self):
        policy = load_policy(ROOT)
        gate = next(row for row in policy["gates"] if row["id"] == "M8_SIOPE_HISTORICAL_R2_FORENSIC_READONLY")
        self.assertEqual("T1_REMOTE_READONLY", gate["tier"])
        self.assertFalse(gate["auto_allowed"])
        self.assertEqual("READ_ONLY_PROVEN", gate["credential_capability"])
        self.assertFalse(gate["effects"]["drive_writes"] or gate["effects"]["publication"])
        self.assertFalse(gate["schedule"] or gate["recurrence"])
        self.assertEqual("BLOCK", evaluate_gate(policy, gate["id"])["decision"])

    def test_task012_observability_taxonomy_is_sanitized_and_authorization_unchanged(self):
        publication = (ROOT / "robo_dados_publicos/product/siope_historical_corrective_publication.py").read_text()
        for stage in (
            "REMOTE_STAGE_SHEET_CREATE", "REMOTE_STAGE_SHEET_METADATA", "REMOTE_STAGE_SHEET_WRITE_RAW",
            "REMOTE_STAGE_SHEET_READBACK", "REMOTE_STAGE_SHEET_SEMANTIC_VALIDATE", "REMOTE_STAGE_PDF_CREATE",
            "REMOTE_STAGE_PDF_READBACK", "REMOTE_STAGE_MANIFEST_CREATE", "REMOTE_STAGE_FINAL_INVENTORY",
        ):
            self.assertIn(stage, publication)
        authorization = json.loads((ROOT / "docs/evidence/TASK_012_M8_CORRECTIVE_R2_OWNER_AUTHORIZATION_0.8.0.json").read_text())
        self.assertTrue(authorization["single_execution"])
        self.assertFalse(authorization["retry_allowed"])


if __name__ == "__main__":
    unittest.main()

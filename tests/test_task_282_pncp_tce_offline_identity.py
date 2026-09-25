from copy import deepcopy
from contextlib import ExitStack
import ast
import hashlib
import http.client
import json
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import unittest
import urllib.request
from unittest.mock import patch

from robo_dados_publicos.reconciliation.accounting_identity import (
    AccountingIdentityStop,
    CommitmentKey,
    digest,
    index_rows,
    namespace_collisions,
    resolve_accounting_cohort,
    row_key,
    supplier_fingerprint,
)
from robo_dados_publicos.research import task282_pncp_tce_bridge_audit as audit_module


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "docs/evidence/fixtures/task282/TASK_282_REAL_ACCOUNTING_ROWS.json"


def block_network_and_processes():
    stack = ExitStack()
    denied = AssertionError("NETWORK_OR_SUBPROCESS_FORBIDDEN")
    stack.enter_context(patch.object(socket.socket, "connect", side_effect=denied))
    stack.enter_context(patch.object(socket.socket, "connect_ex", side_effect=denied))
    stack.enter_context(patch.object(socket, "create_connection", side_effect=denied))
    stack.enter_context(patch.object(urllib.request, "urlopen", side_effect=denied))
    stack.enter_context(patch.object(http.client.HTTPConnection, "request", side_effect=denied))
    stack.enter_context(patch.object(http.client.HTTPSConnection, "request", side_effect=denied))
    stack.enter_context(patch.object(subprocess, "run", side_effect=denied))
    stack.enter_context(patch.object(subprocess, "Popen", side_effect=denied))
    return stack


class Task282OfflineIdentityTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.rows = [dict(record["row"]) for record in self.fixture["records"]]
        self.prefecture = "PREFEITURA MUNICIPAL DE LIMEIRA"
        self.key = CommitmentKey("Limeira", self.prefecture, 2026, "3286")

    def test_fixture_is_directly_consumable_without_mutation(self):
        with block_network_and_processes():
            loaded = audit_module.fixture_rows()
            index = index_rows(loaded)
        self.assertEqual(loaded, self.rows)
        self.assertIn(self.key, index)

    def test_direct_fixture_counterexample_proves_number_year_is_not_global_key(self):
        with block_network_and_processes():
            result = audit_module.repo_local_identity_audit()
        collision = result["collision_counterexample"]
        self.assertEqual((collision["number"], collision["original_year"]), ("1", 2026))
        self.assertEqual(
            collision["entities"],
            [
                "INSTITUTO DE PREVIDÊNCIA MUNICIPAL DE LIMEIRA",
                "PREFEITURA MUNICIPAL DE LIMEIRA",
            ],
        )
        self.assertEqual(
            result["canonical_claim"],
            "NUMBER_YEAR_ALONE_IS_NOT_A_SAFE_ACCOUNTING_IDENTITY_ACROSS_ENTITIES",
        )
        self.assertFalse(result["exhaustive_source_collision_count_claimed"])

    def test_real_negative_control_has_three_stages_but_no_procurement_identity(self):
        with block_network_and_processes():
            config = audit_module.load_config()
            result = resolve_accounting_cohort(index_rows(self.rows), self.key)
        self.assertFalse(config["procurement_promotion_allowed"])
        self.assertEqual(
            [r["official_detail_id"] for r in result["observations"]],
            ["900003286", "900003287", "900003288"],
        )
        self.assertEqual(
            [r["stage"] for r in result["observations"]],
            ["COMMITMENT", "LIQUIDATION", "PAYMENT"],
        )
        self.assertEqual(result["procurement_identity"], "UNRESOLVED")
        self.assertEqual(result["individual_liquidation_payment_pairing"], "UNRESOLVED")
        self.assertFalse(result["payment_attribution_authorized"])
        self.assertEqual(result["amount_allocation"], "NOT_CALCULATED")

    def test_fixture_supplier_identifiers_are_explicitly_synthetic(self):
        self.assertTrue(self.fixture["privacy"]["synthetic_supplier_identifiers_only"])
        self.assertTrue(self.fixture["privacy"]["official_detail_ids_synthetic"])
        self.assertFalse(self.fixture["provenance"]["raw_source_redistributed_here"])
        self.assertEqual(self.fixture["provenance"]["license_status"], "NOT_ASSERTED_BY_TASK282")
        for row in self.rows:
            self.assertRegex(row["identificador_despesa"], r"^FIXTURE_SUPPLIER_[A-Z]+$")
        raw = FIXTURE.read_text(encoding="utf-8")
        self.assertNotIn("vl_despesa", raw)
        self.assertNotIn("ds_despesa", raw)
        self.assertIsNone(re.search(r"(?<!\d)\d{11}(?!\d)|(?<!\d)\d{14}(?!\d)", raw))

    def test_supplier_raw_value_and_exact_fingerprint_never_leave_public_result(self):
        row = deepcopy(self.rows[0])
        for value in ["PUBLIC-SUPPLIER-00ABCD12345678", "MASKED-PERSON-123456"]:
            row["identificador_despesa"] = value
            fingerprint = supplier_fingerprint(row)
            result = resolve_accounting_cohort(index_rows([row]), row_key(row))
            serialized = json.dumps(result, ensure_ascii=False, sort_keys=True)
            self.assertNotIn(value, serialized)
            self.assertNotIn(fingerprint, serialized)
            self.assertNotIn("_supplier_fingerprint", serialized)
            self.assertNotIn("supplier_fingerprint", serialized)

    def test_supplier_change_within_same_scoped_commitment_is_fail_closed(self):
        rows = [deepcopy(r) for r in self.rows if row_key(r) == self.key]
        rows[1]["identificador_despesa"] = "TRANSFER_OR_NOVATION_REQUIRES_EXPLICIT_WITNESS"
        with self.assertRaisesRegex(
            AccountingIdentityStop, "CONFLICTING_SUPPLIER_WITHIN_SCOPED_COMMITMENT"
        ):
            index_rows(rows)

    def test_real_number_collision_is_partitioned_by_entity(self):
        index = index_rows(self.rows)
        collisions = namespace_collisions(index)
        self.assertEqual(len(collisions), 1)
        self.assertEqual(collisions[0]["number"], "1")
        self.assertEqual(collisions[0]["original_year"], 2026)
        self.assertEqual(len(collisions[0]["entities"]), 2)
        for entity in collisions[0]["entities"]:
            result = resolve_accounting_cohort(
                index, CommitmentKey("Limeira", entity, 2026, "1")
            )
            self.assertEqual(len(result["observations"]), 1)

    def test_missing_or_inexact_entity_does_not_match(self):
        with self.assertRaisesRegex(AccountingIdentityStop, "MISSING_ACCOUNTING_SCOPE"):
            CommitmentKey("Limeira", "", 2026, "3286")
        result = resolve_accounting_cohort(
            index_rows(self.rows),
            CommitmentKey("Limeira", "Prefeitura Municipal de Limeira", 2026, "3286"),
        )
        self.assertEqual(result["accounting_status"], "UNRESOLVED")
        self.assertEqual(result["observations"], [])
        with self.assertRaisesRegex(AccountingIdentityStop, "EXPLICIT_SCOPED_KEY_REQUIRED"):
            resolve_accounting_cohort(index_rows(self.rows), "2026:3286")

    def test_year_number_and_municipality_are_independent_namespaces(self):
        index = index_rows(self.rows)
        for key in [
            CommitmentKey("Other", self.prefecture, 2026, "3286"),
            CommitmentKey("Limeira", self.prefecture, 2025, "3286"),
            CommitmentKey("Limeira", self.prefecture, 2026, "45"),
        ]:
            self.assertEqual(resolve_accounting_cohort(index, key)["accounting_status"],
                             "UNRESOLVED")

    def test_unsupported_number_syntax_is_not_digit_stripped(self):
        for value in ["3286/2026", "45/2026", "03286-01", "3286", "x3286-2026", "0-2026"]:
            row = deepcopy(self.rows[0])
            row["nr_empenho"] = value
            with self.subTest(value=value), self.assertRaises(AccountingIdentityStop):
                row_key(row)

    def test_original_year_is_not_replaced_by_accounting_year(self):
        row = deepcopy(self.rows[0])
        row["nr_empenho"] = "0003286-2025"
        index = index_rows([row])
        key = next(iter(index))
        self.assertEqual((key.number, key.original_year), ("3286", 2025))
        self.assertEqual(index[key][0]["ledger_year"], 2026)
        row["nr_empenho"] = "3286-2027"
        with self.assertRaisesRegex(AccountingIdentityStop, "COMMITMENT_AFTER_LEDGER_YEAR"):
            index_rows([row])

    def test_duplicate_official_id_fails_even_if_content_equal(self):
        with self.assertRaisesRegex(AccountingIdentityStop, "DUPLICATE_OFFICIAL_DETAIL_ID"):
            index_rows(self.rows + [deepcopy(self.rows[0])])

    def test_unknown_stage_or_missing_id_fails(self):
        for field, value in [
            ("tp_despesa", "Paid?"),
            ("id_despesa_detalhe", ""),
            ("identificador_despesa", ""),
            ("mes_referencia", "13"),
        ]:
            row = deepcopy(self.rows[0])
            row[field] = value
            with self.subTest(field=field), self.assertRaises(AccountingIdentityStop):
                index_rows([row])

    def test_cancellation_does_not_get_assigned_to_payment(self):
        row = deepcopy(self.rows[0])
        row["tp_despesa"] = "Anulação"
        obs = next(iter(index_rows([row]).values()))[0]
        self.assertEqual((obs["stage"], obs["modifier"]),
                         ("REVERSAL", "UNSPECIFIED_STAGE"))

    def test_deterministic_order_and_row_provenance(self):
        a = resolve_accounting_cohort(index_rows(self.rows), self.key)
        b = resolve_accounting_cohort(index_rows(list(reversed(self.rows))), self.key)
        self.assertEqual(a, b)
        row = next(r for r in self.rows if r["id_despesa_detalhe"] == "900003286")
        self.assertEqual(a["observations"][0]["source_row_sha256"], digest(row))

    def test_all_pinned_repository_inputs_match_their_sha256(self):
        config = audit_module.load_config()
        self.assertNotIn("collision_ranges", config["pinned_repository_inputs"])
        for name, spec in config["pinned_repository_inputs"].items():
            payload = (ROOT / spec["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(payload).hexdigest(), spec["sha256"], name)

    def test_pinned_file_fails_on_missing_or_drifted_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "source.json"
            path.write_bytes(b"original")
            spec = {"path": path.name, "sha256": hashlib.sha256(b"original").hexdigest()}
            self.assertEqual(audit_module.pinned_file(spec, root), b"original")
            path.write_bytes(b"changed")
            with self.assertRaisesRegex(AccountingIdentityStop, "PINNED_SOURCE_DRIFT"):
                audit_module.pinned_file(spec, root)
            with self.assertRaises(FileNotFoundError):
                audit_module.pinned_file(
                    {"path": "missing.json", "sha256": "0" * 64}, root
                )

    def test_runtime_blocks_network_and_subprocess_surfaces(self):
        with block_network_and_processes():
            result = audit_module.repo_local_identity_audit()
        self.assertEqual(result["status"], "PASS_TASK282_REPO_LOCAL_IDENTITY_AUDIT")

    def test_task282_modules_have_no_network_or_subprocess_imports(self):
        blocked = {
            "requests", "urllib", "http", "aiohttp", "httpx",
            "socket", "subprocess", "ftplib", "smtplib",
        }
        paths = [
            ROOT / "robo_dados_publicos/research/task282_pncp_tce_bridge_audit.py",
            ROOT / "robo_dados_publicos/reconciliation/accounting_identity.py",
        ]
        for path in paths:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module.split(".")[0])
            self.assertTrue(blocked.isdisjoint(imported), (path, imported & blocked))


    def test_task282_is_registered_as_manual_only_t0_gate(self):
        policy = json.loads(
            (ROOT / "config/automation_policy.v1.json").read_text(encoding="utf-8")
        )
        matches = [
            gate for gate in policy["gates"]
            if gate["id"] == "TASK282_PNCP_TCE_OFFLINE_IDENTITY"
        ]
        self.assertEqual(len(matches), 1)
        gate = matches[0]
        self.assertEqual(gate["tier"], "T0_OFFLINE")
        self.assertFalse(gate["auto_allowed"])
        self.assertEqual(gate["current_triggers"], ["pull_request:main", "push:main"])
        self.assertEqual(gate["workflow"], ".github/workflows/ci-offline.yml")
        self.assertTrue(gate["validation_only"])
        self.assertFalse(gate["task_runtime_auto_execution"])
        self.assertEqual(gate["credential_capability"], "NONE")
        self.assertEqual(
            gate["script"],
            "robo_dados_publicos/research/task282_pncp_tce_bridge_audit.py",
        )
        self.assertEqual(
            gate["contract"],
            "config/task282_pncp_tce_offline_identity.v1.json",
        )
        self.assertEqual(
            gate["effects"],
            {
                "source_network": False,
                "drive_reads": False,
                "drive_writes": False,
                "publication": False,
            },
        )
        self.assertFalse(gate["workflow_added"])
        self.assertFalse(gate["remote_materialization_authorized"])

    def test_supplier_conflict_exception_does_not_leak_raw_or_fingerprint(self):
        rows = [deepcopy(r) for r in self.rows if row_key(r) == self.key]
        marker = "FIXTURE_SUPPLIER_CONFLICT_MARKER"
        rows[1]["identificador_despesa"] = marker
        fingerprint = supplier_fingerprint(rows[1])
        try:
            index_rows(rows)
        except AccountingIdentityStop as exc:
            message = str(exc)
        else:
            self.fail("Expected fail-closed supplier conflict")
        self.assertNotIn(marker, message)
        self.assertNotIn(fingerprint, message)
        self.assertEqual(message, "CONFLICTING_SUPPLIER_WITHIN_SCOPED_COMMITMENT")

    def test_evidence_and_config_pin_same_base(self):
        config = audit_module.load_config()
        evidence = json.loads(
            (ROOT / "docs/evidence/TASK_282_PNCP_TCE_OFFLINE_AUDIT_0.8.0.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(evidence["base_main_sha"], config["base_main_sha"])
        self.assertEqual(
            config["base_main_sha"],
            "69954f7532da1457c040b745b1a9551cc3551d18",
        )
        self.assertFalse(evidence["production_identity_promoted"])
        self.assertFalse(evidence["negative_control"]["payment_attribution_authorized"])


if __name__ == "__main__":
    unittest.main()

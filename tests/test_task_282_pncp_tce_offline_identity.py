from copy import deepcopy
from contextlib import ExitStack
import ast
import hashlib
import json
from pathlib import Path
import http.client
import re
import socket
import subprocess
import urllib.request
import tempfile
import unittest
from unittest.mock import patch

from robo_dados_publicos.reconciliation.accounting_identity import (
    AccountingIdentityStop, CommitmentKey, digest, index_rows,
    namespace_collisions, resolve_accounting_cohort, row_key,
    supplier_fingerprint,
)
from robo_dados_publicos.research import task282_pncp_tce_bridge_audit as audit_module


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "docs/evidence/fixtures/task282/TASK_282_REAL_ACCOUNTING_ROWS.json"
COLLISIONS = ROOT / "docs/evidence/fixtures/task282/TASK_282_COLLISION_RANGES.json"
POLICY = ROOT / "config/automation_policy.v1.json"


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
        self.rows = []
        for record in self.fixture["records"]:
            row = dict(record["expected"])
            row["identificador_despesa"] = record["synthetic_supplier_marker"]
            row["historico_despesa"] = ""
            self.rows.append(row)
        self.prefecture = "PREFEITURA MUNICIPAL DE LIMEIRA"
        self.key = CommitmentKey("Limeira", self.prefecture, 2026, "3286")

    def test_real_negative_control_has_three_stages_but_no_procurement_identity(self):
        with block_network_and_processes():
            config = audit_module.load_config()
            result = resolve_accounting_cohort(index_rows(self.rows), self.key)
        self.assertFalse(config["procurement_promotion_allowed"])
        self.assertEqual([r["official_detail_id"] for r in result["observations"]],
                         ["667130190", "678095929", "678117536"])
        self.assertEqual([r["stage"] for r in result["observations"]],
                         ["COMMITMENT", "LIQUIDATION", "PAYMENT"])
        self.assertEqual(result["procurement_identity"], "UNRESOLVED")
        self.assertEqual(result["individual_liquidation_payment_pairing"], "UNRESOLVED")
        self.assertFalse(result["payment_attribution_authorized"])
        self.assertEqual(result["amount_allocation"], "NOT_CALCULATED")
        self.assertTrue(all("supplier" not in key
                            for obs in result["observations"] for key in obs))

    def test_real_number_collision_is_partitioned_by_entity(self):
        index = index_rows(self.rows)
        collisions = namespace_collisions(index)
        self.assertEqual(len(collisions), 1)
        self.assertEqual(collisions[0]["number"], "1")
        self.assertEqual(len(collisions[0]["entities"]), 2)
        for entity in collisions[0]["entities"]:
            result = resolve_accounting_cohort(index, CommitmentKey("Limeira", entity, 2026, "1"))
            self.assertEqual(len(result["observations"]), 1)

    def test_missing_or_inexact_entity_does_not_match(self):
        with self.assertRaisesRegex(AccountingIdentityStop, "MISSING_ACCOUNTING_SCOPE"):
            CommitmentKey("Limeira", "", 2026, "3286")
        result = resolve_accounting_cohort(index_rows(self.rows), CommitmentKey(
            "Limeira", "Prefeitura Municipal de Limeira", 2026, "3286"))
        self.assertEqual(result["accounting_status"], "UNRESOLVED")
        self.assertEqual(result["observations"], [])
        with self.assertRaisesRegex(AccountingIdentityStop, "EXPLICIT_SCOPED_KEY_REQUIRED"):
            resolve_accounting_cohort(index_rows(self.rows), "2026:3286")

    def test_year_number_and_municipality_are_independent_namespaces(self):
        index = index_rows(self.rows)
        for key in [CommitmentKey("Other", self.prefecture, 2026, "3286"),
                    CommitmentKey("Limeira", self.prefecture, 2025, "3286"),
                    CommitmentKey("Limeira", self.prefecture, 2026, "45")]:
            self.assertEqual(resolve_accounting_cohort(index, key)["accounting_status"], "UNRESOLVED")

    def test_unsupported_number_syntax_is_not_digit_stripped(self):
        for value in ["3286/2026", "45/2026", "03286-01", "3286", "x3286-2026", "0-2026"]:
            row = deepcopy(self.rows[0]); row["nr_empenho"] = value
            with self.subTest(value=value), self.assertRaises(AccountingIdentityStop):
                row_key(row)

    def test_original_year_is_not_replaced_by_accounting_year(self):
        row = deepcopy(self.rows[0]); row["nr_empenho"] = "0003286-2025"
        index = index_rows([row]); key = next(iter(index))
        self.assertEqual((key.number, key.original_year), ("3286", 2025))
        self.assertEqual(index[key][0]["ledger_year"], 2026)
        row["nr_empenho"] = "3286-2027"
        with self.assertRaisesRegex(AccountingIdentityStop, "COMMITMENT_AFTER_LEDGER_YEAR"):
            index_rows([row])

    def test_duplicate_official_id_fails_even_if_content_equal(self):
        with self.assertRaisesRegex(AccountingIdentityStop, "DUPLICATE_OFFICIAL_DETAIL_ID"):
            index_rows(self.rows + [deepcopy(self.rows[0])])

    def test_supplier_conflict_fails_and_same_supplier_does_not_join_entities(self):
        rows = [deepcopy(r) for r in self.rows if row_key(r) == self.key]
        rows[-1]["identificador_despesa"] = "DIFFERENT_SYNTHETIC_SUPPLIER"
        with self.assertRaisesRegex(AccountingIdentityStop, "CONFLICTING_SUPPLIER"):
            index_rows(rows)
        rows = [deepcopy(self.rows[0]), deepcopy(self.rows[0])]
        rows[1]["id_despesa_detalhe"] = "999999999"
        rows[1]["ds_orgao"] = "OTHER_ENTITY"
        self.assertEqual(len(index_rows(rows)), 2)

    def test_supplier_value_is_fingerprinted_and_never_persisted(self):
        row = deepcopy(self.rows[0])
        values = ["PUBLIC-SUPPLIER-00ABCD12345678", "MASKED-PERSON-123456"]
        fingerprints = []
        for value in values:
            row["identificador_despesa"] = value
            fingerprint = supplier_fingerprint(row)
            fingerprints.append(fingerprint)
            result = resolve_accounting_cohort(index_rows([row]), row_key(row))
            serialized = json.dumps(result, ensure_ascii=False)
            self.assertNotIn(value, serialized)
            self.assertNotIn("supplier_fingerprint", serialized)
            self.assertNotIn(fingerprint, serialized)
            self.assertEqual(result["procurement_identity"], "UNRESOLVED")
        self.assertNotEqual(fingerprints[0], fingerprints[1])

    def test_unknown_stage_or_missing_id_fails(self):
        for field, value in [("tp_despesa", "Paid?"), ("id_despesa_detalhe", ""),
                             ("identificador_despesa", ""), ("mes_referencia", "13")]:
            row = deepcopy(self.rows[0]); row[field] = value
            with self.subTest(field=field), self.assertRaises(AccountingIdentityStop):
                index_rows([row])

    def test_cancellation_does_not_get_assigned_to_payment(self):
        row = deepcopy(self.rows[0]); row["tp_despesa"] = "Anulação"
        obs = next(iter(index_rows([row]).values()))[0]
        self.assertEqual((obs["stage"], obs["modifier"]), ("REVERSAL", "UNSPECIFIED_STAGE"))

    def test_deterministic_order_and_row_provenance(self):
        a = resolve_accounting_cohort(index_rows(self.rows), self.key)
        b = resolve_accounting_cohort(index_rows(list(reversed(self.rows))), self.key)
        self.assertEqual(a, b)
        row = next(r for r in self.rows if r["id_despesa_detalhe"].strip() == "667130190")
        self.assertEqual(a["observations"][0]["source_row_sha256"], digest(row))

    def test_pinned_source_and_full_ledger_byte_mutations_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source.json"; path.write_bytes(b"original")
            spec = {"path": path.name, "sha256": hashlib.sha256(b"original").hexdigest()}
            self.assertEqual(audit_module.pinned_file(spec, Path(tmp)), b"original")
            path.write_bytes(b"changed")
            with self.assertRaisesRegex(AccountingIdentityStop, "PINNED_SOURCE_DRIFT"):
                audit_module.pinned_file(spec, Path(tmp))
            missing = {"path": "missing.json", "sha256": hashlib.sha256(b"missing").hexdigest()}
            with self.assertRaises(FileNotFoundError):
                audit_module.pinned_file(missing, Path(tmp))

    def test_frozen_result_preserves_real_cohort_without_supplier_identity(self):
        result = json.loads((ROOT / "docs/evidence/TASK_282_PNCP_TCE_OFFLINE_AUDIT_0.8.0.json").read_text())
        observations = result["negative_control"]["frozen_minimized_observations"]
        self.assertEqual([r["official_detail_id"] for r in observations],
                         ["667130190", "678095929", "678117536"])
        self.assertEqual([r["stage"] for r in observations],
                         ["COMMITMENT", "LIQUIDATION", "PAYMENT"])
        self.assertTrue(all("supplier_token" not in r and "supplier_fingerprint_sha256" not in r
                            for r in observations))
        local = audit_module.collision_witness_audit()
        self.assertEqual(local["collision_witness_count"], 682)
        self.assertEqual(local["interval_count"], 20)
        self.assertEqual(local["source_row_count_inherited_from_task187"], 39779)
        self.assertEqual(result["negative_control"]["municipal_chain"],
                         "PROVEN_TASK219AA_TASK219AB_PRESERVED")
        self.assertFalse(result["negative_control"]["payment_attribution_authorized"])
        self.assertFalse(result["production_identity_promoted"])
        self.assertFalse(result["full_ledger_extended_replay_is_merge_gate"])

    def test_fixture_is_minimized_and_contains_no_raw_supplier_or_amount(self):
        raw = FIXTURE.read_text(encoding="utf-8")
        fixture = json.loads(raw)
        self.assertEqual(fixture["schema"], "TASK282_MINIMIZED_ACCOUNTING_FIXTURE_V2")
        self.assertFalse(fixture["privacy"]["raw_supplier_identifier_persisted"])
        self.assertNotIn("identificador_despesa", raw)
        self.assertNotIn("vl_despesa", raw)
        self.assertNotIn("ds_despesa", raw)
        self.assertNotIn("historico_despesa", raw)
        self.assertIsNone(re.search(r"(?<!\d)\d{11}(?!\d)|(?<!\d)\d{14}(?!\d)", raw))

    def test_replay_modules_do_not_import_network_clients(self):
        blocked = {"requests", "urllib", "http", "aiohttp", "socket", "subprocess", "ftplib", "smtplib"}
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

    def test_repo_local_collision_witness_is_runtime_no_network(self):
        with block_network_and_processes():
            result = audit_module.collision_witness_audit()
        self.assertEqual(result["status"], "PASS_TASK282_REPO_LOCAL_COLLISION_WITNESS")
        self.assertEqual(result["collision_witness_count"], 682)
        self.assertEqual(result["interval_count"], 20)
        self.assertEqual(result["canonical_claim"],
                         "NUMBER_YEAR_ALONE_IS_NOT_A_SAFE_ACCOUNTING_IDENTITY_ACROSS_ENTITIES")

    def test_collision_witness_is_explicitly_pinned_and_drift_fails(self):
        config = audit_module.load_config()
        pin = config["pinned_repository_inputs"]["collision_ranges"]
        self.assertEqual(pin["path"], config["repo_local_reproducibility"]["collision_witness_path"])
        self.assertEqual(pin["sha256"], config["repo_local_reproducibility"]["collision_witness_sha256"])
        bad = deepcopy(config)
        bad["pinned_repository_inputs"]["collision_ranges"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(AccountingIdentityStop, "PINNED_SOURCE_DRIFT"):
            audit_module.collision_witness_audit(bad)

    def test_collision_witness_entities_cover_fixture_entities(self):
        witness = json.loads(COLLISIONS.read_text(encoding="utf-8"))
        fixture_entities = {record["expected"]["ds_orgao"] for record in self.fixture["records"]}
        self.assertTrue(fixture_entities.issubset(set(witness["entity_codes"])))

    def test_collision_witness_is_small_minimized_and_self_consistent(self):
        raw = COLLISIONS.read_text(encoding="utf-8")
        witness = json.loads(raw)
        self.assertEqual(witness["schema"], "TASK282_COLLISION_RANGES_V3")
        self.assertEqual(witness["collision_witness_count"], 682)
        self.assertFalse(witness["exhaustive_source_collision_count_claimed"])
        self.assertEqual(
            sum(item["b"] - item["a"] + 1 for item in witness["ranges"]), 682)
        self.assertNotIn("identificador_despesa", raw)
        self.assertNotIn("vl_despesa", raw)
        self.assertNotIn("historico_despesa", raw)

    def test_task282_is_registered_as_t0_offline_without_workflow(self):
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        gates = [gate for gate in policy["gates"]
                 if gate["id"] == "TASK_282_PNCP_TCE_OFFLINE_IDENTITY_AUDIT"]
        self.assertEqual(len(gates), 1)
        gate = gates[0]
        self.assertEqual(gate["tier"], "T0_OFFLINE")
        self.assertFalse(gate["auto_allowed"])
        self.assertEqual(gate["credential_capability"], "NONE")
        self.assertEqual(gate["current_triggers"], [])
        self.assertTrue(gate["no_workflow_trigger"])
        self.assertTrue(gate["manual_execution_required"])
        self.assertTrue(gate["owner_authorization_required"])
        self.assertEqual(gate["blockers"], [
            "EXPLICIT_OWNER_OR_ORCHESTRATOR_GATE_REQUIRED_FOR_LOCAL_SNAPSHOT_EXECUTION"
        ])
        self.assertFalse(gate["remote_materialization_authorized"])
        self.assertFalse(gate["financial_identity_promotion_authorized"])
        self.assertEqual(gate["effects"], {
            "source_network": False,
            "drive_reads": False,
            "drive_writes": False,
            "publication": False,
        })

    def test_supplier_change_within_same_scoped_commitment_is_fail_closed(self):
        rows = [deepcopy(r) for r in self.rows if row_key(r) == self.key]
        rows[1]["identificador_despesa"] = "TRANSFER_OR_NOVATION_REQUIRES_EXPLICIT_WITNESS"
        with self.assertRaisesRegex(AccountingIdentityStop,
                                    "CONFLICTING_SUPPLIER_WITHIN_SCOPED_COMMITMENT"):
            index_rows(rows)


if __name__ == "__main__":
    unittest.main()

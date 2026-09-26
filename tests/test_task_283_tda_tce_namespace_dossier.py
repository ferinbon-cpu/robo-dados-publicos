from copy import deepcopy
import ast
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from robo_dados_publicos.automation.policy import evaluate_gate, load_policy, validate_policy
from robo_dados_publicos.research import task283_tda_tce_namespace_dossier as task283


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_283_TDA_TCE_NAMESPACE_DOSSIER_0.8.0.json"


class Task283NamespaceDossierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = task283.load_config()

    def test_current_dossier_is_exactly_unresolved(self):
        result = task283.build_dossier()
        self.assertEqual(
            result["status"], "UNRESOLVED_MISSING_OFFICIAL_NAMESPACE_WITNESS"
        )
        self.assertEqual(
            result["municipal_chain"],
            {
                "contract": "45/2026",
                "typed_procurement": "E00010/2026",
                "tda_commitment": "03286-01",
                "status": "PROVEN",
            },
        )
        self.assertEqual(result["tce_candidate"]["commitment"], "3286-2026")
        self.assertEqual(
            result["tce_candidate"]["key"],
            {
                "municipality": "Limeira",
                "entity": "PREFEITURA MUNICIPAL DE LIMEIRA",
                "original_year": 2026,
                "number": "3286",
            },
        )
        self.assertFalse(result["namespace_edge"]["heuristic_normalization_allowed"])
        self.assertFalse(result["payment_attribution_authorized"])
        self.assertFalse(result["live_acquisition_authorized"])

    def test_canonical_evidence_matches_runtime_boundary(self):
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        runtime = task283.build_dossier()
        self.assertEqual(evidence["status"], runtime["status"])
        self.assertEqual(evidence["municipal_chain"], runtime["municipal_chain"])
        self.assertEqual(evidence["tce_candidate"], runtime["tce_candidate"])
        self.assertEqual(evidence["namespace_edge"]["from"], runtime["namespace_edge"]["from"])
        self.assertEqual(evidence["namespace_edge"]["to"], runtime["namespace_edge"]["to"])
        self.assertEqual(
            evidence["namespace_edge"]["status"], runtime["namespace_edge"]["status"]
        )
        self.assertFalse(evidence["payment_attribution_authorized"])
        self.assertFalse(evidence["live_acquisition_authorized"])

    def test_every_repository_input_is_pinned_by_git_blob_identity(self):
        for name, spec in self.config["pinned_repository_inputs"].items():
            payload = (ROOT / spec["path"]).read_bytes()
            self.assertEqual(task283.git_blob_sha(payload), spec["git_blob_sha"], name)
            loaded = task283.pinned_json(name, self.config)
            self.assertIsInstance(loaded, dict)

    def test_pinned_source_drift_stops(self):
        config = deepcopy(self.config)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "fixture.json").write_text('{"ok": true}', encoding="utf-8")
            config["pinned_repository_inputs"] = {
                "drift": {
                    "path": "fixture.json",
                    "git_blob_sha": "0" * 40,
                }
            }
            with patch.object(task283, "ROOT", root):
                with self.assertRaisesRegex(task283.Task283Stop, "PINNED_SOURCE_DRIFT_DRIFT"):
                    task283.pinned_json("drift", config)

    def positive_witness(self):
        return {
            "authority_class": "PREFEITURA_MUNICIPAL_DE_LIMEIRA",
            "source_locator": "OFFICIAL_DOCUMENT_EXAMPLE",
            "source_sha256": "a" * 64,
            "tda_commitment": "03286-01",
            "tce_number": "3286",
            "tce_original_year": 2026,
            "tce_entity": "PREFEITURA MUNICIPAL DE LIMEIRA",
        }

    def test_only_complete_official_witness_can_prove_namespace(self):
        result = task283.validate_witness(self.positive_witness(), self.config)
        self.assertEqual(result["status"], "PROVEN_OFFICIAL_NAMESPACE_WITNESS")
        self.assertFalse(result["payment_attribution_authorized"])

    def test_witness_missing_any_identity_field_fails_closed(self):
        for field in self.config["positive_witness_contract"]["required_fields"]:
            with self.subTest(field=field):
                witness = self.positive_witness()
                del witness[field]
                with self.assertRaisesRegex(
                    task283.Task283Stop, f"WITNESS_FIELD_MISSING_{field.upper()}"
                ):
                    task283.validate_witness(witness, self.config)

    def test_witness_wrong_identity_value_fails_closed(self):
        mutations = {
            "tda_commitment": "3286",
            "tce_number": "03286",
            "tce_original_year": 2025,
            "tce_entity": "INSTITUTO DE PREVIDÊNCIA MUNICIPAL DE LIMEIRA",
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                witness = self.positive_witness()
                witness[field] = value
                with self.assertRaisesRegex(
                    task283.Task283Stop, f"WITNESS_VALUE_MISMATCH_{field.upper()}"
                ):
                    task283.validate_witness(witness, self.config)

    def test_unapproved_authority_or_bad_provenance_fails_closed(self):
        witness = self.positive_witness()
        witness["authority_class"] = "BLOG_OR_SEARCH_RESULT"
        with self.assertRaisesRegex(task283.Task283Stop, "WITNESS_AUTHORITY_NOT_ALLOWED"):
            task283.validate_witness(witness, self.config)

        for field in self.config["positive_witness_contract"]["provenance_required_fields"]:
            with self.subTest(field=field):
                witness = self.positive_witness()
                witness[field] = ""
                with self.assertRaisesRegex(
                    task283.Task283Stop, f"WITNESS_PROVENANCE_MISSING_{field.upper()}"
                ):
                    task283.validate_witness(witness, self.config)

        witness = self.positive_witness()
        witness["source_sha256"] = "not-a-sha"
        with self.assertRaisesRegex(task283.Task283Stop, "WITNESS_SOURCE_SHA256"):
            task283.validate_witness(witness, self.config)

    def test_heuristic_promotion_is_forbidden_even_with_exact_values(self):
        for marker in self.config["positive_witness_contract"]["heuristics_forbidden"]:
            with self.subTest(marker=marker):
                witness = self.positive_witness()
                witness[marker] = True
                with self.assertRaisesRegex(task283.Task283Stop, "WITNESS_HEURISTIC_FORBIDDEN"):
                    task283.validate_witness(witness, self.config)

    def test_historical_tda_detail_query_was_never_executed(self):
        history = task283.build_dossier()["historical_query_audit"]
        self.assertFalse(history["task219x_query_executed"])
        self.assertFalse(history["task219y_query_executed"])
        self.assertFalse(history["task219z_query_executed"])
        self.assertEqual(history["last_gate"], "STOP_EXACT_DETAIL_SUBMIT_BINDING_NOT_UNIQUE")

    def test_task283_module_has_no_network_browser_or_subprocess_imports(self):
        blocked = {
            "requests", "urllib", "http", "aiohttp", "httpx", "socket",
            "subprocess", "selenium", "playwright", "ftplib", "smtplib",
        }
        path = ROOT / "robo_dados_publicos/research/task283_tda_tce_namespace_dossier.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertTrue(blocked.isdisjoint(imported), imported & blocked)

    def test_task283_policy_gate_is_manual_validation_only(self):
        policy = load_policy(ROOT)
        structural = validate_policy(policy)
        self.assertEqual(structural["status"], "PASS_AUTOMATION_POLICY_STRUCTURE")
        gate = next(
            row for row in policy["gates"]
            if row["id"] == "TASK283_TDA_TCE_NAMESPACE_DOSSIER"
        )
        self.assertEqual(gate["tier"], "T0_OFFLINE")
        self.assertFalse(gate["auto_allowed"])
        self.assertEqual(gate["current_triggers"], [])
        self.assertTrue(gate["validation_only"])
        self.assertTrue(gate["no_workflow_trigger"])
        self.assertTrue(gate["manual_execution_required"])
        self.assertFalse(gate["task_runtime_auto_execution"])
        self.assertEqual(
            evaluate_gate(policy, "TASK283_TDA_TCE_NAMESPACE_DOSSIER")["decision"],
            "BLOCK",
        )


if __name__ == "__main__":
    unittest.main()

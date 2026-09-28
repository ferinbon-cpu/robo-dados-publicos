import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from copy import deepcopy
from robo_dados_publicos.automation.policy import (
    AutomationPolicyError, evaluate_gate, load_policy, validate_policy,
)
from robo_dados_publicos.research.task283_tda_tce_namespace_dossier import Task283Stop
from robo_dados_publicos.research.task284_tda_binding_gate import load_contract, validate_binding


class Task284BindingTests(unittest.TestCase):
    def test_central_policy_blocks_task284_automatic_execution(self):
        policy = load_policy(Path(__file__).resolve().parents[1])
        self.assertEqual(validate_policy(policy)["status"], "PASS_AUTOMATION_POLICY_STRUCTURE")
        gate = next(g for g in policy["gates"] if g["id"] == "TASK284_TDA_NAMESPACE_ACQUISITION")
        self.assertEqual(gate["tier"], "T1_REMOTE_READONLY")
        self.assertEqual(gate["credential_capability"], "PUBLIC_BROWSER_NO_AUTH")
        self.assertFalse(gate["auto_allowed"])
        self.assertFalse(gate["task_runtime_auto_execution"])
        self.assertTrue(gate["manual_execution_required"])
        self.assertTrue(gate["owner_authorization_required"])
        self.assertEqual(gate["current_triggers"], [])
        self.assertFalse(gate["workflow_added"])
        self.assertNotIn("workflow", gate)
        self.assertIn("AUTOMATIC_EXECUTION_NOT_AUTHORIZED", gate["blockers"])
        decision = evaluate_gate(policy, gate["id"])
        self.assertEqual(decision["decision"], "BLOCK")
        self.assertEqual(decision["reason"], "POLICY_AUTO_ALLOWED_FALSE")

    def test_enabling_automatic_execution_without_proven_capability_stops(self):
        policy = load_policy(Path(__file__).resolve().parents[1])
        gate = next(g for g in policy["gates"] if g["id"] == "TASK284_TDA_NAMESPACE_ACQUISITION")
        gate["auto_allowed"] = True
        with self.assertRaisesRegex(AutomationPolicyError, "STOP_AUTO_READONLY_CREDENTIAL_NOT_PROVEN"):
            evaluate_gate(policy, gate["id"])

    def test_consumed_gate_records_no_query_and_does_not_infer_absence(self):
        root = Path(__file__).resolve().parents[1]
        evidence = json.loads((root / "docs/evidence/TASK_284_TDA_NAMESPACE_ACQUISITION_0.8.0.json").read_text())
        self.assertEqual(evidence["status"], "STOP_AREA_IDENTITY_NOT_PROVEN_BEFORE_TOP_ACTION")
        self.assertEqual(evidence["counts"]["target_queries"], 0)
        self.assertEqual(evidence["counts"]["top_area_actions"], 0)
        self.assertEqual(evidence["counts"]["retries"], 0)
        self.assertFalse(evidence["interpretation"]["commitment_existence_tested"])
        self.assertFalse(evidence["interpretation"]["query_negative_result"])
        self.assertTrue(evidence["authorization_consumed"])
        self.assertFalse(evidence["new_session_or_retry_authorized_by_this_record"])
        payload = json.dumps(evidence["sanitized_observation"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        self.assertEqual(hashlib.sha256(payload).hexdigest(), evidence["sanitized_observation_sha256"])
        contract_bytes = (root / "config/task284_tda_namespace_acquisition.v1.json").read_bytes()
        self.assertEqual(hashlib.sha256(contract_bytes).hexdigest(), evidence["contract_sha256"])

    def binding(self):
        return {"area_name": "Detalhe do Empenho", "area_origin": "2_92_guestuser_200_8_DSL0_VIS706", "area_id": "SYNTHETIC_DSA8", "area_count": 1, "filter_id": "AREAFILTER_SYNTHETIC_DSA8", "number_id": "FILTEREDIT_SYNTHETIC_DSA8_epn", "number_count": 1, "number_label": "Nro Empenho", "year_id": "FILTERCOMBO_SYNTHETIC_DSA8_exe", "year_count": 1, "year_label": "Exercício", "year_2026_option_count": 1, "controls_inside_filter": True, "submit_count": 1, "submit_visible": True, "submit_handler": "submmitApply('AREAFILTER_SYNTHETIC_DSA8');", "numeric_query_3286_explicitly_supported": True}

    def test_contract_has_no_automatic_executor_or_pncp(self):
        c = load_contract()
        self.assertFalse(c["automatic_execution_allowed"])
        self.assertEqual(c["limits"]["pncp_requests"], 0)
        self.assertFalse(c["task281_consumed"])

    def test_contract_target_and_authorization_drift_stop(self):
        original = load_contract()
        for key, value in {"start_url": "https://pncp.gov.br/", "query": {"year": "2025", "number": "3286"}, "owner_authorization": "", "tier": "T0_OFFLINE", "task281_consumed": True}.items():
            with self.subTest(key=key):
                data = deepcopy(original); data[key] = value
                with patch.object(Path, "read_text", return_value=json.dumps(data)):
                    with self.assertRaises(Task283Stop): load_contract()

    def test_unique_binding_is_only_query_permission_not_identity(self):
        r = validate_binding(self.binding())
        self.assertFalse(r["namespace_identity_proven"])
        self.assertFalse(r["payment_attribution_authorized"])

    def test_duplicate_stale_unscoped_or_unsupported_controls_stop(self):
        for key, value in {"area_count": 2, "area_origin": "OTHER", "area_id": "OLD_SESSION", "number_count": 2, "number_label": "", "year_count": 0, "year_2026_option_count": 2, "controls_inside_filter": False, "submit_count": 0, "submit_visible": False, "numeric_query_3286_explicitly_supported": False}.items():
            with self.subTest(key=key):
                b = self.binding(); b[key] = value
                with self.assertRaises(Task283Stop): validate_binding(b)

    def test_area_id_only_or_ambiguous_handler_cannot_be_guessed(self):
        for handler in ["submmitApply('SYNTHETIC_DSA8')", "submmitApply('AREAFILTER_OTHER')", "submmitApply('AREAFILTER_SYNTHETIC_DSA8'); otherAction()"]:
            with self.subTest(handler=handler):
                b = self.binding(); b["submit_handler"] = handler
                with self.assertRaisesRegex(Task283Stop, "TASK284_SUBMIT_ARGUMENT"): validate_binding(b)


if __name__ == "__main__":
    unittest.main()

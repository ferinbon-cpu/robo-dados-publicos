import json
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.operational import OperationalCycle, compare_runs
from robo_dados_publicos.operational.model import STAGES


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/operational_cycle.limeira_pilot.v1.json"


class TestTask017OperationalCycle(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(CONFIG.read_text(encoding="utf-8"))

    def run_cycle(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        out = Path(temporary.name) / "out"
        return OperationalCycle(self.config).run(out, started_at="2026-08-31T00:00:00+00:00"), out

    def test_release_and_frozen_series_boundary(self):
        boundary = self.config["release_boundary"]
        self.assertEqual(("0.7.0", "0.8.0"), (boundary["active"], boundary["candidate"]))
        self.assertEqual("2016-2024", boundary["closed_annual_series"])
        self.assertEqual("UNKNOWN/BLOCKED", boundary["gold_2025"])
        self.assertEqual(["PENDING"] * 3, [boundary[x] for x in ("B1", "B2", "B3")])

    def test_pinned_reference_counts_and_identity_are_exact(self):
        self.assertEqual("LIMEIRA_JORNAL_OFICIAL_EDICAO_7310", self.config["source"]["source_id"])
        p = self.config["pinned_reference"]
        self.assertEqual((76, 195540, 53, 148, 68), (p["pages"], p["extracted_characters"], p["gold_events"], p["rag_chunks"], p["reconciliation_tasks"]))

    def test_pinned_reuse_composes_all_stages_offline(self):
        result, out = self.run_cycle()
        self.assertEqual("PASS", result["status"])
        self.assertEqual(list(STAGES), [x["stage"] for x in result["stages"]])
        self.assertTrue((out / "operational_result.json").is_file())
        self.assertTrue((out / "operational_summary.md").is_file())
        self.assertTrue((out / "product/report.pdf").is_file())
        self.assertEqual(0, sum(x["remote_reads"] + x["remote_writes"] for x in result["stages"]))

    def test_zero_network_drive_collection_and_live_reconciliation(self):
        result, _ = self.run_cycle()
        self.assertEqual({"network_requests": 0, "drive_reads": 0, "drive_writes": 0, "source_collection": 0, "live_reconciliation": 0}, result["effects"])

    def test_live_mode_and_default_live_source_block(self):
        self.config["source_mode"] = "LIVE_ONE_SHOT_AUTHORIZED"
        self.config["source"]["authorization_state"] = self.config["default_live_authorization_state"]
        result = OperationalCycle(self.config).run("unused")
        self.assertEqual("STOP_AUTHORIZATION_REQUIRED", result["status"])
        self.assertIn("LIVE_MODE_REQUIRES_OWNER_AUTHORIZATION", result["stop_reasons"])

    def test_pinned_authorization_must_be_exact(self):
        for authorization in ("LIVE_READONLY_AUTHORIZED", "LIVE_CREATE_ONLY_AUTHORIZED"):
            with self.subTest(authorization=authorization):
                config = json.loads(json.dumps(self.config))
                config["source"]["authorization_state"] = authorization
                result = OperationalCycle(config).run("unused")
                self.assertEqual("STOP_AUTHORIZATION_REQUIRED", result["status"])
                self.assertIn("PINNED_REUSE_AUTHORIZATION_INCONSISTENT", result["stop_reasons"])

    def test_stop_prevents_every_downstream_stage(self):
        self.config["schedule"] = "ENABLED"
        result = OperationalCycle(self.config).run("unused")
        self.assertTrue(result["stages"][0]["executed"])
        self.assertTrue(all(not x["executed"] and x["status"] == "STOP_DEPENDENCY" for x in result["stages"][1:]))

    def test_create_only_collision_stops_without_overwrite(self):
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw) / "existing"; out.mkdir(); marker = out / "marker"; marker.write_text("keep")
            result = OperationalCycle(self.config).run(out)
            self.assertEqual("STOP_CONTRACT_UNPROVEN", result["status"])
            self.assertEqual("keep", marker.read_text())

    def test_every_important_pinned_value_is_checked_against_canonical_contracts(self):
        mutations = (
            (("source", "sha256"), "0" * 64),
            (("source", "source_id"), "OTHER_SOURCE"),
            (("source", "edition"), 7311),
            (("processing_identity",), "OTHER_PROCESSING"),
            (("pinned_reference", "pages"), 75),
            (("reconciliation", "limit"), 2),
            (("reconciliation", "allowed_targets"), ["TCE_SP_DESPESAS"]),
            (("reconciliation", "financial_identity_auto_promotion"), "ALLOWED"),
        )
        for path, value in mutations:
            with self.subTest(path=path):
                config = json.loads(json.dumps(self.config))
                target = config
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
                result = OperationalCycle(config).run("unused")
                self.assertEqual("STOP_CONTRACT_UNPROVEN", result["status"])
                self.assertIn("PINNED_EVIDENCE_CONTRACT_DRIFT", result["stop_reasons"])

    def test_release_and_semantic_state_drift_stops(self):
        mutations = (
            ("candidate_status", "ACTIVE"),
            ("closed_annual_series", "2016-2025"),
            ("gold_2025", "PROVEN"),
            ("B1", "RECEIVED/PROVEN"),
            ("annual_closure_status", "PROVEN"),
            ("semantic_comparability_status", "PROVEN"),
        )
        for key, value in mutations:
            with self.subTest(key=key):
                config = json.loads(json.dumps(self.config))
                config["release_boundary"][key] = value
                result = OperationalCycle(config).run("unused")
                self.assertEqual("STOP_CONTRACT_UNPROVEN", result["status"])
                self.assertIn("CANONICAL_RELEASE_STATE_DRIFT", result["stop_reasons"])

    def test_reconciliation_is_bounded_and_never_promotes_identity(self):
        r = self.config["reconciliation"]
        self.assertEqual(["LIMEIRA_CONTRATOS"], r["allowed_targets"])
        self.assertEqual((1, 1), (r["limit"], r["required_selected"]))
        self.assertEqual("PROHIBITED", r["financial_identity_auto_promotion"])
        result, _ = self.run_cycle()
        self.assertEqual(0, result["reconciliation_result_counts_by_status"]["MATCH_CANDIDATE"])

    def test_product_preserves_uncertainty(self):
        _, out = self.run_cycle()
        report = json.loads((out / "product/report.json").read_text())
        self.assertIn("EVIDENCIA_INSUFICIENTE", [row["status"] for row in report["rows"]])
        self.assertFalse(report["semantics"]["presentation_is_evidence"])

    def test_product_provenance_uses_candidate_without_release_promotion(self):
        result, out = self.run_cycle()
        report = json.loads((out / "product/report.json").read_text())
        self.assertEqual("0.7.0", result["software_active"])
        self.assertEqual("0.8.0", result["candidate_version"])
        self.assertEqual("0.8.0", report["report_card"]["software_version"])
        self.assertEqual({"software_version": "0.8.0", "release_status": "CANDIDATE", "active_version": "0.7.0"}, report["software_provenance"])
        self.assertEqual(("ACTIVE", "CANDIDATE"), (self.config["release_boundary"]["active_status"], self.config["release_boundary"]["candidate_status"]))

    def test_run_and_snapshot_identities_are_separate(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            first = OperationalCycle(self.config).run(root / "first", started_at="2026-08-31T00:00:00+00:00")
            same_execution = OperationalCycle(self.config).run(root / "same", started_at="2026-08-31T00:00:00+00:00")
            second = OperationalCycle(self.config).run(root / "second", prior=first, started_at="2026-08-31T01:00:00+00:00")
            first_report = json.loads((root / "first/product/report.json").read_text(encoding="utf-8"))
            second_report = json.loads((root / "second/product/report.json").read_text(encoding="utf-8"))
        self.assertEqual(first["snapshot_id"], same_execution["snapshot_id"])
        self.assertEqual(first["snapshot_id"], second["snapshot_id"])
        self.assertEqual(first["run_id"], same_execution["run_id"])
        self.assertNotEqual(first["run_id"], second["run_id"])
        self.assertEqual(["NO_CHANGE"], second["comparison"])
        self.assertEqual(first["run_id"], first_report["report_card"]["report_id"])
        self.assertEqual(second["run_id"], second_report["report_card"]["report_id"])
        self.assertIn("snapshot_id", second)
        self.assertIn("run_id", second)

    def test_comparison_first_run(self):
        self.assertEqual(["FIRST_RUN"], compare_runs({"profile_id": "P"}, None))

    def test_comparison_no_change(self):
        run = {"profile_id": "P", "source_hashes": ["a"], "stop_reasons": []}
        self.assertEqual(["NO_CHANGE"], compare_runs(run, dict(run)))

    def test_comparison_source_changed(self):
        prior = {"profile_id": "P", "source_hashes": ["a"]}
        current = {"profile_id": "P", "source_hashes": ["b"]}
        self.assertIn("SOURCE_CHANGED", compare_runs(current, prior))

    def test_human_summary_renders_every_simultaneous_change(self):
        prior = {
            "profile_id": self.config["profile_id"],
            "source_identities": [self.config["source"]["source_id"]],
            "source_hashes": ["different"],
            "processed_object_counts": {"pages": 1},
            "gold_event_counts": 1,
            "reconciliation_task_counts": 68,
            "reconciliation_result_counts_by_status": {"MATCH_CANDIDATE": 0, "NO_MATCH": 0},
            "stop_reasons": ["OLD_STOP"],
        }
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw) / "out"
            result = OperationalCycle(self.config).run(out, prior=prior, started_at="2026-08-31T00:00:00+00:00")
            summary = (out / "operational_summary.md").read_text(encoding="utf-8")
        self.assertEqual(["SOURCE_CHANGED", "PROCESSING_CHANGED", "STOP_STATE_CHANGED"], result["comparison"])
        for classification in result["comparison"]:
            self.assertIn(classification, summary)
        self.assertNotIn("Anything new: no", summary)

    def test_no_schedule_recurrence_or_mutating_persistence(self):
        self.assertEqual(("DISABLED", "DISABLED", "CREATE_ONLY_LOCAL"), (self.config["schedule"], self.config["recurrence"], self.config["persistence_policy"]))

    def test_no_siope_fnde_or_tda_scope(self):
        serialized = json.dumps(self.config)
        for forbidden in ("FNDE", "SIOPE", "FALA.BR", "TDA", "TCE_SP_DESPESAS"):
            self.assertNotIn(forbidden, serialized.upper())


if __name__ == "__main__":
    unittest.main()

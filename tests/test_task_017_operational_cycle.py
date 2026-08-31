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

    def test_stop_prevents_every_downstream_stage(self):
        self.config["schedule"] = "ENABLED"
        result = OperationalCycle(self.config).run("unused")
        self.assertTrue(result["stages"][0]["executed"])
        self.assertTrue(all(not x["executed"] and x["status"] == "STOP_DEPENDENCY" for x in result["stages"][1:]))

    def test_create_only_collision_stops_without_overwrite(self):
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw) / "existing"; out.mkdir(); marker = out / "marker"; marker.write_text("keep")
            result = OperationalCycle(self.config).run(out)
            self.assertEqual("STOP_AUTHORIZATION_REQUIRED", result["status"])
            self.assertEqual("keep", marker.read_text())

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

    def test_comparison_first_run(self):
        self.assertEqual(["FIRST_RUN"], compare_runs({"profile_id": "P"}, None))

    def test_comparison_no_change(self):
        run = {"profile_id": "P", "source_hashes": ["a"], "stop_reasons": []}
        self.assertEqual(["NO_CHANGE"], compare_runs(run, dict(run)))

    def test_comparison_source_changed(self):
        prior = {"profile_id": "P", "source_hashes": ["a"]}
        current = {"profile_id": "P", "source_hashes": ["b"]}
        self.assertIn("SOURCE_CHANGED", compare_runs(current, prior))

    def test_no_schedule_recurrence_or_mutating_persistence(self):
        self.assertEqual(("DISABLED", "DISABLED", "CREATE_ONLY_LOCAL"), (self.config["schedule"], self.config["recurrence"], self.config["persistence_policy"]))

    def test_no_siope_fnde_or_tda_scope(self):
        serialized = json.dumps(self.config)
        for forbidden in ("FNDE", "SIOPE", "FALA.BR", "TDA", "TCE_SP_DESPESAS"):
            self.assertNotIn(forbidden, serialized.upper())


if __name__ == "__main__":
    unittest.main()

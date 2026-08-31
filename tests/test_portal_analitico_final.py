import copy
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / "config/bi/portal_analitico_final.v1.json").read_text(encoding="utf-8"))
BI = json.loads((ROOT / "config/bi/analytics_output.v1.json").read_text(encoding="utf-8"))

from scripts.github_portal_analitico_final_gate import validate_field_references


class TestPortalAnaliticoFinal(unittest.TestCase):
    def test_boundary_sources_pages_and_tabs(self):
        self.assertEqual(CONTRACT["tier"], "T0_OFFLINE_PORTAL_ANALYTICS_DESIGN")
        self.assertEqual(CONTRACT["dataset_count"], 6)
        self.assertEqual(CONTRACT["data_studio_report"]["page_count"], 5)
        expected = {item["dataset_id"] for item in BI["datasets"]}
        self.assertEqual({item["dataset_id"] for item in CONTRACT["datasets"]}, expected)
        self.assertEqual(
            {item["serving_name"] for item in CONTRACT["datasets"]},
            {dataset + "__SERVING" for dataset in expected},
        )
        self.assertTrue(
            all(item["analytical_tab"] == "DATA" and item["audit_tab"] == "META"
                for item in CONTRACT["datasets"])
        )

    def test_every_visual_has_complete_design_record(self):
        required = {"question", "source", "dimension", "metric", "aggregation", "filter", "caution"}
        self.assertTrue(CONTRACT["charts"])
        self.assertTrue(all(required <= set(item) for item in CONTRACT["charts"]))

    def test_all_portal_field_references_are_authoritative(self):
        self.assertEqual(validate_field_references(CONTRACT, BI), [])

    def test_invented_table_field_fails_closed(self):
        mutated = copy.deepcopy(CONTRACT)
        mutated["tables"][2]["columns"].append("__NOT_A_REAL_FIELD__")
        errors = validate_field_references(mutated, BI)
        self.assertTrue(any("__NOT_A_REAL_FIELD__" in error for error in errors))

    def test_invented_chart_field_fails_closed(self):
        mutated = copy.deepcopy(CONTRACT)
        mutated["charts"][0]["metric"] = "__NOT_A_REAL_FIELD__"
        errors = validate_field_references(mutated, BI)
        self.assertTrue(any("__NOT_A_REAL_FIELD__" in error for error in errors))

    def test_unknown_source_fails_closed(self):
        mutated = copy.deepcopy(CONTRACT)
        mutated["filters"][0]["source"] = "BI_UNKNOWN"
        errors = validate_field_references(mutated, BI)
        self.assertTrue(any("unknown_source:BI_UNKNOWN" in error for error in errors))

    def test_reconciliation_table_uses_only_real_schema(self):
        fields = {
            item["dataset_id"]: {field["name"] for field in item["fields"]}
            for item in BI["datasets"]
        }
        table = next(item for item in CONTRACT["tables"] if item["id"] == "reconciliation_detail")
        self.assertLessEqual(set(table["columns"]), fields["BI_RECONCILIACAO"])
        self.assertIn("decision", table["columns"])
        self.assertIn("reason_code", table["columns"])
        self.assertNotIn("financial_identity_proven", table["columns"])
        self.assertNotIn("source_event_id", table["columns"])

    def test_semantic_boundaries(self):
        cautions = set(CONTRACT["semantic_cautions"])
        self.assertIn("SIOPE_2025_BLOCKED", cautions)
        self.assertIn("MATCH_CANDIDATE != FINANCIAL_IDENTITY", cautions)
        self.assertIn("JOURNAL_NULL_REMAINS_NULL", cautions)
        self.assertEqual(CONTRACT["calculated_fields"], [])
        self.assertFalse(CONTRACT["provenance_contract"]["portal_modifies_source_of_truth"])
        forbidden = {"MATCH", "FINANCIAL_MATCH", "PROVEN_MATCH"}
        self.assertTrue(forbidden.isdisjoint({item["id"] for item in CONTRACT["charts"]}))

    def test_sites_mapping_and_future_technology(self):
        sites = CONTRACT["google_sites"]
        self.assertTrue(sites["planned"])
        self.assertFalse(sites["build_performed"])
        self.assertFalse(sites["publication_performed"])
        self.assertEqual(len(sites["pages"]), 8)
        self.assertEqual(CONTRACT["workspace_studio_future"]["status"], "NOT_IMPLEMENTED")
        self.assertFalse(CONTRACT["workspace_studio_future"]["active_automation"])
        self.assertFalse(CONTRACT["workspace_studio_future"]["schedule"])
        self.assertFalse(CONTRACT["workspace_studio_future"]["recurrence"])
        self.assertFalse(CONTRACT["bigquery_future"]["used"])
        self.assertFalse(CONTRACT["appsheet_future"]["used"])

    def test_zero_effects_no_active_authorization(self):
        self.assertTrue(CONTRACT["remote_effects"])
        self.assertTrue(all(value == 0 for value in CONTRACT["remote_effects"].values()))
        self.assertIsNone(CONTRACT["active_authorization"])

    def test_runbooks_have_exact_step_counts_and_no_invented_reconciliation_field(self):
        data = (ROOT / "docs/bi/DATA_STUDIO_BUILD_RUNBOOK.md").read_text(encoding="utf-8")
        sites = (ROOT / "docs/bi/GOOGLE_SITES_BUILD_RUNBOOK.md").read_text(encoding="utf-8")
        self.assertTrue(all(f"{index}." in data for index in range(1, 23)))
        self.assertTrue(all(f"{index}." in sites for index in range(1, 18)))
        self.assertNotIn("financial_identity_proven", data)

    def test_qa_covers_required_invariants(self):
        qa = (ROOT / "docs/bi/PORTAL_QA_CHECKLIST.md").read_text(encoding="utf-8")
        for text in (
            "Exatamente seis",
            "2016=P1",
            "2017–2024=P6",
            "2025 ausente",
            "Null do Jornal",
            "MATCH_CANDIDATE != FINANCIAL_IDENTITY",
            "Zero efeitos remotos",
            "Zero Google Cloud, BigQuery e AppSheet",
        ):
            self.assertIn(text, qa)


if __name__ == "__main__":
    unittest.main()

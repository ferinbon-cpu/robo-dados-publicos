"""No network: structured-source parsing, documentary pins and promotion attacks."""
import copy
import importlib.util
import io
from pathlib import Path
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("task246_gate", ROOT / "scripts/github_task_246_ibge_population_gate.py")
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


class PopulationContractTests(unittest.TestCase):
    def setUp(self):
        self.args = {k: GATE.load(ROOT / v) for k, v in GATE.PATHS.items()}
        self.args["snapshots"] = {s["id"].lower(): GATE.load(ROOT / s["decoded_snapshot_path"])
                                  for s in self.args["support"]["sources"] if s.get("decoded_snapshot_path")}

    def run_gate(self):
        return GATE.validate_objects(**self.args)

    def test_offline_actual_evidence_derives_negative_decision(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden")):
            self.assertEqual(GATE.validate(), GATE.PASS)
        decision = self.run_gate()
        self.assertEqual(decision["status"], "NOT_COMPARABLE")
        self.assertEqual(decision["missing_reference_years"], [2023])
        self.assertEqual(decision["projection_revisions"], [2013, 2018, 2024])
        self.assertEqual(len(decision["observed_reference_years"]), 9)

    def test_publication_2023_cannot_fill_reference_2023(self):
        row = self.args["inventory"]["observations"][7]
        row.update(population=291869, reference_date="2023-07-01", classification="CENSUS")
        with self.assertRaisesRegex(ValueError, "inventory"):
            self.run_gate()

    def test_interpolation_and_carry_forward_rejected(self):
        for value in [296298, 291869, 300728, 0]:
            with self.subTest(value=value):
                self.setUp()
                self.args["inventory"]["observations"][7]["population"] = value
                with self.assertRaises(ValueError):
                    self.run_gate()

    def test_all_populations_and_reference_dates_bound_to_official_evidence(self):
        for i in [0, 1, 2, 3, 4, 5, 6, 8, 9]:
            for field in ["population", "reference_date"]:
                with self.subTest(i=i, field=field):
                    self.setUp()
                    row = self.args["inventory"]["observations"][i]
                    row[field] = row[field] + 1 if field == "population" else f"{row['year']}-12-31"
                    with self.assertRaises(ValueError):
                        self.run_gate()

    def test_missing_duplicate_and_out_of_scope_years_rejected(self):
        for operation in ["remove", "duplicate", "2026"]:
            with self.subTest(operation=operation):
                self.setUp()
                rows = self.args["inventory"]["observations"]
                if operation == "remove":
                    rows.pop(7)
                elif operation == "duplicate":
                    rows.append(copy.deepcopy(rows[0]))
                else:
                    rows[-1]["year"] = 2026
                with self.assertRaises(ValueError):
                    self.run_gate()

    def test_publication_date_cannot_be_invented_from_modification(self):
        row = self.args["inventory"]["observations"][3]
        row["publication_date"] = "2022-09-05"
        with self.assertRaises(ValueError):
            self.run_gate()

    def test_document_semantics_cannot_be_promoted_with_consistent_json_hashes(self):
        for field, value in [("same_projection_revision_required", False),
                             ("unadjusted_census_estimate_direct_growth_rejected", False),
                             ("official_harmonizing_adapter_acquired", True)]:
            with self.subTest(field=field):
                self.setUp()
                self.args["contract"]["reviewed_comparison_rules"][field] = value
                self.args["evidence"]["artifact_sha256"][GATE.PATHS["contract"]] = GATE.object_digest(self.args["contract"])
                with self.assertRaisesRegex(ValueError, "unreviewed contract"):
                    self.run_gate()

    def test_regime_and_territorial_proof_cannot_be_fabricated(self):
        for section in ["regimes", "territory", "minimum_closing_evidence"]:
            with self.subTest(section=section):
                self.setUp()
                self.args["contract"][section] = {"status": "PROVEN"}
                with self.assertRaises(ValueError):
                    self.run_gate()

    def test_support_url_hash_or_ods_value_cannot_drift(self):
        for mutation in ["url", "hash", "value"]:
            with self.subTest(mutation=mutation):
                self.setUp()
                support = self.args["support"]
                if mutation == "value":
                    support["ods_extracts"]["REVISED2019"]["population"] += 1
                else:
                    support["sources"][0]["official_url" if mutation == "url" else "raw_sha256"] = "https://third-party.invalid/"
                self.args["evidence"]["artifact_sha256"][GATE.PATHS["support"]] = GATE.object_digest(support)
                with self.assertRaisesRegex(ValueError, "unreviewed support"):
                    self.run_gate()

    def test_api_change_is_not_masked_by_matching_inventory(self):
        series = self.args["snapshots"]["estimates_limeira"][0]["resultados"][0]["series"][0]
        series["serie"]["2019"] = "306115"
        self.args["inventory"]["observations"][3]["population"] = 306115
        with self.assertRaisesRegex(ValueError, "API snapshot drift"):
            self.run_gate()

    def test_no_permission_or_release_can_be_promoted(self):
        for field, old in GATE.PRESERVED.items():
            with self.subTest(field=field):
                self.setUp()
                value = True if old is False else "PROMOTED"
                self.args["evidence"]["preserved_state"][field] = value
                self.args["overlay"]["preserved_state"][field] = value
                with self.assertRaises(ValueError):
                    self.run_gate()

    def test_future_acquisition_cannot_be_enabled(self):
        self.args["acquisition"]["automatic_future_acquisition_authorized"] = True
        with self.assertRaises(ValueError):
            self.run_gate()

    def test_decision_and_denominator_promotion_rejected(self):
        for mutation in ["decision", "denominator", "snapshot", "closing"]:
            with self.subTest(mutation=mutation):
                self.setUp()
                if mutation == "decision":
                    self.args["evidence"]["decision"]["status"] = "PROVEN"
                elif mutation == "denominator":
                    self.args["overlay"]["annual_comparable_denominator_series_materialized"] = True
                elif mutation == "snapshot":
                    self.args["evidence"]["historical_snapshots"].pop()
                else:
                    self.args["evidence"]["minimum_closing_evidence"]["artifact_status"] = "ACQUIRED"
                with self.assertRaises(ValueError):
                    self.run_gate()


class StructuredParserTests(unittest.TestCase):
    def setUp(self):
        self.data = GATE.load(ROOT / "docs/evidence/task246_sources/estimates_limeira.json")

    def parse(self):
        return GATE.parse_population(self.data, "9324", "População residente estimada", GATE.ESTIMATE_YEARS)

    def test_structured_integer_values(self):
        self.assertEqual(self.parse()[2019], 306114)
        self.assertEqual(self.parse()[2025], 301292)

    def test_source_symbols_units_classification_and_wrong_municipality_stop(self):
        for mutation in ["ellipsis", "decimal", "negative", "float", "unit", "classification", "six_digits", "wrong_city", "duplicate", "extra_year"]:
            with self.subTest(mutation=mutation):
                self.setUp()
                var = self.data[0]
                result = var["resultados"][0]
                row = result["series"][0]
                if mutation in ["ellipsis", "decimal", "negative", "float"]:
                    row["serie"]["2019"] = {"ellipsis": "...", "decimal": "306.114", "negative": "-1", "float": 306114.0}[mutation]
                elif mutation == "unit":
                    var["unidade"] = "Mil pessoas"
                elif mutation == "classification":
                    result["classificacoes"] = [{"id": "SOMETHING"}]
                elif mutation == "six_digits":
                    row["localidade"]["id"] = "352690"
                elif mutation == "wrong_city":
                    row["localidade"]["id"] = "3550308"
                elif mutation == "duplicate":
                    result["series"].append(copy.deepcopy(row))
                else:
                    row["serie"]["2023"] = "291869"
                with self.assertRaises(ValueError):
                    self.parse()

    def ods(self, row_repeat=1, population="306114", duplicates=False):
        cells = '<table:table-cell><text:p>SP</text:p></table:table-cell>'
        cells += '<table:table-cell office:value="35"/><table:table-cell office:value="26902"/>'
        cells += '<table:table-cell><text:p>Limeira</text:p></table:table-cell>'
        cells += f'<table:table-cell office:value="{population}"/>'
        row = f'<table:table-row table:number-rows-repeated="{row_repeat}">{cells}</table:table-row>'
        xml = '<office:document-content ' + ' '.join(f'xmlns:{k}="{v}"' for k, v in GATE.NS.items()) + '>'
        xml += '<table:table table:name="Municípios"><table:table-row table:number-rows-repeated="3"/>' + row
        xml += (row if duplicates else '') + '</table:table></office:document-content>'
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as book:
            book.writestr("content.xml", xml)
        return out.getvalue()

    def test_ods_numeric_cell_and_logical_row_are_reproducible(self):
        row = GATE.extract_ods_row(self.ods())
        self.assertEqual(row["population"], 306114)
        self.assertEqual(row["row_1_based"], 4)
        self.assertEqual(row["identity_cells"], ["SP", "35", "26902", "Limeira"])

    def test_ods_duplicate_repeated_target_and_noninteger_are_rejected(self):
        for kwargs in [{"duplicates": True}, {"row_repeat": 2}, {"population": "306114.5"}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                GATE.extract_ods_row(self.ods(**kwargs))


class ComparisonRuleTests(unittest.TestCase):
    """Synthetic reviewed semantics test the rule; they authorize no acquisition."""
    def setUp(self):
        self.rows = [{"year": y, "population": 100, "reference_date": f"{y}-07-01",
                      "unit": "Pessoas", "municipality_ibge_code": GATE.CODE,
                      "classification": "ESTIMATE", "projection_revision": 2024,
                      "territorial_comparability": "PROVEN_COMMON_TERRITORY"} for y in [2024, 2025]]
        self.rules = {"same_projection_revision_required": True, "unadjusted_census_estimate_direct_growth_rejected": True}

    def assess(self):
        return GATE.assess(self.rows, self.rules, [2024, 2025])

    def test_complete_reviewed_homogeneous_synthetic_pair(self):
        self.assertEqual(self.assess()["status"], "PROVEN")

    def test_identical_values_cannot_override_positive_revision_incompatibility(self):
        self.rows[0]["projection_revision"] = 2018
        self.assertEqual(self.assess()["status"], "NOT_COMPARABLE")

    def test_missing_reference_without_positive_break_is_partial(self):
        self.rows[0]["population"] = None
        self.assertEqual(self.assess()["status"], "PARTIAL")

    def test_unknown_territory_is_not_proof_of_break_or_continuity(self):
        self.rows[0]["territorial_comparability"] = "UPDATE_RECORDED_IMPACT_UNRESOLVED"
        self.assertEqual(self.assess()["status"], "PARTIAL")

    def test_different_reference_day_is_not_homogeneous(self):
        self.rows[0]["reference_date"] = "2024-08-01"
        self.assertEqual(self.assess()["status"], "PARTIAL")

    def test_unknown_projection_revision_cannot_be_filled_by_other_year(self):
        self.rows[0]["projection_revision"] = None
        self.assertEqual(self.assess()["status"], "PARTIAL")

    def test_impossible_reference_date_rejected(self):
        self.rows[0]["reference_date"] = "2024-02-31"
        with self.assertRaises(ValueError):
            self.assess()

    def test_census_estimate_break_requires_positive_document_rule(self):
        self.rows[0].update(classification="CENSUS", projection_revision=None)
        self.assertEqual(self.assess()["status"], "NOT_COMPARABLE")
        self.rules["unadjusted_census_estimate_direct_growth_rejected"] = False
        self.assertEqual(self.assess()["status"], "PARTIAL")

    def test_publication_year_cannot_replace_reference_in_evaluator(self):
        self.rows[0]["reference_date"] = "2022-08-01"
        with self.assertRaisesRegex(ValueError, "publication year"):
            self.assess()


if __name__ == "__main__":
    unittest.main()

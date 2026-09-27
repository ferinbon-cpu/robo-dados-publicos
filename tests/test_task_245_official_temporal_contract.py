import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("task245_gate", ROOT / "scripts/github_task_245_official_temporal_contract_gate.py")
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


class Task245EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.args = dict(evidence=GATE.load(GATE.EVIDENCE), contract=GATE.load(GATE.CONTRACT),
                         support=GATE.load(GATE.SUPPORT), task241=GATE.load(GATE.TASK241))

    def run_gate(self):
        return GATE.validate_objects(**self.args)

    def test_acquired_evidence_and_preserved_snapshots_pass(self):
        self.assertEqual(GATE.validate(), GATE.PASS)
        result = self.run_gate()
        self.assertEqual(set(result["metrics"].values()), {"PARTIAL"})
        for row in result["inputs"].values():
            self.assertEqual(set(row["missing"]), set(GATE.DIMENSIONS) - {"period"})
            self.assertTrue(all(years == GATE.YEARS for years in row["missing"].values()))

    def test_every_alias_rejects_stage_and_scope_mutation(self):
        original = copy.deepcopy(self.args["evidence"])
        for i in range(10):
            for field, value in [("expected_stage", "MDE_LEGAL_INDICATOR"),
                                 ("expected_scope", "RREO_LINE33"),
                                 ("temporal_status", "PROVEN_COMPARABLE"),
                                 ("crosswalk_status", "PROVEN_BY_SAME_NAME")]:
                with self.subTest(alias=i, field=field):
                    self.args["evidence"] = copy.deepcopy(original)
                    self.args["evidence"]["financial_inputs"][i][field] = value
                    with self.assertRaises(ValueError): self.run_gate()

    def test_cannot_shrink_any_required_dimension_or_year(self):
        original = copy.deepcopy(self.args["contract"])
        for field in ["required_dimensions", "historical_years", "aliases"]:
            for i in range(len(original[field])):
                with self.subTest(field=field, index=i):
                    self.args["contract"] = copy.deepcopy(original)
                    self.args["contract"][field].pop(i)
                    with self.assertRaises(ValueError): self.run_gate()

    def test_period_boundary_cannot_be_rewritten(self):
        self.args["evidence"]["temporal_claims"][0]["value"]["period"] = 6
        with self.assertRaises(ValueError): self.run_gate()

    def test_consistent_evidence_contract_fabrication_still_rejected(self):
        claim = copy.deepcopy(self.args["evidence"]["temporal_claims"][1])
        claim.update(id="SAME_V1_PROVES_UNIT", dimension="unit", value="BRL_1")
        self.args["evidence"]["temporal_claims"].append(claim)
        self.args["contract"]["reviewed_temporal_claims"].append(claim)
        with self.assertRaisesRegex(ValueError, "unreviewed temporal"): self.run_gate()

    def test_dictionary_unit_and_description_mutations_fail_integrity(self):
        for section, field, value in [("dictionary", "unit_explicit", True),
                                      ("olinda", "effective_year_range_stated", True),
                                      ("installer_catalog", "complete_semantic_changelog", True),
                                      ("metadata_catalog", "package_contents_proven_by_listing", True)]:
            with self.subTest(field=field):
                self.setUp()
                self.args["support"][section][field] = value
                with self.assertRaisesRegex(ValueError, "support integrity"): self.run_gate()

    def test_each_metric_rejects_promotion_from_partial_input(self):
        for i in range(6):
            with self.subTest(metric=i):
                self.setUp()
                self.args["evidence"]["metrics"][i]["status"] = "PROVEN_COMPARABLE"
                with self.assertRaises(ValueError): self.run_gate()

    def test_source_url_or_hash_tampering_rejected(self):
        for field, value in [("official_url", "https://third-party.example/siope"), ("raw_sha256", "0" * 64)]:
            with self.subTest(field=field):
                self.setUp()
                self.args["support"]["sources"][0][field] = value
                with self.assertRaises(ValueError): self.run_gate()

    def test_three_propositions_cannot_be_hidden(self):
        for i in range(3):
            with self.subTest(gap=i):
                self.setUp()
                self.args["evidence"]["gaps"][i]["years"].remove(2020)
                with self.assertRaises(ValueError): self.run_gate()

    def test_no_guard_authorization_can_be_promoted(self):
        for field, original in GATE.PRESERVED.items():
            with self.subTest(field=field):
                self.setUp()
                value = True if original is False else "PROMOTED"
                self.args["evidence"]["preserved_state"][field] = value
                self.args["contract"]["preserved_state"][field] = value
                with self.assertRaises(ValueError): self.run_gate()

    def test_unrelated_change_is_not_target_break(self):
        self.args["evidence"]["positive_target_breaks"] = [{"source_id": "NOTES_2017", "positive_semantic_break": True}]
        with self.assertRaises(ValueError): self.run_gate()

    def test_required_document_cannot_be_reported_as_acquired(self):
        self.args["evidence"]["minimum_closing_evidence"]["artifact_status"] = "ACQUIRED"
        with self.assertRaises(ValueError): self.run_gate()

    def test_summary_cannot_contradict_derived_coverage(self):
        for field, value in [("financial_inputs_partial", 9), ("financial_metrics_partial", 5),
                             ("positive_semantic_break_proven", True)]:
            with self.subTest(field=field):
                self.setUp()
                self.args["evidence"]["decision"][field] = value
                with self.assertRaises(ValueError): self.run_gate()


class TemporalCoverageTests(unittest.TestCase):
    """Synthetic proof fixtures exercise the evaluator, not acquisition approval."""
    def claims(self):
        return [{"id": f"{a}-{d}", "source_id": "SYNTHETIC_REVIEWED_CONTRACT",
                 "aliases": [a], "years": [2016, 2017], "dimension": d,
                 "value": {"canonical_semantic_value": d}}
                for a in ["A", "B"] for d in GATE.DIMENSIONS]

    def run_assessment(self, claims, breaks=None):
        return GATE.assess(["A", "B"], [2016, 2017], GATE.DIMENSIONS,
                           claims, breaks or [], {"M1": ["A"], "M2": ["A", "B"], "M3": ["B"]})

    def test_complete_positive_coverage_required_for_both_inputs(self):
        result = self.run_assessment(self.claims())
        self.assertEqual(set(result["metrics"].values()), {"PROVEN_COMPARABLE"})
        claims = self.claims()
        next(c for c in claims if c["id"] == "B-unit")["years"] = [2017]
        result = self.run_assessment(claims)
        self.assertEqual(result["inputs"]["B"]["missing"], {"unit": [2016]})
        self.assertEqual(result["metrics"], {"M1": "PROVEN_COMPARABLE", "M2": "PARTIAL", "M3": "PARTIAL"})

    def test_documented_break_only_propagates_to_dependent_metrics(self):
        breaks = [{"source_id": "SYNTHETIC_OFFICIAL_CHANGE", "aliases": ["B"],
                   "years": [2017], "positive_semantic_break": True}]
        result = self.run_assessment(self.claims(), breaks)
        self.assertEqual(result["metrics"], {"M1": "PROVEN_COMPARABLE", "M2": "NOT_COMPARABLE", "M3": "NOT_COMPARABLE"})

    def test_absence_of_change_is_not_positive_break_evidence(self):
        with self.assertRaises(ValueError):
            self.run_assessment(self.claims(), [{"source_id": "NO_CHANGE_FOUND", "aliases": ["B"], "years": [2017], "positive_semantic_break": False}])

    def test_complete_presence_does_not_hide_changed_units(self):
        claims = self.claims()
        next(c for c in claims if c["id"] == "B-unit")["years"] = [2016]
        claims.append({"id": "B-unit-new", "source_id": "SYNTHETIC", "aliases": ["B"], "years": [2017], "dimension": "unit", "value": "THOUSANDS"})
        with self.assertRaisesRegex(ValueError, "differ across years"): self.run_assessment(claims)

    def test_unknown_years_duplicate_claims_and_conflicting_claims_fail(self):
        claims = self.claims()
        for mutation in ["year", "duplicate", "conflict"]:
            with self.subTest(mutation=mutation):
                mutated = copy.deepcopy(claims)
                if mutation == "year": mutated[0]["years"] = [2026]
                else:
                    new = copy.deepcopy(mutated[0])
                    if mutation == "conflict": new.update(id="conflict", value="DIFFERENT_SCOPE")
                    mutated.append(new)
                with self.assertRaises(ValueError): self.run_assessment(mutated)


if __name__ == "__main__":
    unittest.main()

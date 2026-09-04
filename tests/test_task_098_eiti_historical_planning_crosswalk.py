from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from robo_dados_publicos.research.eiti_historical_planning import (
    EitiHistoricalPlanningStop,
    load_and_validate_historical_planning_crosswalk,
    validate_historical_planning_crosswalk,
)


ROOT = Path(__file__).resolve().parents[1]
CROSSWALK = ROOT / "config/eiti_historical_planning_crosswalk.v1.json"
TASK055A = ROOT / "docs/evidence/TASK_055A_F01_EITI_TERMINOLOGY_ONTOLOGY_0.8.0.json"
TASK096 = ROOT / "docs/evidence/TASK_096_EITI_LIMEIRA_OFFLINE_CROSSWALK_0.8.0.json"
TASK107 = ROOT / "docs/evidence/TASK_107_LIVE_RESULT_0.8.0.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TestTask098EitiHistoricalPlanningCrosswalk(unittest.TestCase):
    def setUp(self) -> None:
        self.crosswalk = load(CROSSWALK)
        self.task055a = load(TASK055A)
        self.task096 = load(TASK096)
        self.task107 = load(TASK107)

    def validate(self, data=None, *, task107=None):
        return validate_historical_planning_crosswalk(
            data or self.crosswalk,
            task055a=self.task055a,
            task096=self.task096,
            task107=task107 or self.task107,
        )

    def test_canonical_crosswalk_ingests_task107_without_new_reads(self):
        result = load_and_validate_historical_planning_crosswalk(
            CROSSWALK,
            task055a_path=TASK055A,
            task096_path=TASK096,
            task107_path=TASK107,
        )
        self.assertEqual(
            "PASS_TASK108_EITI_HISTORICAL_PLANNING_PRIMARY_EVIDENCE_INGESTED",
            result["status"],
        )
        self.assertEqual(1, result["historical_candidate_periods"])
        self.assertEqual(2, result["primary_proven_periods"])
        self.assertEqual(1, result["historical_primary_gaps_remaining"])
        self.assertEqual("CANDIDATE", result["three_ppa_continuity_status"])
        self.assertEqual("UNKNOWN", result["three_ppa_budgetary_persistence_status"])
        self.assertTrue(result["task096_persistence_preserved"])
        self.assertEqual(0, result["new_source_reads"])
        self.assertEqual(0, result["remote_effects"])

    def test_2018_alias_cannot_be_promoted_from_empty_pdf_text(self):
        data = copy.deepcopy(self.crosswalk)
        data["periods"][0]["planning_signal_status"] = "PROVEN"
        with self.assertRaisesRegex(EitiHistoricalPlanningStop, "2018-2021_PLANNING_STATUS"):
            self.validate(data)

    def test_2022_primary_planning_signal_is_proven_but_policy_link_is_only_candidate(self):
        prior = self.crosswalk["periods"][1]
        self.assertEqual("PROVEN", prior["planning_signal_status"])
        self.assertEqual("CANDIDATE", prior["policy_link_status"])
        self.assertEqual("UNKNOWN", prior["financial_identity_status"])
        self.assertEqual(
            "8e10123b07d83e9a9928fd2444318f595a7560eac2bc06c920761ca7893778f7",
            prior["primary_source_sha256"],
        )
        self.assertEqual(23, prior["preferred_locator"]["page"])

    def test_2022_crosswalk_cannot_change_task107_source_hash(self):
        data = copy.deepcopy(self.crosswalk)
        data["periods"][1]["primary_source_sha256"] = "0" * 64
        with self.assertRaisesRegex(EitiHistoricalPlanningStop, "2022_CROSSWALK_SOURCE_SHA"):
            self.validate(data)

    def test_task107_canonical_hash_is_pinned_and_recomputed(self):
        task107 = copy.deepcopy(self.task107)
        task107["period_results"][1]["source_bytes"] += 1
        with self.assertRaisesRegex(EitiHistoricalPlanningStop, "TASK107_CANONICAL_SHA_MISMATCH"):
            self.validate(task107=task107)

        task107 = copy.deepcopy(self.task107)
        task107["result_canonical_sha256"] = "0" * 64
        with self.assertRaisesRegex(EitiHistoricalPlanningStop, "TASK107_PINNED_CANONICAL_SHA"):
            self.validate(task107=task107)

    def test_missing_task107_input_fails_closed_with_stable_error(self):
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "missing-task107.json"
            with self.assertRaisesRegex(EitiHistoricalPlanningStop, "REQUIRED_INPUT_MISSING"):
                load_and_validate_historical_planning_crosswalk(
                    CROSSWALK,
                    task055a_path=TASK055A,
                    task096_path=TASK096,
                    task107_path=missing,
                )

    def test_2022_primary_status_requires_matching_task107_primary_evidence(self):
        task107 = copy.deepcopy(self.task107)
        period = next(item for item in task107["period_results"] if item["period"] == "2022-2025")
        period["status"] = "CANDIDATE"
        with self.assertRaisesRegex(EitiHistoricalPlanningStop, "2022_PRIMARY_MATCH"):
            self.validate(task107=task107)

    def test_historical_planning_signal_cannot_become_financial_identity(self):
        data = copy.deepcopy(self.crosswalk)
        data["periods"][1]["financial_identity_status"] = "CORROBORATED"
        with self.assertRaisesRegex(EitiHistoricalPlanningStop, "2022-2025_FINANCIAL_IDENTITY"):
            self.validate(data)

    def test_three_ppa_continuity_cannot_be_overpromoted(self):
        data = copy.deepcopy(self.crosswalk)
        data["longitudinal_assessment"]["three_ppa_period_policy_continuity"] = "CORROBORATED"
        with self.assertRaisesRegex(EitiHistoricalPlanningStop, "THREE_PPA_CONTINUITY_OVERCLAIM"):
            self.validate(data)

    def test_existing_task096_persistence_is_not_downgraded_or_redefined(self):
        data = copy.deepcopy(self.crosswalk)
        data["longitudinal_assessment"]["existing_task096_normative_planning_persistence"] = "CANDIDATE"
        with self.assertRaisesRegex(EitiHistoricalPlanningStop, "TASK096_PERSISTENCE_CHANGED"):
            self.validate(data)

    def test_2026_2029_primary_locator_must_remain_typed_and_hashed(self):
        data = copy.deepcopy(self.crosswalk)
        data["periods"][2]["preferred_locator"]["coordinate_system"] = "LEGACY_UNTYPED_PAGE"
        with self.assertRaises(Exception):
            self.validate(data)

    def test_missing_historical_alias_from_task055a_fails_closed(self):
        task055a = copy.deepcopy(self.task055a)
        task055a["ontology"]["B_LOCAL_PLANNING_AND_NORMATIVE_ALIASES"].remove(
            "escolas com programas em tempo integral"
        )
        with self.assertRaisesRegex(EitiHistoricalPlanningStop, "2018-2021_SIGNAL_NOT_IN_TASK055A"):
            validate_historical_planning_crosswalk(
                self.crosswalk,
                task055a=task055a,
                task096=self.task096,
                task107=self.task107,
            )

    def test_only_2018_acquisition_gap_remains_and_requirements_cannot_be_weakened(self):
        self.assertEqual(["2018-2021"], [item["period"] for item in self.crosswalk["acquisition_gaps"]])
        data = copy.deepcopy(self.crosswalk)
        data["acquisition_gaps"][0]["required_before_promotion"].remove(
            "DIRECT_TEXT_OR_VISUAL_EVIDENCE"
        )
        with self.assertRaisesRegex(EitiHistoricalPlanningStop, "2018-2021_GAP_REQUIREMENTS"):
            self.validate(data)

    def test_remote_effect_enablement_fails_closed(self):
        data = copy.deepcopy(self.crosswalk)
        data["remote_effects"]["drive_read"] = True
        with self.assertRaisesRegex(EitiHistoricalPlanningStop, "REMOTE_EFFECT"):
            self.validate(data)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import copy
import json
from pathlib import Path
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


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TestTask098EitiHistoricalPlanningCrosswalk(unittest.TestCase):
    def setUp(self) -> None:
        self.crosswalk = load(CROSSWALK)
        self.task055a = load(TASK055A)
        self.task096 = load(TASK096)

    def test_canonical_crosswalk_passes_without_new_reads(self):
        result = load_and_validate_historical_planning_crosswalk(
            CROSSWALK,
            task055a_path=TASK055A,
            task096_path=TASK096,
        )
        self.assertEqual(
            "PASS_TASK098_EITI_HISTORICAL_PLANNING_COVERAGE_OFFLINE",
            result["status"],
        )
        self.assertEqual(2, result["historical_candidate_periods"])
        self.assertEqual(1, result["primary_proven_periods"])
        self.assertEqual("CANDIDATE", result["three_ppa_continuity_status"])
        self.assertEqual("UNKNOWN", result["three_ppa_budgetary_persistence_status"])
        self.assertTrue(result["task096_persistence_preserved"])
        self.assertEqual(0, result["new_source_reads"])
        self.assertEqual(0, result["remote_effects"])

    def test_task055a_alias_cannot_be_promoted_to_proven_primary_fact(self):
        data = copy.deepcopy(self.crosswalk)
        data["periods"][0]["planning_signal_status"] = "PROVEN"
        with self.assertRaisesRegex(
            EitiHistoricalPlanningStop,
            "2018-2021_PLANNING_STATUS",
        ):
            validate_historical_planning_crosswalk(
                data,
                task055a=self.task055a,
                task096=self.task096,
            )

    def test_task055a_alias_cannot_gain_invented_primary_provenance(self):
        data = copy.deepcopy(self.crosswalk)
        data["periods"][1]["primary_source_hash_versioned"] = True
        with self.assertRaisesRegex(
            EitiHistoricalPlanningStop,
            "2022-2025_PRIMARY_SOURCE_HASH_VERSIONED_OVERCLAIM",
        ):
            validate_historical_planning_crosswalk(
                data,
                task055a=self.task055a,
                task096=self.task096,
            )

    def test_historical_alias_cannot_become_financial_identity(self):
        data = copy.deepcopy(self.crosswalk)
        data["periods"][1]["financial_identity_status"] = "CORROBORATED"
        with self.assertRaisesRegex(
            EitiHistoricalPlanningStop,
            "2022-2025_FINANCIAL_IDENTITY",
        ):
            validate_historical_planning_crosswalk(
                data,
                task055a=self.task055a,
                task096=self.task096,
            )

    def test_three_ppa_continuity_cannot_be_overpromoted(self):
        data = copy.deepcopy(self.crosswalk)
        data["longitudinal_assessment"]["three_ppa_period_policy_continuity"] = "CORROBORATED"
        with self.assertRaisesRegex(
            EitiHistoricalPlanningStop,
            "THREE_PPA_CONTINUITY_OVERCLAIM",
        ):
            validate_historical_planning_crosswalk(
                data,
                task055a=self.task055a,
                task096=self.task096,
            )

    def test_existing_task096_persistence_is_not_downgraded_or_redefined(self):
        data = copy.deepcopy(self.crosswalk)
        data["longitudinal_assessment"]["existing_task096_normative_planning_persistence"] = "CANDIDATE"
        with self.assertRaisesRegex(
            EitiHistoricalPlanningStop,
            "TASK096_PERSISTENCE_CHANGED",
        ):
            validate_historical_planning_crosswalk(
                data,
                task055a=self.task055a,
                task096=self.task096,
            )

    def test_2026_2029_primary_locator_must_remain_typed_and_hashed(self):
        data = copy.deepcopy(self.crosswalk)
        data["periods"][2]["preferred_locator"]["coordinate_system"] = "LEGACY_UNTYPED_PAGE"
        with self.assertRaises(Exception):
            validate_historical_planning_crosswalk(
                data,
                task055a=self.task055a,
                task096=self.task096,
            )

    def test_missing_historical_alias_from_task055a_fails_closed(self):
        task055a = copy.deepcopy(self.task055a)
        task055a["ontology"]["B_LOCAL_PLANNING_AND_NORMATIVE_ALIASES"].remove(
            "escolas com programas em tempo integral"
        )
        with self.assertRaisesRegex(
            EitiHistoricalPlanningStop,
            "2018-2021_SIGNAL_NOT_IN_TASK055A",
        ):
            validate_historical_planning_crosswalk(
                self.crosswalk,
                task055a=task055a,
                task096=self.task096,
            )

    def test_acquisition_gap_requirements_cannot_be_weakened(self):
        data = copy.deepcopy(self.crosswalk)
        data["acquisition_gaps"][0]["required_before_promotion"].remove(
            "DIRECT_TEXT_OR_VISUAL_EVIDENCE"
        )
        with self.assertRaisesRegex(
            EitiHistoricalPlanningStop,
            "2018-2021_GAP_REQUIREMENTS",
        ):
            validate_historical_planning_crosswalk(
                data,
                task055a=self.task055a,
                task096=self.task096,
            )

    def test_remote_effect_enablement_fails_closed(self):
        data = copy.deepcopy(self.crosswalk)
        data["remote_effects"]["drive_read"] = True
        with self.assertRaisesRegex(EitiHistoricalPlanningStop, "REMOTE_EFFECT"):
            validate_historical_planning_crosswalk(
                data,
                task055a=self.task055a,
                task096=self.task096,
            )


if __name__ == "__main__":
    unittest.main()

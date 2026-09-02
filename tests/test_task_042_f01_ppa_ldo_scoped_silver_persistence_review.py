from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.f01_ppa_ldo_scoped_silver_persistence_review import (
    Task042ReviewError,
    validate_task042_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
E42 = ROOT / "docs/evidence/TASK_042_F01_PPA_LDO_SCOPED_SILVER_CREATE_ONLY_READBACK_0.8.0.json"
E41 = ROOT / "docs/evidence/TASK_041_F01_JOM_NATIVE_PPA_LDO_READINESS_REVIEW_0.8.0.json"


class Task042PpaLdoScopedSilverPersistenceReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.e42 = json.loads(E42.read_text(encoding="utf-8"))
        self.e41 = json.loads(E41.read_text(encoding="utf-8"))

    def test_canonical_evidence_passes(self) -> None:
        result = validate_task042_evidence(self.e42, self.e41)
        self.assertEqual(result["status"], "PASS_TASK042_PPA_LDO_SCOPED_SILVER_PERSISTENCE_REVIEW")
        self.assertEqual(result["scoped_silver_families"], ["LOA", "PPA", "LDO"])
        self.assertFalse(result["gold_authorized"])

    def test_wrong_authorization_sha_stops(self) -> None:
        e = copy.deepcopy(self.e42)
        e["authorization"]["authorized_against_sha"] = "0" * 40
        with self.assertRaises(Task042ReviewError):
            validate_task042_evidence(e, self.e41)

    def test_blanket_authorization_stops(self) -> None:
        e = copy.deepcopy(self.e42)
        e["authorization"]["future_blanket_authorizations_accepted"] = True
        with self.assertRaises(Task042ReviewError):
            validate_task042_evidence(e, self.e41)

    def test_collision_stops(self) -> None:
        e = copy.deepcopy(self.e42)
        e["execution"]["target_name_collisions"] = 1
        with self.assertRaises(Task042ReviewError):
            validate_task042_evidence(e, self.e41)

    def test_ppa_hash_drift_stops(self) -> None:
        e = copy.deepcopy(self.e42)
        e["ppa"]["sha256"] = "0" * 64
        with self.assertRaises(Task042ReviewError):
            validate_task042_evidence(e, self.e41)

    def test_ldo_readback_drift_stops(self) -> None:
        e = copy.deepcopy(self.e42)
        e["ldo"]["readback"]["bytes"] += 1
        with self.assertRaises(Task042ReviewError):
            validate_task042_evidence(e, self.e41)

    def test_extra_write_stops(self) -> None:
        e = copy.deepcopy(self.e42)
        e["effects"]["drive_creates"] = 3
        with self.assertRaises(Task042ReviewError):
            validate_task042_evidence(e, self.e41)

    def test_gold_promotion_stops(self) -> None:
        e = copy.deepcopy(self.e42)
        e["promotion"]["gold"] = True
        with self.assertRaises(Task042ReviewError):
            validate_task042_evidence(e, self.e41)

    def test_task041_candidate_hash_drift_stops(self) -> None:
        t = copy.deepcopy(self.e41)
        t["ppa_candidate_sha256"] = "f" * 64
        with self.assertRaises(Task042ReviewError):
            validate_task042_evidence(self.e42, t)


if __name__ == "__main__":
    unittest.main()

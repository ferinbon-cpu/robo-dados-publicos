import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.f01_loa_scoped_silver_v2_persistence_review import (
    Task050ReviewError,
    validate_task050_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
E50 = ROOT / "docs/evidence/TASK_050_F01_LOA_SCOPED_SILVER_V2_CREATE_ONLY_READBACK_0.8.0.json"
E48 = ROOT / "docs/evidence/TASK_048_F01_LOA_SCOPED_SILVER_V2_CANDIDATE_REVIEW_0.8.0.json"
E40 = ROOT / "docs/evidence/TASK_040_LOA_SCOPED_SILVER_CREATE_ONLY_READBACK_0.8.0.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Task050PersistenceReviewTests(unittest.TestCase):
    def test_evidence_passes(self):
        result = validate_task050_evidence(load(E50), load(E48), load(E40))
        self.assertEqual(result["status"], "PASS_TASK050_LOA_SCOPED_SILVER_V2_PERSISTENCE_REVIEW")
        self.assertTrue(result["readback_verified"])
        self.assertFalse(result["gold"])

    def test_fail_closed_if_gold_enabled(self):
        evidence = load(E50)
        evidence["promotion"]["gold"] = True
        with self.assertRaises(Task050ReviewError):
            validate_task050_evidence(evidence, load(E48), load(E40))

    def test_fail_closed_if_hash_changes(self):
        evidence = load(E50)
        evidence["loa"]["sha256"] = "0" * 64
        with self.assertRaises(Task050ReviewError):
            validate_task050_evidence(evidence, load(E48), load(E40))


if __name__ == "__main__":
    unittest.main()

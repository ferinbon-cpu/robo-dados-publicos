from __future__ import annotations

import json
from pathlib import Path
import unittest

from robo_dados_publicos.product.siope_historical_corrective_r3_publication import (
    CorrectivePublicationError,
    OWNER_AUTHORIZATION_PATH,
    validate_owner_authorization,
)


ROOT = Path(__file__).resolve().parents[1]
CLOSURE_PATH = ROOT / "docs/evidence/TASK_015_M8_R3_PUBLICATION_CLOSURE_0.8.0.json"
INCORRECT_SUPERSEDED_TRANSCRIPTION_STATUS = (
    "PASS_M8_SIOPE_HISTORICAL_CORRECTIVE_R3_PUBLICATION_GATE"
)
INCORRECT_SUPERSEDED_TRANSCRIPTION_MATRIX_SHA256 = (
    "7a847b5aacdfff91d26cfe76da9f973f760f5736fcfe841c7035e744c32960c5"
)


class Task015PostPublicationClosureTests(unittest.TestCase):
    def test_checked_in_authorization_is_consumed_and_cannot_execute_again(self):
        authorization = json.loads((ROOT / OWNER_AUTHORIZATION_PATH).read_text(encoding="utf-8"))
        self.assertEqual(authorization["status"], "CONSUMED_SUCCESS")
        self.assertTrue(authorization["consumed"])
        self.assertEqual(authorization["consumed_by_run_id"], 33339989250)
        self.assertEqual(
            authorization["consumed_execution_sha"],
            "8a89eb62f5753e52cb10c33da5c64ebe19e82f48",
        )
        self.assertFalse(authorization["further_execution_authorized"])

        with self.assertRaisesRegex(CorrectivePublicationError, "OWNER_AUTHORIZATION_INVALID"):
            validate_owner_authorization(root=ROOT)

    def test_consumed_authorization_preserves_every_prohibition(self):
        authorization = json.loads((ROOT / OWNER_AUTHORIZATION_PATH).read_text(encoding="utf-8"))
        for key in (
            "retry_allowed",
            "schedule_allowed",
            "recurrence_allowed",
            "overwrite_allowed",
            "replace_allowed",
            "delete_allowed",
            "future_batch_execution_authorized",
        ):
            with self.subTest(key=key):
                self.assertFalse(authorization[key])

    def test_closure_pins_success_without_expanding_scope_or_release(self):
        closure = json.loads(CLOSURE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(closure["schema"], "TASK_015_M8_R3_PUBLICATION_CLOSURE_V1")
        self.assertEqual(closure["status"], "CLOSED_SUCCESS_R3_AUTHORIZATION_CONSUMED")
        self.assertEqual(closure["execution"]["run_id"], 33339989250)
        self.assertEqual(closure["execution"]["github_run_attempt"], 1)
        self.assertEqual(closure["execution"]["conclusion"], "success")
        self.assertEqual(
            closure["publication_result"]["status"],
            "PASS_M8_SIOPE_HISTORICAL_CORRECTIVE_PUBLICATION_GATE",
        )
        self.assertEqual(
            closure["publication_result"]["canonical_matrix_sha256"],
            "0247be1b30d1f3ba9ba8064569cd934811a5fc95535417c9b1c70f67f911de55",
        )
        self.assertEqual(closure["publication_result"]["created_count"], 3)
        self.assertEqual(
            closure["publication_result"]["source_artifact_zip_sha256"],
            "213693b37e8a2123d1d4df4b4dec0495a5ca9536cb51b23f0549e94da72d080e",
        )
        self.assertEqual(closure["publication_scope"], "SIOPE_HISTORICAL_2016_2024")
        self.assertFalse(closure["include_2025"])
        self.assertEqual(closure["release_status"], "CANDIDATE")
        self.assertFalse(closure["release_promotion_performed"])
        self.assertEqual(closure["remote_mutations_performed_by_task_015"], 0)
        self.assertFalse(closure["live_execution_performed_by_task_015"])

    def test_closure_rejects_superseded_transcription_values(self):
        closure = json.loads(CLOSURE_PATH.read_text(encoding="utf-8"))
        result = closure["publication_result"]
        self.assertNotEqual(result["status"], INCORRECT_SUPERSEDED_TRANSCRIPTION_STATUS)
        self.assertNotEqual(
            result["canonical_matrix_sha256"],
            INCORRECT_SUPERSEDED_TRANSCRIPTION_MATRIX_SHA256,
        )
        self.assertEqual(
            closure["evidence_correction"],
            {
                "reason": "TASK015_INITIAL_CLOSURE_TRANSCRIPTION_ERROR",
                "supersedes_main_sha": "948af92328bde869c0939bd02a30383e1ee2d973",
                "source": "run_33339989250_artifact_9740240114_result.json",
                "remote_mutations": 0,
            },
        )

    def test_closure_forbids_reexecution_and_preserves_r2_without_mutation(self):
        closure = json.loads(CLOSURE_PATH.read_text(encoding="utf-8"))
        lifecycle = closure["authorization_lifecycle"]
        for key in (
            "r3_authorization_remaining",
            "r3_retry_authorized",
            "r3_second_execution_authorized",
            "r3_schedule_authorized",
            "r3_recurrence_authorized",
        ):
            with self.subTest(key=key):
                self.assertFalse(lifecycle[key])
        r2 = closure["r2_historical_treatment"]
        self.assertEqual(r2["status"], "RETAINED_FAILED_PARTIAL_HISTORICAL_EVIDENCE")
        for key in ("successful_publication_product", "repaired", "deleted", "overwritten", "retried"):
            with self.subTest(key=key):
                self.assertFalse(r2[key])
        self.assertEqual(closure["remote_mutations_performed_by_task_015"], 0)
        self.assertFalse(closure["live_execution_performed_by_task_015"])


if __name__ == "__main__":
    unittest.main()

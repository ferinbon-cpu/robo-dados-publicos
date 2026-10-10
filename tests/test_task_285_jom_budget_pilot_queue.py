"""TASK285 synthetic regression tests; all execution is local and side-effect free."""

from __future__ import annotations

import unittest

from robo_dados_publicos.research.task285_jom_budget_pilot_queue import (
    PINNED_TARGETS,
    Task285Stop,
    build_pilot_queue,
)


class TestTask285JomBudgetPilotQueue(unittest.TestCase):
    def setUp(self):
        self.source = PINNED_TARGETS.read_text(encoding="utf-8")

    def test_exact_official_five_document_queue(self):
        result = build_pilot_queue()
        self.assertEqual(result["status"], "READY_FOR_SEPARATE_T1_GATE")
        self.assertEqual(result["pinned_document_count"], 87)
        self.assertEqual(result["pilot_document_count"], 5)
        self.assertEqual(
            [d["edition"] for d in result["documents"]],
            [7211, 7208, 7209, 7210, 7212],
        )
        for doc in result["documents"]:
            self.assertTrue(doc["document_url"].startswith(
                "https://ecrie.com.br/Sistema/Conteudos/DiarioOficial/upload/"
            ))
            self.assertEqual(doc["authorization_state"], "NOT_AUTHORIZED_TO_DOWNLOAD")
            self.assertFalse(doc["pdf_content_inspected"])
            self.assertFalse(doc["budget_line_extracted"])
        self.assertTrue(result["documents"][0]["budget_act_confirmed_by_index"])
        self.assertEqual(result["documents"][0]["target_annexes"], ["I", "II"])
        self.assertTrue(all(
            not d["budget_act_confirmed_by_index"]
            for d in result["documents"][1:]
        ))

    def test_no_download_or_publication_capability_is_emitted(self):
        result = build_pilot_queue()
        for key in (
            "network_request_count",
            "pdf_download_count",
            "drive_write_count",
            "publication_count",
            "official_urls_guessed",
        ):
            self.assertEqual(result[key], 0)
        self.assertFalse(result["live_execution_authorized"])
        self.assertFalse(result["retries_authorized"])
        self.assertFalse(result["recurrence_authorized"])
        self.assertFalse(result["absence_inference_allowed"])
        self.assertTrue(result["download_gate_required"])
        self.assertTrue(result["custody_gate_required"])

    def test_missing_row_fails_before_queue(self):
        lines = self.source.splitlines()
        with self.assertRaisesRegex(Task285Stop, "STOP_FIXTURE_ROW_COUNT"):
            build_pilot_queue("\n".join(lines[:-1]) + "\n")

    def test_untrusted_host_fails(self):
        self.assertIn("https://ecrie.com.br/", self.source)
        changed = self.source.replace(
            "https://ecrie.com.br/", "https://example.org/", 1
        )
        with self.assertRaisesRegex(Task285Stop, "STOP_UNTRUSTED_PDF_ROUTE"):
            build_pilot_queue(changed)

    def test_duplicate_edition_fails(self):
        lines = self.source.splitlines()
        entries = [line.split(",") for line in lines[1:]]
        entries[1][0] = entries[0][0]
        changed = lines[0] + "\n" + "\n".join(",".join(r) for r in entries) + "\n"
        with self.assertRaisesRegex(Task285Stop, "STOP_DUPLICATE_EDITION"):
            build_pilot_queue(changed)

    def test_identity_mismatch_fails(self):
        self.assertIn("LIMEIRA_JO_07211", self.source)
        changed = self.source.replace("LIMEIRA_JO_07211", "LIMEIRA_JO_09999", 1)
        with self.assertRaisesRegex(Task285Stop, "STOP_SOURCE_ID"):
            build_pilot_queue(changed)

    def test_missing_pilot_edition_fails(self):
        self.assertIn("7211,2026-03-28,LIMEIRA_JO_07211,", self.source)
        changed = self.source.replace(
            "7211,2026-03-28,LIMEIRA_JO_07211,",
            "7999,2026-03-28,LIMEIRA_JO_07999,",
            1,
        )
        with self.assertRaisesRegex(Task285Stop, "STOP_PILOT_EDITION_MISSING"):
            build_pilot_queue(changed)


if __name__ == "__main__":
    unittest.main()

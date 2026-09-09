from __future__ import annotations

import unittest

from robo_dados_publicos.analytics.task217_jom_school_identity_bridge import (
    build_alias_index,
    build_current_corpus_audit,
    classify_event_school_identity,
    load_config,
    load_school_roster,
)


class TestTask217JomSchoolIdentityBridge(unittest.TestCase):
    def test_contract_and_full_current_roster_validate(self):
        cfg = load_config()
        self.assertEqual(cfg["issue"], 680)
        roster = load_school_roster()
        self.assertEqual(len(roster), 69)
        self.assertEqual(len({row["school_code"] for row in roster}), 69)
        aliases = build_alias_index()
        self.assertEqual(len(aliases["aliases"]), 224)
        self.assertEqual(aliases["ambiguous"], {})

    def test_exact_rafael_name_resolves_and_infrastructure_is_separate_gate(self):
        got = classify_event_school_identity(
            {
                "event_id": "SYNTHETIC_TEST_ONLY",
                "edition": 9999,
                "publication_date": "2026-01-01",
                "page_number": 1,
                "source_sha256": "a" * 64,
                "object_text": "Reforma no CEIEF Rafael Affonso Leite.",
                "excerpt_redacted": None,
            }
        )
        self.assertEqual(got["school_identity_status"], "RESOLVED_EXACT_SCHOOL")
        self.assertEqual(got["resolved_school"]["school_code"], "35470600")
        self.assertEqual(got["resolved_school"]["school_name"], "CEIEF Rafael Affonso Leite")
        self.assertTrue(got["infrastructure_candidate"])
        self.assertIn("reforma", got["infrastructure_markers"])
        self.assertFalse(got["infrastructure_text_created_school_identity"])

    def test_stadium_homonym_does_not_create_school_identity(self):
        got = classify_event_school_identity(
            {
                "event_id": "SYNTHETIC_STADIUM",
                "edition": 9999,
                "publication_date": "2026-01-01",
                "page_number": 1,
                "source_sha256": "a" * 64,
                "object_text": "Manutenção das cadeiras do Estádio Major José Levy Sobrinho.",
                "excerpt_redacted": None,
            }
        )
        self.assertEqual(got["school_identity_status"], "NO_SCHOOL_REFERENCE")
        self.assertIsNone(got["resolved_school"])
        self.assertTrue(got["infrastructure_candidate"])
        self.assertFalse(got["bare_alias_created_school_identity"])

    def test_street_homonym_does_not_create_school_identity(self):
        got = classify_event_school_identity(
            {
                "event_id": "SYNTHETIC_STREET",
                "edition": 9999,
                "publication_date": "2026-01-01",
                "page_number": 1,
                "source_sha256": "a" * 64,
                "object_text": "Reforma de sala em imóvel localizado na Rua Dr. José Carvalho Ferreira, 509.",
                "excerpt_redacted": None,
            }
        )
        self.assertEqual(got["school_identity_status"], "NO_SCHOOL_REFERENCE")
        self.assertIsNone(got["resolved_school"])
        self.assertTrue(got["infrastructure_candidate"])

    def test_true_school_context_still_resolves_arlindo_de_salvo(self):
        got = classify_event_school_identity(
            {
                "event_id": "SYNTHETIC_ARLINDO",
                "edition": 7208,
                "publication_date": "2026-03-25",
                "page_number": 42,
                "source_sha256": "a" * 64,
                "object_text": "Contratação de empresa especializada para manutenção do reservatório de água do CEIEF Prof. Arlindo de Salvo.",
                "excerpt_redacted": None,
            }
        )
        self.assertEqual(got["school_identity_status"], "RESOLVED_EXACT_SCHOOL")
        self.assertEqual(got["resolved_school"]["school_code"], "35295061")
        self.assertTrue(got["infrastructure_candidate"])
        self.assertTrue(
            all(
                match["school_context_guard"] == "PASS_NEARBY_SCHOOL_ANCHOR"
                for match in got["resolved_school"]["matches"]
            )
        )

    def test_abstract_uses_of_infrastructure_words_are_not_physical_infrastructure(self):
        cases = [
            "Escola e ampliação do objeto investigatório.",
            "Escola e construção do conhecimento.",
            "Rede municipal e manutenção de registros pedagógicos.",
        ]
        for idx, text in enumerate(cases):
            got = classify_event_school_identity(
                {
                    "event_id": f"SYNTHETIC_ABSTRACT_{idx}",
                    "edition": 9999,
                    "publication_date": "2026-01-01",
                    "page_number": 1,
                    "source_sha256": "a" * 64,
                    "object_text": text,
                    "excerpt_redacted": None,
                }
            )
            self.assertFalse(got["infrastructure_candidate"], text)
            self.assertEqual(got["infrastructure_markers"], [], text)

    def test_true_physical_maintenance_remains_infrastructure(self):
        got = classify_event_school_identity(
            {
                "event_id": "SYNTHETIC_PHYSICAL",
                "edition": 9999,
                "publication_date": "2026-01-01",
                "page_number": 1,
                "source_sha256": "a" * 64,
                "object_text": "Manutenção do reservatório de água do CEIEF Prof. Arlindo de Salvo.",
                "excerpt_redacted": None,
            }
        )
        self.assertTrue(got["infrastructure_candidate"])
        self.assertIn("manutencao", got["infrastructure_markers"])
        self.assertEqual(got["resolved_school"]["school_code"], "35295061")

    def test_near_spelling_does_not_create_identity(self):
        got = classify_event_school_identity(
            {
                "event_id": "SYNTHETIC_TEST_ONLY",
                "edition": 9999,
                "publication_date": "2026-01-01",
                "page_number": 1,
                "source_sha256": "a" * 64,
                "object_text": "Reforma no CEIEF Rafael Afonso Leite.",
                "excerpt_redacted": None,
            }
        )
        self.assertEqual(got["school_identity_status"], "NO_SCHOOL_REFERENCE")
        self.assertIsNone(got["resolved_school"])
        self.assertTrue(got["infrastructure_candidate"])

    def test_generic_network_playground_is_never_assigned_to_a_school(self):
        got = classify_event_school_identity(
            {
                "event_id": "SYNTHETIC_TEST_ONLY",
                "edition": 9999,
                "publication_date": "2026-01-01",
                "page_number": 1,
                "source_sha256": "a" * 64,
                "object_text": "Aquisição de playground infantil destinado a unidades escolares da rede municipal.",
                "excerpt_redacted": None,
            }
        )
        self.assertEqual(got["school_identity_status"], "GENERIC_SCHOOL_REFERENCE")
        self.assertIsNone(got["resolved_school"])
        self.assertTrue(got["infrastructure_candidate"])
        self.assertIn("playground", got["infrastructure_markers"])

    def test_current_303_row_corpus_is_a_zero_exact_school_result_not_a_global_absence(self):
        got = build_current_corpus_audit()
        self.assertEqual(got["observed"]["exact_school_event_count"], 0)
        self.assertEqual(got["observed"]["ambiguous_school_event_count"], 0)
        self.assertEqual(got["observed"]["infrastructure_candidate_count"], 14)
        self.assertEqual(got["observed"]["exact_school_infrastructure_count"], 0)
        self.assertEqual(got["observed"]["generic_school_infrastructure_count"], 1)
        self.assertEqual(
            got["observed"]["generic_school_infrastructure_event_ids"],
            ["JOEV_84b4ca10af2609ca127a"],
        )
        self.assertEqual(
            got["promotion"]["status"],
            "BLOCKED_NO_EXACT_NAMED_SCHOOL_INFRASTRUCTURE_EVENT_IN_CURRENT_CORPUS",
        )
        self.assertEqual(got["promotion"]["contextual_paths_before"], 33)
        self.assertEqual(got["promotion"]["contextual_paths_after"], 33)
        self.assertFalse(got["guards"]["absence_beyond_current_corpus_inferred"])
        self.assertFalse(got["promotion"]["live_expansion_authorized_by_this_task"])

    def test_task_is_offline_and_does_not_reuse_consumed_live_authorization(self):
        got = build_current_corpus_audit()
        self.assertTrue(all(value is False for value in got["remote_effects"].values()))
        self.assertFalse(got["guards"]["task018_consumed_authorization_reused"])


if __name__ == "__main__":
    unittest.main()

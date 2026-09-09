from __future__ import annotations

import unittest

from robo_dados_publicos.research.task217b_jom_2026_school_infrastructure_expansion import (
    Task217BStop,
    adjudicate_event_rows,
    build_discovery_plan,
    load_config,
    month_windows,
    screen_page_text,
    validate_live_authorization,
    validate_offline_design,
)


def fake_month(month: int):
    day = "08" if month == 9 else "15"
    edition = 7400 + month
    return {
        "status": "PASS_DISCOVERY",
        "year": 2026,
        "month": month,
        "pages_fetched": 1,
        "count": 1,
        "editions": [
            {
                "edition": edition,
                "publication_date": f"2026-{month:02d}-{day}",
                "document_url": f"https://ecrie.com.br/Sistema/Conteudos/DiarioOficial/upload/fake_{edition}.pdf",
                "source_id": f"LIMEIRA_JO_{edition:05d}",
                "logical_key": f"limeira/jornal_oficial/edicao/{edition}",
            }
        ],
    }


class TestTask217BJom2026ExpansionDesign(unittest.TestCase):
    def test_design_is_offline_and_month_scope_is_exact(self):
        cfg = load_config()
        self.assertEqual(cfg["issue"], 680)
        self.assertEqual(cfg["scope"]["start_date"], "2026-01-01")
        self.assertEqual(cfg["scope"]["end_date"], "2026-09-08")
        self.assertEqual(len(month_windows()), 9)
        got = validate_offline_design()
        self.assertEqual(got["status"], "PASS")
        self.assertFalse(got["live_execution_authorized"])
        self.assertFalse(got["task018_authorization_reuse_allowed"])
        self.assertFalse(got["runtime_answerability_promotion_allowed"])
        self.assertFalse(got["network"])

    def test_complete_nine_month_discovery_plan_is_sanitized_and_download_free(self):
        got = build_discovery_plan([fake_month(month) for month in range(1, 10)])
        self.assertTrue(got["complete_scope"])
        self.assertEqual(got["scope"]["months_complete"], 9)
        self.assertEqual(got["total_index_pages"], 9)
        self.assertEqual(got["document_count"], 9)
        self.assertEqual(got["document_downloads_performed"], 0)
        self.assertFalse(got["network_performed_by_this_function"])

    def test_partial_or_out_of_scope_month_stops(self):
        reports = [fake_month(month) for month in range(1, 10)]
        reports[3]["status"] = "PARTIAL_DISCOVERY_PAGINATION_UNRESOLVED"
        with self.assertRaises(Task217BStop):
            build_discovery_plan(reports)

        reports = [fake_month(month) for month in range(1, 10)]
        reports[8]["editions"][0]["publication_date"] = "2026-09-09"
        with self.assertRaises(Task217BStop):
            build_discovery_plan(reports)

    def test_page_screening_finds_exact_school_or_generic_network_without_creating_identity(self):
        exact = screen_page_text("Reforma do CEIEF Rafael Affonso Leite com adequação predial.")
        self.assertTrue(exact["candidate_page"])
        self.assertIn("35470600", exact["exact_school_codes_present"])
        self.assertFalse(exact["page_screening_created_school_identity"])

        generic = screen_page_text("Aquisição de playground para unidades escolares da rede municipal.")
        self.assertTrue(generic["candidate_page"])
        self.assertEqual(generic["exact_school_codes_present"], [])
        self.assertIn("unidades escolares", generic["generic_school_markers"])
        self.assertFalse(generic["page_screening_created_school_identity"])

    def test_page_screening_rejects_abstract_infrastructure_word_uses(self):
        for text in (
            "Escola e ampliação do objeto investigatório.",
            "Escola e construção do conhecimento.",
            "Rede municipal e manutenção de registros.",
        ):
            got = screen_page_text(text)
            self.assertFalse(got["candidate_page"], text)
            self.assertEqual(got["infrastructure_markers"], [], text)

    def test_event_level_adjudication_can_resolve_exact_school_but_never_auto_promotes(self):
        got = adjudicate_event_rows(
            [
                {
                    "event_id": "SYNTHETIC_TEST_ONLY_EXACT",
                    "edition": 9991,
                    "publication_date": "2026-02-01",
                    "page_number": 3,
                    "source_sha256": "a" * 64,
                    "object_text": "Reforma do CEIEF Rafael Affonso Leite",
                    "excerpt_redacted": None,
                },
                {
                    "event_id": "SYNTHETIC_TEST_ONLY_GENERIC",
                    "edition": 9992,
                    "publication_date": "2026-02-02",
                    "page_number": 4,
                    "source_sha256": "b" * 64,
                    "object_text": "Aquisição de playground para unidades escolares da rede municipal",
                    "excerpt_redacted": None,
                },
            ]
        )
        self.assertEqual(got["resolved_exact_school_infrastructure_count"], 1)
        self.assertEqual(
            got["resolved_exact_school_infrastructure_events"][0]["resolved_school"]["school_code"],
            "35470600",
        )
        self.assertEqual(got["generic_unassigned_school_infrastructure_count"], 1)
        self.assertFalse(got["runtime_answerability_promotion"])
        self.assertTrue(got["canonization_required"])

    def test_live_authorization_rejects_task018_and_requires_exact_sha_contract(self):
        self.assertEqual(
            validate_live_authorization(
                {"task": "TASK_018", "task018_authorization_reused": True},
                expected_sha="abc",
            )["status"],
            "STOP_TASK018_AUTHORIZATION_REUSE",
        )
        cfg = load_config()
        auth = {
            "task": cfg["authorization"]["required_task"],
            "repository": "ferinbon-cpu/robo-dados-publicos",
            "branch": "main",
            "implementation_sha": "abc",
            "source": cfg["source"]["family"],
            "operation": cfg["authorization"]["required_operation"],
            "start_date": cfg["scope"]["start_date"],
            "end_date": cfg["scope"]["end_date"],
            "attempt_count": 1,
            "owner_authorized": True,
            "drive_write_authorized": False,
            "publication_authorized": False,
            "serving_authorized": False,
            "promotion_authorized": False,
            "recurrence_authorized": False,
            "schedule_authorized": False,
        }
        self.assertEqual(
            validate_live_authorization(auth, expected_sha="abc")["status"],
            "PASS_LIVE_AUTHORIZATION",
        )


if __name__ == "__main__":
    unittest.main()

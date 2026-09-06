import json
import unittest
from pathlib import Path

from robo_dados_publicos.journal.processing import parse_events_from_page, _EVENT_STARTS
from robo_dados_publicos.journal.semantic_layers import classify_event, validate_config


ROOT = Path(__file__).resolve().parents[1]
TAXONOMY = ROOT / "config/jornal_event_taxonomy.v2.json"


def parse(text):
    return parse_events_from_page(
        text,
        edition=9999,
        publication_date="2026-09-05",
        page_number=1,
        source_url="https://example.invalid/jom.pdf",
        source_sha256="a" * 64,
    )


class TestTask174BroadenJomEventTaxonomy(unittest.TestCase):
    def test_taxonomy_contract_contains_legacy_and_new_types(self):
        obj = json.loads(TAXONOMY.read_text(encoding="utf-8"))
        self.assertEqual(obj["schema"], "JORNAL_OFICIAL_EVENT_TAXONOMY_V2")
        self.assertEqual(len(obj["legacy_event_types"]), 11)
        self.assertEqual(len(obj["new_event_types"]), 10)
        parser_types = {name for name, _ in _EVENT_STARTS}
        self.assertTrue(set(obj["legacy_event_types"]) <= parser_types)
        self.assertTrue(set(obj["new_event_types"]) <= parser_types)
        self.assertTrue(obj["retification_rule"]["target_act_must_be_explicit"])
        self.assertFalse(obj["retification_rule"]["nearby_act_identity_inheritance"])

    def test_all_new_explicit_heading_types_parse(self):
        text = """CONSELHO MUNICIPAL DE EDUCAÇÃO
COMUNICADO CME Nº 12/2026
Calendário escolar e matrícula.
PARECER CME Nº 02/2026
Dispõe sobre organização da educação municipal.
INSTRUÇÃO NORMATIVA Nº 04/2026
Normatiza a atribuição de aulas.
DELIBERAÇÃO Nº 07/2026
Delibera sobre funcionamento escolar.
RETIFICAÇÃO DO EDITAL Nº 45/2026
Corrige exclusivamente o item 3 do edital.
TERMO DE COLABORAÇÃO Nº 15/2026
OBJETO: Atendimento educacional complementar.
TERMO DE FOMENTO Nº 16/2026
OBJETO: Projeto de inclusão escolar.
ACORDO DE COOPERAÇÃO Nº 17/2026
OBJETO: Cooperação para formação docente.
CRÉDITO ADICIONAL Nº 77/2026
Abre crédito adicional para manutenção de escolas.
AVISO DE MATRÍCULA
Escola municipal informa período de matrícula escolar.
"""
        events = parse(text)
        got = [e.event_type for e in events]
        self.assertEqual(
            got,
            [
                "COMUNICADO",
                "PARECER",
                "INSTRUCAO_NORMATIVA",
                "DELIBERACAO",
                "RETIFICACAO",
                "TERMO_COLABORACAO",
                "TERMO_FOMENTO",
                "ACORDO_COOPERACAO",
                "ATO_CREDITO_ORCAMENTARIO",
                "AVISO_OPERACAO_ESCOLAR",
            ],
        )

    def test_retification_requires_and_preserves_explicit_target(self):
        events = parse(
            """SECRETARIA MUNICIPAL DE EDUCAÇÃO
RETIFICAÇÃO DA PORTARIA Nº 123/2026
Onde se lê 10 de março, leia-se 11 de março.
"""
        )
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event.event_type, "RETIFICACAO")
        self.assertEqual(event.target_act_type, "PORTARIA")
        self.assertEqual(event.target_act_number, "123/2026")
        self.assertIsNone(event.act_number)

    def test_unscoped_retification_and_ordinary_prose_remain_unstructured(self):
        events = parse(
            """SECRETARIA MUNICIPAL DE EDUCAÇÃO
RETIFICAÇÃO
Corrige informação publicada anteriormente.
A Secretaria comunica aos interessados que haverá reunião.
Parecer técnico favorável foi juntado ao processo 123.
"""
        )
        self.assertEqual(events, [])

    def test_credit_act_is_authorization_not_payment(self):
        event = parse(
            """SECRETARIA MUNICIPAL DE FAZENDA
CRÉDITO ESPECIAL Nº 88/2026
Abre crédito especial no orçamento para reforma de escola municipal.
"""
        )[0].to_dict()
        sem = classify_event(event)
        self.assertEqual(event["event_type"], "ATO_CREDITO_ORCAMENTARIO")
        self.assertIn("BUDGET_AUTHORIZATION", sem["evidence_layers"])
        self.assertIn("AUTHORIZATION", sem["financial_stages"])
        self.assertNotIn("PAYMENT", sem["financial_stages"])
        self.assertFalse(sem["semantic_classification_proves_payment"])
        self.assertFalse(sem["semantic_classification_proves_financial_identity"])

    def test_school_operation_notice_gets_specific_topics(self):
        event = parse(
            """SECRETARIA MUNICIPAL DE EDUCAÇÃO
AVISO DE CALENDÁRIO ESCOLAR
Escola municipal informa calendário escolar, ano letivo e horário escolar.
"""
        )[0].to_dict()
        sem = classify_event(event)
        self.assertEqual(event["event_type"], "AVISO_OPERACAO_ESCOLAR")
        self.assertIn("EDUCATION", sem["policy_domains"])
        self.assertIn("SCHOOL_OR_SERVICE_OPERATION", sem["evidence_layers"])
        self.assertIn("SCHOOL_CALENDAR", sem["education_topics"])
        self.assertIn("HOURS_SHIFT", sem["education_topics"])
        self.assertFalse(sem["semantic_classification_proves_policy_identity"])

    def test_partnership_instruments_are_governance_not_procurement_by_type(self):
        event = parse(
            """SECRETARIA MUNICIPAL DE EDUCAÇÃO
TERMO DE FOMENTO Nº 16/2026
OBJETO: Projeto educacional com organização da sociedade civil.
"""
        )[0].to_dict()
        sem = classify_event(event)
        self.assertIn("GOVERNANCE", sem["evidence_layers"])
        self.assertNotIn("PROCUREMENT_CONTRACT", sem["evidence_layers"])
        self.assertFalse(sem["semantic_classification_proves_policy_identity"])

    def test_semantic_config_still_passes_with_expansion(self):
        got = validate_config()
        self.assertEqual(got["status"], "PASS")
        self.assertGreaterEqual(got["education_topic_count"], 13)


if __name__ == "__main__":
    unittest.main()

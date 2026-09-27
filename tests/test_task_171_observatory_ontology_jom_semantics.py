import json
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.journal.processing import JournalPdfProcessor
from robo_dados_publicos.journal.semantic_layers import classify_event, validate_config


ROOT = Path(__file__).resolve().parents[1]
ONTOLOGY = ROOT / "config/observatory_question_ontology.v1.json"
BUDGET_MAP = ROOT / "config/budget_fiscal_source_acquisition_map.v1.json"
FIXTURE = Path(__file__).parent / "fixtures" / "jornal_oficial_fixture_2pages.pdf"


class TestTask171ObservatoryOntologyJomSemantics(unittest.TestCase):
    def test_observatory_scope_is_general_and_eiti_not_global_boundary(self):
        obj = json.loads(ONTOLOGY.read_text(encoding="utf-8"))
        self.assertEqual(obj["system_scope"], "GENERAL_MUNICIPAL_PUBLIC_DATA_OBSERVATORY")
        ids = {x["id"] for x in obj["domains"]}
        required = {
            "NETWORK_ENROLLMENT",
            "LEARNING_FLOW",
            "FINANCING",
            "PLANNING_BUDGET",
            "ACCOUNTING_EXECUTION",
            "PROCUREMENT_CONTRACTS",
            "NORMS_SCHOOL_FUNCTIONING",
            "JOURNAL_EVENT_RADAR",
        }
        self.assertTrue(required <= ids)
        self.assertGreaterEqual(len(ids), 15)

    def test_answer_contract_requires_number_context_explanation_source_and_caution(self):
        obj = json.loads(ONTOLOGY.read_text(encoding="utf-8"))
        parts = set(obj["answer_contract"]["required_parts_when_available"])
        self.assertTrue(
            {
                "NUMBER_OR_FACT",
                "TIME_REFERENCE",
                "PLAIN_LANGUAGE_EXPLANATION",
                "SOURCE_AND_PROVENANCE",
                "CAUTION_OR_LIMIT",
            }
            <= parts
        )
        self.assertTrue(obj["answer_contract"]["numbers_must_be_deterministic"])

    def test_budget_map_preserves_stage_separation_and_direct_json_first(self):
        obj = json.loads(BUDGET_MAP.read_text(encoding="utf-8"))
        self.assertEqual(obj["acquisition_order"][0], "DIRECT_OFFICIAL_JSON_API_GET")
        self.assertIn("PAYMENT", obj["stages"])
        by_id = {x["id"]: x for x in obj["sources"]}
        self.assertEqual(by_id["TDA_LIMEIRA"]["machine_readable_status"], "MISSING_DECLARED_PUBLIC_JSON_ROUTE")
        self.assertEqual(by_id["PNCP_CONSULTA"]["granularity_limit"], "PROCUREMENT_AND_CONTRACT_PUBLICATION_NE_PAYMENT")
        self.assertIn("SICONFI_STN_RREO_RGF", obj["missing_json_route_priority_after_task171"])

    def test_jom_semantic_config_passes(self):
        result = validate_config()
        self.assertEqual(result["status"], "PASS")
        self.assertGreaterEqual(result["evidence_layer_count"], 9)

    def test_jom_event_can_have_multiple_independent_facets(self):
        event = {
            "event_id": "JOEV_TEST",
            "source_id": "LIMEIRA_JO_99999",
            "edition": 99999,
            "page_number": 1,
            "source_sha256": "a" * 64,
            "event_type": "DECRETO",
            "organ": "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
            "object_text": "Abre crédito suplementar para reforma de escola em tempo integral.",
            "excerpt_redacted": "DECRETO 10. Abre crédito suplementar para reforma de escola em tempo integral.",
        }
        got = classify_event(event)
        self.assertIn("EDUCATION", got["policy_domains"])
        self.assertIn("NORMATIVE", got["evidence_layers"])
        self.assertIn("BUDGET_AUTHORIZATION", got["evidence_layers"])
        self.assertIn("INFRASTRUCTURE", got["evidence_layers"])
        self.assertIn("FULL_TIME_EDUCATION", got["education_topics"])
        self.assertIn("AUTHORIZATION", got["financial_stages"])
        self.assertFalse(got["semantic_classification_proves_financial_identity"])

    def test_procurement_value_or_contract_does_not_become_payment(self):
        event = {
            "event_id": "JOEV_CONTRACT",
            "source_id": "LIMEIRA_JO_99998",
            "edition": 99998,
            "page_number": 2,
            "source_sha256": "b" * 64,
            "event_type": "CONTRATO",
            "organ": "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
            "object_text": "Contrato de transporte escolar no valor de R$ 100.000,00.",
            "excerpt_redacted": "CONTRATO Nº 1/2026. Transporte escolar. VALOR R$ 100.000,00.",
        }
        got = classify_event(event)
        self.assertIn("PROCUREMENT_CONTRACT", got["evidence_layers"])
        self.assertIn("PROCUREMENT", got["financial_stages"])
        self.assertNotIn("PAYMENT", got["financial_stages"])
        self.assertFalse(got["semantic_classification_proves_payment"])

    def test_explicit_payment_requires_accounting_execution_marker(self):
        event = {
            "event_id": "JOEV_PAY",
            "source_id": "LIMEIRA_JO_99997",
            "edition": 99997,
            "page_number": 3,
            "source_sha256": "c" * 64,
            "event_type": "PORTARIA",
            "organ": "SECRETARIA MUNICIPAL DE FAZENDA",
            "object_text": "Registra pagamento e liquidação do empenho 123.",
            "excerpt_redacted": "PAGAMENTO LIQUIDAÇÃO EMPENHO 123.",
        }
        got = classify_event(event)
        self.assertIn("ACCOUNTING_EXECUTION", got["evidence_layers"])
        self.assertIn("PAYMENT", got["financial_stages"])
        self.assertTrue(got["explicit_payment_marker"])
        self.assertTrue(got["payment_evidence_candidate"])
        self.assertFalse(got["semantic_classification_proves_payment"])
        self.assertFalse(got["semantic_classification_proves_financial_identity"])

    def test_existing_journal_pipeline_emits_semantic_gold_sidecar(self):
        with tempfile.TemporaryDirectory() as td:
            out = JournalPdfProcessor().process(
                FIXTURE,
                edition=7309,
                publication_date="2026-08-21",
                source_url="https://example.org/7309.pdf",
                out_dir=td,
            )
            self.assertEqual(out["gold_events"], out["semantic_event_facets"])
            sidecar = Path(td) / "event_semantics_gold.jsonl"
            self.assertTrue(sidecar.exists())
            rows = [json.loads(x) for x in sidecar.read_text(encoding="utf-8").splitlines() if x.strip()]
            self.assertEqual(out["gold_events"], len(rows))
            self.assertTrue(all("event_id" in x and "evidence_layers" in x for x in rows))


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.journal.processing import JournalPdfProcessor
from robo_dados_publicos.accounting.tcesp_current import (
    Task173Stop,
    normalize_tcesp_expense_row,
    route_jom_event_to_tcesp,
    validate_contracts,
)


def row(**updates):
    base = {
        "tp_despesa": "Empenhado",
        "nr_empenho": "1234",
        "identificador_despesa": "EXP-2026-0001",
        "ds_despesa": "Despesa de educação",
        "dt_emissao_despesa": "2026-03-10",
        "vl_despesa": "1.234,56",
        "ds_funcao_governo": "Educação",
        "ds_subfuncao_governo": "Ensino Fundamental",
        "cd_programa": "2001",
        "ds_programa": "Educação de Qualidade",
        "cd_acao": "2010",
        "ds_acao": "Manutenção do Ensino Fundamental",
        "ds_fonte_recurso": "Tesouro",
        "ds_cd_aplicacao_fixo": "2200000",
        "ds_modalidade_lic": "Pregão Eletrônico",
        "ds_elemento": "Material de Consumo",
        "historico_despesa": "Aquisição de materiais para unidades escolares.",
    }
    base.update(updates)
    return base


FIXTURE = Path(__file__).parent / "fixtures" / "jornal_oficial_fixture_2pages.pdf"


class TestTask173TcespAccountingLedgerJomRouter(unittest.TestCase):
    def test_contracts_pass_and_remain_route_scoped(self):
        got = validate_contracts()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["proven_column_count"], 17)
        self.assertFalse(got["family_wide_auto_ingest_promoted"])
        self.assertFalse(got["network"])

    def test_commitment_normalizes_into_canonical_observation(self):
        got = normalize_tcesp_expense_row(row())
        self.assertEqual(got["stage"], "COMMITMENT")
        self.assertEqual(got["amount_semantic"], "COMMITTED_VALUE")
        self.assertEqual(got["amount_brl"], "1234.56")
        self.assertEqual(got["transaction_keys"]["source_expense_identifier"], "EXP-2026-0001")
        self.assertEqual(got["transaction_keys"]["fiscal_year_plus_empenho"], "2026:1234")
        self.assertEqual(got["identity_status"], "ACCOUNTING_TRANSACTION_KEY_AVAILABLE")
        self.assertFalse(got["policy_identity_proven"])
        self.assertFalse(got["financial_policy_identity_proven"])

    def test_stage_semantics_are_distinct(self):
        self.assertEqual(normalize_tcesp_expense_row(row(tp_despesa="Liquidado"))["stage"], "LIQUIDATION")
        self.assertEqual(normalize_tcesp_expense_row(row(tp_despesa="Pago"))["stage"], "PAYMENT")
        self.assertEqual(normalize_tcesp_expense_row(row(tp_despesa="Anulado"))["stage"], "REVERSAL")
        self.assertEqual(normalize_tcesp_expense_row(row(tp_despesa="Evento novo"))["stage"], "OTHER_REVIEW")

    def test_education_is_only_policy_domain_hint(self):
        got = normalize_tcesp_expense_row(row())
        self.assertIn("EDUCATION", got["policy_domain_hints"])
        self.assertEqual(got["policy_link_status"], "NOT_PROVEN")
        self.assertFalse(got["policy_identity_proven"])

    def test_program_action_application_do_not_create_policy_identity(self):
        got = normalize_tcesp_expense_row(
            row(
                cd_programa="2001",
                ds_programa="Programa de Educação Integral",
                cd_acao="2050",
                ds_acao="Escola em Tempo Integral",
                ds_cd_aplicacao_fixo="2607004",
            )
        )
        self.assertIn("EDUCATION", got["policy_domain_hints"])
        self.assertFalse(got["policy_identity_proven"])
        self.assertFalse(got["financial_policy_identity_proven"])

    def test_missing_proven_source_column_fails_closed(self):
        bad = row()
        bad.pop("nr_empenho")
        with self.assertRaisesRegex(Task173Stop, "TASK173_SOURCE_SCHEMA_MISSING_COLUMNS"):
            normalize_tcesp_expense_row(bad)

    def test_jom_exact_empenho_becomes_strong_queryable_key_only(self):
        event = {
            "event_id": "JOEV_1",
            "source_id": "LIMEIRA_JO_07310",
            "publication_date": "2026-03-11",
            "event_type": "PORTARIA",
            "object_text": "Referente ao empenho nº 1234.",
            "excerpt_redacted": "EMPENHO Nº 1234",
            "value_brl": "1234.56",
        }
        semantics = {
            "policy_domains": ["EDUCATION"],
            "evidence_layers": ["ACCOUNTING_EXECUTION"],
            "financial_stages": ["COMMITMENT"],
        }
        got = route_jom_event_to_tcesp(event, semantics)
        self.assertEqual(got["route_state"], "READY_EXACT_ACCOUNTING_KEY_QUERY")
        self.assertEqual(got["strong_queryable_keys"]["nr_empenho"], "1234")
        self.assertFalse(got["financial_identity_proven"])
        self.assertFalse(got["payment_proven"])

    def test_jom_cnpj_contract_process_are_strong_external_hints_not_assumed_tce_columns(self):
        event = {
            "event_id": "JOEV_2",
            "publication_date": "2026-05-01",
            "event_type": "CONTRATO",
            "contract_number": "170/2026",
            "process_number": "123/2026",
            "cnpj": "12.345.678/0001-90",
            "object_text": "Serviço para escola municipal.",
        }
        got = route_jom_event_to_tcesp(event, {"policy_domains": ["EDUCATION"]})
        self.assertEqual(got["route_state"], "CANDIDATE_EXTERNAL_KEY_REQUIRES_TCE_COLUMN_OR_CROSSWALK")
        self.assertEqual(got["strong_external_identity_hints_not_proven_queryable"]["cnpj"], "12345678000190")
        self.assertNotIn("cnpj", got["strong_queryable_keys"])
        self.assertFalse(got["financial_identity_proven"])

    def test_amount_date_text_are_weak_only(self):
        event = {
            "event_id": "JOEV_3",
            "publication_date": "2026-05-01",
            "event_type": "DECRETO",
            "value_brl": "100000.00",
            "object_text": "Educação integral.",
        }
        got = route_jom_event_to_tcesp(event, {"policy_domains": ["EDUCATION"]})
        self.assertEqual(got["route_state"], "CONTEXTUAL_FILTER_ONLY_NO_IDENTITY")
        self.assertEqual(got["weak_corroborators"]["value_brl"], "100000.00")
        self.assertFalse(got["amount_date_text_can_create_identity"])
        self.assertFalse(got["semantic_facets_can_create_identity"])

    def test_normal_journal_pipeline_emits_accounting_query_sidecar(self):
        with tempfile.TemporaryDirectory() as td:
            out = JournalPdfProcessor().process(
                FIXTURE,
                edition=7309,
                publication_date="2026-08-21",
                source_url="https://example.org/7309.pdf",
                out_dir=td,
            )
            self.assertEqual(out["gold_events"], out["accounting_query_tasks"])
            path = Path(td) / "accounting_query_tasks.jsonl"
            self.assertTrue(path.exists())
            rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
            self.assertEqual(out["gold_events"], len(rows))
            self.assertTrue(all(x["target_source"] == "TCESP_LIMEIRA_2026_DESPESAS" for x in rows))
            self.assertTrue(all(x["financial_identity_proven"] is False for x in rows))

    def test_query_id_is_deterministic(self):
        event = {
            "event_id": "JOEV_4",
            "publication_date": "2026-01-02",
            "event_type": "CONTRATO",
            "excerpt_redacted": "Nota de Empenho 999/2026",
        }
        a = route_jom_event_to_tcesp(event)
        b = route_jom_event_to_tcesp(event)
        self.assertEqual(a["query_id"], b["query_id"])


if __name__ == "__main__":
    unittest.main()

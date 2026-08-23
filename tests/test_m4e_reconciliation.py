import json
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.journal.processing import JournalPdfProcessor
from robo_dados_publicos.reconciliation.planner import ReconciliationPlanner
from robo_dados_publicos.state.registry import StateRegistry

FIXTURE = Path(__file__).parent / 'fixtures' / 'jornal_oficial_fixture_2pages.pdf'


def contract_event():
    return {
        'event_id': 'JOEV_contract_001',
        'source_id': 'LIMEIRA_JO_07309',
        'event_type': 'CONTRATO',
        'publication_date': '2026-08-21',
        'contract_number': '51/2025',
        'process_number': '903.586/2025',
        'edital_number': '20/2025',
        'bidding_modality': 'PREGÃO ELETRÔNICO',
        'bidding_number': '19/2025',
        'contractor': 'Consórcio Exemplo Ltda',
        'cnpj': '61086929000170',
        'object_text': 'Contratação de serviços especializados',
        'value_brl': '532800.00',
    }


class TestReconciliationPlanner(unittest.TestCase):
    def test_contract_event_creates_cross_source_tasks(self):
        tasks = ReconciliationPlanner().plan_event(contract_event())
        targets = {t.target_source for t in tasks}
        self.assertEqual({'LIMEIRA_CONTRATOS', 'TCE_SP_DESPESAS', 'TDA_LIMEIRA', 'LIMEIRA_LICITACOES'}, targets)

    def test_contract_registry_prefers_identifier_year_over_publication_year(self):
        tasks = ReconciliationPlanner().plan_event(contract_event())
        task = next(t for t in tasks if t.target_source == 'LIMEIRA_CONTRATOS')
        self.assertEqual(2025, task.match_keys['year'])

    def test_tce_task_keeps_candidate_years_and_does_not_claim_identity(self):
        tasks = ReconciliationPlanner().plan_event(contract_event())
        task = next(t for t in tasks if t.target_source == 'TCE_SP_DESPESAS')
        self.assertEqual([2025, 2026], task.match_keys['candidate_years'])
        self.assertEqual('A', task.minimum_link_confidence)
        self.assertIn('não prova vínculo', task.identity_rule.lower())

    def test_tda_task_is_blocked_until_connector_discovery(self):
        tasks = ReconciliationPlanner().plan_event(contract_event())
        task = next(t for t in tasks if t.target_source == 'TDA_LIMEIRA')
        self.assertEqual('BLOCKED_CONNECTOR_DISCOVERY', task.status)
        self.assertIn('estágio explícito', task.identity_rule)

    def test_legislative_event_routes_to_siave(self):
        event = {
            'event_id': 'JOEV_portaria_001', 'source_id': 'LIMEIRA_JO_07309',
            'event_type': 'PORTARIA', 'publication_date': '2026-08-21', 'act_number': '123/2026'
        }
        tasks = ReconciliationPlanner().plan_event(event)
        self.assertEqual(1, len(tasks))
        self.assertEqual('SIAVE_LIMEIRA', tasks[0].target_source)
        self.assertEqual(2026, tasks[0].match_keys['year'])

    def test_task_ids_are_deterministic_and_plan_is_idempotent(self):
        planner = ReconciliationPlanner()
        a = planner.plan_events([contract_event(), contract_event()])
        b = planner.plan_events([contract_event()])
        self.assertEqual([x.task_id for x in b], [x.task_id for x in a])
        self.assertEqual(4, len(a))

    def test_state_queue_upsert_is_idempotent_and_filterable(self):
        planner = ReconciliationPlanner()
        tasks = planner.plan_event(contract_event())
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / 'state.sqlite'
            with StateRegistry(db) as st:
                for task in tasks + tasks:
                    st.upsert_reconciliation_task(task)
                all_rows = st.list_reconciliation_tasks()
                blocked = st.list_reconciliation_tasks(status='BLOCKED_CONNECTOR_DISCOVERY')
                self.assertEqual(4, len(all_rows))
                self.assertEqual(1, len(blocked))
                ready = next(x for x in all_rows if x['target_source'] == 'LIMEIRA_CONTRATOS')
                st.update_reconciliation_task(ready['task_id'], 'MATCH_CANDIDATE', {'records': 2})
                changed = next(x for x in st.list_reconciliation_tasks() if x['task_id'] == ready['task_id'])
                self.assertEqual('MATCH_CANDIDATE', changed['status'])
                self.assertEqual({'records': 2}, changed['result'])

    def test_journal_pipeline_emits_reconciliation_queue_without_network(self):
        with tempfile.TemporaryDirectory() as td:
            out = JournalPdfProcessor().process(
                FIXTURE, edition=7309, publication_date='2026-08-21',
                source_url='https://example.org/7309.pdf', out_dir=td,
            )
            self.assertEqual('PASS_DOCUMENT_PROCESSING', out['status'])
            self.assertGreater(out['reconciliation_tasks'], 0)
            path = Path(td) / 'reconciliation_tasks.jsonl'
            self.assertTrue(path.exists())
            rows = [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
            self.assertEqual(out['reconciliation_tasks'], len(rows))
            self.assertTrue(any(x['target_source'] == 'TDA_LIMEIRA' and x['status'] == 'BLOCKED_CONNECTOR_DISCOVERY' for x in rows))


if __name__ == '__main__':
    unittest.main()

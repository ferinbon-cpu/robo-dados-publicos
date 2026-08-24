import json
import unittest
from pathlib import Path


class TestM4EPromotion(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parent.parent

    def load_json(self, relative_path):
        return json.loads((self.root / relative_path).read_text(encoding='utf-8'))

    def test_candidate_evidence_is_preserved_after_promotion(self):
        candidate = self.load_json('release_manifest_v01_0.5.8.json')
        active = self.load_json('release_manifest_v01_0.5.8_active.json')
        self.assertEqual('CANDIDATE', candidate['status'])
        self.assertEqual('ACTIVE', active['status'])
        self.assertEqual('0.5.8', active['promoted_from_candidate'])

    def test_promotion_keeps_financial_identity_fail_closed(self):
        active = self.load_json('release_manifest_v01_0.5.8_active.json')
        self.assertEqual('PROHIBITED', active['safety']['financial_identity_auto_promotion'])
        self.assertEqual('CANDIDATE_ONLY', active['safety']['reconciliation_matches'])

    def test_tda_remains_blocked_and_production_collection_opt_in(self):
        active = self.load_json('release_manifest_v01_0.5.8_active.json')
        discovery = self.load_json('config/limeira_sources_discovery.json')
        tda = next(x for x in discovery['surfaces'] if x['source_id'] == 'LIMEIRA_TDA_PORTAL')
        journal = next(x for x in discovery['surfaces'] if x['source_id'] == 'LIMEIRA_JORNAL_OFICIAL')
        self.assertEqual('BLOCKED_NO_PUBLIC_ENDPOINT_PROVEN', active['open_gates']['tda_limeira'])
        self.assertEqual('BLOCKED_NO_PUBLIC_ENDPOINT_PROVEN', tda['status'])
        self.assertFalse(tda['production_collection_enabled'])
        self.assertFalse(journal['production_collection_enabled'])

    def test_0_6_1_candidate_evidence_is_preserved_after_promotion(self):
        candidate = self.load_json('release_manifest_v01_0.6.1.json')
        active = self.load_json('release_manifest_v01_0.6.1_active.json')
        self.assertEqual('CANDIDATE', candidate['status'])
        self.assertEqual('ACTIVE', active['status'])
        self.assertEqual('0.6.1', active['promoted_from_candidate'])

    def test_0_6_1_live_processing_gate_and_metrics_are_recorded(self):
        active = self.load_json('release_manifest_v01_0.6.1_active.json')
        gate = active['live_gate']
        evidence = active['processing_evidence']
        self.assertEqual('PASS_GITHUB_JOURNAL_PROCESSING_GATE', gate['status'])
        self.assertEqual(32761758504, gate['workflow_run'])
        self.assertEqual(97541993609, gate['job'])
        self.assertEqual(76, evidence['pages'])
        self.assertEqual(53, evidence['gold_events'])
        self.assertEqual(148, evidence['rag_chunks'])
        self.assertEqual(68, evidence['reconciliation_tasks'])

    def test_0_6_1_five_derived_outputs_are_recorded_without_private_metadata(self):
        evidence = (self.root / 'docs/M4E_FIRST_SOURCE_PROCESSING_EVIDENCE_2026-08-24.md').read_text(encoding='utf-8')
        expected_outputs = (
            'edition_manifest.json',
            'pages_silver.jsonl',
            'events_gold.jsonl',
            'reconciliation_tasks.jsonl',
            'chunks_rag.jsonl',
        )
        self.assertTrue(all(value in evidence for value in expected_outputs))
        self.assertIn('identificadores remotos: não publicados', evidence)
        self.assertIn('Hashes, tamanhos e IDs privados permanecem apenas na auditoria', evidence)

    def test_0_6_1_processing_rerun_and_automatic_identity_are_disabled(self):
        active = self.load_json('release_manifest_v01_0.6.1_active.json')
        workflow = (self.root / '.github/workflows/robo-dados-publicos.yml').read_text(encoding='utf-8')
        self.assertEqual('DISABLED_IN_WORKFLOW', active['safety']['source_processing_rerun'])
        self.assertEqual('PROHIBITED', active['safety']['financial_identity_auto_promotion'])
        self.assertNotIn('confirm_processing:', workflow)
        self.assertNotIn('scripts/github_processing_gate.py', workflow)

    def test_0_6_2_candidate_evidence_is_preserved_after_promotion(self):
        candidate = self.load_json('release_manifest_v01_0.6.2.json')
        active = self.load_json('release_manifest_v01_0.6.2_active.json')
        self.assertEqual('CANDIDATE', candidate['status'])
        self.assertEqual('ACTIVE', active['status'])
        self.assertEqual('0.6.2', active['promoted_from_candidate'])

    def test_0_6_2_live_reconciliation_gate_is_recorded(self):
        gate = self.load_json('release_manifest_v01_0.6.2_active.json')['live_gate']
        self.assertEqual('PASS_GITHUB_RECONCILIATION_EXECUTION_GATE', gate['status'])
        self.assertEqual(8, gate['workflow_dispatch_sequence'])
        self.assertEqual('bca696c4792fe8e6a87be716b26855f450c22459', gate['source_commit'])
        self.assertEqual('33s', gate['total_duration'])
        self.assertEqual({'MATCH_CANDIDATE': 1}, gate['result_status_counts'])
        self.assertEqual('REPLACED', gate['state_remote'])
        self.assertEqual('CREATED', gate['append_only_log'])

    def test_0_6_2_match_remains_candidate_only_and_protected(self):
        active = self.load_json('release_manifest_v01_0.6.2_active.json')
        evidence = active['reconciliation_evidence']
        safety = active['safety']
        self.assertEqual(1, evidence['candidate_evidence_edges'])
        self.assertEqual(0, evidence['financial_identity_edges'])
        self.assertTrue(evidence['protected_targets_unchanged'])
        self.assertEqual('CANDIDATE_ONLY', safety['reconciliation_matches'])
        self.assertEqual('PROHIBITED', safety['financial_identity_auto_promotion'])

    def test_0_6_2_reconciliation_rerun_and_schedule_are_disabled(self):
        active = self.load_json('release_manifest_v01_0.6.2_active.json')
        workflow = (self.root / '.github/workflows/robo-dados-publicos.yml').read_text(encoding='utf-8')
        active_lines = [line for line in workflow.splitlines() if not line.lstrip().startswith('#')]
        self.assertEqual('DISABLED_IN_WORKFLOW', active['safety']['reconciliation_rerun'])
        self.assertEqual('DISABLED', active['safety']['broad_reconciliation_execution'])
        self.assertEqual('BLOCKED_NO_PUBLIC_ENDPOINT_PROVEN', active['safety']['tda_limeira'])
        self.assertNotIn('confirm_reconciliation:', workflow)
        self.assertNotIn('scripts/github_reconciliation_gate.py', workflow)
        self.assertFalse(any(line.strip() == 'schedule:' for line in active_lines))


if __name__ == '__main__':
    unittest.main()

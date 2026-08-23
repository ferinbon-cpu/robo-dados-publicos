import unittest, tempfile
from pathlib import Path
from robo_dados_publicos.ingest.gates import decide_version
from robo_dados_publicos.temporal.rules import temporal_decision
from robo_dados_publicos.answers.contracts import evidence_insufficient

class TestCoreContracts(unittest.TestCase):
    def test_version_gate(self):
        self.assertEqual('DUPLICATE_SKIP', decide_version('abc','abc',True))
        self.assertEqual('NEW_VERSION_REVIEW', decide_version('abc','def',True))
        self.assertEqual('NEW_INGEST', decide_version(None,'def',False))
    def test_temporal_same_period_revision(self):
        self.assertEqual('REVISED_SAME_PERIOD', temporal_decision('2026-03','new','2026-03','old'))
    def test_evidence_insufficient_contract(self):
        x=evidence_insufficient('faltou execução',('fonte1',))
        self.assertEqual('EVIDENCIA_INSUFICIENTE', x.status)
        self.assertIn('execução', x.cautela)

if __name__ == '__main__': unittest.main()

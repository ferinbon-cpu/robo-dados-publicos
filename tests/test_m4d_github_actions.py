import unittest
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
WORKFLOW = ROOT / '.github' / 'workflows' / 'robo-dados-publicos.yml'

class TestM4DGitHubActions(unittest.TestCase):
    def test_workflow_security_contract(self):
        text = WORKFLOW.read_text(encoding='utf-8')
        self.assertIn('workflow_dispatch:', text)
        self.assertIn('permissions:\n  contents: read', text)
        self.assertIn('actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd', text)
        self.assertIn('actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97', text)
        self.assertIn('persist-credentials: false', text)
        self.assertIn("python-version: '3.12'", text)
        self.assertIn('${{ secrets.GOOGLE_DRIVE_CLIENT_ID }}', text)
        self.assertIn('${{ secrets.GOOGLE_DRIVE_CLIENT_SECRET }}', text)
        self.assertIn('${{ secrets.GOOGLE_DRIVE_REFRESH_TOKEN }}', text)
        self.assertIn('python scripts/github_preflight.py --require-oauth', text)
        self.assertIn('python scripts/github_run_gate.py', text)
        self.assertIn('confirm_source_collection:', text)
        self.assertIn('inputs.confirm_source_collection == true', text)
        self.assertIn('--source-config config/sources.jornal_oficial_7310_gate.json', text)
        self.assertNotIn('ya' + '29.', text)
        self.assertNotIn('1' + '//', text)

    def test_workflow_is_manual_only_and_requires_confirmation(self):
        text = WORKFLOW.read_text(encoding='utf-8')
        active_lines = [line for line in text.splitlines() if not line.lstrip().startswith('#')]
        self.assertFalse(any(line.strip() == 'schedule:' for line in active_lines))
        self.assertIn('confirm_persistence:', text)
        self.assertIn('confirm_source_collection:', text)
        self.assertIn('default: false', text)
        self.assertIn('inputs.confirm_persistence == true', text)

    def test_offline_preflight_passes_without_credentials(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / 'scripts' / 'github_preflight.py')],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertEqual('PASS_OFFLINE', json.loads(proc.stdout)['status'])

    def test_live_preflight_stops_when_credentials_are_missing(self):
        env = os.environ.copy()
        for name in ('GOOGLE_DRIVE_CLIENT_ID', 'GOOGLE_DRIVE_CLIENT_SECRET', 'GOOGLE_DRIVE_REFRESH_TOKEN'):
            env.pop(name, None)
        proc = subprocess.run(
            [sys.executable, str(ROOT / 'scripts' / 'github_preflight.py'), '--require-oauth'],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        payload = json.loads(proc.stdout)
        self.assertEqual(3, proc.returncode)
        self.assertEqual('STOP_MISSING_GITHUB_SECRETS', payload['status'])
        self.assertEqual(3, len(payload['missing_oauth_secrets']))

if __name__ == '__main__':
    unittest.main()

import json
import tomllib
import unittest
from pathlib import Path

from robo_dados_publicos import __version__
from robo_dados_publicos.discovery.portal_probe import PortalProbe
from robo_dados_publicos.journal.official import JornalOficialLimeira
from robo_dados_publicos.reconciliation.resolvers import LimeiraContractsResolver, TcespExpenseResolver
from robo_dados_publicos.release import (
    ACTIVE_VALIDATED_VERSION,
    CURRENT_CANDIDATE_VERSION,
    RELEASE_STATUS,
    RESEARCH_USER_AGENT,
    USER_AGENT,
)
from robo_dados_publicos.sources.collector import SourceCollector


class TestReleaseConsistency(unittest.TestCase):
    def test_pyproject_and_package_version_match(self):
        root = Path(__file__).resolve().parent.parent
        with open(root / 'pyproject.toml', 'rb') as f:
            project = tomllib.load(f)
        self.assertEqual(project['project']['version'], __version__)

    def test_current_release_metadata_match(self):
        root = Path(__file__).resolve().parent.parent

        def load_json(relative_path):
            return json.loads((root / relative_path).read_text(encoding='utf-8'))

        manifest = load_json('release_manifest_v01.json')
        active_manifest = load_json(manifest['active_manifest'])
        candidate_manifest = load_json(manifest['candidate_manifest'])
        current_qa = load_json('QA_SOFTWARE_V01.json')
        target_config = load_json('config/reconciliation_targets.json')

        self.assertEqual('0.6.2', manifest['current_active'])
        self.assertEqual(__version__, manifest['current_candidate'])
        self.assertEqual('0.6.2', manifest['last_active_validated'])
        self.assertEqual('0.6.2', active_manifest['version'])
        self.assertEqual('ACTIVE', active_manifest['status'])
        self.assertEqual(__version__, candidate_manifest['version'])
        self.assertEqual('CANDIDATE', candidate_manifest['status'])
        self.assertEqual(__version__, current_qa['version'])
        self.assertEqual('CANDIDATE', current_qa['status'])
        self.assertEqual('0.6.2', target_config['generated_for_software'])
        readme = (root / 'README.md').read_text(encoding='utf-8')
        self.assertIn('**Software ativo:** 0.6.2 ACTIVE', readme)
        self.assertIn(f'**Candidata corrente:** {__version__} CANDIDATE', readme)
        release_index = (root / 'docs/RELEASE_NOTES_V01.md').read_text(encoding='utf-8')
        self.assertIn(f'**{__version__} CANDIDATE', release_index)
        self.assertTrue((root / f'docs/RELEASE_NOTES_V01_{__version__}.md').is_file())

    def test_active_release_identity_is_explicit(self):
        self.assertEqual('CANDIDATE', RELEASE_STATUS)
        self.assertEqual('0.6.2', ACTIVE_VALIDATED_VERSION)
        self.assertEqual(__version__, CURRENT_CANDIDATE_VERSION)

    def test_runtime_user_agents_use_current_version(self):
        self.assertEqual(USER_AGENT, SourceCollector(None, 'BRONZE', 'QUARANTINE').http.user_agent)
        self.assertEqual(USER_AGENT, JornalOficialLimeira().user_agent)
        self.assertEqual(RESEARCH_USER_AGENT, PortalProbe().user_agent)
        self.assertEqual(RESEARCH_USER_AGENT, TcespExpenseResolver().user_agent)
        self.assertEqual(RESEARCH_USER_AGENT, LimeiraContractsResolver().user_agent)


if __name__ == '__main__':
    unittest.main()

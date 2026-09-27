import unittest, importlib.util
from pathlib import Path
from urllib.parse import urlparse, parse_qs

SPEC=importlib.util.spec_from_file_location('oauth_bootstrap',Path(__file__).parents[1]/'scripts'/'oauth_bootstrap_drive.py')
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class TestOAuthBootstrap(unittest.TestCase):
    def test_pkce_and_auth_url(self):
        verifier,challenge=mod.pkce_pair()
        self.assertGreater(len(verifier),40); self.assertGreater(len(challenge),40)
        url=mod.build_auth_url('CID','http://127.0.0.1:9876',mod.SCOPES['drive'],'STATE',challenge)
        q=parse_qs(urlparse(url).query)
        self.assertEqual(['code'],q['response_type'])
        self.assertEqual(['offline'],q['access_type'])
        self.assertEqual(['S256'],q['code_challenge_method'])
        self.assertEqual([mod.SCOPES['drive']],q['scope'])

    def test_readonly_scope_is_available_for_least_privilege_gates(self):
        self.assertEqual(
            'https://www.googleapis.com/auth/drive.readonly',
            mod.SCOPES['drive.readonly'],
        )
        verifier,challenge=mod.pkce_pair()
        url=mod.build_auth_url(
            'CID',
            'http://127.0.0.1:9876',
            mod.SCOPES['drive.readonly'],
            'STATE',
            challenge,
        )
        q=parse_qs(urlparse(url).query)
        self.assertEqual([mod.SCOPES['drive.readonly']],q['scope'])
        self.assertGreater(len(verifier),40)

if __name__=='__main__': unittest.main()

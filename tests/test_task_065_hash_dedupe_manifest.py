from __future__ import annotations
import unittest
from robo_dados_publicos.manual_ingest.hash_dedupe import compare_content, sha256_bytes, validate_sha256

class Task065Tests(unittest.TestCase):
    def test_sha_is_stable(self):
        self.assertEqual(sha256_bytes(b"abc"), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
    def test_same_hash_reuses_identity(self):
        h=sha256_bytes(b"x")
        self.assertEqual(compare_content(incoming_sha256=h,existing_sha256=h).state,"DUPLICATE_CONTENT_REUSE_IDENTITY")
    def test_same_title_different_hash_stays_distinct(self):
        a=sha256_bytes(b"a"); b=sha256_bytes(b"b")
        self.assertEqual(compare_content(incoming_sha256=a,existing_sha256=b,same_title=True).state,"DISTINCT_CONTENT_KEEP_BOTH")
    def test_no_existing_is_create_only_eligible(self):
        h=sha256_bytes(b"x")
        self.assertEqual(compare_content(incoming_sha256=h,existing_sha256=None).state,"NEW_CONTENT_CREATE_ONLY_BRONZE_ELIGIBLE")
    def test_sha_validation(self):
        self.assertTrue(validate_sha256("a"*64)); self.assertFalse(validate_sha256("z"*64))

if __name__ == "__main__": unittest.main()

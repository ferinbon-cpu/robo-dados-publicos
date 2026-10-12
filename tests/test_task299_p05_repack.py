"""Offline guard tests for TASK299 P05 package handling."""
import unittest
from unittest.mock import patch
from scripts import repackage_task299_p05_existing_artifact as t

class TestTask299(unittest.TestCase):
    def test_expected_source_and_partitions(self):
        self.assertEqual(t.SOURCE_RUN, 38256908207)
        self.assertEqual(t.PART_COUNT, 5)
        self.assertEqual(t.PART_BYTES, 70*1024*1024)
        self.assertEqual(len(t.EDITIONS), 9)

    def test_dispatch_gate(self):
        valid = {
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GITHUB_REF": "refs/heads/main",
            "GITHUB_RUN_ATTEMPT": "1",
            "TASK299_OWNER_CONFIRM": "true",
            "TASK299_SOURCE_RUN": str(t.SOURCE_RUN),
            "GITHUB_SHA": "a"*40,
        }
        t.validate_owner_context(valid)
        for key, invalid in (("GITHUB_EVENT_NAME","push"),
                             ("GITHUB_REF","refs/heads/other"),
                             ("TASK299_OWNER_CONFIRM","false"),
                             ("GITHUB_RUN_ATTEMPT","2")):
            with self.assertRaises(t.Stop299):
                t.validate_owner_context({**valid,key:invalid})

if __name__=="__main__":
    unittest.main()

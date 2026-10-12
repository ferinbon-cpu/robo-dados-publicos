"""Offline guard tests for TASK300 P07 package handling."""
import unittest
from unittest.mock import patch
from scripts import repackage_task300_p07_existing_artifact as t

class TestTask300(unittest.TestCase):
    def test_expected_source_and_partitions(self):
        self.assertEqual(t.SOURCE_RUN, 38275577819)
        self.assertEqual(t.PART_COUNT, 6)
        self.assertEqual(t.PART_BYTES, 70*1024*1024)
        self.assertEqual(t.EDITIONS, (7278,7279,7280,7281,7282,7285,7286,7295,7296))

    def test_dispatch_gate(self):
        valid = {
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GITHUB_REF": "refs/heads/main",
            "GITHUB_RUN_ATTEMPT": "1",
            "TASK300_OWNER_CONFIRM": "true",
            "TASK300_SOURCE_RUN": str(t.SOURCE_RUN),
            "GITHUB_SHA": "a"*40,
        }
        t.validate_owner_context(valid)
        for key, invalid in (("GITHUB_EVENT_NAME","push"),
                             ("GITHUB_REF","refs/heads/other"),
                             ("TASK300_OWNER_CONFIRM","false"),
                             ("GITHUB_RUN_ATTEMPT","2")):
            with self.assertRaises(t.Stop300):
                t.validate_owner_context({**valid,key:invalid})

if __name__=="__main__":
    unittest.main()

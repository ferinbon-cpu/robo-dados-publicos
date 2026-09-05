from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from robo_dados_publicos.research.direct_json_first_source_discovery import validate

P = ROOT / "config/direct_json_first_source_discovery_policy.v1.json"


class TestTask165DirectJsonFirst(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = json.loads(P.read_text(encoding="utf-8"))

    def test_validator(self):
        out = validate()
        self.assertEqual("VALID", out["status"])
        self.assertEqual("DIRECT_OFFICIAL_JSON_OR_API_GET", out["first_strategy"])

    def test_reverse_engineering_is_last_resort(self):
        order = [x["strategy"] for x in sorted(self.p["strategy_order"], key=lambda x: x["rank"])]
        self.assertEqual("HTML_DOM_JS_PATH_REVERSE_ENGINEERING_FALLBACK", order[-1])

    def test_authorization_reused_inside_explicit_scope(self):
        a = self.p["authorization_reuse"]
        self.assertIn("page_number", a["typical_reusable_variations"])
        self.assertIn("modality_or_category_filter_within_authorized_source_scope", a["typical_reusable_variations"])
        self.assertIn("new_host_outside_scope", a["new_authorization_required_when_any"])
        self.assertIn("method_changes_to_write_or_mutation", a["new_authorization_required_when_any"])

    def test_safety_boundaries_still_apply(self):
        d = self.p["direct_json_preference"]["does_not_override"]
        self.assertIn("authentication_requirements", d)
        self.assertIn("access_control", d)
        self.assertIn("owner_authorization_scope", d)
        self.assertIn("mutation_prohibitions", d)

    def test_transport_and_pagination_are_fail_closed(self):
        self.assertFalse(self.p["response_validation"]["transport_failure_is_no_match"])
        self.assertTrue(self.p["pagination"]["exhaustive_negative_requires_complete_pagination"])
        self.assertFalse(self.p["pagination"]["partial_result_can_create_exhaustive_no_match"])

    def test_pncp_is_reference_case(self):
        ref = self.p["reference_example"]
        self.assertEqual("PNCP", ref["source"])
        self.assertEqual(
            "UNMETERED_WITHIN_PNCP_SCOPE_UNTIL_REVOKED_OR_SUPERSEDED",
            ref["authorization_metering"]
        )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import inspect
import json
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_official_olinda_api_application_dom_syntax_skeleton_diagnostics import (
    COUNT_FIELDS,
    SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError,
)
from robo_dados_publicos.sources.siope_official_olinda_api_application_dom_syntax_skeleton_runtime_v2 import (
    SystemChromeCdpDomSyntaxSkeletonRuntimeV2,
    _evaluation_value_or_stop,
)

ROOT = Path(__file__).resolve().parents[1]
GATE_SCRIPT = ROOT / "scripts/github_siope_official_olinda_api_application_dom_syntax_skeleton_diagnostics_gate.py"
FAILED_EVIDENCE = ROOT / "docs/evidence/M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SYNTAX_SKELETON_DIAGNOSTICS_RUN_1_STOP_0.8.0.json"


class TestM7SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonRuntimeV2(unittest.TestCase):
    def test_by_value_mapping_is_accepted_without_raw_material(self):
        counts = {field: 0 for field in COUNT_FIELDS}
        counts["minimal_contract_container_count"] = 1
        counts["callable_occurrence_in_minimal_container_count"] = 1
        result = _evaluation_value_or_stop({"result": {"type": "object", "value": counts}})
        self.assertEqual(result, counts)

    def test_javascript_exception_becomes_explicit_sanitized_stop(self):
        with self.assertRaises(SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError) as ctx:
            _evaluation_value_or_stop({
                "result": {"type": "object"},
                "exceptionDetails": {"text": "must not escape"},
            })
        self.assertIn("DOM_EVALUATION_EXCEPTION", str(ctx.exception))
        self.assertEqual(ctx.exception.diagnostics, {"javascript_exception_observed": True})
        self.assertNotIn("must not escape", json.dumps(ctx.exception.diagnostics))

    def test_missing_by_value_mapping_is_explicit_stop_not_count_fields(self):
        with self.assertRaises(SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError) as ctx:
            _evaluation_value_or_stop({"result": {"type": "undefined"}})
        self.assertIn("DOM_EVALUATION_VALUE", str(ctx.exception))
        self.assertNotIn("COUNT_FIELDS", str(ctx.exception))

    def test_runtime_v2_uses_string_only_known_syntax_comparisons(self):
        source = inspect.getsource(SystemChromeCdpDomSyntaxSkeletonRuntimeV2)
        self.assertNotIn("new RegExp", source)
        self.assertNotIn("const esc =", source)
        self.assertIn("compactAfter.includes('$format=')", source)
        self.assertIn("bindingToken", source)
        self.assertIn("aliasTokens", source)
        self.assertIn("returnByValue", source)

    def test_runtime_v2_preserves_fail_closed_network_and_no_raw_dom_return(self):
        source = inspect.getsource(SystemChromeCdpDomSyntaxSkeletonRuntimeV2)
        self.assertIn('"Fetch.failRequest"', source)
        self.assertIn('"Browser.setDownloadBehavior", {"behavior": "deny"}', source)
        self.assertNotIn("outerHTML", source)
        self.assertNotIn("innerHTML", source)
        self.assertNotIn("getResponseBody", source)
        self.assertNotIn("getRequestPostData", source)

    def test_gate_uses_runtime_v2_for_live_only(self):
        text = GATE_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("SystemChromeCdpDomSyntaxSkeletonRuntimeV2", text)
        self.assertIn("runtime=SystemChromeCdpDomSyntaxSkeletonRuntimeV2()", text)
        self.assertIn("if dry:", text)
        self.assertIn("return dry_run(config, design)", text)

    def test_failed_run_one_is_preserved_as_technical_stop(self):
        evidence = json.loads(FAILED_EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(evidence["run_id"], 32922438033)
        self.assertEqual(evidence["job_id"], 98038496960)
        self.assertEqual(
            evidence["artifact"]["digest"],
            "sha256:d3dc5aa897dea35e110e68e8bbe0afea01a6bedce9359219415de371d57f24ef",
        )
        self.assertEqual(evidence["qa"]["unit_test_passes"], 749)
        self.assertEqual(evidence["qa"]["historical_regression_passes"], 109)
        self.assertEqual(
            evidence["failure_classification"],
            "TECHNICAL_RUNTIME_COUNT_CONTRACT_STOP_NOT_DOMAIN_RESULT",
        )
        self.assertFalse(evidence["interpretation"]["siope_semantic_result_available"])
        self.assertFalse(evidence["safety"]["dynamic_candidate_network_sent"])
        self.assertFalse(evidence["safety"]["pilot_limeira_values_sent"])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_official_olinda_api_application_dom_navigation_match_distribution_diagnostics_review import (
    SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsReviewError,
    run_review,
)
from robo_dados_publicos.sources.siope_official_olinda_api_application_loaded_script_signature_diagnostics_design import (
    SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsDesignError,
    run_design,
)
from robo_dados_publicos.sources.siope_official_olinda_api_application_loaded_script_signature_diagnostics import (
    COUNT_FIELDS,
    SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError,
    _analyze_source_into_counts,
    _empty_counts,
    dry_run,
    run_loaded_script_signature_diagnostics,
    validate_config,
)

ROOT = Path(__file__).resolve().parents[1]
REVIEW_CONFIG_PATH = ROOT / "config/source_expansion.siope_official_olinda_api_application_dom_navigation_match_distribution_diagnostics_review.json"
DESIGN_CONFIG_PATH = ROOT / "config/source_expansion.siope_official_olinda_api_application_loaded_script_signature_diagnostics_design.json"
LIVE_CONFIG_PATH = ROOT / "config/source_expansion.siope_official_olinda_api_application_loaded_script_signature_diagnostics.json"
WORKFLOW_PATH = ROOT / ".github/workflows/siope-official-olinda-api-application-loaded-script-signature-diagnostics-gate.yml"
SOURCE_PATH = ROOT / "robo_dados_publicos/sources/siope_official_olinda_api_application_loaded_script_signature_diagnostics.py"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def review_result() -> dict:
    config = load(REVIEW_CONFIG_PATH)
    evidence = load(ROOT / config["evidence_path"])
    return run_review(config, evidence)


def design_result() -> dict:
    return run_design(load(DESIGN_CONFIG_PATH), review_result())


class FakeRuntime:
    def __init__(self, counts: dict, *, candidates: list | None = None):
        self.counts = counts
        self.candidates = candidates or []

    def run_probe(self, config: dict) -> dict:
        return {
            "initial_document_continued_count": 1,
            "static_assets_continued_count": 23,
            "local_requests_continued_count": 0,
            "application_surface_verified": True,
            "fragment_present": True,
            "loaded_script_signature_counts": self.counts,
            "blocked_shapes": [
                {
                    "candidate_dynamic_request": False,
                    "host": "www.fnde.gov.br",
                    "intercepted_before_network": True,
                    "method": "GET",
                    "network_sent": False,
                    "occurrences": 1,
                    "official_host": True,
                    "query_keys": [],
                    "query_present": False,
                    "resource_type": "Other",
                    "route_without_query": "https://www.fnde.gov.br/favicon.ico",
                    "scheme": "https",
                }
            ],
            "candidate_shapes": self.candidates,
            "browser_download_denied": True,
            "script_source_transient_read_performed": True,
        }


class TestM7SiopeOfficialOlindaLoadedScriptSignatureDiagnostics(unittest.TestCase):
    def test_pinned_navigation_distribution_review_passes_and_exhausts_href_track(self):
        result = review_result()
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_MATCH_DISTRIBUTION_DIAGNOSTICS_REVIEW")
        self.assertEqual(result["navigation_attribute_strategy_status"], "EXHAUSTED_FOR_RESOURCE_ROUTE_ON_PINNED_RUN")
        self.assertEqual(result["resource_route_contract_status"], "UNPROVEN")
        self.assertFalse(result["resource_get_authorized"])

    def test_tampered_navigation_distribution_evidence_fails_closed(self):
        config = load(REVIEW_CONFIG_PATH)
        evidence = load(ROOT / config["evidence_path"])
        tampered = copy.deepcopy(evidence)
        tampered["navigation_match_distribution_counts"]["query_present_match_count"] = 1
        with self.assertRaises(SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsReviewError):
            run_review(config, tampered)

    def test_design_passes_with_exact_known_public_identifiers_and_closed_operations(self):
        config = load(DESIGN_CONFIG_PATH)
        result = run_design(config, review_result())
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_SIGNATURE_DIAGNOSTICS_DESIGN")
        self.assertIn("Dados_Gerais_Siope", result["known_public_identifiers"])
        self.assertIn("_Dados_Gerais_Siope", result["known_public_identifiers"])
        self.assertFalse(result["new_script_network_request_authorized"])
        self.assertFalse(result["script_source_return_authorized"])
        self.assertFalse(result["script_source_persistence_authorized"])
        self.assertFalse(result["resource_get_authorized"])

    def test_design_rejects_relaxed_script_source_return(self):
        config = load(DESIGN_CONFIG_PATH)
        config["future_script_source_return"] = "ALLOWED"
        with self.assertRaises(SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsDesignError):
            run_design(config, review_result())

    def test_exact_callable_boundary_does_not_confuse_leading_underscore_name(self):
        config = load(LIVE_CONFIG_PATH)
        counts = _empty_counts()
        counts["parsed_script_count"] = 1
        counts["source_read_count"] = 1
        _analyze_source_into_counts("const x='_Dados_Gerais_Siope';", config, counts)
        self.assertEqual(counts["service_document_name_script_count"], 1)
        self.assertEqual(counts["callable_name_script_count"], 0)
        self.assertEqual(counts["callable_occurrence_count"], 0)

    def test_synthetic_callable_contract_counts_only_known_relations(self):
        config = load(LIVE_CONFIG_PATH)
        counts = _empty_counts()
        counts["parsed_script_count"] = 1
        counts["source_read_count"] = 1
        source = "const u='/odata/Dados_Gerais_Siope(Ano_Consulta=@Ano_Consulta,Num_Peri=@Num_Peri,Sig_UF=@Sig_UF)?@Ano_Consulta=x&@Num_Peri=y&@Sig_UF=z&$format=json';"
        _analyze_source_into_counts(source, config, counts)
        self.assertEqual(counts["callable_occurrence_count"], 1)
        self.assertEqual(counts["callable_name_script_count"], 1)
        self.assertEqual(counts["callable_open_parenthesis_window_count"], 1)
        self.assertEqual(counts["all_parameter_names_window_count"], 1)
        self.assertEqual(counts["all_at_parameter_names_window_count"], 1)
        self.assertEqual(counts["ordered_callable_parameter_sequence_window_count"], 1)
        self.assertEqual(counts["odata_literal_window_count"], 1)
        self.assertEqual(counts["format_token_window_count"], 1)
        self.assertEqual(counts["query_marker_window_count"], 1)
        self.assertEqual(counts["contract_like_window_count"], 1)

    def test_dry_run_has_no_network_source_read_or_authorization(self):
        result = dry_run(load(LIVE_CONFIG_PATH), design_result())
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_SIGNATURE_DIAGNOSTICS_DRY_RUN")
        self.assertFalse(result["network_called"])
        self.assertFalse(result["script_source_transient_read_performed"])
        self.assertFalse(result["script_source_returned"])
        self.assertFalse(result["resource_get_authorized"])

    def test_valid_bounded_fake_runtime_passes_without_route_promotion(self):
        config = load(LIVE_CONFIG_PATH)
        counts = _empty_counts()
        counts.update({
            "parsed_script_count": 4,
            "source_read_count": 4,
            "source_read_failure_count": 0,
            "callable_occurrence_count": 2,
            "callable_name_script_count": 1,
            "service_document_name_script_count": 0,
            "both_names_same_script_count": 0,
            "callable_open_parenthesis_window_count": 1,
            "all_parameter_names_window_count": 1,
            "all_at_parameter_names_window_count": 1,
            "ordered_callable_parameter_sequence_window_count": 1,
            "odata_literal_window_count": 1,
            "format_token_window_count": 1,
            "query_marker_window_count": 1,
            "contract_like_window_count": 1,
        })
        result = run_loaded_script_signature_diagnostics(config, design_result(), runtime=FakeRuntime(counts))
        self.assertEqual(result["loaded_script_signature_counts"], counts)
        self.assertTrue(result["script_source_transient_read_performed"])
        self.assertFalse(result["script_source_returned"])
        self.assertFalse(result["script_source_persisted"])
        self.assertFalse(result["route_synthesized_or_guessed"])
        self.assertFalse(result["automatic_route_promotion"])
        self.assertFalse(result["resource_get_authorized"])

    def test_extra_count_field_and_overflow_fail_closed(self):
        config = load(LIVE_CONFIG_PATH)
        counts = _empty_counts()
        counts["parsed_script_count"] = 1
        counts["source_read_count"] = 1
        extra = dict(counts)
        extra["raw_source"] = 1
        with self.assertRaises(SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError):
            run_loaded_script_signature_diagnostics(config, design_result(), runtime=FakeRuntime(extra))
        overflow = dict(counts)
        overflow["parsed_script_count"] = 129
        overflow["source_read_count"] = 129
        with self.assertRaises(SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError):
            run_loaded_script_signature_diagnostics(config, design_result(), runtime=FakeRuntime(overflow))

    def test_unexpected_dynamic_candidate_fails_closed_before_any_promotion(self):
        config = load(LIVE_CONFIG_PATH)
        counts = _empty_counts()
        counts["parsed_script_count"] = 1
        counts["source_read_count"] = 1
        candidate = [{"network_sent": False, "candidate_dynamic_request": True}]
        with self.assertRaises(SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError):
            run_loaded_script_signature_diagnostics(config, design_result(), runtime=FakeRuntime(counts, candidates=candidate))

    def test_runtime_source_uses_debugger_loaded_source_but_never_returns_raw_material(self):
        text = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn('Debugger.getScriptSource', text)
        self.assertIn('Debugger.scriptParsed', text)
        self.assertNotIn('print(source)', text)
        self.assertNotIn('write_text(source', text)
        self.assertIn('"script_source_returned": False', text)
        self.assertIn('"script_url_returned": False', text)
        self.assertIn('"source_snippet_returned": False', text)

    def test_workflow_is_manual_read_only_full_qa_and_sanitized(self):
        text = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("confirm_official_olinda_application_loaded_script_signature_diagnostics", text)
        self.assertIn("permissions:\n  contents: read", text)
        self.assertNotIn("schedule:", text)
        self.assertNotIn("push:", text)
        self.assertNotIn("curl ", text)
        self.assertNotIn("wget ", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("python main.py selftest", text)
        live = text.index("--output siope-official-olinda-application-loaded-script-signature-diagnostics-evidence/result.json")
        self.assertLess(text.index("python -m unittest discover -s tests -v"), live)
        self.assertLess(text.index("python main.py selftest"), live)
        self.assertIn("actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02", text)
        self.assertIn("if: ${{ steps.live.outcome == 'failure' }}", text)

    def test_live_config_keeps_every_operational_switch_closed(self):
        config = load(LIVE_CONFIG_PATH)
        validate_config(config, design_result())
        self.assertEqual(config["script_source_transient_read"], "ALLOWED_EPHEMERAL_MEMORY_ONLY_AFTER_SCRIPT_ALREADY_LOADED")
        for key in (
            "new_script_network_request", "script_source_return", "script_source_persistence", "script_url_return", "script_id_return",
            "source_snippet_return", "source_offset_return", "dynamic_candidate_network_send", "resource_data_request", "pilot_limeira_values_send",
            "dom_interaction", "navigation_execution", "form_submission", "post_request_send", "head_request", "authentication", "artifact_download",
            "remote_writes", "route_synthesis_or_guessing", "automatic_route_promotion",
        ):
            self.assertEqual(config[key], "PROHIBITED", key)
        self.assertEqual(set(config["returned_count_fields"]), set(COUNT_FIELDS))


if __name__ == "__main__":
    unittest.main()

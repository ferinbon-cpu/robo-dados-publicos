from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_official_olinda_api_application_loaded_script_global_relation_diagnostics_review import (
    SiopeOfficialOlindaApiApplicationLoadedScriptGlobalRelationDiagnosticsReviewError,
    run_review,
)
from robo_dados_publicos.sources.siope_official_olinda_api_application_loaded_script_locality_diagnostics_design import run_design
from robo_dados_publicos.sources.siope_official_olinda_api_application_loaded_script_locality_diagnostics import (
    COUNT_FIELDS,
    RADII,
    SiopeOfficialOlindaApiApplicationLoadedScriptLocalityDiagnosticsError,
    _analyze_source_into_counts,
    _empty_counts,
    dry_run,
    run_locality_diagnostics,
)

ROOT = Path(__file__).resolve().parents[1]
GLOBAL_REVIEW_CONFIG_PATH = ROOT / "config/source_expansion.siope_official_olinda_api_application_loaded_script_global_relation_diagnostics_review.json"
DESIGN_CONFIG_PATH = ROOT / "config/source_expansion.siope_official_olinda_api_application_loaded_script_locality_diagnostics_design.json"
LIVE_CONFIG_PATH = ROOT / "config/source_expansion.siope_official_olinda_api_application_loaded_script_locality_diagnostics.json"
WORKFLOW_PATH = ROOT / ".github/workflows/siope-official-olinda-api-application-loaded-script-locality-diagnostics-gate.yml"
SOURCE_PATH = ROOT / "robo_dados_publicos/sources/siope_official_olinda_api_application_loaded_script_locality_diagnostics.py"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def global_review_result() -> dict:
    config = load(GLOBAL_REVIEW_CONFIG_PATH)
    evidence_path = ROOT / config["evidence_path"]
    return run_review(config, load(evidence_path), evidence_path=evidence_path)


def design_result() -> dict:
    return run_design(load(DESIGN_CONFIG_PATH), global_review_result())


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
            "blocked_shapes": [{
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
            }],
            "candidate_shapes": self.candidates,
            "browser_download_denied": True,
            "script_source_transient_read_performed": True,
        }


class TestM7SiopeOfficialOlindaLoadedScriptLocalityDiagnostics(unittest.TestCase):
    def test_pinned_global_relation_review_passes_and_keeps_route_unproven(self):
        result = global_review_result()
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_GLOBAL_RELATION_DIAGNOSTICS_REVIEW")
        self.assertEqual(result["combined_contract_token_status"], "PROVEN_ONE_CALLABLE_SCRIPT_CONTAINS_ALL_PARAMETER_NAMES_ODATA_AND_FORMAT")
        self.assertEqual(result["same_scope_or_expression_status"], "UNPROVEN_SAME_SCRIPT_COLOCATION_ONLY")
        self.assertEqual(result["resource_route_contract_status"], "UNPROVEN")
        self.assertFalse(result["resource_get_authorized"])

    def test_tampered_global_relation_evidence_fails_closed(self):
        config = load(GLOBAL_REVIEW_CONFIG_PATH)
        evidence_path = ROOT / config["evidence_path"]
        evidence = load(evidence_path)
        tampered = copy.deepcopy(evidence)
        tampered["loaded_script_global_relation_counts"]["callable_and_all_at_parameter_names_same_script_count"] = 1
        with self.assertRaises(SiopeOfficialOlindaApiApplicationLoadedScriptGlobalRelationDiagnosticsReviewError):
            run_review(config, tampered, evidence_path=evidence_path)

    def test_design_passes_with_expanding_windows_and_closed_operations(self):
        result = design_result()
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_LOCALITY_DIAGNOSTICS_DESIGN")
        self.assertEqual(result["window_radii_chars"], RADII)
        self.assertEqual(len(result["returned_observations"]), 33)
        self.assertEqual(result["returned_observations"], COUNT_FIELDS)
        self.assertFalse(result["script_source_return_authorized"])
        self.assertFalse(result["new_script_network_request_authorized"])
        self.assertFalse(result["resource_get_authorized"])

    def test_expanding_windows_measure_locality_without_returning_material(self):
        config = load(LIVE_CONFIG_PATH)
        counts = _empty_counts()
        counts["parsed_script_count"] = 1
        counts["source_read_count"] = 1
        near = "const resource='Dados_Gerais_Siope'; const params=['Ano_Consulta','Num_Peri','Sig_UF'];"
        source = near + ("x" * 2500) + "const base='/odata/'; const fmt='$format';"
        _analyze_source_into_counts(source, config, counts)
        self.assertEqual(counts["callable_occurrence_count"], 1)
        self.assertEqual(counts["callable_exact_string_literal_occurrence_count"], 1)
        self.assertEqual(counts["all_parameter_names_window_1024_count"], 1)
        self.assertEqual(counts["all_parameter_exact_string_literals_window_1024_count"], 1)
        self.assertEqual(counts["odata_literal_window_1024_count"], 0)
        self.assertEqual(counts["format_token_window_1024_count"], 0)
        self.assertEqual(counts["all_parameter_names_odata_format_window_1024_count"], 0)
        self.assertEqual(counts["odata_literal_window_4096_count"], 1)
        self.assertEqual(counts["format_token_window_4096_count"], 1)
        self.assertEqual(counts["all_parameter_names_odata_format_window_4096_count"], 1)
        self.assertEqual(counts["all_parameter_exact_string_literals_odata_format_window_4096_count"], 1)
        self.assertEqual(counts["all_at_parameter_names_odata_format_window_4096_count"], 0)

    def test_dry_run_has_zero_network_and_no_authorization(self):
        result = dry_run(load(LIVE_CONFIG_PATH), design_result())
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_LOCALITY_DIAGNOSTICS_DRY_RUN")
        self.assertFalse(result["network_called"])
        self.assertFalse(result["script_source_transient_read_performed"])
        self.assertFalse(result["resource_get_authorized"])

    def test_valid_fake_runtime_passes_and_keeps_route_closed(self):
        config = load(LIVE_CONFIG_PATH)
        counts = _empty_counts()
        counts["parsed_script_count"] = 1
        counts["source_read_count"] = 1
        source = "const resource='Dados_Gerais_Siope'; const params=['Ano_Consulta','Num_Peri','Sig_UF']; const base='/odata/'; const fmt='$format';"
        _analyze_source_into_counts(source, config, counts)
        result = run_locality_diagnostics(config, design_result(), runtime=FakeRuntime(counts))
        self.assertEqual(result["loaded_script_locality_counts"], counts)
        self.assertEqual(result["window_radii_chars"], RADII)
        self.assertTrue(result["script_source_transient_read_performed"])
        self.assertFalse(result["script_source_returned"])
        self.assertFalse(result["route_synthesized_or_guessed"])
        self.assertFalse(result["resource_get_authorized"])

    def test_nonmonotonic_extra_count_or_candidate_fails_closed(self):
        config = load(LIVE_CONFIG_PATH)
        counts = _empty_counts()
        counts["parsed_script_count"] = 1
        counts["source_read_count"] = 1
        counts["callable_occurrence_count"] = 1
        counts["all_parameter_names_window_1024_count"] = 1
        counts["all_parameter_names_window_4096_count"] = 0
        with self.assertRaises(SiopeOfficialOlindaApiApplicationLoadedScriptLocalityDiagnosticsError):
            run_locality_diagnostics(config, design_result(), runtime=FakeRuntime(counts))
        extra = _empty_counts()
        extra["parsed_script_count"] = 1
        extra["source_read_count"] = 1
        extra["raw_source"] = 1
        with self.assertRaises(SiopeOfficialOlindaApiApplicationLoadedScriptLocalityDiagnosticsError):
            run_locality_diagnostics(config, design_result(), runtime=FakeRuntime(extra))
        valid = _empty_counts()
        valid["parsed_script_count"] = 1
        valid["source_read_count"] = 1
        with self.assertRaises(SiopeOfficialOlindaApiApplicationLoadedScriptLocalityDiagnosticsError):
            run_locality_diagnostics(config, design_result(), runtime=FakeRuntime(valid, candidates=[{"network_sent": False, "candidate_dynamic_request": True}]))

    def test_source_reuses_base_runtime_and_restores_analyzer(self):
        text = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("base.SystemChromeCdpLoadedScriptSignatureRuntime", text)
        self.assertIn("original_empty = base._empty_counts", text)
        self.assertIn("finally:", text)
        self.assertIn("base._empty_counts = original_empty", text)
        self.assertIn("base._analyze_source_into_counts = original_analyze", text)
        self.assertNotIn("print(source)", text)
        self.assertNotIn("write_text(source", text)

    def test_workflow_is_manual_read_only_full_qa_and_sanitized(self):
        text = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("confirm_official_olinda_application_loaded_script_locality_diagnostics", text)
        self.assertIn("permissions:\n  contents: read", text)
        self.assertNotIn("schedule:", text)
        self.assertNotIn("push:", text)
        self.assertNotIn("curl ", text)
        self.assertNotIn("wget ", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("python main.py selftest", text)
        live = text.index("--output siope-official-olinda-application-loaded-script-locality-diagnostics-evidence/result.json")
        self.assertLess(text.index("python -m unittest discover -s tests -v"), live)
        self.assertLess(text.index("python main.py selftest"), live)
        self.assertIn("actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02", text)
        self.assertIn("if: ${{ steps.live.outcome == 'failure' }}", text)

    def test_live_config_is_exact_nonpilot_and_all_switches_closed(self):
        config = load(LIVE_CONFIG_PATH)
        self.assertEqual(config["exact_application_url"], "https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/aplicacao")
        self.assertNotIn("352690", config["exact_application_url"])
        self.assertEqual(config["window_radii_chars"], RADII)
        self.assertEqual(config["returned_count_fields"], COUNT_FIELDS)
        for key in (
            "new_script_network_request", "script_source_return", "script_source_persistence", "script_url_return",
            "script_id_return", "source_snippet_return", "source_offset_return", "dynamic_candidate_network_send",
            "resource_data_request", "pilot_limeira_values_send", "dom_interaction", "navigation_execution",
            "form_submission", "post_request_send", "head_request", "authentication", "artifact_download",
            "remote_writes", "route_synthesis_or_guessing", "automatic_route_promotion",
        ):
            self.assertEqual(config[key], "PROHIBITED", key)
        for key in ("resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled"):
            self.assertFalse(config[key], key)


if __name__ == "__main__":
    unittest.main()

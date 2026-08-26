from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_official_olinda_api_application_loaded_script_signature_diagnostics_review import (
    SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsReviewError,
    run_review,
)
from robo_dados_publicos.sources.siope_official_olinda_api_application_loaded_script_global_relation_diagnostics_design import run_design
from robo_dados_publicos.sources.siope_official_olinda_api_application_loaded_script_global_relation_diagnostics import (
    COUNT_FIELDS,
    SiopeOfficialOlindaApiApplicationLoadedScriptGlobalRelationDiagnosticsError,
    _analyze_source_into_counts,
    _empty_counts,
    dry_run,
    run_global_relation_diagnostics,
)

ROOT = Path(__file__).resolve().parents[1]
REVIEW_CONFIG_PATH = ROOT / "config/source_expansion.siope_official_olinda_api_application_loaded_script_signature_diagnostics_review.json"
DESIGN_CONFIG_PATH = ROOT / "config/source_expansion.siope_official_olinda_api_application_loaded_script_global_relation_diagnostics_design.json"
LIVE_CONFIG_PATH = ROOT / "config/source_expansion.siope_official_olinda_api_application_loaded_script_global_relation_diagnostics.json"
WORKFLOW_PATH = ROOT / ".github/workflows/siope-official-olinda-api-application-loaded-script-global-relation-diagnostics-gate.yml"
SOURCE_PATH = ROOT / "robo_dados_publicos/sources/siope_official_olinda_api_application_loaded_script_global_relation_diagnostics.py"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def review_result() -> dict:
    config = load(REVIEW_CONFIG_PATH)
    evidence_path = ROOT / config["evidence_path"]
    return run_review(config, load(evidence_path), evidence_path=evidence_path)


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


class TestM7SiopeOfficialOlindaLoadedScriptGlobalRelationDiagnostics(unittest.TestCase):
    def test_pinned_loaded_script_review_passes_and_keeps_route_unproven(self):
        result = review_result()
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_SIGNATURE_DIAGNOSTICS_REVIEW")
        self.assertEqual(result["technical_callable_presence_status"], "PROVEN_TWO_SCRIPTS_FOUR_OCCURRENCES_ON_PINNED_RUN")
        self.assertEqual(result["local_executable_contract_status"], "NOT_OBSERVED_NO_PAREN_QUERY_AT_PARAMS_ODATA_OR_FORMAT_TOKEN")
        self.assertEqual(result["resource_route_contract_status"], "UNPROVEN")
        self.assertFalse(result["resource_get_authorized"])

    def test_tampered_pinned_evidence_fails_closed(self):
        config = load(REVIEW_CONFIG_PATH)
        evidence_path = ROOT / config["evidence_path"]
        evidence = load(evidence_path)
        tampered = copy.deepcopy(evidence)
        tampered["loaded_script_signature_counts"]["odata_literal_window_count"] = 1
        with self.assertRaises(SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsReviewError):
            run_review(config, tampered, evidence_path=evidence_path)

    def test_design_passes_with_sixteen_counts_and_closed_operations(self):
        result = design_result()
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_GLOBAL_RELATION_DIAGNOSTICS_DESIGN")
        self.assertEqual(len(result["returned_observations"]), 16)
        self.assertFalse(result["script_source_return_authorized"])
        self.assertFalse(result["new_script_network_request_authorized"])
        self.assertFalse(result["resource_get_authorized"])

    def test_exact_callable_boundary_does_not_confuse_leading_underscore(self):
        config = load(LIVE_CONFIG_PATH)
        counts = _empty_counts()
        counts["parsed_script_count"] = 1
        counts["source_read_count"] = 1
        _analyze_source_into_counts("const x='_Dados_Gerais_Siope';", config, counts)
        self.assertEqual(counts["service_document_name_script_count"], 1)
        self.assertEqual(counts["callable_name_script_count"], 0)
        self.assertEqual(counts["callable_occurrence_count"], 0)

    def test_synthetic_whole_script_contract_relations_are_counted_without_material_return(self):
        config = load(LIVE_CONFIG_PATH)
        counts = _empty_counts()
        counts["parsed_script_count"] = 1
        counts["source_read_count"] = 1
        source = "const resource='Dados_Gerais_Siope'; const params=['Ano_Consulta','Num_Peri','Sig_UF']; const aliases='@Ano_Consulta @Num_Peri @Sig_UF'; const base='/odata/'; const fmt='$format';"
        _analyze_source_into_counts(source, config, counts)
        self.assertEqual(counts["callable_occurrence_count"], 1)
        self.assertEqual(counts["callable_exact_string_literal_occurrence_count"], 1)
        self.assertEqual(counts["callable_name_script_count"], 1)
        self.assertEqual(counts["callable_and_all_parameter_names_same_script_count"], 1)
        self.assertEqual(counts["callable_and_all_parameter_exact_string_literals_same_script_count"], 1)
        self.assertEqual(counts["callable_and_all_at_parameter_names_same_script_count"], 1)
        self.assertEqual(counts["callable_and_odata_literal_same_script_count"], 1)
        self.assertEqual(counts["callable_and_format_token_same_script_count"], 1)
        self.assertEqual(counts["callable_and_odata_and_format_same_script_count"], 1)
        self.assertEqual(counts["callable_and_all_parameter_names_and_odata_and_format_same_script_count"], 1)
        self.assertEqual(counts["callable_and_all_at_params_and_odata_and_format_same_script_count"], 1)

    def test_dry_run_has_zero_network_and_no_authorization(self):
        result = dry_run(load(LIVE_CONFIG_PATH), design_result())
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_GLOBAL_RELATION_DIAGNOSTICS_DRY_RUN")
        self.assertFalse(result["network_called"])
        self.assertFalse(result["script_source_transient_read_performed"])
        self.assertFalse(result["resource_get_authorized"])

    def test_valid_fake_runtime_passes_and_keeps_route_closed(self):
        config = load(LIVE_CONFIG_PATH)
        counts = _empty_counts()
        counts.update({
            "parsed_script_count": 4,
            "source_read_count": 4,
            "source_read_failure_count": 0,
            "callable_occurrence_count": 2,
            "callable_exact_string_literal_occurrence_count": 2,
            "callable_name_script_count": 1,
            "service_document_name_script_count": 0,
            "both_names_same_script_count": 0,
            "callable_and_all_parameter_names_same_script_count": 1,
            "callable_and_all_parameter_exact_string_literals_same_script_count": 1,
            "callable_and_all_at_parameter_names_same_script_count": 0,
            "callable_and_odata_literal_same_script_count": 0,
            "callable_and_format_token_same_script_count": 0,
            "callable_and_odata_and_format_same_script_count": 0,
            "callable_and_all_parameter_names_and_odata_and_format_same_script_count": 0,
            "callable_and_all_at_params_and_odata_and_format_same_script_count": 0,
        })
        result = run_global_relation_diagnostics(config, design_result(), runtime=FakeRuntime(counts))
        self.assertEqual(result["loaded_script_global_relation_counts"], counts)
        self.assertTrue(result["script_source_transient_read_performed"])
        self.assertFalse(result["script_source_returned"])
        self.assertFalse(result["route_synthesized_or_guessed"])
        self.assertFalse(result["resource_get_authorized"])

    def test_extra_count_or_dynamic_candidate_fails_closed(self):
        config = load(LIVE_CONFIG_PATH)
        counts = _empty_counts()
        counts["parsed_script_count"] = 1
        counts["source_read_count"] = 1
        extra = dict(counts)
        extra["raw_source"] = 1
        with self.assertRaises(SiopeOfficialOlindaApiApplicationLoadedScriptGlobalRelationDiagnosticsError):
            run_global_relation_diagnostics(config, design_result(), runtime=FakeRuntime(extra))
        with self.assertRaises(SiopeOfficialOlindaApiApplicationLoadedScriptGlobalRelationDiagnosticsError):
            run_global_relation_diagnostics(config, design_result(), runtime=FakeRuntime(counts, candidates=[{"network_sent": False, "candidate_dynamic_request": True}]))

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
        self.assertIn("confirm_official_olinda_application_loaded_script_global_relation_diagnostics", text)
        self.assertIn("permissions:\n  contents: read", text)
        self.assertNotIn("schedule:", text)
        self.assertNotIn("push:", text)
        self.assertNotIn("curl ", text)
        self.assertNotIn("wget ", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("python main.py selftest", text)
        live = text.index("--output siope-official-olinda-application-loaded-script-global-relation-diagnostics-evidence/result.json")
        self.assertLess(text.index("python -m unittest discover -s tests -v"), live)
        self.assertLess(text.index("python main.py selftest"), live)
        self.assertIn("actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02", text)
        self.assertIn("if: ${{ steps.live.outcome == 'failure' }}", text)

    def test_live_config_is_exact_nonpilot_and_all_switches_closed(self):
        config = load(LIVE_CONFIG_PATH)
        self.assertEqual(config["exact_application_url"], "https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/aplicacao")
        self.assertNotIn("352690", config["exact_application_url"])
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

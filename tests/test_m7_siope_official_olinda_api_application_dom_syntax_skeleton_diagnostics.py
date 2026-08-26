from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_official_olinda_api_application_loaded_script_syntax_skeleton_diagnostics_review import (
    SiopeOfficialOlindaApiApplicationLoadedScriptSyntaxSkeletonDiagnosticsReviewError,
    load_json as load_review_json,
    run_review,
)
from robo_dados_publicos.sources.siope_official_olinda_api_application_dom_syntax_skeleton_diagnostics_design import run_design
from robo_dados_publicos.sources.siope_official_olinda_api_application_dom_syntax_skeleton_diagnostics import (
    COUNT_FIELDS,
    SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError,
    _analyze_minimal_container_texts,
    dry_run,
    load_json,
    run_dom_syntax_skeleton_diagnostics,
)

ROOT = Path(__file__).resolve().parents[1]
REVIEW_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_loaded_script_syntax_skeleton_diagnostics_review.json"
DESIGN_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_dom_syntax_skeleton_diagnostics_design.json"
LIVE_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_dom_syntax_skeleton_diagnostics.json"
WORKFLOW = ROOT / ".github/workflows/siope-official-olinda-api-application-dom-syntax-skeleton-diagnostics-gate.yml"


def review_result():
    cfg = load_review_json(REVIEW_CONFIG)
    evidence_path = ROOT / cfg["evidence_path"]
    return run_review(cfg, load_review_json(evidence_path), evidence_path=evidence_path)


def design_result():
    return run_design(load_json(DESIGN_CONFIG), review_result())


class FakeRuntime:
    def __init__(self, counts=None, candidates=None):
        self.counts = counts
        self.candidates = candidates or []

    def run_probe(self, config):
        counts = self.counts or _analyze_minimal_container_texts([
            "Dados_Gerais_Siope(Ano_Consulta=@Ano_Consulta, Num_Peri=@Num_Peri, Sig_UF=@Sig_UF)?@Ano_Consulta=2024&@Num_Peri=6&@Sig_UF='SP'&$format=json"
        ], config)
        return {
            "application_surface_verified": True,
            "fragment_present": True,
            "dom_syntax_skeleton_counts": counts,
            "initial_document_continued_count": 1,
            "official_static_asset_network_sent_count": 23,
            "local_request_count": 0,
            "blocked_shapes": [{"network_sent": False, "candidate_dynamic_request": False}],
            "candidate_shapes": self.candidates,
            "browser_download_denied": True,
        }


class TestM7SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnostics(unittest.TestCase):
    def test_pinned_loaded_script_review_passes_and_exhausts_known_text_skeleton(self):
        result = review_result()
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_SYNTAX_SKELETON_DIAGNOSTICS_REVIEW")
        self.assertEqual(result["loaded_script_known_syntax_strategy_status"], "EXHAUSTED_FOR_THIS_KNOWN_TEXTUAL_SKELETON_ON_PINNED_RUN")
        self.assertEqual(result["resource_route_contract_status"], "UNPROVEN")

    def test_tampered_pinned_evidence_fails_closed(self):
        cfg = load_review_json(REVIEW_CONFIG)
        evidence = load_review_json(ROOT / cfg["evidence_path"])
        evidence["loaded_script_syntax_skeleton_counts"]["callable_open_paren_occurrence_count"] = 1
        with self.assertRaises(SiopeOfficialOlindaApiApplicationLoadedScriptSyntaxSkeletonDiagnosticsReviewError):
            run_review(cfg, evidence)

    def test_design_passes_with_exact_sixteen_counts_and_closed_operations(self):
        cfg = load_json(DESIGN_CONFIG)
        result = run_design(cfg, review_result())
        self.assertEqual(result["returned_observations"], COUNT_FIELDS)
        self.assertFalse(result["resource_get_authorized"])
        self.assertFalse(result["network_called"])

    def test_dry_run_has_zero_network_and_no_authorization(self):
        result = dry_run(load_json(LIVE_CONFIG), design_result())
        self.assertFalse(result["network_called"])
        self.assertFalse(result["dynamic_candidate_network_sent"])
        self.assertFalse(result["resource_get_authorized"])

    def test_full_known_signature_in_minimal_text_is_counted(self):
        cfg = load_json(LIVE_CONFIG)
        counts = _analyze_minimal_container_texts([
            "Dados_Gerais_Siope(Ano_Consulta=@Ano_Consulta,Num_Peri=@Num_Peri,Sig_UF=@Sig_UF)?@Ano_Consulta=2023&@Num_Peri=6&@Sig_UF='PE'&$format=json"
        ], cfg)
        self.assertEqual(counts["minimal_contract_container_count"], 1)
        self.assertEqual(counts["callable_occurrence_in_minimal_container_count"], 1)
        self.assertEqual(counts["callable_full_known_signature_skeleton_4096_in_minimal_container_count"], 1)

    def test_metadata_only_text_does_not_become_executable_skeleton(self):
        cfg = load_json(LIVE_CONFIG)
        counts = _analyze_minimal_container_texts([
            "Dados_Gerais_Siope Ano_Consulta Num_Peri Sig_UF documentação de parâmetros"
        ], cfg)
        self.assertEqual(counts["callable_occurrence_in_minimal_container_count"], 1)
        self.assertEqual(counts["callable_ordered_parameter_names_512_in_minimal_container_count"], 1)
        self.assertEqual(counts["callable_open_paren_in_minimal_container_count"], 0)
        self.assertEqual(counts["callable_full_known_signature_skeleton_4096_in_minimal_container_count"], 0)

    def test_valid_fake_runtime_passes_without_route_promotion(self):
        result = run_dom_syntax_skeleton_diagnostics(load_json(LIVE_CONFIG), design_result(), runtime=FakeRuntime())
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SYNTAX_SKELETON_DIAGNOSTICS")
        self.assertEqual(result["candidate_shape_count"], 0)
        self.assertFalse(result["safety"]["route_synthesized_or_guessed"])
        self.assertFalse(result["safety"]["resource_get_authorized"])

    def test_invalid_extra_noninteger_or_subset_count_fails_closed(self):
        cfg = load_json(LIVE_CONFIG)
        valid = _analyze_minimal_container_texts(["Dados_Gerais_Siope Ano_Consulta Num_Peri Sig_UF"], cfg)
        variants = []
        extra = copy.deepcopy(valid); extra["raw_text"] = 1; variants.append(extra)
        nonint = copy.deepcopy(valid); nonint["minimal_contract_container_count"] = True; variants.append(nonint)
        subset = copy.deepcopy(valid); subset["callable_full_known_signature_skeleton_4096_in_minimal_container_count"] = 1; variants.append(subset)
        for counts in variants:
            with self.subTest(counts=counts):
                with self.assertRaises(SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError):
                    run_dom_syntax_skeleton_diagnostics(cfg, design_result(), runtime=FakeRuntime(counts=counts))

    def test_unexpected_dynamic_candidate_fails_closed(self):
        with self.assertRaises(SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError):
            run_dom_syntax_skeleton_diagnostics(load_json(LIVE_CONFIG), design_result(), runtime=FakeRuntime(candidates=[{"network_sent": False}]))

    def test_live_config_is_exact_nonpilot_and_operations_closed(self):
        cfg = load_json(LIVE_CONFIG)
        self.assertNotIn("352690", cfg["exact_application_url"])
        self.assertNotIn("Limeira", cfg["exact_application_url"])
        for key in ("dynamic_candidate_network_send", "resource_data_request", "dom_interaction", "navigation_execution", "post_request_send", "head_request", "route_synthesis_or_guessing"):
            self.assertEqual(cfg[key], "PROHIBITED")

    def test_workflow_is_manual_read_only_full_qa_and_sanitized(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertNotIn("schedule:", text)
        self.assertIn("contents: read", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("confirm_official_olinda_application_dom_syntax_skeleton_diagnostics", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("python main.py selftest", text)
        self.assertIn("siope-official-olinda-application-dom-syntax-skeleton-diagnostics-evidence/result.json", text)
        for forbidden in ("352690", "Limeira", "curl ", "wget ", "requests.get", "requests.post", "Page.click", "form.submit"):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()

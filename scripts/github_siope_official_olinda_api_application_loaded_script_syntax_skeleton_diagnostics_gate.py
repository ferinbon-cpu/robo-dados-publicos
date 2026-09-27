from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_official_olinda_api_application_loaded_script_locality_diagnostics_review import load_json as load_review_json, run_review
from robo_dados_publicos.sources.siope_official_olinda_api_application_loaded_script_syntax_skeleton_diagnostics_design import load_json as load_design_json, run_design
from robo_dados_publicos.sources.siope_official_olinda_api_application_loaded_script_syntax_skeleton_diagnostics import (
    SiopeOfficialOlindaApiApplicationLoadedScriptSyntaxSkeletonDiagnosticsError,
    dry_run,
    load_json,
    run_syntax_skeleton_diagnostics,
)

CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_loaded_script_syntax_skeleton_diagnostics.json"


def _write(path: str | None, result: dict) -> None:
    if not path:
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _design_result(config: dict) -> dict:
    design_config = load_design_json(ROOT / config["design_config_path"])
    review_config = load_review_json(ROOT / design_config["locality_review_config_path"])
    evidence_path = ROOT / review_config["evidence_path"]
    evidence = load_review_json(evidence_path)
    review = run_review(review_config, evidence, evidence_path=evidence_path)
    return run_design(design_config, review)


def run_gate(*, dry: bool = False) -> dict:
    config = load_json(CONFIG)
    design = _design_result(config)
    return dry_run(config, design) if dry else run_syntax_skeleton_diagnostics(config, design)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        result = run_gate(dry=args.dry_run)
        exit_code = 0
    except SiopeOfficialOlindaApiApplicationLoadedScriptSyntaxSkeletonDiagnosticsError as exc:
        result = {
            "status": "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_SYNTAX_SKELETON_DIAGNOSTICS",
            "error_code": str(exc),
            **exc.diagnostics,
            "dynamic_candidate_network_sent": False,
            "script_source_returned": False,
            "script_source_persisted": False,
            "script_url_returned": False,
            "script_id_returned": False,
            "source_snippet_returned": False,
            "source_offset_returned": False,
            "new_script_network_request_performed": False,
            "pilot_limeira_values_sent": False,
            "resource_data_request_performed": False,
            "dom_interaction_performed": False,
            "navigation_executed": False,
            "dom_text_returned": False,
            "fragment_value_returned": False,
            "html_returned": False,
            "response_body_persisted": False,
            "request_body_persisted": False,
            "query_values_persisted": False,
            "authentication_performed": False,
            "captcha_bypass": False,
            "credentials_captured": False,
            "cookies_captured": False,
            "artifact_downloaded": False,
            "remote_writes": "NONE",
            "route_synthesized_or_guessed": False,
            "automatic_route_promotion": False,
            "resource_get_authorized": False,
            "collection_authorized": False,
            "processing_authorized": False,
            "recurrence_authorized": False,
            "schedule_enabled": False,
        }
        exit_code = 1
    _write(args.output, result)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

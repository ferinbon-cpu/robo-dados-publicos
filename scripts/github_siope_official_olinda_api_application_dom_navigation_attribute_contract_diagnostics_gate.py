from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_official_olinda_api_application_dom_navigation_attribute_contract_diagnostics import (  # noqa: E402
    SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsError,
    dry_run,
    load_json,
    run_navigation_attribute_contract_diagnostics,
)
from scripts.github_siope_official_olinda_api_application_dom_navigation_attribute_contract_diagnostics_design_gate import run_gate as run_design_gate  # noqa: E402

CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_application_dom_navigation_attribute_contract_diagnostics.json"


def _write(path: str | None, result: dict) -> None:
    if not path:
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def run_gate(*, dry: bool = False) -> dict:
    config = load_json(CONFIG)
    design_result = run_design_gate()
    return dry_run(config, design_result) if dry else run_navigation_attribute_contract_diagnostics(config, design_result)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        result = run_gate(dry=args.dry_run)
        exit_code = 0
    except SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsError as exc:
        result = {
            "status": "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_ATTRIBUTE_CONTRACT_DIAGNOSTICS",
            "error_code": str(exc),
            **exc.diagnostics,
            "dynamic_candidate_network_sent": False,
            "pilot_limeira_values_sent": False,
            "resource_data_request_performed": False,
            "dom_interaction_performed": False,
            "navigation_executed": False,
            "navigation_attribute_value_returned": False,
            "navigation_path_returned": False,
            "navigation_query_returned": False,
            "navigation_fragment_returned": False,
            "element_material_returned": False,
            "tag_name_returned": False,
            "dom_text_returned": False,
            "fragment_value_returned": False,
            "html_returned": False,
            "script_source_returned": False,
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

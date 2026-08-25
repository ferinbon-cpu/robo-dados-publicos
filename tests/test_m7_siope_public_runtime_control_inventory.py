from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_public_runtime_control_inventory import (
    SiopePublicRuntimeControlInventoryError,
    inventory_public_runtime_controls,
    load_json,
    sanitize_control,
    validate_inventory_config,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_public_runtime_control_inventory_gate.json"


class FakeRuntime:
    def __init__(self, raw: dict):
        self.raw = raw

    def run_inventory(self, config: dict, public_config: dict) -> dict:
        return copy.deepcopy(self.raw)


def _raw(*, controls=None, blocked=None, challenge=False, interaction=False, truncated=False):
    controls = list(controls or [])
    return {
        "browser_binary_name": "google-chrome",
        "browser_version": "TEST",
        "page_surface_verified": True,
        "human_challenge_active_dom": challenge,
        "initial_document_continued_count": 1,
        "initial_document_network_sent": True,
        "static_assets_continued_count": 3,
        "local_requests_continued_count": 0,
        "blocked_requests": list(blocked or []),
        "browser_download_denied": True,
        "dom_interaction_performed": interaction,
        "form_submission": False,
        "navigation_after_initial_document": False,
        "dynamic_candidate_network_sent": False,
        "inventory_total_count": len(controls),
        "inventory_truncated": truncated,
        "raw_controls": controls,
    }


class TestM7SiopePublicRuntimeControlInventory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        cls.public_config = load_json(ROOT / cls.config["public_runtime_config_path"])
        cls.design_config = load_json(ROOT / cls.config["design_config_path"])

    def test_config_is_pinned_to_design_and_keeps_interaction_closed(self):
        validate_inventory_config(self.config, self.public_config, self.design_config)
        self.assertEqual(self.design_config["next_gate"], self.config["gate_id"])
        self.assertEqual(self.config["dom_interaction"], "PROHIBITED")
        self.assertEqual(self.config["control_identity_promotion"], "PROHIBITED")
        self.assertNotIn("352690", json.dumps(self.config, sort_keys=True))

    def test_sanitizer_ignores_values_text_html_and_unknown_fields(self):
        raw = {
            "associated_stable_label": "Planilha:",
            "tag_name": "select",
            "type": "select",
            "id": "planilha",
            "name": "planilha",
            "disabled": False,
            "option_count": 7,
            "form_method": "POST",
            "form_action_scheme": "https",
            "form_action_host": "www.fnde.gov.br",
            "form_action_path": "/siope/dadosInformadosMunicipio.do",
            "value": "SECRET_VALUE",
            "option_text": "SECRET_TEXT",
            "option_value": "SECRET_OPTION",
            "innerHTML": "SECRET_HTML",
        }
        clean = sanitize_control(raw, self.config)
        serialized = json.dumps(clean, sort_keys=True)
        for secret in ("SECRET_VALUE", "SECRET_TEXT", "SECRET_OPTION", "SECRET_HTML"):
            self.assertNotIn(secret, serialized)
        self.assertEqual(set(clean), set(self.config["allowed_persisted_fields"]))

    def test_pass_reports_structural_controls_without_promoting_identity(self):
        controls = [{
            "associated_stable_label": "UF:",
            "tag_name": "select",
            "type": "select",
            "id": "cod_uf",
            "name": "cod_uf",
            "disabled": False,
            "option_count": 28,
            "form_method": "GET",
            "form_action_scheme": "https",
            "form_action_host": "www.fnde.gov.br",
            "form_action_path": "/siope/dadosInformadosMunicipio.do",
        }]
        result = inventory_public_runtime_controls(
            self.config,
            self.public_config,
            self.design_config,
            runtime=FakeRuntime(_raw(controls=controls)),
        )
        self.assertEqual(result["status"], "PASS_M7_SIOPE_PUBLIC_RUNTIME_CONTROL_INVENTORY")
        self.assertEqual(result["control_count"], 1)
        self.assertEqual(result["associated_stable_label_control_count"], 1)
        self.assertFalse(result["control_identity_promoted"])
        self.assertFalse(result["dom_interaction_performed"])
        self.assertFalse(result["control_values_captured"])
        self.assertEqual(result["candidate_shape_count"], 0)

    def test_unexpected_same_host_xhr_stops_without_sending_it(self):
        blocked = [{
            "url": "https://www.fnde.gov.br/siope/dadosAjax.do?acao=SECRET",
            "method": "GET",
            "resource_type": "XHR",
        }]
        with self.assertRaisesRegex(SiopePublicRuntimeControlInventoryError, "UNEXPECTED_DYNAMIC_CANDIDATE") as ctx:
            inventory_public_runtime_controls(
                self.config,
                self.public_config,
                self.design_config,
                runtime=FakeRuntime(_raw(blocked=blocked)),
            )
        serialized = json.dumps(ctx.exception.diagnostics, sort_keys=True)
        self.assertNotIn("SECRET", serialized)
        self.assertIn("acao", serialized)
        self.assertIn('"network_sent": false', serialized)

    def test_any_dom_interaction_or_human_challenge_fails_closed(self):
        with self.assertRaisesRegex(SiopePublicRuntimeControlInventoryError, "DOM_INTERACTION"):
            inventory_public_runtime_controls(
                self.config, self.public_config, self.design_config, runtime=FakeRuntime(_raw(interaction=True))
            )
        with self.assertRaisesRegex(SiopePublicRuntimeControlInventoryError, "HUMAN_CHALLENGE_ACTIVE"):
            inventory_public_runtime_controls(
                self.config, self.public_config, self.design_config, runtime=FakeRuntime(_raw(challenge=True))
            )

    def test_control_limit_fails_closed(self):
        raw = _raw(controls=[], truncated=True)
        raw["inventory_total_count"] = self.config["max_controls"] + 1
        with self.assertRaisesRegex(SiopePublicRuntimeControlInventoryError, "CONTROL_LIMIT"):
            inventory_public_runtime_controls(
                self.config, self.public_config, self.design_config, runtime=FakeRuntime(raw)
            )

    def test_source_inventory_expression_has_no_value_option_text_html_or_interaction(self):
        source = (ROOT / "robo_dados_publicos" / "sources" / "siope_public_runtime_control_inventory.py").read_text(encoding="utf-8")
        for forbidden in (
            ".click(", "dispatchEvent", ".submit(", "requestSubmit", "getAttribute('value')",
            'getAttribute("value")', ".innerHTML", ".outerHTML", ".options[", ".selectedOptions",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn("el.options.length", source)
        self.assertIn("Fetch.failRequest", source)
        self.assertIn("Browser.setDownloadBehavior", source)

    def test_operational_authorizations_remain_closed(self):
        self.assertFalse(self.config["collection_authorized"])
        self.assertFalse(self.config["processing_authorized"])
        self.assertFalse(self.config["recurrence_authorized"])
        self.assertFalse(self.config["schedule_enabled"])
        for key in (
            "browser_download_or_install", "dom_interaction", "control_value_capture", "option_text_capture",
            "option_value_capture", "html_capture", "free_text_capture", "navigation_after_initial_document",
            "pilot_limeira_values_send", "dynamic_candidate_network_send", "form_submission", "captcha_bypass",
            "authentication", "credential_capture", "cookie_capture", "request_body_capture", "response_body_capture",
            "query_value_persistence", "head_request", "artifact_download", "remote_writes",
            "route_synthesis_or_guessing", "control_identity_promotion",
        ):
            self.assertEqual(self.config[key], "PROHIBITED")


if __name__ == "__main__":
    unittest.main()

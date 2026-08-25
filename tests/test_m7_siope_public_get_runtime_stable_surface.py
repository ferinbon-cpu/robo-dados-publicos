from __future__ import annotations

from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_public_get_runtime_cdp_direct import (
    RUNTIME_STABLE_SURFACE_MARKERS,
    _stable_surface_contract_matches,
)
from robo_dados_publicos.sources.siope_public_get_runtime_route_diagnostics import (
    load_public_get_runtime_route_diagnostics_config,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_public_get_runtime_route_diagnostics_gate.json"
SOURCE = ROOT / "robo_dados_publicos" / "sources" / "siope_public_get_runtime_cdp_direct.py"


class TestM7SiopePublicGetRuntimeStableSurface(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_public_get_runtime_route_diagnostics_config(CONFIG)

    def _state(self):
        return {
            "ready": "complete",
            "loadingA": False,
            "loadingB": False,
            "stableMarkers": [True, True, True, True],
            "challenge": False,
            "route": {
                "scheme": "https",
                "host": "www.fnde.gov.br",
                "path": "/siope/dadosInformadosMunicipio.do",
                "query_present": True,
                "query_keys": [
                    "acao",
                    "admin",
                    "cod_muni",
                    "cod_uf",
                    "num_ano",
                    "num_peri",
                    "pag",
                    "tp_relatorio",
                ],
            },
        }

    def test_stable_markers_are_ascii_and_specific(self):
        self.assertEqual(RUNTIME_STABLE_SURFACE_MARKERS, ("Exibir:", "Ano:", "UF:", "Planilha:"))
        for marker in RUNTIME_STABLE_SURFACE_MARKERS:
            marker.encode("ascii")

    def test_transient_loading_markers_are_not_required_for_runtime_surface(self):
        state = self._state()
        self.assertFalse(state["loadingA"])
        self.assertFalse(state["loadingB"])
        self.assertTrue(_stable_surface_contract_matches(state, self.config))

    def test_all_stable_markers_are_required(self):
        state = self._state()
        state["stableMarkers"][2] = False
        self.assertFalse(_stable_surface_contract_matches(state, self.config))

    def test_exact_final_route_contract_is_required(self):
        for key, bad_value in (
            ("scheme", "http"),
            ("host", "example.invalid"),
            ("path", "/siope/other.do"),
            ("query_present", False),
        ):
            state = self._state()
            state["route"][key] = bad_value
            self.assertFalse(_stable_surface_contract_matches(state, self.config))

        state = self._state()
        state["route"]["query_keys"] = state["route"]["query_keys"][:-1]
        self.assertFalse(_stable_surface_contract_matches(state, self.config))

    def test_runtime_keeps_network_policy_and_loading_markers_only_as_telemetry(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("_matches_exact_indexed_document", source)
        self.assertIn("_is_allowed_static_asset", source)
        self.assertIn("Fetch.failRequest", source)
        self.assertIn("loadingA:", source)
        self.assertIn("loadingB:", source)
        self.assertIn("_stable_surface_contract_matches(page_state, config)", source)
        self.assertNotIn('page_state.get("loadingA") and page_state.get("loadingB")', source)
        self.assertNotIn("Network.getResponseBody", source)
        self.assertNotIn("Fetch.getResponseBody", source)
        self.assertNotIn('request.get("postData"', source)


if __name__ == "__main__":
    unittest.main()

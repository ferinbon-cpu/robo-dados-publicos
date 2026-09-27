from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from robo_dados_publicos.sources.siope_artifact_download_event_diagnostics import (
    _connect_cdp_with_retry,
    _wait_browser_debug_version,
)
from robo_dados_publicos.sources.siope_export_runtime_route_probe import SiopeRuntimeRouteProbeError

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "robo_dados_publicos" / "sources" / "siope_artifact_download_event_diagnostics.py"


class FakeProcess:
    def poll(self):
        return None


class TestM7SiopeArtifactDownloadEventCdpReadiness(unittest.TestCase):
    def test_version_endpoint_retries_after_active_port_marker(self) -> None:
        good = {
            "webSocketDebuggerUrl": "ws://127.0.0.1:41234/devtools/browser/opaque-guid"
        }
        with patch(
            "robo_dados_publicos.sources.siope_artifact_download_event_diagnostics._local_json",
            side_effect=[OSError("not ready"), good],
        ) as mocked:
            result = _wait_browser_debug_version(41234, FakeProcess(), timeout_s=1.0)
        self.assertEqual(result, good)
        self.assertGreaterEqual(mocked.call_count, 2)

    def test_version_endpoint_rejects_wrong_host_or_port(self) -> None:
        bad = {
            "webSocketDebuggerUrl": "ws://example.invalid:9999/devtools/browser/opaque-guid"
        }
        with patch(
            "robo_dados_publicos.sources.siope_artifact_download_event_diagnostics._local_json",
            return_value=bad,
        ):
            with self.assertRaises(SiopeRuntimeRouteProbeError) as ctx:
                _wait_browser_debug_version(41234, FakeProcess(), timeout_s=0.02)
        self.assertEqual(str(ctx.exception), "STOP_SIOPE_ARTIFACT_DOWNLOAD_EVENT_DIAGNOSTICS_BROWSER_VERSION_ENDPOINT")

    def test_cdp_connect_retries_only_connect_race(self) -> None:
        transient = SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_CDP_CONNECT")
        sentinel = object()
        with patch(
            "robo_dados_publicos.sources.siope_artifact_download_event_diagnostics._CdpSession",
            side_effect=[transient, sentinel],
        ) as mocked:
            result = _connect_cdp_with_retry(
                "ws://127.0.0.1:41234/devtools/browser/opaque-guid",
                command_timeout_s=5.0,
                process=FakeProcess(),
                timeout_s=1.0,
            )
        self.assertIs(result, sentinel)
        self.assertEqual(mocked.call_count, 2)

    def test_non_connect_cdp_error_is_not_swallowed(self) -> None:
        fatal = SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_WEBSOCKET_DEPENDENCY")
        with patch(
            "robo_dados_publicos.sources.siope_artifact_download_event_diagnostics._CdpSession",
            side_effect=fatal,
        ):
            with self.assertRaises(SiopeRuntimeRouteProbeError) as ctx:
                _connect_cdp_with_retry(
                    "ws://127.0.0.1:41234/devtools/browser/opaque-guid",
                    command_timeout_s=5.0,
                    process=FakeProcess(),
                    timeout_s=0.2,
                )
        self.assertEqual(str(ctx.exception), "STOP_SIOPE_RUNTIME_ROUTE_PROBE_WEBSOCKET_DEPENDENCY")

    def test_source_uses_chrome_version_endpoint_and_keeps_download_denied(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('/json/version', source)
        self.assertIn('_connect_cdp_with_retry(', source)
        self.assertIn('"behavior": "deny"', source)
        self.assertNotIn('"behavior": "allow"', source)
        self.assertNotIn('f"ws://127.0.0.1:{port}{browser_ws_path}"', source)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from robo_dados_publicos.sources.siope_artifact_download_event_diagnostics import _read_devtools_active_port

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "robo_dados_publicos" / "sources" / "siope_artifact_download_event_diagnostics.py"


class TestM7SiopeArtifactDownloadEventCdpBootstrap(unittest.TestCase):
    def test_reads_valid_devtools_active_port_without_persisting_browser_guid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp)
            (profile / "DevToolsActivePort").write_text(
                "43123\n/devtools/browser/opaque-guid\n",
                encoding="utf-8",
            )
            self.assertEqual(
                _read_devtools_active_port(profile),
                (43123, "/devtools/browser/opaque-guid"),
            )

    def test_rejects_invalid_active_port_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp)
            marker = profile / "DevToolsActivePort"
            marker.write_text("0\n/devtools/browser/x\n", encoding="utf-8")
            self.assertIsNone(_read_devtools_active_port(profile))
            marker.write_text("43123\n/not-browser/x\n", encoding="utf-8")
            self.assertIsNone(_read_devtools_active_port(profile))

    def test_source_uses_chrome_assigned_port_and_keeps_download_denied(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('"--remote-debugging-port=0"', source)
        self.assertIn('DevToolsActivePort', source)
        self.assertNotIn('_free_local_port', source)
        self.assertIn('"behavior": "deny"', source)
        self.assertIn('"eventsEnabled": True', source)
        self.assertNotIn('"behavior": "allow"', source)


if __name__ == "__main__":
    unittest.main()

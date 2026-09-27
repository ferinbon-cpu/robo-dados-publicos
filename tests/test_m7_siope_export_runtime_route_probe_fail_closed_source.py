from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "robo_dados_publicos" / "sources" / "siope_export_runtime_route_probe.py"


class TestM7SiopeRuntimeRouteProbeFailClosedSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SOURCE.read_text(encoding="utf-8")

    def test_continue_request_exists_only_in_preclick_branch(self):
        marker = 'if phase["value"] == "PRE_CLICK":'
        self.assertIn(marker, self.text)
        pre_start = self.text.index(marker)
        post_start = self.text.index("post_click_aborted += 1", pre_start)
        post_end = self.text.index("page_session.event_handler = handle_event", post_start)
        post_block = self.text[post_start:post_end]
        self.assertIn('Fetch.failRequest', post_block)
        self.assertNotIn('Fetch.continueRequest', post_block)

    def test_browser_is_always_terminated_in_finally(self):
        self.assertIn("finally:", self.text)
        self.assertIn("process.terminate()", self.text)
        self.assertIn("process.kill()", self.text)

    def test_no_response_or_request_body_cdp_capture_commands(self):
        forbidden = (
            "Network.getResponseBody",
            "Fetch.getResponseBody",
            "Network.getRequestPostData",
            "Storage.getCookies",
            "Network.getAllCookies",
        )
        for item in forbidden:
            with self.subTest(item=item):
                self.assertNotIn(item, self.text)


if __name__ == "__main__":
    unittest.main()

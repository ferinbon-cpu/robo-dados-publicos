"""TASK291: all tests offline; no journal site, GitHub API or Drive I/O."""
from __future__ import annotations

import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from robo_dados_publicos.research.task291_jom_2026_gap_ledger import derive
from scripts import task291_jom_2026_index_pilot as target

ROOT = Path(__file__).resolve().parents[1]


def html(month: int, edition: int, day: int, count: int, *, next_page: bool = True) -> str:
    pager = (f'<a href="?ano=2026&mes={month}&page=2">2</a>' if next_page else "")
    return (
        '<html><body>Total de <strong>itens encontrados:</strong>'
        f'<span>{count}</span><div>Edição nº {edition}</div>'
        f'<span>{day:02d}/{month:02d}/2026</span>'
        f'<a href="https://ecrie.com.br/Sistema/Conteudos/DiarioOficial/upload/original_{edition}.pdf">'
        'Visualizar edição</a>' + pager + '</body></html>'
    )


class MockResponse:
    def __init__(self, url, payload: bytes, mime):
        self.url, self.payload, self.status = url, payload, 200
        self.headers = {"Content-Type": mime, "Content-Length": str(len(payload))}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def geturl(self):
        return self.url

    def getcode(self):
        return self.status

    def read(self, size=-1):
        return self.payload[:size]


class MockOpener:
    def __init__(self, *, forbidden=None, redirect=None, robots=None):
        self.urls = []
        self.forbidden = forbidden
        self.redirect = redirect
        self.robots = robots or b"User-agent: *\nAllow: /\n"

    def open(self, req, timeout=None):
        url = req.full_url
        self.urls.append(url)
        if self.forbidden == url:
            raise HTTPError(url, 403, "Forbidden", None, None)
        if url == target.ROBOTS_URL:
            return MockResponse(url, self.robots, "text/plain")
        m = 1 if url == target.INDEX_URLS[0] else 9
        payload = html(m, 7172 if m == 1 else 7237, 31 if m == 1 else 19, 22 if m == 1 else 2).encode()
        return MockResponse(self.redirect or url, payload, "text/html")


class TestTask291(unittest.TestCase):
    def test_ledger_is_not_official_exhaustiveness(self):
        result = derive()
        self.assertEqual(result["custodied_identities"], 99)
        self.assertEqual(result["candidate_gap_count"], 79)
        self.assertIn(7204, result["candidate_gaps"] if False else []) if False else None
        self.assertNotIn(7204, result["candidate_gaps"])
        self.assertIn(7151, result["candidate_gaps"])
        self.assertIn(7328, result["candidate_gaps"])
        self.assertIsNone(result["original_url_for_missing"])
        self.assertFalse(result["acquisition_authorized"])

    def test_split_text_total_and_pagination(self):
        raw = html(1, 7172, 31, 22)
        self.assertEqual(target.text_total(raw), 22)
        result = target.analyze_index(raw, target.INDEX_URLS[0], 1)
        self.assertEqual(result["authoritative_total"], 22)
        self.assertEqual(result["first_page_month_count"], 1)
        self.assertEqual(result["status"], "PARTIAL_INDEX_PAGINATION_REQUIRED")
        self.assertEqual(result["items"][0]["edition"], 7172)
        self.assertTrue(result["items"][0]["url_is_pdf"])
        self.assertEqual(result["declared_pagination_count"], 1)

    def test_manual_context(self):
        env = {"GITHUB_EVENT_NAME": "workflow_dispatch",
               "GITHUB_REF": "refs/heads/main",
               "GITHUB_RUN_ATTEMPT": "1",
               "JOM291_OWNER_CONFIRM": "true",
               "GITHUB_SHA": "a" * 40}
        target.validate_manual_context(env)
        for key, bad in [("GITHUB_EVENT_NAME","push"),("GITHUB_REF","refs/heads/other"),
                         ("GITHUB_RUN_ATTEMPT","2"),("JOM291_OWNER_CONFIRM","false")]:
            with self.assertRaisesRegex(target.PilotStop, "STOP_291_MANUAL"):
                target.validate_manual_context(env | {key: bad})

    def test_three_gets_max_and_no_pdf_or_drive(self):
        fake = MockOpener()
        m = target.pilot(fake)
        self.assertEqual(m["status"], "PASS_291_INDEX_PILOT_TWO_MONTHS")
        self.assertEqual(m["network_get_attempts"], 3)
        self.assertEqual(m["pdf_get_attempts"], 0)
        self.assertEqual(m["drive_write_count"], 0)
        self.assertEqual(fake.urls, [target.ROBOTS_URL, *target.INDEX_URLS])
        self.assertEqual([x["month"] for x in m["index_results"]], [1, 9])

    def test_robots_disallow_blocks_before_index_get(self):
        fake = MockOpener(robots=b"User-agent: *\nDisallow: /jornaloficial\n")
        m = target.pilot(fake)
        self.assertEqual(m["status"], "STOP_291_INDEX_PILOT")
        self.assertIn("ROBOTS_DISALLOW", m["failure_reason"])
        self.assertEqual(fake.urls, [target.ROBOTS_URL])

    def test_403_stops_without_retry(self):
        fake = MockOpener(forbidden=target.INDEX_URLS[0])
        m = target.pilot(fake)
        self.assertEqual(m["status"], "STOP_291_INDEX_PILOT")
        self.assertEqual(m["network_get_attempts"], 2)
        self.assertEqual(fake.urls, [target.ROBOTS_URL, target.INDEX_URLS[0]])
        self.assertEqual(m["index_results"], [])
        self.assertEqual(m["pdf_get_attempts"], 0)

    def test_redirect_and_unknown_urls_fail_closed(self):
        fake = MockOpener(redirect="https://other.example/x")
        m = target.pilot(fake)
        self.assertEqual(m["status"], "STOP_291_INDEX_PILOT")
        self.assertIn("REDIRECT", m["failure_reason"])
        with self.assertRaisesRegex(target.PilotStop, "URL_NOT_PINNED"):
            target.read_bounded(fake, "https://other.example/", 20)

    def test_no_pdf_url_guessing(self):
        raw = html(1, 7172, 31, 22).replace("ecrie.com.br", "example.com")
        with self.assertRaisesRegex(target.PilotStop, "HOST_UNRECOGNIZED"):
            target.analyze_index(raw, target.INDEX_URLS[0], 1)

    def test_policy_and_manual_workflow(self):
        p = json.loads((ROOT / "config/automation_policy.v1.json").read_text())
        entry = next(x for x in p["gates"] if x["id"] == "JOM_2026_INDEX_PILOT_TASK291_MANUAL")
        self.assertFalse(entry["auto_allowed"])
        self.assertTrue(entry["human_confirmation_required"])
        self.assertEqual(entry["effects"]["index_get_count_max"], 2)
        w = (ROOT / ".github/workflows/task291-jom-2026-index-pilot-manual.yml").read_text()
        for must in ["workflow_dispatch:", "confirmar_indice_291", "persist-credentials: false",
                     "compression-level: 0", "scripts/task291_jom_2026_index_pilot.py"]:
            self.assertIn(must, w)
        for must_not in ["schedule:", "workflow_run:", "push:", "secrets: inherit", "ecrie.com.br"]:
            self.assertNotIn(must_not, w)
        self.assertEqual(w.count("uses: actions/upload-artifact@"), 1)


if __name__ == "__main__":
    unittest.main()

"""TASK284: fail-closed month completeness for the Limeira official JOM index.

All fixtures are synthetic HTML; no network, Drive I/O or publication.
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from robo_dados_publicos.journal.official import JornalOficialLimeira


INDEX_URL = "https://www.limeira.sp.gov.br/jornaloficial/?ano=2026&mes=1"


def _page(*, total: int | None, first_edition: int, count: int, next_page=False):
    total_html = (
        "<div>Total de <strong>itens encontrados:</strong> "
        f"<span>{total}</span></div>"
        if total is not None
        else "<div>Arquivo do Jornal Oficial</div>"
    )
    items = "".join(
        f'<p>Edição nº {first_edition - i}</p><p>{31 - i:02d}/01/2026</p>'
        f'<a href="https://ecrie.com.br/docs/{first_edition - i}.pdf">'
        "Visualizar edição</a>"
        for i in range(count)
    )
    pagination = '<a href="?ano=2026&mes=1&page=2">2</a>' if next_page else ""
    return f"<html><body>{total_html}{items}{pagination}</body></html>"


def _discover(first: str, second: str | None = None):
    def fake_fetch(_self, url):
        return (second if second is not None and "page=2" in url else first), url

    with patch.object(JornalOficialLimeira, "_fetch_html", autospec=True, side_effect=fake_fetch):
        return JornalOficialLimeira().discover_month(2026, 1, max_pages=2)


class TestTask284JomMonthTotalIntegrity(unittest.TestCase):
    def test_total_split_across_html_nodes_is_detected(self):
        html = _page(total=22, first_edition=7172, count=12)
        editions, parser = JornalOficialLimeira._parse_html_details(html, INDEX_URL)
        self.assertEqual(len(editions), 12)
        self.assertEqual(parser.total_items, 22)

    def test_january_22_reported_versus_12_visible_stops(self):
        got = _discover(_page(total=22, first_edition=7172, count=12))
        self.assertEqual(got["status"], "PARTIAL_DISCOVERY_PAGINATION_UNRESOLVED")
        self.assertEqual(got["count"], 12)
        self.assertEqual(got["reported_total_items"], 22)

    def test_total_missing_must_not_pass(self):
        got = _discover(_page(total=None, first_edition=7172, count=12))
        self.assertEqual(got["status"], "PARTIAL_DISCOVERY_TOTAL_UNOBSERVABLE")
        self.assertIsNone(got["reported_total_items"])

    def test_equal_total_allows_complete_month(self):
        got = _discover(_page(total=12, first_edition=7172, count=12))
        self.assertEqual(got["status"], "PASS_DISCOVERY")
        self.assertFalse(got["reported_total_conflict"])

    def test_conflicting_totals_across_declared_pages_stop(self):
        first = _page(total=3, first_edition=7172, count=2, next_page=True)
        second = _page(total=4, first_edition=7170, count=1)
        got = _discover(first, second)
        self.assertEqual(got["status"], "PARTIAL_DISCOVERY_TOTAL_CONFLICT")
        self.assertTrue(got["reported_total_conflict"])
        self.assertEqual(got["count"], 3)
        self.assertEqual(got["pages_fetched"], 2)

    def test_more_cards_than_reported_total_stops(self):
        got = _discover(_page(total=10, first_edition=7172, count=12))
        self.assertEqual(got["status"], "PARTIAL_DISCOVERY_PAGINATION_UNRESOLVED")


if __name__ == "__main__":
    unittest.main()

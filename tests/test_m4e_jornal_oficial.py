import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from robo_dados_publicos.journal.official import JournalEdition, JournalIndexParser, JornalOficialLimeira


MODERN_HTML = '''<!doctype html><html><body>
<p>Total de itens encontrados: 3</p>
<h3>Edição nº 7309</h3><p>21/08/2026</p>
<a href="https://ecrie.example/upload/u_137_a.pdf">Visualizar edição</a>
<h3>Edição nº 7308</h3><p>20 de Agosto de 2026</p>
<a href="/docs/7308">Visualizar edição</a>
<a href="?ano=2026&mes=8&page=2">2</a>
</body></html>'''

LEGACY_HTML = '''<html><body>
<a href="/jornal/6411.pdf">Edição 6411 - Jornal Oficial - 25 de janeiro de 2023.pdf</a>
<a href="/jornal/6410.pdf">Edição 6410 - Jornal Oficial - 24 de janeiro de 2023.pdf</a>
</body></html>'''


MODERN_PAGE2 = '''<!doctype html><html><body><p>Total de itens encontrados: 3</p><h3>Edição nº 7307</h3><p>19/08/2026</p><a href="https://ecrie.example/upload/u_137_b.pdf">Visualizar edição</a></body></html>'''


class JournalHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/robots.txt':
            body=b'User-agent: *\nAllow: /\n'
            self.send_response(200); self.send_header('Content-Type','text/plain'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body); return
        if self.path.startswith('/jornaloficial'):
            body=(MODERN_PAGE2 if 'page=2' in self.path else MODERN_HTML).encode()
            self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body); return
        self.send_response(404); self.end_headers()
    def log_message(self,*args): pass


class TestJornalOficial(unittest.TestCase):
    def test_modern_parser_extracts_declared_document_routes_without_guessing(self):
        editions, links = JornalOficialLimeira.parse_html(MODERN_HTML, 'https://www.limeira.sp.gov.br/jornaloficial/?ano=2026&mes=8')
        self.assertEqual([7309,7308], [x.edition for x in editions])
        self.assertEqual('2026-08-21', editions[0].publication_date)
        self.assertTrue(editions[0].document_url.endswith('.pdf'))
        self.assertEqual('https://www.limeira.sp.gov.br/docs/7308', editions[1].document_url)
        self.assertFalse(editions[1].looks_like_pdf)
        self.assertTrue(any('page=2' in x for x in links))

    def test_legacy_parser_extracts_anchor_label(self):
        editions, _ = JornalOficialLimeira.parse_html(LEGACY_HTML, 'https://www.limeira.sp.gov.br/imprensa/jornal-oficial-anteriores-a-01022023', archive_class='legacy')
        self.assertEqual([6411,6410], [x.edition for x in editions])
        self.assertEqual('2023-01-25', editions[0].publication_date)
        self.assertEqual('legacy', editions[0].archive_class)

    def test_merge_overlap_dedupes_by_edition_preferring_pdf(self):
        a=JournalEdition(6411,'2023-01-25','https://example.org/view/6411','https://example.org/current','modern')
        b=JournalEdition(6411,'2023-01-25','https://example.org/6411.pdf','https://example.org/legacy','legacy')
        got=JornalOficialLimeira.merge_editions([a],[b])
        self.assertEqual(1,len(got)); self.assertTrue(got[0].looks_like_pdf)

    def test_generated_inventory_is_disabled_and_pdf_contracted(self):
        e=JournalEdition(7309,'2026-08-21','https://example.org/a.pdf','https://example.org/index','modern')
        inv=JornalOficialLimeira.emit_disabled_inventory([e])
        self.assertFalse(inv['sources'][0]['enabled'])
        self.assertEqual(['application/pdf'],inv['sources'][0]['expected_content_types'])
        self.assertEqual('LIMEIRA_JO_07309',inv['sources'][0]['source_id'])

    def test_month_url_matches_public_query_contract(self):
        self.assertEqual('https://www.limeira.sp.gov.br/jornaloficial/?ano=2026&mes=5', JornalOficialLimeira.modern_month_url(2026,5))
        with self.assertRaises(ValueError): JornalOficialLimeira.modern_month_url(2026,13)

    def test_live_style_discovery_respects_robots_and_emits_no_download(self):
        server=HTTPServer(('127.0.0.1',0),JournalHandler)
        th=threading.Thread(target=server.serve_forever,daemon=True); th.start()
        try:
            jo=JornalOficialLimeira(allow_insecure_localhost=True)
            url=f'http://127.0.0.1:{server.server_port}/jornaloficial/?ano=2026&mes=8'
            out=jo.discover_page(url)
            self.assertEqual('PARTIAL_DISCOVERY_PAGINATION_POSSIBLE',out['status'])
            self.assertEqual(2,out['count'])
            self.assertEqual(7309,out['editions'][0]['edition'])
        finally:
            server.shutdown(); server.server_close()

    def test_month_discovery_follows_declared_pagination_and_filters_recent_block(self):
        server=HTTPServer(('127.0.0.1',0),JournalHandler)
        th=threading.Thread(target=server.serve_forever,daemon=True); th.start()
        try:
            jo=JornalOficialLimeira(allow_insecure_localhost=True)
            previous=JornalOficialLimeira.MODERN_INDEX
            JornalOficialLimeira.MODERN_INDEX=f'http://127.0.0.1:{server.server_port}/jornaloficial'
            out=jo.discover_month(2026,8)
            JornalOficialLimeira.MODERN_INDEX=previous
            self.assertEqual('PASS_DISCOVERY',out['status'])
            self.assertEqual(3,out['count'])
            self.assertEqual(2,out['pages_fetched'])
            self.assertEqual([7309,7308,7307],[x['edition'] for x in out['editions']])
        finally:
            server.shutdown(); server.server_close()


if __name__ == '__main__': unittest.main()

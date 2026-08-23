import io
import json
import tempfile
import threading
import unittest
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from robo_dados_publicos.reconciliation.planner import ReconciliationPlanner
from robo_dados_publicos.reconciliation.resolvers import (
    LimeiraContractsResolver,
    ReconciliationExecutor,
    TcespExpenseResolver,
    _TableParser,
)
from robo_dados_publicos.state.registry import StateRegistry


def make_zip(csv_text: str, name: str = 'despesas.csv') -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(name, csv_text.encode('utf-8'))
    return buf.getvalue()


def tce_task(year=2026):
    return {
        'task_id': f'RECTASK_tce_{year}',
        'origin_event_id': 'JOEV_contract_001',
        'origin_source_id': 'LIMEIRA_JO_07309',
        'target_source': 'TCE_SP_DESPESAS',
        'task_type': 'FIND_EXPENSE_EVENTS_FOR_SUPPLIER',
        'status': 'READY_SEARCH',
        'priority': 90,
        'rationale': 'test',
        'match_keys': {
            'candidate_years': [year],
            'cnpj': '45132495000140',
            'contractor': 'JAIME FACHINELLI',
        },
        'search_hints': {},
        'minimum_link_confidence': 'A',
        'identity_rule': 'supplier alone does not prove contract',
    }


def contract_task():
    return {
        'task_id': 'RECTASK_contracts_2025',
        'origin_event_id': 'JOEV_contract_001',
        'origin_source_id': 'LIMEIRA_JO_07309',
        'target_source': 'LIMEIRA_CONTRATOS',
        'task_type': 'FIND_CONTRACT_RECORD',
        'status': 'READY_SEARCH',
        'priority': 100,
        'rationale': 'test',
        'match_keys': {
            'year': 2025,
            'contract_number': '51/2025',
            'cnpj': '61086929000170',
            'contractor': 'Consórcio Exemplo Ltda',
        },
        'search_hints': {'object_text': 'serviços especializados'},
        'minimum_link_confidence': 'A',
        'identity_rule': 'test',
    }


class ResolverHandler(BaseHTTPRequestHandler):
    tce_zip = make_zip(
        'orgao;mes;evento;nr_empenho;id_fornecedor;nm_fornecedor;dt_emissao_despesa;vl_despesa\n'
        'PREFEITURA MUNICIPAL DE LIMEIRA;Março;Empenhado;3351-2026;CNPJ - PESSOA JURÍDICA - 45132495000140;JAIME FACHINELLI;09/03/2026;259,67\n'
        'PREFEITURA MUNICIPAL DE LIMEIRA;Março;Valor Liquidado;3351-2026;CNPJ - PESSOA JURÍDICA - 45132495000140;JAIME FACHINELLI;13/03/2026;259,67\n'
        'PREFEITURA MUNICIPAL DE LIMEIRA;Março;Valor Pago;3351-2026;CNPJ - PESSOA JURÍDICA - 45132495000140;JAIME FACHINELLI;18/03/2026;259,67\n'
        'PREFEITURA MUNICIPAL DE LIMEIRA;Março;Empenhado;9999-2026;CNPJ - PESSOA JURÍDICA - 00000000000199;OUTRO FORNECEDOR;20/03/2026;10,00\n'
    )
    bad_zip = make_zip('foo;bar\n1;2\n')
    live_schema_zip = make_zip(
        'id_despesa_detalhe;ano_exercicio;ds_municipio;ds_orgao;mes_referencia;mes_ref_extenso;tp_despesa;nr_empenho;identificador_despesa;ds_despesa;dt_emissao_despesa;vl_despesa;historico_despesa\n'
        '1;2028;Limeira;PREFEITURA MUNICIPAL DE LIMEIRA;1;Janeiro;Empenhado;1390-2028;CNPJ - PESSOA JURÍDICA - 45132495000140;JAIME FACHINELLI;02/01/2028;48914,91;TESTE\n',
        'despesas-limeira-2028.csv',
    )
    hits = []

    def log_message(self, fmt, *args):
        pass

    def _send(self, body: bytes, ctype='text/html; charset=utf-8', code=200, headers=None):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        self.__class__.hits.append(self.path)
        if parsed.path == '/municipio/limeira/2026':
            body = b'<html><body><a href="/files/despesas-limeira-2026.zip">Despesa Detalhada</a></body></html>'
            return self._send(body)
        if parsed.path == '/municipio/limeira/2027':
            body = b'<html><body><a href="/files/despesas-limeira-2027.zip">Despesa Detalhada</a></body></html>'
            return self._send(body)
        if parsed.path == '/municipio/limeira/2028':
            body = b'<html><body><a href="/files/despesas-limeira-2028.zip">Despesa Detalhada</a></body></html>'
            return self._send(body)
        if parsed.path == '/files/despesas-limeira-2026.zip':
            return self._send(self.tce_zip, 'application/zip')
        if parsed.path == '/files/despesas-limeira-2027.zip':
            return self._send(self.bad_zip, 'application/zip')
        if parsed.path == '/files/despesas-limeira-2028.zip':
            return self._send(self.live_schema_zip, 'application/zip')
        if parsed.path.startswith('/api/json/despesas/limeira/2019/'):
            month = int(parsed.path.rsplit('/', 1)[-1])
            rows = []
            if month == 1:
                rows = [{
                    'orgao': 'PREFEITURA MUNICIPAL DE LIMEIRA', 'mes': 'Janeiro',
                    'evento': 'Pago', 'nr_empenho': '77-2019',
                    'id_fornecedor': 'CNPJ - PESSOA JURÍDICA - 45132495000140',
                    'nm_fornecedor': 'JAIME FACHINELLI', 'dt_emissao_despesa': '15/01/2019',
                    'vl_despesa': '100,00',
                }]
            return self._send(json.dumps(rows).encode('utf-8'), 'application/json')
        if parsed.path == '/contracts':
            body = '''<html><body>
            <form method="get" action="/contracts/results">
              <label>Ano de Pesquisa <input name="ano" type="text"></label>
              <label>Numero do Contrato <input name="numero_contrato" type="text"></label>
              <label>Objeto <input name="objeto" type="text"></label>
              <label>Fornecedor <input name="fornecedor" type="text"></label>
              <input name="acao" type="submit" value="Pesquisar">
            </form></body></html>'''.encode('utf-8')
            return self._send(body)
        if parsed.path == '/contracts/results':
            q = parse_qs(parsed.query)
            year = q.get('ano', [''])[0]
            num = q.get('numero_contrato', [''])[0]
            if year == '2025' and num == '51':
                body = '''<html><body><table>
                <tr><th>Contrato</th><th>Ano</th><th>Fornecedor</th><th>CNPJ</th></tr>
                <tr><td>51/2025</td><td>2025</td><td>Consórcio Exemplo Ltda</td><td>61.086.929/0001-70</td></tr>
                </table></body></html>'''.encode('utf-8')
            else:
                body = b'<html><body><table><tr><th>Contrato</th></tr></table></body></html>'
            return self._send(body)
        if parsed.path == '/contracts-scriptcase':
            body = '''<html><body>
            <script>
              $("#id_ac_numero").change(function() { $("#SC_numero").val($(this).val()); });
              $("#id_ac_objeto").change(function() { $("#SC_objeto").val($(this).val()); });
              $("#id_ac_fornecedor").change(function() { $("#SC_fornecedor").val($(this).val()); });
            </script>
            <form method="get" action="/contracts-scriptcase-results">
              <label>Ano de Pesquisa <input id="SC_ano_ano" name="ano_ano" type="text"></label>
              <label>Numero do Contrato
                <input id="SC_numero" name="numero" type="text" style="display: none">
                <input id="id_ac_numero" name="numero_autocomp" type="text">
              </label>
              <label>Objeto
                <input id="SC_objeto" name="objeto" type="text" style="display: none">
                <input id="id_ac_objeto" name="objeto_autocomp" type="text">
              </label>
              <label>Fornecedor
                <input id="SC_fornecedor" name="fornecedor" type="text">
                <input id="id_ac_fornecedor" name="fornecedor_autocomp" type="text">
              </label>
            </form></body></html>'''.encode('utf-8')
            return self._send(body, headers={'Set-Cookie': 'SCSESSION=proved; Path=/'})
        if parsed.path == '/contracts-scriptcase-results':
            q = parse_qs(parsed.query)
            cookie_ok = 'SCSESSION=proved' in (self.headers.get('Cookie') or '')
            if cookie_ok and q.get('ano_ano', [''])[0] == '2025' and q.get('numero', [''])[0] == '51' and q.get('numero_autocomp', [''])[0] == '51':
                body = '''<html><body><table>
                <tr><th>Contrato</th><th>Ano</th><th>Fornecedor</th><th>CNPJ</th></tr>
                <tr><td>51/2025</td><td>2025</td><td>Consórcio Exemplo Ltda</td><td>61.086.929/0001-70</td></tr>
                </table></body></html>'''.encode('utf-8')
            else:
                body = b'<html><body><table><tr><th>Contrato</th></tr></table></body></html>'
            return self._send(body)
        if parsed.path == '/contracts-no-form':
            return self._send(b'<html><body>Pesquisa manual apenas</body></html>')
        return self._send(b'not found', 'text/plain', 404)


class TestM4E5Resolvers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ResolverHandler.hits = []
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), ResolverHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_address[1]}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=5)
        cls.server.server_close()

    def test_tce_2020plus_discovers_resource_and_filters_exact_cnpj(self):
        resolver = TcespExpenseResolver(base_url=self.base, allow_insecure_localhost=True)
        with tempfile.TemporaryDirectory() as td:
            out = resolver.resolve(tce_task(2026), work_dir=td)
        self.assertEqual('MATCH_CANDIDATE', out.status)
        self.assertEqual(3, len(out.candidates))
        self.assertEqual({'EMPENHADO', 'LIQUIDADO', 'PAGO'}, {x['stage'] for x in out.candidates})
        ev = out.evidence['years']['2026']
        self.assertEqual('MUNICIPAL_YEAR_DOWNLOAD_DISCOVERED_FROM_PANEL', ev['mode'])
        self.assertTrue(ev['resource_url'].endswith('/files/despesas-limeira-2026.zip'))
        self.assertEqual(3, ev['matched_records'])

    def test_tce_current_unknown_schema_stops_fail_closed(self):
        resolver = TcespExpenseResolver(base_url=self.base, allow_insecure_localhost=True)
        task = tce_task(2027)
        with tempfile.TemporaryDirectory() as td:
            out = resolver.resolve(task, work_dir=td)
        self.assertEqual('STOP_SCHEMA_UNKNOWN', out.status)
        self.assertEqual([], out.candidates)

    def test_tce_current_live_schema_aliases_are_supported(self):
        resolver = TcespExpenseResolver(base_url=self.base, allow_insecure_localhost=True)
        with tempfile.TemporaryDirectory() as td:
            out = resolver.resolve(tce_task(2028), work_dir=td)
        self.assertEqual('MATCH_CANDIDATE', out.status)
        self.assertEqual(1, len(out.candidates))
        self.assertEqual('EMPENHADO', out.candidates[0]['stage'])
        meta = out.evidence['years']['2028']['csv'][0]
        self.assertEqual('tp_despesa', meta['mapping']['event'])
        self.assertEqual('identificador_despesa', meta['mapping']['supplier_id'])

    def test_tce_historical_2019_uses_documented_month_api(self):
        resolver = TcespExpenseResolver(base_url=self.base, allow_insecure_localhost=True)
        with tempfile.TemporaryDirectory() as td:
            out = resolver.resolve(tce_task(2019), work_dir=td)
        self.assertEqual('MATCH_CANDIDATE', out.status)
        self.assertEqual(1, len(out.candidates))
        self.assertEqual('PAGO', out.candidates[0]['stage'])
        self.assertEqual('DOCUMENTED_API_2014_2019', out.evidence['years']['2019']['mode'])

    def test_contract_resolver_discovers_form_and_submits_exact_year_contract_stem(self):
        resolver = LimeiraContractsResolver(search_url=self.base + '/contracts', allow_insecure_localhost=True)
        out = resolver.resolve(contract_task())
        self.assertEqual('MATCH_CANDIDATE', out.status)
        self.assertEqual(1, len(out.candidates))
        self.assertIn('CONTRACT_FULL', out.candidates[0]['match_signals'])
        self.assertIn('CNPJ', out.candidates[0]['match_signals'])
        self.assertEqual('PASS_FORM_DISCOVERY', out.evidence['form_discovery']['status'])

    def test_contract_resolver_proves_scriptcase_autocomplete_pairs_before_submit(self):
        resolver = LimeiraContractsResolver(search_url=self.base + '/contracts-scriptcase', allow_insecure_localhost=True)
        out = resolver.resolve(contract_task())
        self.assertEqual('MATCH_CANDIDATE', out.status)
        selected = out.evidence['form_discovery']['selected']
        self.assertEqual('FOUND_SCRIPTCASE_AUTOCOMPLETE_PAIR', selected['contract']['status'])
        self.assertEqual('numero', selected['contract']['field'])
        self.assertEqual('numero_autocomp', selected['contract']['companion_field'])

    def test_contract_autocomplete_pair_without_copy_script_stays_ambiguous(self):
        resolver = LimeiraContractsResolver(search_url=self.base + '/contracts', allow_insecure_localhost=True)
        html = '''<form method="get">
          <label>Ano <input name="ano_ano"></label>
          <label>Contrato <input id="SC_numero" name="numero"><input id="id_ac_numero" name="numero_autocomp"></label>
        </form>'''
        discovered, evidence = resolver._discover_form(html)
        self.assertIsNone(discovered)
        self.assertEqual('STOP_CONTRACT_FORM_UNPROVEN', evidence['status'])

    def test_contract_scriptcase_autosubmit_relay_requires_explicit_hidden_search_form(self):
        html = '''<form style="display:none" name="form_ok" method="POST" action="./">
          <input type="hidden" name="script_case_init" value="6527">
          <input type="hidden" name="script_case_session" value="session-token">
          <input type="hidden" name="nmgp_opcao" value="pesq">
        </form><script>document.form_ok.submit();</script>'''
        relay, evidence = LimeiraContractsResolver._discover_autosubmit_relay(html)
        self.assertEqual('PASS_PROVEN_AUTOSUBMIT_RELAY', evidence['status'])
        self.assertEqual('pesq', relay['params']['nmgp_opcao'])

        unsafe = html.replace('document.form_ok.submit();', '')
        relay, evidence = LimeiraContractsResolver._discover_autosubmit_relay(unsafe)
        self.assertIsNone(relay)
        self.assertEqual('NO_PROVEN_AUTOSUBMIT_RELAY', evidence['status'])

    def test_contract_table_parser_preserves_outer_scriptcase_grid_row(self):
        html = '''<table><tr>
          <td><table><tr><td><input type="image"></td></tr></table></td>
          <td>CONTRATOS</td><td><a>51/2025</a></td><td>903586/2025</td>
          <td>07/07/2025</td><td>06/11/2025</td><td>CONSORCIO LIMPA LIMEIRA</td>
          <td>SERVIÇO DE ROÇAGEM</td><td>R$532.800,00</td>
        </tr></table>'''
        parser = _TableParser()
        parser.feed(html)
        candidates = LimeiraContractsResolver._candidate_rows(parser.rows, {'year': 2025, 'contract_number': '51/2025'})
        self.assertEqual(1, len(candidates))
        self.assertIn('CONTRACT_FULL', candidates[0]['match_signals'])

    def test_contract_resolver_does_not_submit_when_form_contract_unproven(self):
        resolver = LimeiraContractsResolver(search_url=self.base + '/contracts-no-form', allow_insecure_localhost=True)
        before = len(ResolverHandler.hits)
        out = resolver.resolve(contract_task())
        after_hits = ResolverHandler.hits[before:]
        self.assertEqual('STOP_CONTRACT_FORM_UNPROVEN', out.status)
        self.assertEqual(1, len(after_hits))
        self.assertEqual('/contracts-no-form', after_hits[0])

    def test_contract_resolver_does_not_fall_back_to_broad_object_search(self):
        task = contract_task()
        task['match_keys'].pop('contract_number')
        task['match_keys'].pop('contractor')
        before = len(ResolverHandler.hits)
        out = LimeiraContractsResolver(search_url=self.base + '/contracts', allow_insecure_localhost=True).resolve(task)
        after_hits = ResolverHandler.hits[before:]
        self.assertEqual('STOP_MISSING_CONTRACT_OR_SUPPLIER_KEY', out.status)
        self.assertEqual(['/contracts'], after_hits)

    def test_executor_dry_run_keeps_ready_status(self):
        planner = ReconciliationPlanner()
        task = next(t for t in planner.plan_event({
            'event_id': 'JOEV_contract_001', 'source_id': 'LIMEIRA_JO_07309', 'event_type': 'CONTRATO',
            'publication_date': '2026-08-21', 'contract_number': '51/2025',
            'contractor': 'Consórcio Exemplo Ltda', 'cnpj': '61086929000170',
        }) if t.target_source == 'TCE_SP_DESPESAS')
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / 'state.sqlite'
            with StateRegistry(db) as st:
                st.upsert_reconciliation_task(task)
            ex = ReconciliationExecutor(
                tce_resolver=TcespExpenseResolver(base_url=self.base, allow_insecure_localhost=True),
                contracts_resolver=LimeiraContractsResolver(search_url=self.base + '/contracts', allow_insecure_localhost=True),
            )
            out = ex.run_queue(db, work_dir=Path(td) / 'work', dry_run=True, targets=['TCE_SP_DESPESAS'])
            self.assertEqual('PASS_RECONCILIATION_EXECUTOR_DRY_RUN', out['status'])
            with StateRegistry(db) as st:
                row = st.list_reconciliation_tasks()[0]
                self.assertEqual('READY_SEARCH', row['status'])

    def test_executor_persists_resolution_result(self):
        task = tce_task(2026)
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / 'state.sqlite'
            with StateRegistry(db) as st:
                st.upsert_reconciliation_task(task)
            ex = ReconciliationExecutor(
                tce_resolver=TcespExpenseResolver(base_url=self.base, allow_insecure_localhost=True),
                contracts_resolver=LimeiraContractsResolver(search_url=self.base + '/contracts', allow_insecure_localhost=True),
            )
            out = ex.run_queue(db, work_dir=Path(td) / 'work', targets=['TCE_SP_DESPESAS'])
            self.assertEqual('PASS_RECONCILIATION_EXECUTION', out['status'])
            self.assertEqual({'MATCH_CANDIDATE': 1}, out['status_counts'])
            with StateRegistry(db) as st:
                row = st.list_reconciliation_tasks()[0]
                self.assertEqual('MATCH_CANDIDATE', row['status'])
                self.assertEqual('TCE_SP_DESPESAS', row['result']['target_source'])
                self.assertEqual(3, len(row['result']['candidates']))


if __name__ == '__main__':
    unittest.main()

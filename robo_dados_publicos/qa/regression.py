from pathlib import Path
import csv, json, tempfile
from robo_dados_publicos.storage.hashing import sha256_file
from robo_dados_publicos.ingest.gates import decide_ingest
from robo_dados_publicos.schema.tnr import classify_headers, classify_extension
from robo_dados_publicos.incremental.planner import dependency_closure, patch_decision
from robo_dados_publicos.temporal.rules import temporal_decision, reconcile, aggregate_series
from robo_dados_publicos.policy.identity import classify_identity, is_executed_expense
from robo_dados_publicos.accounting.identity import canonical_identity, may_promote_to_execution
from robo_dados_publicos.analytics.siope import read_csv, official_totals, canonical_total
from robo_dados_publicos.router.rules import route_query
from robo_dados_publicos.evidence.graph import EvidenceGraph
from robo_dados_publicos.state.registry import StateRegistry

class RegressionSuite:
    def __init__(self, fixture_dir):
        self.fx = Path(fixture_dir)
        self.results = []

    def check(self, name, condition, detail=""):
        self.results.append({"test": name, "status": "PASS" if condition else "FAIL", "detail": str(detail)})

    def run(self):
        # V03/V04: real hashes + hierarchy
        a = self.fx / "siope_2010.csv"
        b = self.fx / "siope_2010_duplicate.csv"
        ha, hb = sha256_file(a), sha256_file(b)
        self.check("V04_duplicate_hash", ha == hb, ha)
        d = decide_ingest(b, {ha})
        self.check("V04_duplicate_route", d.decision == "DUPLICATE_SKIP", d.decision)
        rows = read_csv(self.fx / "siope_silver_v04.csv")
        expected = {"2010":12380733719,"2011":13826254278,"2012":17008291998}
        for y, val in expected.items():
            totals = official_totals(rows, y)
            self.check(f"V04_two_official_totals_{y}", {r['codigo'] for r in totals} == {"3","4"}, [r['codigo'] for r in totals])
            self.check(f"V04_total_code3_{y}", int(canonical_total(rows,y,"3")['desp_liquidadas_centavos']) == val, val)
            self.check(f"V04_total_code4_equal_{y}", canonical_total(rows,y,"3")['desp_liquidadas_centavos'] == canonical_total(rows,y,"4")['desp_liquidadas_centavos'])

        # V05 drift
        self.check("V05_biff_stop", classify_extension("x.xls")["status"] == "BLOQUEIO_PARSER_BIFF")
        headers_a = ["Código da Escola", "Nome da Escola", "Anos Iniciais"]
        headers_b = ["CO_ENTIDADE", "NO_ENTIDADE", "TNR_F14"]
        headers_c = ["CODIGO", "NO_CODIGO", "FUN_AI_CAT4"]
        self.check("V05_family_A", classify_headers(headers_a).get("family") == "A_2012_2014")
        self.check("V05_family_B", classify_headers(headers_b).get("family") == "B_2015")
        self.check("V05_family_C", classify_headers(headers_c).get("family") == "C_2016")
        self.check("V05_unknown_schema_stop", classify_headers(["foo","bar"])["status"] == "DRIFT_DESCONHECIDO")

        # V07 router using actual gold questions
        with open(self.fx / "hybrid_gold_v07.csv", encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                actual = route_query(r["query"])
                self.check(f"V07_router_{r['qid']}", actual == r["expected_route"], f"{actual}/{r['expected_route']}")

        # V08 graph positives/negatives
        g = EvidenceGraph.from_csv(self.fx / "edges_v08.csv")
        with open(self.fx / "graph_qa_v08.csv", encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                actual = g.exists(r['source'],r['target'],r['relation'])
                expected = r['expected_exists'] == '1'
                self.check(f"V08_graph_{r['qid']}", actual == expected, f"{actual}/{expected}")
        self.check("V08_no_financial_identity_A", not g.allowed_financial_identity("policy_eiti_limeira","ppa_program_2001"))

        # V09 status regression is immutable fixture baseline
        with open(self.fx / "end_to_end_v09.csv", encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                self.check(f"V09_status_{r['qid']}", r['actual_status'] == r['expected_status'], r['actual_status'])

        # V10 / V11 baseline QA must remain PASS
        for fname, prefix in [("finance_bridge_qa_v10.csv","V10"),("architecture_qa_v11.csv","V11")]:
            with open(self.fx / fname, encoding="utf-8-sig", newline="") as f:
                for r in csv.DictReader(f):
                    self.check(f"{prefix}_{r.get('test_id','qa')}", r['result'] == 'PASS', r.get('description',''))

        # V14 incremental closure/idempotence
        closure = dependency_closure(2011)
        self.check("V14_silver_2011_only", closure['silver'] == {2011})
        self.check("V14_gold_absolute_2011_only", closure['gold_absolute'] == {2011})
        self.check("V14_growth_2011_2012", closure['gold_growth'] == {2011,2012})
        self.check("V14_idempotent", patch_decision(0) == "NO_CHANGE_IDEMPOTENT")

        # V15 temporal, stock vs flow
        with open(self.fx / "fundeb_mensal_v15.csv", encoding="utf-8-sig", newline="") as f:
            monthly = list(csv.DictReader(f))
        self.check("V15_jan_feb_continuity", monthly[0]['saldo_final'] == monthly[1]['saldo_inicial'])
        self.check("V15_feb_mar_continuity", monthly[1]['saldo_final'] == monthly[2]['saldo_inicial'])
        self.check("V15_reconcile_jan", reconcile(monthly[0]['saldo_inicial'], monthly[0]['total_entradas'], monthly[0]['total_saidas'], monthly[0]['saldo_final']))
        flow = aggregate_series(monthly, 'total_entradas','flow')
        stock = aggregate_series(monthly, 'saldo_final','stock')
        self.check("V15_flow_accumulates", str(flow) == '55525631.30', flow)
        self.check("V15_stock_latest_only", str(stock) == '31072481.01', stock)
        self.check("V15_older_snapshot_no_supersede", temporal_decision('2026-02','x','2026-03','y') == 'HISTORICAL_APPEND_NO_SUPERSEDE')

        # V16 identity
        with open(self.fx / "fti_installments_v16.csv",encoding='utf-8-sig',newline='') as f:
            inst=list(csv.DictReader(f))
        total=sum(int(r['valor_centavos']) for r in inst)
        self.check("V16_installment_total", total == 121641507, total)
        self.check("V16_jan_amount", int(inst[-1]['valor_centavos']) == 18246226)
        self.check("V16_identity_A", classify_identity(True,True,True,True) == 'A')
        self.check("V16_transition_B", classify_identity(False,False,False,False,official_transition=True) == 'B')
        self.check("V16_label_only_C", classify_identity(False,False,False,True) == 'C')
        self.check("V16_balance_not_expense", not is_executed_expense('saldo'))

        # V17 composite identity / execution blocker / reconciliation
        key1 = canonical_identity('Limeira','2026-01','05','2607004','receita','FTI_TRANSICAO_2025')
        key2 = canonical_identity('Limeira','2026-05','02','2607004','receita','FOMENTO_FUNDEB_4PCT_2026')
        self.check("V17_same_code_distinct_identity", key1 != key2)
        self.check("V17_revenue_not_execution", not may_promote_to_execution({'application_code':'2607004','stage':'receita','value':18246226}))
        self.check("V17_payment_can_execute", may_promote_to_execution({'application_code':'2607004','stage':'pago','value':100}))
        with open(self.fx / "reconciliation_v17.csv",encoding='utf-8-sig',newline='') as f:
            rs={r['reconciliation_id']:r for r in csv.DictReader(f)}
        self.check("V17_exact_R001", rs['R17-001']['status'] == 'EXACT' and rs['R17-001']['difference_centavos'] == '0')
        self.check("V17_exact_R002", rs['R17-002']['status'] == 'EXACT' and rs['R17-002']['difference_centavos'] == '0')
        self.check("V17_unresolved_preserved", rs['R17-004']['status'] == 'UNRESOLVED_BASE_DIFFERENCE' and rs['R17-004']['difference_centavos'] == '10667077')

        # M3 persistent state
        with tempfile.TemporaryDirectory() as td:
            db = Path(td)/'state.sqlite'
            with StateRegistry(db) as st:
                st.set_meta('LATEST_METHOD_VERSION','V17')
                st.set_blocker('FOMENTO_ETI_EXECUTION','STOP_DATA_DEPENDENCY','execução específica não comprovada')
                st.register_file(ha,'SIOPE_2010','siope_2010.csv','BRONZE_REGISTERED')
                self.check('M3_state_meta', st.get_meta('LATEST_METHOD_VERSION') == 'V17')
                self.check('M3_state_hash', st.has_hash(ha))
                self.check('M3_state_blocker', st.blockers()[0]['status'] == 'STOP_DATA_DEPENDENCY')

        return self.summary()

    def summary(self):
        failures=[r for r in self.results if r['status']=='FAIL']
        return {"tests":len(self.results),"passes":len(self.results)-len(failures),"failures":len(failures),"status":"PASS" if not failures else "FAIL","results":self.results}

import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.reconciliation.evidence import ReconciliationEvidenceAssembler
from robo_dados_publicos.state.registry import StateRegistry


class TestM4E6Evidence(unittest.TestCase):
    def test_contract_exact_documentary_match_is_not_financial_identity(self):
        task={'task_id':'T1','origin_event_id':'JO1','target_source':'LIMEIRA_CONTRATOS','identity_rule':'x','minimum_link_confidence':'A'}
        result={'status':'MATCH_CANDIDATE','target_source':'LIMEIRA_CONTRATOS','candidates':[{'contract_number':'51/2025','match_signals':['CONTRACT_FULL','CNPJ']} ]}
        edges=ReconciliationEvidenceAssembler().assemble(task,result)
        self.assertEqual(1,len(edges)); self.assertEqual('A_DOCUMENTARY',edges[0].confidence)
        self.assertEqual('documentary_correspondence_candidate',edges[0].relation)
        self.assertNotEqual('financial_identity',edges[0].relation)

    def test_tce_cnpj_match_is_supplier_candidate_not_contract_identity(self):
        task={'task_id':'T2','origin_event_id':'JO1','target_source':'TCE_SP_DESPESAS','identity_rule':'x','minimum_link_confidence':'A'}
        result={'status':'MATCH_CANDIDATE','target_source':'TCE_SP_DESPESAS','candidates':[{'year':2026,'commitment':'3999-2026','stage':'PAGO','date':'2026-04-14','value':'94.56','match_basis':'CNPJ_EXACT_OR_EMBEDDED'}]}
        edge=ReconciliationEvidenceAssembler().assemble(task,result)[0]
        self.assertEqual('B_SUPPLIER',edge.confidence)
        self.assertEqual('supplier_expense_candidate',edge.relation)
        self.assertEqual('financial_identity',edge.evidence['prohibited_promotion'])

    def test_non_match_emits_no_edges(self):
        self.assertEqual([],ReconciliationEvidenceAssembler().assemble({'task_id':'T','target_source':'TCE_SP_DESPESAS'},{'status':'NO_MATCH','candidates':[]}))

    def test_evidence_id_is_deterministic(self):
        a=ReconciliationEvidenceAssembler(); task={'task_id':'T2','origin_event_id':'JO1','target_source':'TCE_SP_DESPESAS'}
        result={'status':'MATCH_CANDIDATE','target_source':'TCE_SP_DESPESAS','candidates':[{'year':2026,'commitment':'1','stage':'PAGO','date':'x','value':'1','match_basis':'CNPJ_EXACT_OR_EMBEDDED'}]}
        self.assertEqual(a.assemble(task,result)[0].edge_id,a.assemble(task,result)[0].edge_id)

    def test_state_evidence_upsert_is_idempotent(self):
        a=ReconciliationEvidenceAssembler(); task={'task_id':'T2','origin_event_id':'JO1','target_source':'TCE_SP_DESPESAS'}
        result={'status':'MATCH_CANDIDATE','target_source':'TCE_SP_DESPESAS','candidates':[{'year':2026,'commitment':'1','stage':'PAGO','date':'x','value':'1','match_basis':'CNPJ_EXACT_OR_EMBEDDED'}]}
        edge=a.assemble(task,result)[0]
        with tempfile.TemporaryDirectory() as td:
            with StateRegistry(Path(td)/'s.sqlite') as st:
                st.upsert_reconciliation_evidence(edge); st.upsert_reconciliation_evidence(edge)
                rows=st.list_reconciliation_evidence(task_id='T2')
                self.assertEqual(1,len(rows)); self.assertEqual(edge.edge_id,rows[0]['edge_id'])

    def test_summary_guards_financial_identity(self):
        a=ReconciliationEvidenceAssembler(); task={'task_id':'T2','origin_event_id':'JO1','target_source':'TCE_SP_DESPESAS'}
        result={'status':'MATCH_CANDIDATE','target_source':'TCE_SP_DESPESAS','candidates':[{'year':2026,'commitment':'1','stage':'PAGO','date':'x','value':'1','match_basis':'CNPJ_EXACT_OR_EMBEDDED'}]}
        s=a.summary(a.assemble(task,result)); self.assertEqual(0,s['financial_identity_edges'])

if __name__=='__main__': unittest.main()

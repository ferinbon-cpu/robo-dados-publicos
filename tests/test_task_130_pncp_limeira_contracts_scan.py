from copy import deepcopy
from pathlib import Path
import unittest

from robo_dados_publicos.research.task129_pncp_limeira_contracts_scan import (
    load_task129_contract,scan_pncp_page
)
from robo_dados_publicos.research.task130_pncp_limeira_contracts_scan import (
    Task130Stop,combine_remaining_pages,load_task130_contract,validate_task130_contract
)

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"config/task130_pncp_limeira_contracts_pages3_5.v1.json"
P129=ROOT/"config/task129_pncp_limeira_contracts_pages2_5.v1.json"

def payload(page,rows=1,strong=False,total=2023,pages=5):
    data=[]
    for i in range(rows):
        data.append({
            "numeroControlePNCP":f"CTRL-{page}-{i}",
            "objetoContrato":"Educação Integral - contratação de oficinas" if strong and i==0 else "material escolar",
            "informacaoComplementar":"",
            "valorGlobal":1000.0
        })
    return {"data":data,"totalRegistros":total,"totalPaginas":pages,"numeroPagina":page,"paginasRestantes":max(0,5-page),"empty":False}

class TestTask130(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=load_task130_contract(P,root=ROOT)
        cls.c129=load_task129_contract(P129,root=ROOT)

    def test_only_pages3_5_and_timeout60(self):
        self.assertEqual([3,4,5],self.c["source"]["pages"])
        self.assertEqual(3,self.c["transport"]["get_requests_max"])
        self.assertEqual(60,self.c["transport"]["timeout_seconds"])
        self.assertEqual(0,self.c["transport"]["retry"])

    def test_reuses_exact_task129_matching(self):
        r=scan_pncp_page(payload(3,strong=True),deepcopy(self.c129),requested_page=3)
        self.assertEqual(1,r["candidate_count"])
        self.assertIn("EDUCACAO INTEGRAL",r["candidates"][0]["strong_policy_markers"])

    def test_full_remaining_zero_candidate_scan_closes_2023_rows(self):
        rs=[
            scan_pncp_page(payload(3,rows=500),deepcopy(self.c129),requested_page=3),
            scan_pncp_page(payload(4,rows=500),deepcopy(self.c129),requested_page=4),
            scan_pncp_page(payload(5,rows=23),deepcopy(self.c129),requested_page=5),
        ]
        out=combine_remaining_pages(rs,deepcopy(self.c))
        self.assertEqual("NO_MATCH_WITHIN_PNCP_CNPJ_DATE_SCOPE_ONLY",out["status"])
        self.assertEqual(2023,out["coverage"]["rows_scanned_total"])
        self.assertTrue(out["coverage"]["exhaustive_within_query_scope"])

    def test_candidate_on_remaining_page_is_preserved_secondary_only(self):
        rs=[
            scan_pncp_page(payload(3,rows=500,strong=True),deepcopy(self.c129),requested_page=3),
            scan_pncp_page(payload(4,rows=500),deepcopy(self.c129),requested_page=4),
            scan_pncp_page(payload(5,rows=23),deepcopy(self.c129),requested_page=5),
        ]
        out=combine_remaining_pages(rs,deepcopy(self.c))
        self.assertEqual("CANDIDATE_MATCH_WITHIN_PNCP_CNPJ_DATE_SCOPE",out["status"])
        self.assertEqual(1,out["candidate_count"])
        self.assertFalse(out["financial_identity_promoted"])
        self.assertTrue(out["municipal_primary_verification_required"])

    def test_snapshot_drift_prevents_exhaustive_combination(self):
        rs=[
            scan_pncp_page(payload(3,rows=500,total=2024),deepcopy(self.c129),requested_page=3),
            scan_pncp_page(payload(4,rows=500),deepcopy(self.c129),requested_page=4),
            scan_pncp_page(payload(5,rows=23),deepcopy(self.c129),requested_page=5),
        ]
        out=combine_remaining_pages(rs,deepcopy(self.c))
        self.assertFalse(out["coverage"]["exhaustive_within_query_scope"])

    def test_scope_widening_or_retry_fails_closed(self):
        x=deepcopy(self.c); x["source"]["pages"]=[2,3,4,5]
        with self.assertRaisesRegex(Task130Stop,"PAGES"): validate_task130_contract(x,root=ROOT)
        x=deepcopy(self.c); x["transport"]["retry"]=1
        with self.assertRaisesRegex(Task130Stop,"RETRY"): validate_task130_contract(x,root=ROOT)

if __name__=="__main__": unittest.main()

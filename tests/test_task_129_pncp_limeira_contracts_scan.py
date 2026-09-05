from copy import deepcopy
from pathlib import Path
import unittest

from robo_dados_publicos.research.task129_pncp_limeira_contracts_scan import (
    Task129Stop,combine_task128_and_task129,load_task129_contract,scan_pncp_page,validate_task129_contract
)

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"config/task129_pncp_limeira_contracts_pages2_5.v1.json"

def payload(page,rows=1,strong=False,total=2023,pages=5):
    data=[]
    for i in range(rows):
        data.append({
            "numeroControlePNCP":f"CTRL-{page}-{i}",
            "objetoContrato":"Programa Escola em Tempo Integral - oficinas" if strong and i==0 else "material escolar",
            "informacaoComplementar":"",
            "valorGlobal":1000.0
        })
    return {"data":data,"totalRegistros":total,"totalPaginas":pages,"numeroPagina":page,"paginasRestantes":max(0,5-page),"empty":False}

class TestTask129(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.c=load_task129_contract(P,root=ROOT)

    def test_exact_pages_and_budget(self):
        self.assertEqual([2,3,4,5],self.c["source"]["pages"])
        self.assertEqual(4,self.c["transport"]["get_requests_max"])
        self.assertEqual(0,self.c["transport"]["retry"])
        self.assertEqual(0,self.c["transport"]["redirects_max"])

    def test_strong_marker_yields_secondary_candidate_only(self):
        r=scan_pncp_page(payload(2,strong=True),deepcopy(self.c),requested_page=2)
        self.assertEqual("PAGE_SCANNED",r["status"])
        self.assertEqual(1,r["candidate_count"])
        self.assertFalse(r["candidates"][0]["automatic_financial_identity"])
        self.assertEqual("CANDIDATE_REQUIRES_MUNICIPAL_PRIMARY_VERIFICATION",r["candidates"][0]["status"])

    def test_weak_only_does_not_qualify(self):
        p=payload(2)
        p["data"][0]["objetoContrato"]="Contratação de oficineiro extracurricular"
        r=scan_pncp_page(p,deepcopy(self.c),requested_page=2)
        self.assertEqual(0,r["candidate_count"])

    def test_snapshot_metadata_drift_stops_without_exhaustive_claim(self):
        r=scan_pncp_page(payload(2,total=2024),deepcopy(self.c),requested_page=2)
        self.assertEqual("STOP_SNAPSHOT_METADATA_DRIFT_NO_EXHAUSTIVE_CONCLUSION",r["status"])

    def test_full_zero_candidate_coverage_is_bounded_no_match(self):
        rs=[
            scan_pncp_page(payload(2,rows=500),deepcopy(self.c),requested_page=2),
            scan_pncp_page(payload(3,rows=500),deepcopy(self.c),requested_page=3),
            scan_pncp_page(payload(4,rows=500),deepcopy(self.c),requested_page=4),
            scan_pncp_page(payload(5,rows=23),deepcopy(self.c),requested_page=5),
        ]
        out=combine_task128_and_task129(rs,deepcopy(self.c))
        self.assertEqual("NO_MATCH_WITHIN_PNCP_CNPJ_DATE_SCOPE_ONLY",out["status"])
        self.assertTrue(out["coverage"]["exhaustive_within_query_scope"])
        self.assertEqual(2023,out["coverage"]["rows_scanned_total"])

    def test_candidate_any_remaining_page_yields_candidate_result(self):
        rs=[
            scan_pncp_page(payload(2,rows=500),deepcopy(self.c),requested_page=2),
            scan_pncp_page(payload(3,rows=500,strong=True),deepcopy(self.c),requested_page=3),
            scan_pncp_page(payload(4,rows=500),deepcopy(self.c),requested_page=4),
            scan_pncp_page(payload(5,rows=23),deepcopy(self.c),requested_page=5),
        ]
        out=combine_task128_and_task129(rs,deepcopy(self.c))
        self.assertEqual("CANDIDATE_MATCH_WITHIN_PNCP_CNPJ_DATE_SCOPE",out["status"])
        self.assertEqual(1,out["candidate_count"])

    def test_drift_in_any_page_blocks_combination(self):
        rs=[
            scan_pncp_page(payload(2,rows=500),deepcopy(self.c),requested_page=2),
            scan_pncp_page(payload(3,rows=500,total=2024),deepcopy(self.c),requested_page=3),
            scan_pncp_page(payload(4,rows=500),deepcopy(self.c),requested_page=4),
            scan_pncp_page(payload(5,rows=23),deepcopy(self.c),requested_page=5),
        ]
        out=combine_task128_and_task129(rs,deepcopy(self.c))
        self.assertEqual("STOP_SNAPSHOT_METADATA_DRIFT_NO_EXHAUSTIVE_CONCLUSION",out["status"])
        self.assertFalse(out["exhaustive_within_query_scope"])

    def test_scope_widening_fails_closed(self):
        x=deepcopy(self.c); x["source"]["pages"]=[1,2,3,4,5]
        with self.assertRaisesRegex(Task129Stop,"PAGES"): validate_task129_contract(x,root=ROOT)
        x=deepcopy(self.c); x["transport"]["get_requests_max"]=5
        with self.assertRaisesRegex(Task129Stop,"GET_BUDGET"): validate_task129_contract(x,root=ROOT)

if __name__=="__main__": unittest.main()

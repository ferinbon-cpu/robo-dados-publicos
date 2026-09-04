from __future__ import annotations
import copy,json
from pathlib import Path
import tempfile,unittest
from robo_dados_publicos.research.eiti_historical_planning import EitiHistoricalPlanningStop,load_and_validate_historical_planning_crosswalk,validate_historical_planning_crosswalk

ROOT=Path(__file__).resolve().parents[1]
CROSSWALK=ROOT/"config/eiti_historical_planning_crosswalk.v1.json"
TASK055A=ROOT/"docs/evidence/TASK_055A_F01_EITI_TERMINOLOGY_ONTOLOGY_0.8.0.json"
TASK096=ROOT/"docs/evidence/TASK_096_EITI_LIMEIRA_OFFLINE_CROSSWALK_0.8.0.json"
TASK107=ROOT/"docs/evidence/TASK_107_LIVE_RESULT_0.8.0.json"
TASK112=ROOT/"docs/evidence/TASK_112_REAL_PPA_OCR_RESULT_0.8.0.json"
TASK114=ROOT/"docs/evidence/TASK_114_ONTOLOGY_OCR_RESULT_0.8.0.json"

def load(p): return json.loads(p.read_text(encoding="utf-8"))

class TestTask098EitiHistoricalPlanningCrosswalk(unittest.TestCase):
    def setUp(self):
        self.crosswalk,self.t55,self.t96,self.t107,self.t112,self.t114=map(load,[CROSSWALK,TASK055A,TASK096,TASK107,TASK112,TASK114])
    def validate(self,data=None,**kw):
        return validate_historical_planning_crosswalk(data or self.crosswalk,task055a=kw.get("task055a",self.t55),task096=self.t96,task107=self.t107,task112=kw.get("task112",self.t112),task114=kw.get("task114",self.t114))
    def test_canonical_crosswalk_has_no_acquisition_gap_and_one_bounded_negative_record(self):
        result=load_and_validate_historical_planning_crosswalk(CROSSWALK,task055a_path=TASK055A,task096_path=TASK096,task107_path=TASK107,task112_path=TASK112,task114_path=TASK114)
        self.assertEqual("PASS_TASK115_HISTORICAL_EVIDENCE_ADJUDICATED",result["status"])
        self.assertEqual(3,result["primary_documents_acquired"])
        self.assertEqual(2,result["primary_positive_planning_periods"])
        self.assertEqual(1,result["conflicted_planning_periods"])
        self.assertEqual(0,result["historical_acquisition_gaps_remaining"])
        self.assertEqual(1,result["bounded_negative_evidence_records"])
        self.assertEqual("CONFLICTED",result["three_ppa_continuity_status"])
    def test_2018_is_conflicted_not_proven_or_refuted(self):
        self.assertEqual("CONFLICTED",self.crosswalk["periods"][0]["planning_signal_status"])
        for bad in ("PROVEN","REFUTED","CANDIDATE"):
            data=copy.deepcopy(self.crosswalk); data["periods"][0]["planning_signal_status"]=bad
            with self.assertRaisesRegex(EitiHistoricalPlanningStop,"2018_SIGNAL_STATUS"): self.validate(data)
    def test_acquisition_gap_cannot_be_reopened_without_new_evidence_model(self):
        data=copy.deepcopy(self.crosswalk); data["acquisition_gaps"]=[{"period":"2018-2021"}]
        with self.assertRaisesRegex(EitiHistoricalPlanningStop,"ACQUISITION_GAPS_NOT_CLOSED"): self.validate(data)
    def test_bounded_negative_cannot_be_laundered_into_global_absence(self):
        data=copy.deepcopy(self.crosswalk); data["bounded_negative_evidence"][0]["limitations"].remove("NEGATIVE_EVIDENCE_DOES_NOT_PROVE_GLOBAL_ABSENCE")
        with self.assertRaisesRegex(EitiHistoricalPlanningStop,"NEGATIVE_LIMITATION"): self.validate(data)
    def test_task114_candidate_tampering_fails_closed(self):
        t=copy.deepcopy(self.t114); t["candidate_count"]=1
        with self.assertRaisesRegex(EitiHistoricalPlanningStop,"TASK114_CANDIDATES"): self.validate(task114=t)
    def test_source_sha_must_match_task112_and_task114(self):
        t=copy.deepcopy(self.t112); t["source"]["source_sha256"]="0"*64
        with self.assertRaisesRegex(EitiHistoricalPlanningStop,"TASK112_SHA"): self.validate(task112=t)
    def test_financial_identity_remains_unknown_all_periods(self):
        self.assertTrue(all(x["financial_identity_status"]=="UNKNOWN" for x in self.crosswalk["periods"]))
    def test_2022_and_2026_positive_statuses_remain_unchanged(self):
        self.assertEqual(("PROVEN","CANDIDATE"),(self.crosswalk["periods"][1]["planning_signal_status"],self.crosswalk["periods"][1]["policy_link_status"]))
        self.assertEqual(("PROVEN","CORROBORATED"),(self.crosswalk["periods"][2]["planning_signal_status"],self.crosswalk["periods"][2]["policy_link_status"]))
    def test_missing_task114_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(EitiHistoricalPlanningStop,"REQUIRED_INPUT_MISSING"):
                load_and_validate_historical_planning_crosswalk(CROSSWALK,task055a_path=TASK055A,task096_path=TASK096,task107_path=TASK107,task112_path=TASK112,task114_path=Path(td)/"missing.json")
    def test_remote_effect_enablement_fails_closed(self):
        data=copy.deepcopy(self.crosswalk); data["remote_effects"]["drive_read"]=True
        with self.assertRaisesRegex(EitiHistoricalPlanningStop,"REMOTE_EFFECT"): self.validate(data)

if __name__=="__main__": unittest.main()

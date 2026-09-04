from __future__ import annotations
import json
from pathlib import Path
from typing import Any

EXPECTED_PERIODS=("2018-2021","2022-2025","2026-2029")
TASK112_SHA="685a621a2f5fa8859e4b7f8518627c1523a2fbc5f3402ff48d4aa7573300113d"
TASK114_RESULT_SHA="ab663f4f5f8a192e4cf9cf64c8e8ee3da2731f61d32041b7486244290f485c81"

class EitiHistoricalPlanningStop(RuntimeError):
    pass

def _require(condition: bool, code: str) -> None:
    if not condition:
        raise EitiHistoricalPlanningStop(code)

def validate_historical_planning_crosswalk(data: dict[str,Any], *, task055a:dict[str,Any], task096:dict[str,Any], task107:dict[str,Any], task112:dict[str,Any], task114:dict[str,Any]) -> dict[str,Any]:
    _require(data.get("schema")=="EITI_HISTORICAL_PLANNING_CROSSWALK_V1","TASK115_SCHEMA")
    _require(data.get("mode")=="T0_OFFLINE_VERSIONED_REPOSITORY_EVIDENCE_ONLY","TASK115_MODE")
    _require(data.get("policy_id")=="POLICY:EITI_LIMEIRA","TASK115_POLICY")
    _require(all(v is False for v in (data.get("remote_effects") or {}).values()),"TASK115_REMOTE_EFFECT")

    aliases=set((task055a.get("ontology") or {}).get("B_LOCAL_PLANNING_AND_NORMATIVE_ALIASES") or [])
    _require("escolas com programas em tempo integral" in aliases,"TASK115_TASK055A_2018_ALIAS")
    _require("indice de alunos em Educacao Integral" in aliases,"TASK115_TASK055A_2022_ALIAS")
    _require((task055a.get("matching_rules") or {}).get("no_semantic_overreach") is True,"TASK115_OVERREACH_GUARD")
    _require((task096.get("institutionalization_matrix") or {}).get("budgetary_persistence")=="UNKNOWN","TASK115_BUDGETARY_BASELINE")

    _require(task112.get("status")=="NO_MATCH_TASK112_EXPECTED_PLANNING_SIGNAL_NOT_FOUND","TASK115_TASK112_STATUS")
    _require((task112.get("source") or {}).get("source_sha256")==TASK112_SHA,"TASK115_TASK112_SHA")
    _require((task112.get("document") or {}).get("page_count")==80,"TASK115_TASK112_PAGES")
    _require((task112.get("law_identity") or {}).get("page")==1,"TASK115_TASK112_LAW_LOCATOR")
    _require(task112.get("planning_signal") is None,"TASK115_TASK112_SIGNAL")
    _require(task112.get("retry_performed") is False,"TASK115_TASK112_RETRY")

    _require(task114.get("status")=="NO_CANDIDATES_FOUND","TASK115_TASK114_STATUS")
    _require((task114.get("source") or {}).get("source_sha256")==TASK112_SHA,"TASK115_TASK114_SHA")
    _require((task114.get("document") or {}).get("page_count")==80,"TASK115_TASK114_PAGES")
    _require(task114.get("candidate_count")==0 and task114.get("candidate_page_count")==0,"TASK115_TASK114_CANDIDATES")
    _require(task114.get("result_canonical_sha256")==TASK114_RESULT_SHA,"TASK115_TASK114_RESULT_SHA")
    _require(all(v is False for v in (task114.get("promotion") or {}).values()),"TASK115_TASK114_PROMOTION")

    periods=data.get("periods")
    _require(isinstance(periods,list) and tuple(x.get("period") for x in periods)==EXPECTED_PERIODS,"TASK115_PERIODS")
    p={x["period"]:x for x in periods}
    p18=p["2018-2021"]
    _require(p18.get("primary_document_entity_versioned") is True,"TASK115_2018_DOCUMENT")
    _require(p18.get("primary_source_hash_versioned") is True,"TASK115_2018_SOURCE_HASH")
    _require(p18.get("planning_signal_status")=="CONFLICTED","TASK115_2018_SIGNAL_STATUS")
    _require(p18.get("policy_link_status")=="UNKNOWN","TASK115_2018_POLICY_LINK")
    _require(p18.get("financial_identity_status")=="UNKNOWN","TASK115_2018_FINANCIAL")
    _require(p18.get("primary_source_sha256")==TASK112_SHA,"TASK115_2018_CROSSWALK_SHA")
    _require((p18.get("document_identity_locator") or {}).get("page")==1,"TASK115_2018_DOC_LOCATOR")
    _require(p18.get("positive_planning_signal_locator") is None,"TASK115_2018_NO_POSITIVE_LOCATOR")

    p22=p["2022-2025"]
    _require(p22.get("planning_signal_status")=="PROVEN","TASK115_2022_PLANNING")
    _require(p22.get("policy_link_status")=="CANDIDATE","TASK115_2022_LINK")
    _require(p22.get("financial_identity_status")=="UNKNOWN","TASK115_2022_FINANCIAL")
    _require((p22.get("preferred_locator") or {}).get("page")==23,"TASK115_2022_LOCATOR")

    p26=p["2026-2029"]
    _require(p26.get("planning_signal_status")=="PROVEN","TASK115_2026_PLANNING")
    _require(p26.get("policy_link_status")=="CORROBORATED","TASK115_2026_LINK")
    _require(p26.get("financial_identity_status")=="UNKNOWN","TASK115_2026_FINANCIAL")

    longitudinal=data.get("longitudinal_assessment") or {}
    _require(longitudinal.get("three_ppa_period_policy_continuity")=="CONFLICTED","TASK115_CONTINUITY")
    _require(longitudinal.get("three_ppa_period_budgetary_persistence")=="UNKNOWN","TASK115_BUDGETARY")
    _require(longitudinal.get("two_of_three_primary_planning_periods_proven") is True,"TASK115_TWO_OF_THREE")
    _require(longitudinal.get("all_three_primary_documents_acquired") is True,"TASK115_ALL_ACQUIRED")

    gaps=data.get("acquisition_gaps")
    _require(isinstance(gaps,list) and gaps==[],"TASK115_ACQUISITION_GAPS_NOT_CLOSED")
    neg=data.get("bounded_negative_evidence")
    _require(isinstance(neg,list) and len(neg)==1,"TASK115_NEGATIVE_EVIDENCE")
    n=neg[0]
    _require(n.get("period")=="2018-2021","TASK115_NEGATIVE_PERIOD")
    _require(n.get("status")=="BOUNDED_NO_CANDIDATES","TASK115_NEGATIVE_STATUS")
    _require(n.get("source_sha256")==TASK112_SHA,"TASK115_NEGATIVE_SHA")
    _require(n.get("pages_ocr_scanned")==80,"TASK115_NEGATIVE_COVERAGE")
    _require(n.get("ontology_family_count")==3 and n.get("ontology_term_count")==29,"TASK115_NEGATIVE_ONTOLOGY")
    _require(n.get("candidate_count")==0 and n.get("candidate_page_count")==0,"TASK115_NEGATIVE_CANDIDATES")
    _require(n.get("task114_result_canonical_sha256")==TASK114_RESULT_SHA,"TASK115_NEGATIVE_RESULT_SHA")
    _require("NEGATIVE_EVIDENCE_DOES_NOT_PROVE_GLOBAL_ABSENCE" in (n.get("limitations") or []),"TASK115_NEGATIVE_LIMITATION")

    forbidden=set(data.get("forbidden_promotions") or [])
    _require("BOUNDED_NO_MATCH_TO_GLOBAL_ABSENCE" in forbidden,"TASK115_GLOBAL_ABSENCE_GUARD")
    _require("HISTORICAL_ALIAS_TO_FINANCIAL_IDENTITY" in forbidden,"TASK115_FINANCIAL_GUARD")

    return {
      "status":"PASS_TASK115_HISTORICAL_EVIDENCE_ADJUDICATED",
      "period_count":3,
      "primary_documents_acquired":3,
      "primary_positive_planning_periods":2,
      "conflicted_planning_periods":1,
      "historical_acquisition_gaps_remaining":0,
      "bounded_negative_evidence_records":1,
      "three_ppa_continuity_status":"CONFLICTED",
      "three_ppa_budgetary_persistence_status":"UNKNOWN",
      "new_source_reads":0,
      "remote_effects":0,
    }

def load_and_validate_historical_planning_crosswalk(crosswalk_path:str|Path, *, task055a_path:str|Path, task096_path:str|Path, task107_path:str|Path, task112_path:str|Path, task114_path:str|Path) -> dict[str,Any]:
    try:
        values=[json.loads(Path(p).read_text(encoding="utf-8")) for p in [crosswalk_path,task055a_path,task096_path,task107_path,task112_path,task114_path]]
    except FileNotFoundError as exc:
        raise EitiHistoricalPlanningStop("TASK115_REQUIRED_INPUT_MISSING") from exc
    except json.JSONDecodeError as exc:
        raise EitiHistoricalPlanningStop("TASK115_REQUIRED_INPUT_MALFORMED_JSON") from exc
    return validate_historical_planning_crosswalk(values[0],task055a=values[1],task096=values[2],task107=values[3],task112=values[4],task114=values[5])

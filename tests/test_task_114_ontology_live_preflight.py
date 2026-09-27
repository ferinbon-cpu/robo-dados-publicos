from __future__ import annotations

import json
from pathlib import Path
import unittest

from robo_dados_publicos.research.ppa_2018_ontology_live import ontology_candidates_for_page

ROOT=Path(__file__).resolve().parents[1]
LEXICAL=ROOT/"config/task113_ppa2018_ontology_lexical.v1.json"


def page(text: str):
    return {
        "page":10,
        "coordinate_system":"SOURCE_PDF_PAGE_1_BASED",
        "normalized_text":text,
        "raw_text":text,
        "rendered_page_sha256":"a"*64,
        "ocr_tsv_sha256":"b"*64,
        "confidence_count":10,
        "confidence_min":80.0,
        "confidence_max":99.0,
        "confidence_mean":93.0,
    }


class TestTask114OntologyLivePreflight(unittest.TestCase):
    def setUp(self):
        self.lexical=json.loads(LEXICAL.read_text(encoding="utf-8"))

    def test_strong_a_term_becomes_candidate_only(self):
        items=ontology_candidates_for_page(
            page_result=page("EDUCACAO INTEGRAL EM TEMPO INTEGRAL"),
            lexical_contract=self.lexical,
        )
        self.assertTrue(any(x["family"]=="A_CANONICAL_POLICY_IDENTIFIERS" for x in items))
        self.assertTrue(all("financial" not in x for x in items))

    def test_weak_numeric_without_context_is_rejected(self):
        items=ontology_candidates_for_page(
            page_result=page("ATENDIMENTO SETE HORAS"),
            lexical_contract=self.lexical,
        )
        self.assertFalse(any(x["term"]=="sete horas" for x in items))

    def test_weak_numeric_with_school_context_is_candidate(self):
        items=ontology_candidates_for_page(
            page_result=page("ESCOLA JORNADA SETE HORAS"),
            lexical_contract=self.lexical,
        )
        match=[x for x in items if x["term"]=="sete horas"]
        self.assertEqual(1,len(match))
        self.assertIn("ESCOLA",match[0]["companion_hits"])

    def test_financing_terms_are_not_searched(self):
        items=ontology_candidates_for_page(
            page_result=page("FUNDEB EMPENHO PAGAMENTO DOTACAO ORCAMENTARIA"),
            lexical_contract=self.lexical,
        )
        self.assertEqual([],items)

    def test_page_candidate_limit_is_enforced(self):
        data=json.loads(json.dumps(self.lexical))
        data["future_live_gate"]["max_candidates_per_page"]=1
        items=ontology_candidates_for_page(
            page_result=page("EDUCACAO EM TEMPO INTEGRAL EDUCACAO INTEGRAL EM TEMPO INTEGRAL"),
            lexical_contract=data,
        )
        self.assertEqual(1,len(items))

if __name__=="__main__":
    unittest.main()

from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from robo_dados_publicos.research.answer_renderer import (
    REMOTE_EFFECT_KEYS,
    ResearchAnswerRenderStop,
    load_renderer_contract,
    render_research_answer_markdown,
)
from robo_dados_publicos.research.query import execute_research_query


ROOT = Path(__file__).resolve().parents[1]
RENDERER_CONTRACT = ROOT / "config/research_answer_renderer.v1.json"
EITI = ROOT / "config/eiti_limeira_research_crosswalk.v1.json"
HISTORICAL = ROOT / "config/eiti_historical_planning_crosswalk.v1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TestTask100OfflineResearchAnswerRenderer(unittest.TestCase):
    def setUp(self) -> None:
        eiti = load(EITI)
        historical = load(HISTORICAL)
        self.packet = execute_research_query(
            eiti["research_bundle"],
            {
                "query_id": "Q:EITI_STATUS_TASK100",
                "query_type": "POLICY_STATUS_PACKET",
                "subject_id": "POLICY:EITI_LIMEIRA",
                "include_evidence": True,
                "include_unknown_gaps": True,
            },
            institutionalization_matrix=eiti["institutionalization_matrix"],
            historical_planning=historical,
        )

    def test_contract_is_t0_remote_effect_free_and_complete(self):
        contract = load_renderer_contract(RENDERER_CONTRACT)
        self.assertEqual("T0_OFFLINE_DETERMINISTIC_MARKDOWN_RENDERER", contract["mode"])
        self.assertEqual(set(REMOTE_EFFECT_KEYS), set(contract["remote_effects"]))
        self.assertTrue(all(value is False for value in contract["remote_effects"].values()))

    def test_eiti_packet_renders_deterministically(self):
        first = render_research_answer_markdown(self.packet)
        second = render_research_answer_markdown(copy.deepcopy(self.packet))
        self.assertEqual(first, second)
        self.assertEqual(64, len(first["markdown_sha256"]))
        self.assertEqual(self.packet["result_sha256"], first["source_result_sha256"])

    def test_claim_text_and_status_are_preserved_verbatim(self):
        rendered = render_research_answer_markdown(self.packet)["markdown"]
        financial = next(
            claim
            for claim in self.packet["claims"]
            if claim["claim_id"] == "CLAIM:EITI_FINANCIAL_IDENTITY"
        )
        self.assertIn(financial["text"], rendered)
        section = rendered.split("### CLAIM:EITI_FINANCIAL_IDENTITY", 1)[1]
        self.assertIn("**Status:** UNKNOWN", section)

    def test_evidence_source_identity_and_locator_are_visible(self):
        rendered = render_research_answer_markdown(self.packet)["markdown"]
        claim = next(item for item in self.packet["claims"] if item.get("evidence"))
        evidence = claim["evidence"][0]
        self.assertIn(evidence["source_document_id"], rendered)
        self.assertIn(evidence["source_document_label"], rendered)
        locator = json.dumps(
            evidence["locator"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        self.assertIn(locator, rendered)

    def test_matrix_unknowns_and_historical_gaps_remain_visible(self):
        rendered = render_research_answer_markdown(self.packet)["markdown"]
        self.assertIn("**budgetary_policy_identity** — UNKNOWN", rendered)
        self.assertIn("**transaction_execution_identity** — UNKNOWN", rendered)
        self.assertIn("**outcome_effect** — UNKNOWN", rendered)
        self.assertIn("### 2018-2021", rendered)
        self.assertIn("### 2022-2025", rendered)
        self.assertIn("PRIMARY_PPA_DOCUMENT_IDENTITY", rendered)
        self.assertIn("DIRECT_TEXT_OR_VISUAL_EVIDENCE", rendered)

    def test_renderer_metadata_preserves_guardrails(self):
        result = render_research_answer_markdown(self.packet)
        self.assertEqual(0, result["status_promotions_performed"])
        self.assertFalse(result["financial_identity_created"])
        self.assertFalse(result["causal_effect_created"])
        self.assertFalse(result["free_form_generation_performed"])
        self.assertFalse(result["remote_effects_performed"])

    def test_wrong_input_schema_fails_closed(self):
        packet = copy.deepcopy(self.packet)
        packet["schema"] = "OTHER"
        with self.assertRaisesRegex(ResearchAnswerRenderStop, "RESULT_SCHEMA"):
            render_research_answer_markdown(packet)

    def test_status_promotion_marker_fails_closed(self):
        packet = copy.deepcopy(self.packet)
        packet["status_promotions_performed"] = 1
        with self.assertRaisesRegex(ResearchAnswerRenderStop, "STATUS_PROMOTION"):
            render_research_answer_markdown(packet)

    def test_upstream_free_form_generation_fails_closed(self):
        packet = copy.deepcopy(self.packet)
        packet["natural_language_generation_performed"] = True
        with self.assertRaisesRegex(ResearchAnswerRenderStop, "UPSTREAM_NATURAL_LANGUAGE_GENERATION"):
            render_research_answer_markdown(packet)

    def test_invalid_evidence_locator_fails_closed(self):
        packet = copy.deepcopy(self.packet)
        claim = next(item for item in packet["claims"] if item.get("evidence"))
        claim["evidence"][0]["locator"] = {}
        with self.assertRaisesRegex(ResearchAnswerRenderStop, "EVIDENCE_LOCATOR"):
            render_research_answer_markdown(packet)

    def test_invalid_matrix_status_fails_closed(self):
        packet = copy.deepcopy(self.packet)
        packet["institutionalization_dimensions"][0]["status"] = "CERTAIN"
        with self.assertRaisesRegex(ResearchAnswerRenderStop, "MATRIX_STATUS"):
            render_research_answer_markdown(packet)

    def test_malformed_historical_gap_fails_closed(self):
        packet = copy.deepcopy(self.packet)
        packet["historical_acquisition_gaps"][0]["required_before_promotion"] = []
        with self.assertRaisesRegex(ResearchAnswerRenderStop, "HISTORICAL_REQUIREMENTS"):
            render_research_answer_markdown(packet)

    def test_truthy_or_incomplete_remote_effect_contract_fails_closed(self):
        contract = load(RENDERER_CONTRACT)
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "contract.json"

            truthy = copy.deepcopy(contract)
            truthy["remote_effects"]["network"] = True
            path.write_text(json.dumps(truthy), encoding="utf-8")
            with self.assertRaisesRegex(ResearchAnswerRenderStop, "REMOTE_EFFECT"):
                load_renderer_contract(path)

            incomplete = copy.deepcopy(contract)
            incomplete["remote_effects"].pop("network")
            path.write_text(json.dumps(incomplete), encoding="utf-8")
            with self.assertRaisesRegex(ResearchAnswerRenderStop, "REMOTE_EFFECT_KEYS"):
                load_renderer_contract(path)


if __name__ == "__main__":
    unittest.main()

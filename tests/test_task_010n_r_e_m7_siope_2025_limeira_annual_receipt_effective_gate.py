import copy
import json
import unittest

from scripts.github_task_010n_r_e_m7_siope_2025_limeira_annual_receipt_effective_gate import DECISION, EVIDENCE, validate


class Task010NREM7GateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def reject(self, mutation, pattern):
        data = copy.deepcopy(self.data)
        mutation(data)
        with self.assertRaisesRegex(ValueError, pattern):
            validate(data)

    def test_pinned_advancement_passes(self):
        self.assertEqual(DECISION, validate(copy.deepcopy(self.data)))

    def test_rejects_scope_identity_mutations(self):
        for key, value in (("year", 2024), ("period", 5), ("period_label", "Bimester"), ("municipality", "Campinas"), ("municipality_code", 350950)):
            with self.subTest(key=key):
                self.reject(lambda d, key=key, value=value: d["scope"].update({key: value}), "drifted")

    def test_rejects_receipt_and_timestamp_drift(self):
        surface = lambda d: d["user_mediated_handoff"]["receipt_surface"]
        self.reject(lambda d: surface(d).update(receipt_number_surface="428478"), "receipt")
        self.reject(lambda d: surface(d).update(transmission_timestamp="09/02/2026 14:11"), "timestamp")
        self.reject(lambda d: surface(d).update(processing_timestamp="13/02/2026 12:48"), "timestamp")
        self.reject(lambda d: d["user_mediated_handoff"]["official_receipt_pdf"].update(receipt_number="428477"), "PDF")

    def test_rejects_missing_successful_delivery_statement(self):
        self.reject(lambda d: d["user_mediated_handoff"]["official_receipt_pdf"].update(successful_delivery_proposition=""), "successful-delivery")

    def test_rejects_mavs_protocol_order_and_failed_protocol_promotion(self):
        self.reject(lambda d: d["user_mediated_handoff"]["mavs_history"]["ordered_history"].reverse(), "protocol/order")
        self.reject(lambda d: d["user_mediated_handoff"]["mavs_history"]["ordered_history"][1].update(protocol="832393"), "protocol/order")
        self.reject(lambda d: d["guards"].update(protocol_831423_treated_as_successful_final_submission=True), "guard")

    def test_rejects_protocol_receipt_conflation(self):
        self.reject(lambda d: d["deterministic_reconciliation"].update(identifier_rule="832393_EQUALS_428477"), "distinct-identifier")
        self.reject(lambda d: d["guards"].update(protocol_and_receipt_conflated=True), "guard")

    def test_rejects_retransmission_as_formal_retification(self):
        self.reject(lambda d: d["user_mediated_handoff"]["mavs_history"].update(formal_retifying_declaration="PROVEN"), "conflation")
        self.reject(lambda d: d["guards"].update(retransmission_treated_as_formal_retification=True), "guard")

    def test_rejects_status_shortcuts_to_effectiveness_or_finality(self):
        for guard in ("non_retifying_used_as_immutable_finality", "processing_success_used_alone_as_current_effective", "publication_ready_used_alone_as_current_effective"):
            with self.subTest(guard=guard):
                self.reject(lambda d, guard=guard: d["guards"].update({guard: True}), "guard")
        self.reject(lambda d: d["proof_status"].update(CURRENTLY_EFFECTIVE_DECLARATION="PROVEN"), "boundary")

    def test_rejects_fabricated_pdf_hash_or_byte_metadata(self):
        pdf = lambda d: d["user_mediated_handoff"]["official_receipt_pdf"]
        self.reject(lambda d: pdf(d).update(sha256="0" * 64), "unavailable-byte")
        self.reject(lambda d: pdf(d).update(byte_size=123), "unavailable-byte")
        self.reject(lambda d: d["guards"].update(pdf_hash_fabricated=True), "guard")

    def test_rejects_financial_values_in_b3_logic(self):
        self.reject(lambda d: d["guards"].update(financial_indicator_values_in_b3_logic=True), "guard")
        self.reject(lambda d: d["user_mediated_handoff"]["official_receipt_pdf"].update(financial_indicator=99), "PDF")

    def test_rejects_s1_s2_semantic_series_gold_release_and_2026_promotions(self):
        mutations = (("S1_NUM_POPU", "PROVEN"), ("S2_FINANCIAL_ALIAS_BRIDGE", "PROVEN"), ("VL_DESP_DOTA_ATUA_EDU", "PROVEN"), ("semantic_comparability_status", "PROVEN"), ("closed_annual_series", "2016-2025"), ("gold_2025", "PROVEN"), ("release_0_8_0", "ACTIVE"), ("year_2026", "PROVEN"))
        for key, value in mutations:
            with self.subTest(key=key):
                self.reject(lambda d, key=key, value=value: d["canonical_state"].update({key: value}), "forbidden")

    def test_rejects_closed_series_eligibility_or_annual_closure_promotion(self):
        self.reject(lambda d: d["resulting_state"].update(closed_series_2025_eligibility="ELIGIBLE"), "forbidden")
        self.reject(lambda d: d["resulting_state"].update(annual_closure_status="PROVEN_CLOSED_EFFECTIVE_ANNUAL_DECLARATION"), "forbidden")

    def test_rejects_unproved_supersession_or_surface_selection_rule(self):
        self.reject(lambda d: d["documentary_discovery"].update(supersession_or_effective_selection_rule="PROVEN"), "unsupported")
        self.reject(lambda d: d["documentary_discovery"].update(secondary_question_result="SURFACE_IS_LATEST"), "unsupported")


if __name__ == "__main__":
    unittest.main()

import unittest

from robo_dados_publicos.analytics.task184_local_bundle import (
    build_jom_product,
    build_planning_product,
    build_task184_bundle,
    load_contract,
    load_jom_events,
    load_planning_rows,
)


GENERATED_AT = "2026-09-06T09:00:00-03:00"
SOFTWARE_VERSION = "0.8.0"


class TestTask184LocalBundle(unittest.TestCase):
    def bundle(self):
        return build_task184_bundle(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )

    def test_contract_pins_real_sources_and_blocks_synthetic_accounting(self):
        c = load_contract()
        self.assertEqual(c["jom"]["source_row_count"], 303)
        self.assertEqual(c["jom"]["source_snapshot_id"], "d126c0df36075f759b687c05")
        self.assertEqual(
            c["jom"]["canonical_matrix_sha256"],
            "d126c0df36075f759b687c0554a7dbbf5a4e4897384707a588ddc5033697f252",
        )
        self.assertEqual(c["accounting"]["bundle_status"], "NOT_MATERIALIZED")
        self.assertEqual(c["accounting"]["task172_live_row_count_observed"], 39780)
        self.assertFalse(c["accounting"]["raw_payload_persisted"])
        self.assertFalse(c["accounting"]["synthetic_fixture_allowed"])
        self.assertFalse(c["remote_effects"]["drive_write"])
        self.assertFalse(c["remote_effects"]["serving"])

    def test_jom_fixture_is_exact_303_validated_unique_events(self):
        events = load_jom_events()
        self.assertEqual(len(events), 303)
        self.assertEqual(len({x["event_id"] for x in events}), 303)
        self.assertTrue(all(x["extraction_status"] == "VALIDATED" for x in events))
        self.assertTrue(all(x["confidence_class"] == "VALIDATED" for x in events))
        self.assertTrue(all(x["gold_id"] == x["event_id"] for x in events))

    def test_jom_semantics_are_recomputed_without_proving_identity_or_payment(self):
        product, stats = build_jom_product(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        self.assertEqual(product["row_count"], 303)
        self.assertTrue(stats["semantics_recomputed"])
        self.assertFalse(stats["event_identity_rewritten"])
        self.assertEqual(stats["event_type_counts"], {
            "ATA_REGISTRO_PRECOS": 32,
            "CONTRATO": 20,
            "CONVENIO": 8,
            "DECRETO": 66,
            "EDITAL": 81,
            "LEI": 8,
            "PORTARIA": 79,
            "RESOLUCAO": 4,
            "TERMO_ADITIVO_CONTRATO": 5,
        })
        self.assertEqual(stats["evidence_layer_counts"].get("PERSONNEL", 0), 0)
        self.assertEqual(stats["evidence_layer_counts"].get("INFRASTRUCTURE", 0), 3)
        self.assertEqual(stats["evidence_layer_counts"].get("PROCUREMENT_CONTRACT", 0), 76)
        self.assertEqual(stats["policy_domain_counts"].get("EDUCATION", 0), 2)
        self.assertTrue(
            all(
                row["caution"]
                == "PUBLICATION_NE_IMPLEMENTATION_AND_SEMANTIC_FACETS_NE_IDENTITY"
                for row in product["rows"]
            )
        )

    def test_planning_rows_use_real_primary_hashes_and_exact_locators(self):
        rows = load_planning_rows()
        self.assertEqual(len(rows), 7)
        by_doc = {}
        for row in rows:
            by_doc.setdefault(row["document_id"], []).append(row)
            self.assertTrue(row["locator"])
            self.assertEqual(len(row["source_sha256"]), 64)

        self.assertEqual(
            by_doc["PPA_2026_2029_LEI_7213_2025"][0]["source_sha256"],
            "3e5deb53448c2e5eea56217a4e5d7f20f7fc3859eff7fcb93a7de7eb17011c1a",
        )
        self.assertEqual(
            by_doc["LDO_2026_LEI_7141_2025"][0]["source_sha256"],
            "6f28017bb61fe6dbd7db44e2306bd1a48f813d8d40411d87c130fba78fca2406",
        )
        self.assertEqual(
            by_doc["LOA_2026_LEI_7223_2025"][0]["source_sha256"],
            "bc4c8bf4b2b1e8f59e880318c37ec7f7fbd4357a85a8b46c97750444dbf01d4b",
        )
        self.assertEqual(
            by_doc["CME_02_2021_EDUCACAO_TEMPO_INTEGRAL"][0]["source_sha256"],
            "5d01a883bd5ec721b9a9a8b0a0f2c985eea8958da23de8d475d7c73d3109c07c",
        )
        self.assertEqual(
            by_doc["DECRETO_118_2024_EITI_LIMEIRA"][0]["source_sha256"],
            "a534b99711652d437e1672dbaf39b9f56fe8f35c042f3648ae8483187c909b60",
        )

    def test_loa_is_metadata_only_and_cannot_be_promoted_to_substantive_annex_coverage(self):
        rows = load_planning_rows()
        loa = next(x for x in rows if x["document_type"] == "LOA")
        self.assertEqual(loa["evidence_role"], "PRIMARY_METADATA_ONLY")
        self.assertEqual(loa["substantive_status"], "PRIMARY_METADATA_ONLY")
        self.assertEqual(loa["quality_status"], "PARTIAL")
        self.assertIn("NOT_PARSED", loa["caution"])

    def test_planning_product_has_five_real_documents_and_seven_evidence_rows(self):
        product, stats = build_planning_product(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        self.assertEqual(product["row_count"], 7)
        self.assertEqual(stats["document_count"], 5)
        self.assertEqual(stats["evidence_role_counts"], {
            "PRIMARY_METADATA_ONLY": 1,
            "PRIMARY_NORMATIVE": 2,
            "PRIMARY_SUBSTANTIVE": 4,
        })
        self.assertEqual(
            stats["primary_substantive_document_types"],
            ["LDO", "PPA"],
        )
        self.assertEqual(
            stats["primary_normative_source_families"],
            ["CME", "MUNICIPAL_LEGISLATION"],
        )
        self.assertFalse(stats["loa_substantive_parsed"])

    def test_final_pack_bundles_jom_and_planning_but_not_accounting(self):
        b = self.bundle()
        products = b["products"]
        self.assertEqual(products["SCHOOL_INDICATOR_SERIES"]["row_count"], 1017)
        self.assertEqual(products["FISCAL_SERIES"]["row_count"], 38)
        self.assertEqual(products["JOM_EVENT_INDEX"]["row_count"], 303)
        self.assertEqual(products["PLANNING_DOCUMENT_INDEX"]["row_count"], 7)
        self.assertEqual(products["QUERY_PRODUCT_CATALOG"]["row_count"], 4)
        self.assertNotIn("ACCOUNTING_LEDGER", products)
        self.assertFalse(b["product_stats"]["ACCOUNTING_LEDGER"]["materialized"])
        self.assertEqual(b["answerability"]["gain_accounting"]["changed_question_count"], 0)

    def test_jom_radar_becomes_answerable_but_personnel_stays_partial(self):
        b = self.bundle()
        base = {x["question_id"]: x for x in b["answerability"]["baseline"]["questions"]}
        jom = {x["question_id"]: x for x in b["answerability"]["jom_only"]["questions"]}
        final = {x["question_id"]: x for x in b["answerability"]["final"]["questions"]}

        self.assertEqual(base["JOM_Q1"]["status"], "ROUTE_READY_PRODUCT_NOT_BUNDLED")
        self.assertEqual(jom["JOM_Q1"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(final["JOM_Q2"]["status"], "MATERIALIZED_ANSWERABLE")

        self.assertEqual(base["PERS_Q1"]["status"], "ROUTE_READY_PRODUCT_NOT_BUNDLED")
        self.assertEqual(jom["PERS_Q1"]["status"], "MATERIALIZED_PARTIAL")
        self.assertEqual(final["PERS_Q2"]["status"], "MATERIALIZED_PARTIAL")
        self.assertTrue(
            any("ROW_CRITERIA" in gap for gap in final["PERS_Q1"]["product_content_gaps"])
        )

    def test_procurement_and_accounting_questions_do_not_become_fully_answerable(self):
        b = self.bundle()
        final = {x["question_id"]: x for x in b["answerability"]["final"]["questions"]}
        for qid in ("PROC_Q1", "PROC_Q2", "PROC_Q3"):
            self.assertEqual(final[qid]["status"], "MATERIALIZED_PARTIAL")
            self.assertIn("ACCOUNTING_LEDGER", final[qid]["required_nonbundled_products"])
        for qid in ("ACC_Q1", "ACC_Q2", "ACC_Q3"):
            self.assertEqual(final[qid]["status"], "ROUTE_READY_PRODUCT_NOT_BUNDLED")
            self.assertIn("ACCOUNTING_LEDGER", final[qid]["required_nonbundled_products"])

    def test_planning_questions_are_partial_until_substantive_loa_is_parsed(self):
        b = self.bundle()
        planning = {x["question_id"]: x for x in b["answerability"]["planning_only"]["questions"]}
        final = {x["question_id"]: x for x in b["answerability"]["final"]["questions"]}
        for qid in ("PLAN_Q1", "PLAN_Q2"):
            self.assertEqual(planning[qid]["status"], "MATERIALIZED_PARTIAL")
            self.assertEqual(final[qid]["status"], "MATERIALIZED_PARTIAL")
            self.assertTrue(
                any(
                    "DOCUMENT_ROLE:LOA:PRIMARY_SUBSTANTIVE" in gap
                    for gap in final[qid]["product_content_gaps"]
                )
            )
        self.assertEqual(final["PLAN_Q3"]["status"], "MATERIALIZED_PARTIAL")
        self.assertIn("ACCOUNTING_LEDGER", final["PLAN_Q3"]["required_nonbundled_products"])

    def test_public_policy_gain_requires_both_real_jom_and_primary_normative_rows(self):
        b = self.bundle()
        base = {x["question_id"]: x for x in b["answerability"]["baseline"]["questions"]}
        jom = {x["question_id"]: x for x in b["answerability"]["jom_only"]["questions"]}
        planning = {x["question_id"]: x for x in b["answerability"]["planning_only"]["questions"]}
        final = {x["question_id"]: x for x in b["answerability"]["final"]["questions"]}

        self.assertEqual(base["POLICY_Q1"]["status"], "ROUTE_READY_PRODUCT_NOT_BUNDLED")
        self.assertEqual(jom["POLICY_Q1"]["status"], "MATERIALIZED_PARTIAL")
        self.assertEqual(planning["POLICY_Q1"]["status"], "MATERIALIZED_PARTIAL")
        self.assertEqual(final["POLICY_Q1"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(final["POLICY_Q2"]["status"], "MATERIALIZED_ANSWERABLE")

    def test_school_norms_remain_partial_because_old_jom_has_sparse_education_semantics(self):
        b = self.bundle()
        final = {x["question_id"]: x for x in b["answerability"]["final"]["questions"]}
        for qid in ("NORMS_Q1", "NORMS_Q2"):
            self.assertEqual(final[qid]["status"], "MATERIALIZED_PARTIAL")
            self.assertTrue(
                any(
                    gap.startswith("JOM_EVENT_INDEX::ROW_CRITERIA")
                    for gap in final[qid]["product_content_gaps"]
                )
            )

    def test_gain_reports_are_exact_and_accounting_gain_is_zero(self):
        b = self.bundle()
        self.assertGreater(
            b["answerability"]["gain_jom_independent"]["changed_question_count"],
            0,
        )
        self.assertGreater(
            b["answerability"]["gain_planning_independent"]["changed_question_count"],
            0,
        )
        self.assertGreater(
            b["answerability"]["gain_final"]["changed_question_count"],
            b["answerability"]["gain_jom_independent"]["changed_question_count"],
        )
        self.assertEqual(b["answerability"]["gain_accounting"]["changed_question_count"], 0)
        self.assertEqual(
            len(b["answerability"]["gain_final"]["changes"]),
            b["answerability"]["gain_final"]["changed_question_count"],
        )

    def test_sample_packets_use_real_new_snapshots(self):
        b = self.bundle()
        samples = b["sample_packets"]
        self.assertEqual(set(samples), {"JOM_RADAR", "SCHOOL_NORMS", "PLANNING_2026"})
        self.assertGreaterEqual(samples["JOM_RADAR"]["document_record_count"], 303)
        self.assertEqual(
            samples["JOM_RADAR"]["document_record_counts_by_product"]["JOM_EVENT_INDEX"],
            303,
        )
        self.assertGreater(samples["SCHOOL_NORMS"]["document_record_count"], 0)
        self.assertGreater(samples["PLANNING_2026"]["document_record_count"], 0)
        self.assertIn("JOM_EVENT_INDEX", samples["JOM_RADAR"]["used_snapshots"])
        self.assertIn(
            "PLANNING_DOCUMENT_INDEX",
            samples["PLANNING_2026"]["used_snapshots"],
        )

    def test_hard_guards_remain_true(self):
        b = self.bundle()
        self.assertTrue(b["guards"]["publication_ne_execution"])
        self.assertTrue(b["guards"]["planning_ne_execution"])
        self.assertTrue(b["guards"]["loa_metadata_ne_substantive_annex_coverage"])
        self.assertTrue(b["guards"]["accounting_not_synthesized"])
        self.assertFalse(b["guards"]["llm_may_fill_missing_numeric_evidence"])
        self.assertFalse(b["remote_effects"]["network"])
        self.assertFalse(b["remote_effects"]["drive_write"])
        self.assertFalse(b["remote_effects"]["serving"])


if __name__ == "__main__":
    unittest.main()

import copy
import unittest

from robo_dados_publicos.analytics.observatory_products import (
    Task176Stop,
    build_accounting_ledger,
    build_fiscal_series,
    build_jom_event_index,
    build_planning_document_index,
    build_product_catalog,
    build_school_indicator_series,
    coverage_report,
    materialize_product,
    query_observatory,
    query_products,
    validate_contract,
)
from robo_dados_publicos.accounting.tcesp_current import normalize_tcesp_expense_row
from robo_dados_publicos.journal.semantic_layers import classify_event
from robo_dados_publicos.router.observatory import route_observatory_question


GENERATED_AT = "2026-09-06T00:00:00Z"
SOFTWARE = "0.8.0"
SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64


def school_row(
    indicator_id="enrollment",
    value=600,
    *,
    source_family="CENSO_ESCOLAR",
    scope_id="CEIEF_RAL",
    period="2025",
    context="Municipal school context.",
):
    return {
        "scope_level": "SCHOOL",
        "scope_id": scope_id,
        "school_code": "35000001",
        "school_name": "CEIEF Rafael Affonso Leite",
        "network": "MUNICIPAL",
        "period": period,
        "indicator_id": indicator_id,
        "indicator_name": indicator_id.upper(),
        "value": value,
        "unit": "COUNT" if indicator_id == "enrollment" else "INDEX",
        "context": context,
        "observation_period": period,
        "source_family": source_family,
        "source_sha256": SHA_A,
        "provenance_ref": f"PROV_{indicator_id}",
        "quality_status": "VALIDATED",
        "caution": "Comparison requires context.",
    }


def fiscal_row(
    metric_id="education_initial_appropriation",
    value=465355000,
    *,
    source_family="SICONFI_STN",
    period="2025",
):
    return {
        "entity_id": "3526902",
        "period": period,
        "metric_id": metric_id,
        "metric_name": metric_id.upper(),
        "value": value,
        "unit": "BRL",
        "stage_semantic": "BUDGET_AUTHORIZATION",
        "observation_period": period,
        "source_family": source_family,
        "source_sha256": SHA_B,
        "provenance_ref": f"PROV_{metric_id}",
        "quality_status": "VALIDATED",
        "caution": "Authorization is not execution.",
    }


def planning_row(document_type="PPA", document_id="PPA_2022_2025", text="Programa educação."):
    return {
        "document_id": document_id,
        "document_type": document_type,
        "period": "2022-2025",
        "evidence_role": "PLANNING_PRIMARY",
        "locator": "page:10#paragraph:3",
        "text_redacted": text,
        "policy_domains": ["EDUCATION"],
        "topics": ["PLANNING"],
        "observation_period": "2022-2025",
        "source_family": document_type,
        "source_sha256": SHA_C,
        "provenance_ref": f"PROV_{document_id}",
        "quality_status": "VALIDATED",
        "caution": "Planning does not prove execution.",
    }


def tce_source_row(**updates):
    row = {
        "tp_despesa": "Empenhado",
        "nr_empenho": "1234",
        "identificador_despesa": "EXP-2026-0001",
        "ds_despesa": "Reforma de escola municipal",
        "dt_emissao_despesa": "2026-03-10",
        "vl_despesa": "150.000,00",
        "ds_funcao_governo": "Educação",
        "ds_subfuncao_governo": "Ensino Fundamental",
        "cd_programa": "2001",
        "ds_programa": "Educação de Qualidade",
        "cd_acao": "2010",
        "ds_acao": "Manutenção de unidades escolares",
        "ds_fonte_recurso": "Tesouro",
        "ds_cd_aplicacao_fixo": "2200000",
        "ds_modalidade_lic": "Pregão Eletrônico",
        "ds_elemento": "Obras e Instalações",
        "historico_despesa": "Reforma de unidade escolar.",
    }
    row.update(updates)
    return row


def journal_event(
    event_id="JOEV_REFORMA_1",
    *,
    event_type="CONTRATO",
    object_text="Reforma de escola municipal.",
    publication_date="2026-03-11",
):
    return {
        "event_id": event_id,
        "source_id": "LIMEIRA_JO_07310",
        "edition": 7310,
        "publication_date": publication_date,
        "page_number": 5,
        "start_line": 10,
        "end_line": 20,
        "event_type": event_type,
        "organ": "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "act_number": None,
        "contract_number": "170/2026",
        "process_number": "123/2026",
        "edital_number": None,
        "bidding_modality": "PREGÃO ELETRÔNICO",
        "bidding_number": "45/2026",
        "contractor": "EMPRESA EXEMPLO",
        "cnpj": "12345678000190",
        "object_text": object_text,
        "value_brl": "150000.00",
        "signature_date": "10/03/2026",
        "target_act_type": None,
        "target_act_number": None,
        "source_url": "https://example.invalid/7310.pdf",
        "source_sha256": SHA_D,
        "excerpt_redacted": object_text,
        "pii_redactions": 0,
    }


class TestTask176ObservatoryQueryProducts(unittest.TestCase):
    def build_bundle(self):
        school = build_school_indicator_series(
            [
                school_row(),
                school_row("ideb", 7.0, source_family="IDEB", period="2023"),
                school_row("infrastructure_accessibility", 1, period="2025"),
            ],
            generated_at=GENERATED_AT,
            software_version=SOFTWARE,
        )

        event = journal_event()
        sem = classify_event(event)
        jom = build_jom_event_index(
            [event],
            {event["event_id"]: sem},
            generated_at=GENERATED_AT,
            software_version=SOFTWARE,
        )

        observation = normalize_tcesp_expense_row(tce_source_row())
        accounting = build_accounting_ledger(
            [observation],
            generated_at=GENERATED_AT,
            software_version=SOFTWARE,
        )

        fiscal = build_fiscal_series(
            [
                fiscal_row(),
                fiscal_row("fundeb_revenue", 200000000, source_family="FUNDEB", period="2026"),
                fiscal_row("education_expenditure", 300000000, source_family="SIOPE", period="2024"),
            ],
            generated_at=GENERATED_AT,
            software_version=SOFTWARE,
        )

        planning = build_planning_document_index(
            [
                planning_row(),
                planning_row("LDO", "LDO_2026", "Diretrizes orçamentárias da educação."),
                planning_row("LOA", "LOA_2026", "Dotação autorizada para educação."),
                planning_row("CME", "CME_PARECER_002_2024", "Parecer sobre funcionamento da educação municipal."),
            ],
            generated_at=GENERATED_AT,
            software_version=SOFTWARE,
        )
        return {
            "SCHOOL_INDICATOR_SERIES": school,
            "JOM_EVENT_INDEX": jom,
            "ACCOUNTING_LEDGER": accounting,
            "FISCAL_SERIES": fiscal,
            "PLANNING_DOCUMENT_INDEX": planning,
        }

    def test_contract_passes_and_covers_six_products_and_fifteen_domains(self):
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["product_count"], 6)
        self.assertEqual(got["domain_count"], 15)
        self.assertFalse(got["network"])
        self.assertFalse(got["drive_write"])

    def test_materialization_is_deterministic_and_snapshot_is_content_derived(self):
        rows = [school_row(), school_row("ideb", 7.0, source_family="IDEB", period="2023")]
        a = build_school_indicator_series(rows, generated_at=GENERATED_AT, software_version=SOFTWARE)
        b = build_school_indicator_series(list(reversed(rows)), generated_at=GENERATED_AT, software_version=SOFTWARE)
        self.assertEqual(a["snapshot_id"], b["snapshot_id"])
        self.assertEqual(a["content_sha256"], b["content_sha256"])
        self.assertEqual(a["rows"], b["rows"])
        self.assertEqual(len(a["snapshot_id"]), 24)

    def test_generated_at_is_required_not_implicit_clock(self):
        with self.assertRaisesRegex(Task176Stop, "TASK176_GENERATED_AT_REQUIRED"):
            materialize_product(
                "SCHOOL_INDICATOR_SERIES",
                [school_row()],
                generated_at="",
                software_version=SOFTWARE,
            )

    def test_invalid_source_family_fails_closed(self):
        bad = school_row(source_family="RANDOM_SOURCE")
        with self.assertRaisesRegex(Task176Stop, "TASK176_SOURCE_FAMILY_SCHOOL_INDICATOR_SERIES"):
            build_school_indicator_series([bad], generated_at=GENERATED_AT, software_version=SOFTWARE)

    def test_accounting_ledger_preserves_stage_and_programmatic_dimensions(self):
        obs = normalize_tcesp_expense_row(tce_source_row())
        product = build_accounting_ledger([obs], generated_at=GENERATED_AT, software_version=SOFTWARE)
        row = product["rows"][0]
        self.assertEqual(row["stage"], "COMMITMENT")
        self.assertEqual(row["amount_semantic"], "COMMITTED_VALUE")
        self.assertEqual(row["program_code"], "2001")
        self.assertEqual(row["action_code"], "2010")
        self.assertEqual(row["source_family"], "TCE_SP_EXPENSES")
        self.assertFalse(row["policy_identity_proven"])

    def test_jom_event_index_requires_semantics_and_preserves_locator(self):
        event = journal_event()
        with self.assertRaisesRegex(Task176Stop, "TASK176_JOM_SEMANTICS_MISSING"):
            build_jom_event_index([event], {}, generated_at=GENERATED_AT, software_version=SOFTWARE)

        sem = classify_event(event)
        product = build_jom_event_index(
            [event],
            {event["event_id"]: sem},
            generated_at=GENERATED_AT,
            software_version=SOFTWARE,
        )
        row = product["rows"][0]
        self.assertEqual(row["source_locator"]["page_number"], 5)
        self.assertIn("EDUCATION", row["policy_domains"])
        self.assertIn("PROCUREMENT_CONTRACT", row["evidence_layers"])

    def test_catalog_records_product_snapshots_without_becoming_source_truth(self):
        bundle = self.build_bundle()
        catalog = build_product_catalog(
            bundle,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE,
            coverage_domains={
                "SCHOOL_INDICATOR_SERIES": ["LEARNING_FLOW", "NETWORK_ENROLLMENT"],
                "JOM_EVENT_INDEX": ["JOURNAL_EVENT_RADAR"],
                "ACCOUNTING_LEDGER": ["ACCOUNTING_EXECUTION"],
                "FISCAL_SERIES": ["FINANCING"],
                "PLANNING_DOCUMENT_INDEX": ["PLANNING_BUDGET"],
            },
        )
        self.assertEqual(catalog["product_name"], "QUERY_PRODUCT_CATALOG")
        self.assertEqual(catalog["row_count"], 5)
        self.assertTrue(all(x["caution"] == "DERIVED_QUERY_CACHE_NOT_SOURCE_OF_TRUTH" for x in catalog["rows"]))

    def test_school_reform_query_returns_school_jom_and_accounting_products(self):
        bundle = self.build_bundle()
        packet = query_observatory(
            "SCHOOLS_INFRASTRUCTURE",
            bundle,
            question_text="Quais reformas e obras aconteceram nas escolas e quanto foi gasto?",
        )
        numeric_products = {x["product_name"] for x in packet["numeric_records"]}
        doc_products = {x["product_name"] for x in packet["document_records"]}
        self.assertIn("SCHOOL_INDICATOR_SERIES", numeric_products)
        self.assertIn("ACCOUNTING_LEDGER", numeric_products)
        self.assertIn("JOM_EVENT_INDEX", doc_products)
        self.assertFalse(packet["join_semantics"]["weak_can_create_identity"])
        self.assertFalse(packet["llm_numeric_truth_allowed"])

    def test_transport_query_surfaces_missing_products_as_gaps_instead_of_invention(self):
        bundle = self.build_bundle()
        packet = query_observatory(
            "PROCUREMENT_CONTRACTS",
            bundle,
            question_text="Quanto custa o transporte escolar e quais contratos existem?",
        )
        self.assertTrue(any(x["product_name"] == "JOM_EVENT_INDEX" for x in packet["document_records"]))
        self.assertTrue(any(x["product_name"] == "ACCOUNTING_LEDGER" for x in packet["numeric_records"]))
        self.assertTrue(packet["upstream_evidence_gaps"])
        self.assertTrue(packet["numeric_truth_from_structured_records_only"])

    def test_financing_query_combines_fiscal_and_accounting_without_merging_stages(self):
        bundle = self.build_bundle()
        packet = query_observatory(
            "FINANCING",
            bundle,
            question_text="Quanto Limeira gasta com educação e quanto vem do Fundeb?",
        )
        products = {x["product_name"] for x in packet["numeric_records"]}
        self.assertIn("FISCAL_SERIES", products)
        self.assertIn("ACCOUNTING_LEDGER", products)
        accounting_rows = [x for x in packet["numeric_records"] if x["product_name"] == "ACCOUNTING_LEDGER"]
        self.assertTrue(all(x["stage"] in {"COMMITMENT", "LIQUIDATION", "PAYMENT", "REVERSAL", "OTHER_REVIEW"} for x in accounting_rows))

    def test_norm_query_requires_document_locator(self):
        bundle = self.build_bundle()
        packet = query_observatory(
            "NORMS_SCHOOL_FUNCTIONING",
            bundle,
            question_text="Que norma mudou o funcionamento das escolas?",
        )
        self.assertTrue(packet["document_records"])
        planning = [x for x in packet["document_records"] if x["product_name"] == "PLANNING_DOCUMENT_INDEX"]
        self.assertTrue(all(x["locator"] for x in planning))

    def test_time_and_school_filters_are_deterministic(self):
        bundle = self.build_bundle()
        packet = query_observatory(
            "LEARNING_FLOW",
            bundle,
            question_text="Como está o IDEB da escola?",
            timeframe="2023",
            school_or_unit="CEIEF_RAL",
        )
        self.assertTrue(packet["numeric_records"])
        self.assertTrue(all("2023" in str(x.get("period") or x.get("observation_period") or "") for x in packet["numeric_records"]))
        self.assertTrue(all(x.get("scope_id") == "CEIEF_RAL" for x in packet["numeric_records"]))

    def test_coverage_report_is_explicit_for_all_fifteen_domains(self):
        bundle = self.build_bundle()
        catalog = build_product_catalog(
            bundle,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE,
        )
        full = {**bundle, "QUERY_PRODUCT_CATALOG": catalog}
        got = coverage_report(full)
        self.assertEqual(got["domain_count"], 15)
        self.assertTrue(got["all_domains_explicit"])
        self.assertEqual(sum(got["counts"].values()), 15)
        self.assertEqual(got["counts"]["NO_PRODUCTS"], 0)

    def test_transparency_control_can_return_product_catalog_records(self):
        bundle = self.build_bundle()
        bundle["QUERY_PRODUCT_CATALOG"] = build_product_catalog(
            bundle,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE,
        )
        packet = query_observatory("TRANSPARENCY_CONTROL", bundle)
        self.assertTrue(packet["catalog_records"])
        self.assertTrue(all(x["product_name"] == "QUERY_PRODUCT_CATALOG" for x in packet["catalog_records"]))

    def test_missing_product_becomes_explicit_gap(self):
        plan = route_observatory_question("LEARNING_FLOW", question_text="Como está o IDEB?")
        packet = query_products(plan, {})
        self.assertEqual(packet["numeric_records"], [])
        self.assertTrue(any(x["product_name"] == "SCHOOL_INDICATOR_SERIES" for x in packet["product_gaps"]))
        self.assertFalse(packet["source_layers_replaced"])


if __name__ == "__main__":
    unittest.main()

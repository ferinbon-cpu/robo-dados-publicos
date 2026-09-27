#!/usr/bin/env python3
"""Offline, fail-closed B3 evidence gate for TASK 010N-R-E-M7."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_010N_R_E_M7_SIOPE_2025_LIMEIRA_ANNUAL_RECEIPT_EFFECTIVE_DECLARATION_0.8.0.json"
DECISION = "KEEP_ANNUAL_CLOSURE_UNKNOWN_VALID_ANNUAL_SUBMISSION_PROVEN_EFFECTIVE_SELECTION_RULE_MISSING"
SUCCESS = "Formulário SIOPE 2025 Anual entregue com sucesso em 09/02/2026 às 14:10:26."
SCOPE = {"year": 2025, "period": 6, "period_label": "Annual", "uf": "SP", "uf_name": "Sao Paulo", "municipality_code": 352690, "municipality": "Limeira", "boundary": "B3_ONLY"}
PROOF = {"ANNUAL_CONSOLIDATION": "PROVEN", "OFFICIAL_RECEIPT_SURFACE": "PROVEN", "LIMEIRA_2025_ANNUAL_RECEIPT_IDENTITY": "PROVEN_USER_MEDIATED_OFFICIAL", "LIMEIRA_2025_ANNUAL_RECEIPT_NUMBER": "428477-6", "SUCCESSFUL_ANNUAL_DELIVERY": "PROVEN_OFFICIAL_RECEIPT", "VALID_ANNUAL_SUBMISSION": "PROVEN", "CURRENTLY_EFFECTIVE_DECLARATION": "NOT_PROVEN_EFFECTIVE_SELECTION_RULE_MISSING", "immutable_finality": "NOT_PROVEN_NOT_REQUIRED"}
HISTORY = [
    ("831423", "05/02/2026 15:37", "05/02/2026 15:37", "Aguardando Validação do RREO pelo Secretário(a) de Educação"),
    ("831423", "05/02/2026 15:37", "06/02/2026 15:53", "Aguardando retransmissão da declaração SIOPE"),
    ("832393", "09/02/2026 14:10", "09/02/2026 14:10", "Aguardando Validação do RREO pelo Secretário(a) de Educação"),
    ("832393", "09/02/2026 14:10", "09/02/2026 14:42", "Aguardando validação do demonstrativo do FUNDEB pelo presidente do CACS"),
    ("832393", "09/02/2026 14:10", "13/02/2026 11:33", "Disponibilizada para Publicação"),
]
CANONICAL = {"release_0_7_0": "ACTIVE", "release_0_8_0": "CANDIDATE", "year_2025": "PROVEN_STRUCTURAL_RECENT", "S1_NUM_POPU": "NOT_PROVEN", "S2_FINANCIAL_ALIAS_BRIDGE": "NOT_PROVEN", "financial_aliases_proven_exact_operational": "9/10", "annual_closure_status": "UNKNOWN", "semantic_comparability_status": "UNKNOWN", "closed_annual_series": "2016-2024", "gold_2025": "UNKNOWN/BLOCKED", "year_2026": "UNPROVEN_CURRENT_YEAR"}
RESULT = {"annual_closure_status": "UNKNOWN", "closed_series_2025_eligibility": "BLOCKED_BY_B3_EFFECTIVE_SELECTION_RULE_PLUS_S1_S2_SEMANTIC_COMPARABILITY", "semantic_comparability_status": "UNKNOWN", "closed_annual_series": "2016-2024", "gold_2025": "UNKNOWN/BLOCKED"}
CONTEXT = {"VL_DESP_DOTA_ATUA_EDU": "PARTIAL_CURRENT_EXACT_1000_VARIANCE_NO_SOURCE_DEFINED_INCLUSION_RULE"}
SOURCES = [
    ("FNDE", "https://www.fnde.gov.br/phocadownload/sistemas/siope/Manuais/DICIONARIO%20DE%20DADOS%20SIOPE%202019.pdf", "Dicionário de Dados SIOPE 2019", "2019", "Period 6 is annual consolidation from 2017.", "A rule selecting the currently effective/latest declaration or superseding earlier transmissions."),
    ("FNDE", "https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/guia_prefeitos_2025.pdf", "Guia para Novos Prefeitos 2025", "2025", "Annual receipt, deadline, transmission and validation of P6.", "A current/latest receipt display rule or declaration supersession rule."),
    ("FNDE", "https://www.gov.br/fnde/pt-br/assuntos/sistemas/siope/media/Tutorial_Bsico_Siope_2024_v2.pdf", "Tutorial Básico SIOPE 2024 v2", "2024 v2", "P6 may be formally rectified after authorization by the SIOPE technical team. In section 4, Abrir Declaração, the official application screenshot models RETIFICADORA, RECIBO, and RECIBO ANTERIOR columns.", "That a retifying declaration necessarily supersedes the prior declaration for every public/API surface; that the receipt surface displays only the current/latest effective version; or that Limeira receipt 428477-6 is immutable or permanently final."),
    ("FNDE/SIOPE", "https://www.fnde.gov.br/siope/recibosTransmissao.do", "SIOPE — Recibos de Transmissão", "USER_OBSERVATION_2026-08-30", "The user-observed Limeira row exposes a successfully processed 2025 Annual receipt and a non-retifying indicator.", "That the surface displays only the current/latest valid receipt or that the row can never be superseded."),
]
STRUCTURAL = {"classification": "PARTIAL_STRUCTURAL_RETIFICATION_CHAIN_EVIDENCE", "source_title": "Tutorial Básico SIOPE 2024 v2", "section": "4. Abrir Declaração", "observed_columns": ["RETIFICADORA", "RECIBO", "RECIBO ANTERIOR"], "supports": "The official SIOPE application explicitly models a declaration as having a retifying indicator, a current receipt field, and a previous receipt field.", "does_not_support": ["That a retifying declaration necessarily supersedes the prior declaration for every public/API surface.", "That the receipt surface displays only the current/latest effective version.", "That Limeira receipt 428477-6 is immutable or permanently final."], "promotion_effect": "NONE_CURRENTLY_EFFECTIVE_DECLARATION_REMAINS_NOT_PROVEN"}
SEARCH_TERMS = ["declaração retificadora", "retificação", "retransmissão", "substitui a declaração anterior", "substituição", "declaração anterior", "última declaração", "última transmissão", "último recibo", "vigente", "declaração vigente", "nova declaração", "novo recibo", "recibo anterior", "cancelamento", "sobrescreve", "reabre", "reabertura", "sexto bimestre", "6º bimestre", "anual", "recibo de transmissão", "Disponibilizada para Publicação", "MAVS"]
DISCOVERY = {"attempted_on": "2026-08-30", "official_only": True, "allowed_hosts": ["gov.br/fnde", "fnde.gov.br", "webservice.fnde.gov.br"], "search_terms": SEARCH_TERMS, "direct_official_access_result": "CONNECT_TUNNEL_HTTP_403", "official_search_connector_result": "HTTP_401_UNAUTHORIZED", "new_source_bytes_acquired": 0, "artifact_hashes_added": 0, "primary_question_result": "NOT_FOUND_OR_PINNED", "secondary_question_result": "NOT_FOUND_OR_PINNED", "supersession_or_effective_selection_rule": "MISSING", "limitation": "Official-only discovery could not acquire new source bytes; the already pinned official documents do not define supersession or current/latest selection."}


def validate(data):
    identity = (data.get("evidence_schema"), data.get("task"), data.get("base_main_sha"), data.get("tier"), data.get("decision"))
    if identity != ("TASK_010N_R_E_M7_SIOPE_2025_LIMEIRA_ANNUAL_RECEIPT_EFFECTIVE_DECLARATION_V1", "TASK_010N-R-E-M7", "c7c952ad641629db7acb7d93548f571da0ae79a3", "T0_OFFLINE_USER_MEDIATED_EVIDENCE_REVIEW", DECISION):
        raise ValueError("M7 identity, base, tier, or decision drifted")
    if data.get("scope") != SCOPE:
        raise ValueError("year, Annual/P6, UF, municipality, or municipality code drifted")
    if data.get("proof_status") != PROOF:
        raise ValueError("valid annual submission or effective-declaration boundary drifted")

    handoff = data.get("user_mediated_handoff", {})
    surface = handoff.get("receipt_surface", {})
    required_surface = {"provenance_class": "USER_MEDIATED_OFFICIAL_RECEIPT_STATUS", "source_authority": "FNDE/SIOPE", "url": "https://www.fnde.gov.br/siope/recibosTransmissao.do", "administration": "Municipal", "year": 2025, "period": 6, "period_label": "Annual", "uf": "SP", "uf_name": "São Paulo", "municipality_code": 352690, "municipality": "Limeira", "receipt_number_surface": "428477", "processing_timestamp": "13/02/2026 12:47", "transmission_timestamp": "09/02/2026 14:10", "situation": "Processado com sucesso\nCom manifestação do CACS", "declaration_retificadora": "Não", "mavs_availability": "Histórico", "artifact_sha256": None}
    if surface != required_surface:
        raise ValueError("receipt surface identity, receipt, timestamp, status, or hash drifted")

    mavs = handoff.get("mavs_history", {})
    rows = [(r.get("protocol"), r.get("transmission_timestamp"), r.get("action_timestamp"), r.get("status")) for r in mavs.get("ordered_history", [])]
    if rows != HISTORY or mavs.get("workflow_classification") != "RETRANSMISSION_WORKFLOW" or mavs.get("formal_retifying_declaration") != "NOT_INFERRED":
        raise ValueError("MAVS protocol/order drift or retransmission/retification conflation")
    if (mavs.get("year"), mavs.get("period"), mavs.get("municipality_code"), mavs.get("municipality")) != (2025, 6, 352690, "Limeira"):
        raise ValueError("MAVS identity drifted")

    pdf = handoff.get("official_receipt_pdf", {})
    required_pdf = {"provenance_class": "USER_MEDIATED_OFFICIAL_RECEIPT_PDF", "source_authority": "FNDE/SIOPE", "original_filename": "M352690_2025_6_428477.pdf", "artifact_available_in_workspace": True, "sha256": "41d5dba704d9de9309819ac1cb58a08bdbd85ae88d5dfdc3d1b936c654790e29", "byte_size": 22133, "magic_file_type": "application/pdf", "year": 2025, "period": 6, "period_label": "Annual", "uf_name": "Sao Paulo", "municipality_code": 352690, "municipality": "Limeira", "receipt_number": "428477-6", "siope_version": "25.0.4.5", "validation_code": "DA1C61.2776C0.971674.F240C0.", "document_title": "RECIBO DE TRANSMISSÃO", "successful_delivery_proposition": SUCCESS, "pdf_version": "1.3", "page_count": 1}
    if pdf != required_pdf:
        raise ValueError("PDF identity, receipt, validation, successful-delivery statement, or byte metadata drifted")

    reconciliation = data.get("deterministic_reconciliation", {})
    required_reconciliation = {"identity_match": {"year": 2025, "period": "Annual / 6", "uf": "SP / Sao Paulo", "municipality_code": 352690, "municipality": "Limeira"}, "receipt_surface_transmission": "09/02/2026 14:10", "mavs_protocol_832393_transmission": "09/02/2026 14:10", "pdf_successful_delivery": "09/02/2026 14:10:26", "receipt_surface_number": "428477", "pdf_receipt_number": "428477-6", "processing_timestamp": "13/02/2026 12:47", "mavs_publication_ready_timestamp": "13/02/2026 11:33", "identifier_rule": "MAVS_PROTOCOL_AND_RECEIPT_NUMBER_ARE_DISTINCT_IDENTIFIERS"}
    if reconciliation != required_reconciliation:
        raise ValueError("deterministic timestamp, identity, or distinct-identifier reconciliation drifted")

    sources = data.get("official_documentary_sources", [])
    signatures = [(s.get("authority"), s.get("url"), s.get("title"), s.get("version_or_date"), s.get("supports"), s.get("does_not_support")) for s in sources]
    if signatures != SOURCES:
        raise ValueError("exact ordered official source signature drifted")
    if data.get("partial_structural_retification_chain_evidence") != STRUCTURAL:
        raise ValueError("partial structural retification-chain proposition drifted")
    if data.get("documentary_discovery") != DISCOVERY:
        raise ValueError("exact documentary discovery record drifted")

    if data.get("resulting_state") != RESULT or data.get("canonical_state") != CANONICAL or data.get("context_only") != CONTEXT:
        raise ValueError("forbidden S1, S2, semantic, series, Gold, release, or 2026 promotion")
    guards = data.get("guards", {})
    expected_guards = {"protocol_831423_treated_as_successful_final_submission", "protocol_and_receipt_conflated", "retransmission_treated_as_formal_retification", "non_retifying_used_as_immutable_finality", "processing_success_used_alone_as_current_effective", "publication_ready_used_alone_as_current_effective", "pdf_hash_fabricated", "financial_indicator_values_in_b3_logic", "remote_writes", "publication"}
    if set(guards) != expected_guards or any(value not in (False, 0) for value in guards.values()):
        raise ValueError("B3 fail-closed guard drifted")
    return DECISION


def main():
    print(validate(json.loads(EVIDENCE.read_text(encoding="utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

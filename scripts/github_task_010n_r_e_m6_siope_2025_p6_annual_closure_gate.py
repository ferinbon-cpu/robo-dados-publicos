#!/usr/bin/env python3
"""Fail-closed offline B3 closure/finality gate for TASK 010N-R-E-M6."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_010N_R_E_M6_SIOPE_2025_P6_ANNUAL_CLOSURE_FINALITY_0.8.0.json"
DECISION = "KEEP_ANNUAL_CLOSURE_UNKNOWN_RECEIPT_STATUS_SURFACE_FOUND_EFFECTIVE_SELECTION_RULE_AND_LIMEIRA_ANNUAL_STATUS_NOT_PINNED"
FIELDS = ["DAT_DECL", "IDN_DECL_RETI", "DS_JUST_RETIFICACAO", "NUM_RECI", "NUM_SOLI", "TIPO", "IDN_TIPO_DECL", "DS_NOTA_RODAPE_RREO", "DS_NOTA_RODAPE_FUNDEB", "IDN_POSS_CERT_TC", "IDN_POSS_DECI_JUDI"]
RECEIPT_COLUMNS = ["Período", "Situação", "Nº do Recibo", "Data de Processamento", "Data de Transmissão", "Declaração Retificadora", "MAVS"]
SEARCH_TERMS = ["Recibos de Transmissão", "Declaração Retificadora", "Situação", "Processado com sucesso", "recibo anterior", "declaração anterior", "retificação", "substitui", "vigente", "último recibo", "última transmissão", "histórico", "MAVS"]
PROMOTION_BOUNDARY = "Observation alone cannot promote B3 without an official current/latest/effective selection rule for retifications or supersessions."
OBSERVATION_CONSTRAINTS = {"authentication": False, "drive": False, "financial_values": False, "NUM_POPU": False, "publication": False}
INDEXED_EXAMPLES = [
    {"provenance_kind": "TASK_HANDOFF_INDEXED_OFFICIAL_EVIDENCE_NOT_DOWNLOADED_BY_CODEX", "authority": "FNDE", "url": "https://www.fnde.gov.br/siope/recibosTransmissao.do?cod_uf=12&cod_uf_mun=24&consultar=Consultar&municipios=240860&tipoDeRecibo=1", "artifact_sha256": None, "propositions": ["Official indexed receipt page exposes 2025 - Anual.", "The official receipt surface supports the Declaração Retificadora Sim/Não distinction."], "does_not_support": "Current, latest, or effective declaration selection; Limeira 2025 status; immutable finality."},
    {"provenance_kind": "TASK_HANDOFF_INDEXED_OFFICIAL_EVIDENCE_NOT_DOWNLOADED_BY_CODEX", "authority": "FNDE", "url": "https://www.fnde.gov.br/siope/recibosTransmissao.do?cod_uf=12&cod_uf_mun=31&consultar=Consultar&municipios=313170&tipoDeRecibo=1", "artifact_sha256": None, "propositions": ["Official indexed receipt page exposes 2025 - Anual.", "At least one official indexed example exposes Declaração Retificadora = Sim.", "The official receipt surface supports the Declaração Retificadora Sim/Não distinction."], "does_not_support": "Current, latest, or effective declaration selection; Limeira 2025 status; immutable finality."},
]
SOURCE_SIGNATURES = [
    ("FNDE", "https://www.fnde.gov.br/phocadownload/sistemas/siope/Manuais/DICIONARIO%20DE%20DADOS%20SIOPE%202019.pdf", "Dicionário de Dados SIOPE 2019", "From 2017, period 6 is annual consolidation.", "A current-effective, superseded, pending-rectification, final, or locked status rule for Dados_Gerais_Siope."),
    ("FNDE", "https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/guia_prefeitos_2025.pdf", "Guia para Novos Prefeitos 2025", "Annual receipts, transmission deadlines, and transmission/validation of P6 as exercise-end delivery.", "Which API field/value proves that the exposed declaration is currently effective or source-final."),
    ("FNDE", "https://www.gov.br/fnde/pt-br/assuntos/sistemas/siope/media/Tutorial_Bsico_Siope_2024_v2.pdf", "Tutorial Básico SIOPE 2024 v2", "P6 can be formally rectified with authorization from the SIOPE technical team.", "That rectification possibility makes every submitted annual declaration ineffective, or a field/value selecting the current effective declaration."),
    ("FNDE", "https://www.fnde.gov.br/siope/recibosTransmissao.do", "SIOPE — Recibos de Transmissão", "SIOPE exposes receipt/status rows per period, including indexed 2025 - Anual examples, with processing status, receipt number, processing and transmission timestamps, explicit Declaração Retificadora Sim/Não, and MAVS.", "That a displayed row is Limeira 2025, current/latest/effective, that processing success proves repository closure, or that a non-retifying row cannot later be superseded."),
]
STATE = {"release_0_7_0": "ACTIVE", "release_0_8_0": "CANDIDATE", "year_2025": "PROVEN_STRUCTURAL_RECENT", "S1_NUM_POPU": "NOT_PROVEN", "S2_FINANCIAL_ALIAS_BRIDGE": "NOT_PROVEN", "financial_aliases_proven_exact_operational": "9/10", "annual_closure_status": "UNKNOWN", "semantic_comparability_status": "UNKNOWN", "closed_annual_series": "2016-2024", "gold_2025": "UNKNOWN/BLOCKED", "year_2026": "UNPROVEN_CURRENT_YEAR"}


def validate(data):
    identity = (data.get("evidence_schema"), data.get("task"), data.get("base_main_sha"), data.get("tier"))
    if identity != ("TASK_010N_R_E_M6_SIOPE_2025_P6_ANNUAL_CLOSURE_FINALITY_V1", "TASK_010N-R-E-M6", "bef759cd11f364519f84c822522cac1d028ca604", "T0_OFFLINE_REVIEW_WITH_BOUNDED_PUBLIC_DOCUMENTARY_DISCOVERY"):
        raise ValueError("identity, base, or tier drifted")
    if data.get("scope") != {"year": 2025, "period": 6, "municipality": "Limeira", "municipality_code": 352690, "uf": "SP", "resource": "Dados_Gerais_Siope"}:
        raise ValueError("year, P6, or Limeira identity drifted")
    model = data.get("closure_proof_model", {})
    required = {"ANNUAL_CONSOLIDATION", "VALID_ANNUAL_SUBMISSION", "CURRENTLY_EFFECTIVE_DECLARATION", "RECTIFICATION_POSSIBLE", "RECTIFICATION_PENDING", "SUPERSEDED_DECLARATION", "SOURCE_FINAL_LOCKED_STATE", "REPOSITORY_CLOSED_SERIES_ELIGIBILITY", "OFFICIAL_SIOPE_TRANSMISSION_RECEIPT_SURFACE"}
    if set(model) != required or not model["ANNUAL_CONSOLIDATION"].startswith("PROVEN:") or not model["CURRENTLY_EFFECTIVE_DECLARATION"].startswith("NOT_PROVEN:") or not model["OFFICIAL_SIOPE_TRANSMISSION_RECEIPT_SURFACE"].startswith("PROVEN_EXISTS"):
        raise ValueError("closure model, annual consolidation boundary, or official receipt surface missing")
    if data.get("historical_reconciliation", {}).get("classification") != "F_REPOSITORY_CONVENTION_WITHOUT_EXPLICIT_SOURCE_FINALITY_PROOF":
        raise ValueError("historical proof standard unreconciled")
    rows = data.get("candidate_field_inventory", [])
    if [r.get("field") for r in rows] != FIELDS:
        raise ValueError("status field missing or inventory drifted")
    expected_keys = {"field", "structural_presence", "observed_value", "official_definition", "original_vs_rectifying", "currently_effective", "proof_kind"}
    if any(set(r) != expected_keys or not r["structural_presence"] or r["observed_value"] is not None or r["official_definition"] is not None or r["original_vs_rectifying"] != "NOT_PROVEN" or r["currently_effective"] != "NOT_PROVEN" or r["proof_kind"] != "UNKNOWN" for r in rows):
        raise ValueError("unsupported or undocumented status semantics or fabricated status value")
    sources = data.get("official_documentary_sources", [])
    signatures = [(r.get("authority"), r.get("url"), r.get("title"), r.get("supports"), r.get("does_not_support")) for r in sources]
    if signatures != SOURCE_SIGNATURES:
        raise ValueError("official source rule URL, authority, title, or proposition drifted")
    if sources[-1].get("receipt_surface_columns") != RECEIPT_COLUMNS:
        raise ValueError("official receipt surface column drifted")
    if data.get("indexed_official_receipt_examples") != INDEXED_EXAMPLES:
        raise ValueError("indexed official receipt example URL, provenance, or proposition drifted")
    discovery = data.get("documentary_discovery", {})
    expected_discovery = {"attempted_on": "2026-08-30", "official_only": True, "search_terms": SEARCH_TERMS, "allowed_hosts": ["gov.br/fnde", "fnde.gov.br"], "receipt_surface_direct_attempt_result": "ENVIRONMENT_CONNECT_TUNNEL_HTTP_403", "official_search_connector_result": "HTTP_401_UNAUTHORIZED", "new_source_bytes_acquired": 0, "artifact_hashes_added": 0, "source_data_get_count": 0, "indexed_official_surface_proposition_incorporated_from_task_handoff": True, "selection_or_supersession_rule_result": "NOT_FOUND_OR_PINNED", "limitation": "The environment blocked the direct official page before an FNDE response and the search connector was unauthorized; no source bytes or selection/supersession rule were acquired."}
    if discovery != expected_discovery:
        raise ValueError("documentary discovery outcome drifted")
    observation = data.get("current_observation", {})
    if observation.get("performed") is not False or observation.get("next_action") != "USER_MEDIATED_OFFICIAL_RECEIPT_STATUS_HANDOFF" or observation.get("capture_only") != ["page identity/header", "municipality identity", *RECEIPT_COLUMNS] or observation.get("target") != {"administration": "Municipal", "uf": "São Paulo", "municipality": "Limeira", "exercise": 2025, "period": "Anual"} or observation.get("constraints") != OBSERVATION_CONSTRAINTS or observation.get("promotion_boundary") != PROMOTION_BOUNDARY:
        raise ValueError("Limeira annual receipt status fabricated or handoff drifted")
    if data.get("decision") != DECISION:
        raise ValueError("B3 decision drifted")
    expected_result = {"annual_closure_status": "UNKNOWN", "immutable_finality": "NOT_PROVEN_NOT_REQUIRED_FOR_MODEL_BUT_EFFECTIVE_STATUS_RULE_MISSING", "semantic_comparability_status": "UNKNOWN", "closed_series_2025_eligibility": "BLOCKED_BY_B3_EFFECTIVE_SELECTION_AND_LIMEIRA_STATUS_PLUS_S1_S2_SEMANTIC_COMPARABILITY", "closed_annual_series": "2016-2024", "gold_2025": "UNKNOWN/BLOCKED"}
    if data.get("resulting_state") != expected_result or data.get("canonical_state") != STATE:
        raise ValueError("forbidden semantic, series, Gold, release, or 2026 promotion")
    guards = data.get("guards", {})
    if set(guards) != {"annual_consolidation_alone_used_as_finality", "field_semantics_inferred", "rectification_possible_treated_as_automatic_ineffectiveness", "future_immutability_assumed", "remote_writes", "publication", "gold_computation", "receipt_row_claimed_current_latest_without_rule", "processing_success_used_as_immutable_finality", "non_retifying_used_as_immutable_finality", "limeira_annual_status_fabricated"} or any(value not in (False, 0) for value in guards.values()):
        raise ValueError("receipt finality or fail-closed guard drifted")
    return DECISION


def main():
    print(validate(json.loads(EVIDENCE.read_text(encoding="utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

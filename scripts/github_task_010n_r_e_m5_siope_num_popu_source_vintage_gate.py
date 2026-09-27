#!/usr/bin/env python3
"""Fail-closed, offline validator for TASK 010N-R-E-M5 evidence."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_010N_R_E_M5_SIOPE_NUM_POPU_SOURCE_VINTAGE_PROOF_0.8.0.json"
DECISION = "KEEP_S1_NUM_POPU_NOT_PROVEN_DEFINITION_SOURCE_VINTAGE_MISSING"
EXPECTED_TERMS = ["NUM_POPU", "POPULACAO", "POPULAÇÃO", "POPULACAO_ESTIMADA", "POP_ESTIMADA", "IBGE", "ESTIMATIVA", "CENSO", "HABITANTES", "Dados_Municipio", "population", "população residente", "data de referência", "ano de referência"]
EXPECTED_FILES = {
    "docs/tasks/TASK_007_SIOPE_2025_OFFICIAL_DOCUMENTARY_PROOF.md": "3081f0268c476b093bd2d5805e430b00da5ea3abbddc4dc17b08fe575382c27b",
    "docs/tasks/TASK_008_SIOPE_2025_ALIAS_FINALITY_AUDIT.md": "590742a5b7b306c95bdc5fc0ef042528ce8c37a73117998c808492600d220952",
    "docs/tasks/TASK_010A_SIOPE_2025_METADATA_OFFLINE_INSPECTOR.md": "0103bf8613a07889e4cf745cd851256b30f958008cb3bf002cd9129f24cedfa5",
    "docs/tasks/TASK_010J_SIOPE_2025_CML_CZIP_DECODER.md": "654083e4aa9a56f78aecd17c571455cb53fd83fef2ac8bfd56cb3f6f2159d791",
    "docs/evidence/TASK_010K_SIOPE_2025_OFFLINE_SEMANTIC_REVIEW_0.8.0.json": "6861167287d0c7a7415fd4b214977590730b95b757ef2200aa1c81017463c6a1",
    "docs/tasks/TASK_010N_SIOPE_2016_2025_CONTRACT_CONTINUITY_AUDIT.md": "9720fe83855c86e1c941d6d3db50162a0f233013e648b92d524218515f73a56c",
    "docs/tasks/TASK_010N_R_SIOPE_PROOF_STANDARD_RECONCILIATION.md": "f48c37243756e70ca5c64dc3c53210b60c321c2695ebd09601bdaa9c8165cf63",
    "docs/tasks/TASK_010N_R_E_M_SIOPE_DIRECT_METADATA_STOP.md": "de47bc0a2e4d5c8231e734309d088f971c18d92c9da9bb48491c7f693f4055a8",
    "docs/evidence/TASK_010N_R_E_M2_SIOPE_EDMX_HANDOFF_AUDIT_0.8.0.json": "72d2dbdddb74b7a24c648ccdf10583080ffae9c6b4a0c5c53ba9cd950fcbd91f",
    "robo_dados_publicos/sources/siope_client.py": "1573c346c2a9f2b1a49af337a7ffb41faeda01472eb80eaa67648baf3ceeaf33",
    "config/siope_historical_regimes.v1.json": "86f0267095a0bc72ca08a39fad79b90afdbc607d73076e84aab83d1b3f75cd58",
}
EXPECTED_SOURCES = [
    ("FNDE", "https://www.gov.br/fnde/pt-br/assuntos/sistemas/siope/downloads", None),
    ("FNDE", "https://www.fnde.gov.br/phocadownload/sistemas/siope/Manuais/DICIONARIO%20DE%20DADOS%20SIOPE%202019.pdf", None),
    ("FNDE", "https://www.gov.br/fnde/pt-br/assuntos/sistemas/siope/media/Tutorial_Bsico_Siope_2024_v2.pdf", None),
    ("FNDE", "https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata/$metadata", "6bf6a37ef190389db9420a6e6cd26f2ec7967c8920bcf61799252a017cdb30ca"),
]
EXPECTED_RESULTS = {
    "NUM_POPU_2025_SEMANTICS": "NOT_PROVEN_EXACT_SEMANTIC_DEFINITION_MISSING",
    "NUM_POPU_2025_SOURCE": "NOT_PROVEN_OFFICIAL_SOURCE_MAPPING_MISSING",
    "NUM_POPU_2025_VINTAGE": "NOT_PROVEN_REFERENCE_DATE_YEAR_VERSION_RULE_MISSING",
    "NUM_POPU_2025_VALUE_RECONCILIATION": "NOT_PERFORMED_SOURCE_AND_VINTAGE_RULE_NOT_PROVEN",
    "NUM_POPU_2016_2024_CONTINUITY": "NOT_PROVEN_NO_VERSIONED_HISTORICAL_SOURCE_AND_VINTAGE_RULE",
}
EXPECTED_STATE = {"release_0_7_0": "ACTIVE", "release_0_8_0": "CANDIDATE", "year_2025": "PROVEN_STRUCTURAL_RECENT", "S1_NUM_POPU": "NOT_PROVEN", "S2_FINANCIAL_ALIAS_BRIDGE": "NOT_PROVEN", "financial_aliases_proven_exact_operational": "9/10", "annual_closure_status": "UNKNOWN", "semantic_comparability_status": "UNKNOWN", "closed_annual_series": "2016-2024", "gold_2025": "UNKNOWN/BLOCKED", "year_2026": "UNPROVEN_CURRENT_YEAR"}


def validate(data, *, verify_files=True):
    identity = (data.get("evidence_schema"), data.get("software_version"), data.get("task"), data.get("base_main_sha"), data.get("tier"))
    if identity != ("TASK_010N_R_E_M5_SIOPE_NUM_POPU_SOURCE_VINTAGE_PROOF_V1", "0.8.0", "TASK_010N-R-E-M5", "0ebe0ffbb0d4ef85b3d07b4664c800ed22164567", "T0_OFFLINE_REVIEW_WITH_BOUNDED_PUBLIC_DOCUMENTARY_DISCOVERY"):
        raise ValueError("identity, base, version, or tier drifted")
    if data.get("scope") != {"year": 2025, "period": 6, "municipality": "Limeira", "uf": "SP", "field": "NUM_POPU"}:
        raise ValueError("observed year, period, municipality, UF, or field drifted")
    if data.get("search_terms") != EXPECTED_TERMS:
        raise ValueError("required search terms drifted")
    rows = data.get("offline_inventory", [])
    indexed = {row.get("path"): row.get("sha256") for row in rows if set(row) == {"path", "sha256", "finding"} and row.get("finding")}
    if len(rows) != len(EXPECTED_FILES) or indexed != EXPECTED_FILES:
        raise ValueError("offline inventory path, finding, or hash drifted")
    if verify_files:
        for path, expected in EXPECTED_FILES.items():
            if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
                raise ValueError(f"pinned offline artifact changed: {path}")
    sources = data.get("official_documentary_sources", [])
    if [(r.get("authority"), r.get("url"), r.get("artifact_sha256")) for r in sources] != EXPECTED_SOURCES:
        raise ValueError("official authority, URL, or artifact hash drifted")
    required_source_keys = {"authority", "url", "title", "publication_or_version_date", "artifact_sha256", "supports", "does_not_support"}
    if any(set(r) != required_source_keys or not r["title"] or not r["publication_or_version_date"] or not r["supports"] or not r["does_not_support"] for r in sources):
        raise ValueError("source proposition or provenance is incomplete")
    if data.get("proof_results") != EXPECTED_RESULTS:
        raise ValueError("definition, source, vintage, reconciliation, or continuity result drifted")
    target = data.get("observed_target")
    expected_target = {"year": 2025, "period": 6, "municipality": "Limeira", "uf": "SP", "value_used_for_reconciliation": None, "comparison_mode": "DISABLED_UNTIL_RULE_PROVEN", "approximate_equality_accepted": False}
    if target != expected_target:
        raise ValueError("observed target changed or approximate/value reconciliation was enabled")
    discovery = data.get("bounded_discovery", {})
    if discovery != {"attempted_on": "2026-08-30", "allowlisted_official_url_attempt_count": 3, "successful_official_artifact_download_count": 0, "result": "ENVIRONMENT_CONNECT_TUNNEL_HTTP_403", "authentication_attempt_count": 0, "siope_data_endpoint_call_count": 0, "drive_call_count": 0, "limitation": "The environment blocked direct official-site connections before an HTTP response from the source; no new source bytes or claims were obtained."}:
        raise ValueError("bounded discovery limits or observed limitation drifted")
    next_artifact = data.get("smallest_human_mediated_artifact_needed", {})
    if set(next_artifact) != {"artifact", "acceptance"} or not all(next_artifact.values()):
        raise ValueError("smallest human-mediated artifact is missing")
    if data.get("canonical_state") != EXPECTED_STATE:
        raise ValueError("forbidden global state promotion")
    guards = {"historical_rule_substituted_for_current": False, "field_name_semantics_inferred": False, "numerical_coincidence_used_to_invent_rule": False, "remote_writes": 0, "publication": False, "gold_computation": False}
    if data.get("guards") != guards or data.get("decision") != DECISION:
        raise ValueError("fail-closed guard or S1 decision drifted")
    return DECISION


def main():
    print(validate(json.loads(EVIDENCE.read_text(encoding="utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

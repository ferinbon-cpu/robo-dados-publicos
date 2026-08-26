from __future__ import annotations

import hashlib
import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_EXACT_CONTRACT_CORROBORATION_REVIEW"

EXPECTED_COUNTS = {
    "parsed_script_count": 40,
    "source_read_count": 40,
    "source_read_failure_count": 0,
    "callable_occurrence_count": 4,
    "location_hash_family_count": 2,
    "ngroute_family_count": 2,
    "ambiguous_family_count": 0,
    "location_hash_family_all_parameter_names_1024_count": 2,
    "location_hash_token_nearest_left_4096_count": 2,
    "location_hash_token_nearest_right_4096_count": 0,
    "location_hash_token_nearest_tie_4096_count": 0,
    "format_nearest_left_16384_count": 2,
    "format_nearest_right_16384_count": 0,
    "format_nearest_tie_16384_count": 0,
    "format_absent_16384_count": 0,
    "odata_nearest_left_65536_count": 0,
    "odata_nearest_right_65536_count": 2,
    "odata_nearest_tie_65536_count": 0,
    "odata_absent_65536_count": 0,
    "nearest_location_hash_and_format_same_side_count": 2,
    "nearest_format_and_odata_same_side_count": 0,
    "nearest_all_three_same_side_count": 0,
    "nearest_all_three_left_count": 0,
    "nearest_all_three_right_count": 0,
}

EXPECTED_INTERPRETATION = {
    "loaded_script_coverage_status": "FORTY_PARSED_FORTY_READ_ZERO_FAILURES_ON_PINNED_RUN",
    "family_partition_status": "EXACT_TWO_LOCATION_HASH_AND_TWO_NGROUTE_WITH_ZERO_AMBIGUOUS_OCCURRENCES",
    "parameter_locality_status": "BOTH_LOCATION_HASH_OCCURRENCES_HAVE_ALL_THREE_PARAMETER_NAMES_WITHIN_1024_CHARS",
    "location_hash_side_status": "BOTH_LOCATION_HASH_TOKENS_NEAREST_LEFT_WITHIN_4096",
    "format_side_status": "BOTH_FORMAT_TOKENS_NEAREST_LEFT_WITHIN_16384",
    "odata_side_status": "BOTH_ODATA_TOKENS_NEAREST_RIGHT_WITHIN_65536",
    "location_hash_format_relation_status": "LOCATION_HASH_AND_FORMAT_SAME_SIDE_FOR_BOTH_LOCATION_HASH_FAMILY_OCCURRENCES",
    "format_odata_relation_status": "FORMAT_AND_ODATA_OPPOSITE_SIDES_FOR_BOTH_LOCATION_HASH_FAMILY_OCCURRENCES",
    "all_three_relation_status": "ZERO_ALL_THREE_SAME_SIDE_OCCURRENCES",
    "semantic_limit": "SIDE_AND_ORDER_COUNTS_ONLY_NOT_SAME_STATEMENT_EXPRESSION_DATAFLOW_OR_EXECUTABLE_RESOURCE_CONTRACT",
    "resource_route_contract_status": "UNPROVEN",
    "callable_semantics_status": "UNPROVEN",
    "next_safe_surface": "EXACT_CONTRACT_CORROBORATION_REVIEW_BEFORE_ANY_MINIMAL_RESOURCE_GET",
}

EXPECTED_CORROBORATORS = [
    "StrategicProjects/tesouror@6781890d7174f4ab9cbf9ce7bfbd38dc723c949f",
    "StrategicProjects/tesouropy@b49f5e46f03e199f336675bf370da231cc0fd57a",
    "BrenoNsm/painelEduca",
    "tuffyli/RA_work",
    "InstitutoSESI/dashboard-pne-react",
    "michaelferreir12345678/plataforma_fiscal_backend",
]


class SiopeOfficialOlindaExactContractCorroborationReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaExactContractCorroborationReviewError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def git_blob_sha(path: str | Path) -> str:
    data = Path(path).read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaExactContractCorroborationReviewError(f"{ERROR}_{code}")


def run_review(
    config: dict,
    evidence: dict,
    *,
    evidence_path: str | Path,
    corroboration_path: str | Path,
) -> dict:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_EXACT_CONTRACT_CORROBORATION_REVIEW_0_8_0", "GATE")
    _require(config.get("software_version"), "0.8.0", "VERSION")
    _require(config.get("mode"), "OFFLINE_PINNED_OFFICIAL_EVIDENCE_AND_EXTERNAL_CORROBORATION_REVIEW", "MODE")
    _require(config.get("network_called"), False, "NETWORK")
    _require(git_blob_sha(evidence_path), config.get("pinned_evidence_blob_sha"), "EVIDENCE_BLOB_SHA")
    _require(git_blob_sha(corroboration_path), config.get("pinned_corroboration_blob_sha"), "CORROBORATION_BLOB_SHA")

    _require(evidence.get("run_id"), config.get("pinned_run_id"), "RUN")
    _require(evidence.get("run_number"), config.get("pinned_run_number"), "RUN_NUMBER")
    _require(evidence.get("job_id"), config.get("pinned_job_id"), "JOB")
    _require(evidence.get("event"), "workflow_dispatch", "EVENT")
    _require(evidence.get("branch"), "main", "BRANCH")
    _require(evidence.get("head_sha"), config.get("pinned_head_sha"), "HEAD")
    _require(evidence.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOCATION_HASH_ODATA_SIDE_DIAGNOSTICS", "STATUS")
    _require(evidence.get("location_hash_odata_side_counts"), EXPECTED_COUNTS, "COUNTS")
    _require(evidence.get("interpretation"), EXPECTED_INTERPRETATION, "INTERPRETATION")

    artifact = evidence.get("artifact") or {}
    _require(artifact.get("id"), config.get("pinned_artifact_id"), "ARTIFACT_ID")
    _require(artifact.get("digest"), config.get("pinned_artifact_digest"), "ARTIFACT_DIGEST")
    qa = evidence.get("qa") or {}
    _require(qa.get("unit_tests"), config.get("pinned_unit_tests"), "QA_UNIT")
    _require(qa.get("unit_tests_passed"), config.get("pinned_unit_tests"), "QA_UNIT_PASS")
    _require(qa.get("historical_regressions"), config.get("pinned_historical_regressions"), "QA_HIST")
    _require(qa.get("historical_regressions_passed"), config.get("pinned_historical_regressions"), "QA_HIST_PASS")

    _require(config.get("candidate_base_url"), "https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata", "BASE_URL")
    _require(config.get("candidate_resource"), "Dados_Gerais_Siope(Ano_Consulta=@Ano_Consulta,Num_Peri=@Num_Peri,Sig_UF=@Sig_UF)", "RESOURCE")
    _require(config.get("candidate_query_keys"), ["@Ano_Consulta", "@Num_Peri", "@Sig_UF", "$format"], "QUERY_KEYS")
    _require(config.get("required_independent_corroborators"), EXPECTED_CORROBORATORS, "CORROBORATORS")
    _require(config.get("external_corroboration_is_authorization"), False, "EXTERNAL_AUTHORIZATION")
    for key in ("resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled"):
        _require(config.get(key), False, key.upper())
    for key in ("route_synthesis_or_guessing", "automatic_route_promotion", "pilot_limeira_values_send"):
        _require(config.get(key), "PROHIBITED", key.upper())

    safety = evidence.get("safety") or {}
    _require(safety.get("resource_data_request_performed"), False, "RESOURCE_REQUEST_ALREADY_PERFORMED")
    _require(safety.get("pilot_limeira_values_sent"), False, "LIMEIRA_VALUES")
    _require(safety.get("route_synthesized_or_guessed"), False, "ROUTE_GUESSED")
    _require(safety.get("automatic_route_promotion"), False, "ROUTE_PROMOTED")
    _require(safety.get("remote_writes"), "NONE", "REMOTE_WRITES")

    dossier = Path(corroboration_path).read_text(encoding="utf-8")
    for marker in (
        "CORROBORATION_ONLY_NOT_AUTHORIZATION",
        "Dados_Gerais_Siope(Ano_Consulta=@Ano_Consulta,Num_Peri=@Num_Peri,Sig_UF=@Sig_UF)",
        "StrategicProjects/tesouror",
        "StrategicProjects/tesouropy",
        "BrenoNsm/painelEduca",
        "tuffyli/RA_work",
        "InstitutoSESI/dashboard-pne-react",
        "michaelferreir12345678/plataforma_fiscal_backend",
        "nenhum GET de recurso foi realizado",
    ):
        if marker not in dossier:
            raise SiopeOfficialOlindaExactContractCorroborationReviewError(f"{ERROR}_DOSSIER_MARKER")

    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_EXACT_CONTRACT_CORROBORATION_REVIEW",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "review_mode": config["mode"],
        "official_evidence_run_id": config["pinned_run_id"],
        "official_evidence_artifact_id": config["pinned_artifact_id"],
        "corroborator_count": len(EXPECTED_CORROBORATORS),
        "contract_status": "OFFICIAL_PASSIVE_EVIDENCE_PLUS_STRONG_EXTERNAL_CORROBORATION_READY_FOR_MINIMAL_GET_DESIGN",
        "semantic_limit": "CORROBORATION_DOES_NOT_PROVE_EXECUTABLE_CONTRACT_UNTIL_MANUAL_MINIMAL_GET_GATE_PASSES",
        "network_called": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }

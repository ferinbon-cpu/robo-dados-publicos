from __future__ import annotations

import hashlib
import json
from pathlib import Path

from robo_dados_publicos.sources.siope_client import PROVEN_DADOS_GERAIS_FIELDS, build_dados_gerais_url
from robo_dados_publicos.sources.siope_client_limeira_historical_parameterized_generalization import build_parameterized_plan

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_PARAMETERIZED_PIPELINE_DRY_RUN"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_PARAMETERIZED_PIPELINE_DRY_RUN"

EXPECTED_STAGES = (
    "SOURCE_CAPTURE",
    "BRONZE_CREATE_ONLY",
    "BRONZE_READBACK",
    "SILVER_LOSSLESS",
    "SILVER_CREATE_ONLY",
    "SILVER_READBACK",
    "GOLD_ARITHMETIC",
    "GOLD_CREATE_ONLY",
    "GOLD_READBACK",
)


class HistoricalParameterizedPipelineDryRunError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise HistoricalParameterizedPipelineDryRunError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise HistoricalParameterizedPipelineDryRunError(f"{ERROR}_{code}")


def _git_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()  # noqa: S324


def validate_config(config: dict) -> dict:
    expected = {
        "batch_live_authorized": False,
        "drive_called": False,
        "drive_write_authorized": False,
        "dry_run_years": [2024, 2023, 2022, 2021],
        "equivalence_years": [2024, 2023, 2022],
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_PARAMETERIZED_PIPELINE_DRY_RUN_0_8_0",
        "generalization_evidence": {
            "blob_sha": "d24cac39e7ceeff176b88415e647e1a3281ffd40",
            "path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_PARAMETERIZED_GENERALIZATION_RUN_1_0.8.0.json",
            "run_id": 33117758959,
        },
        "historical_collection_authorized": False,
        "individual_year_workflow_duplication_authorized": False,
        "max_years_per_future_batch": 5,
        "mode": "OFFLINE_HISTORICAL_PARAMETERIZED_PIPELINE_DRY_RUN",
        "municipality_code": 352690,
        "municipality_name": "Limeira",
        "network_called": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_PARAMETERIZED_SINGLE_YEAR_PILOT_0_8_0",
        "pagination_authorized": False,
        "period": 6,
        "pilot_year": 2021,
        "processing_live_authorized": False,
        "recurrence_authorized": False,
        "retry_authorized": False,
        "schedule_enabled": False,
        "schema_key_count": 52,
        "software_version": "0.8.0",
        "source_get_authorized": False,
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "stage_count": 9,
        "uf": "SP",
    }
    _require(config, expected, "CONFIG_DRIFT")
    return config


def _validate_generalization_evidence(evidence: dict, *, run_id: int) -> None:
    expected = {
        "artifact_digest": "sha256:235a1dd3400f1cb26cfa71e3e259554a975e77ecaf35450a90500d677f0fde5b",
        "artifact_id": 9665193591,
        "artifact_name": "siope-client-limeira-historical-parameterized-generalization-33117758959",
        "artifact_result_sha256": "e3b178a85071818b9724cffc3fb031c685b716f22ed6c8f9a7ccd92576cd8ba7",
        "artifact_result_size_bytes": 914,
        "artifact_size_bytes": 526,
        "batch_live_authorized": False,
        "bounded_batch_plan_year_count": 5,
        "drive_called": False,
        "full_pipeline_evidence_years": [2024, 2023, 2022],
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_PARAMETERIZED_GENERALIZATION_0_8_0",
        "generic_year_parameter_verified": True,
        "head_sha": "6ba078901c31bfcfda9c401458fc34f1557fd3de",
        "historical_failures": 0,
        "historical_passes": 109,
        "historical_tests": 109,
        "individual_year_workflow_duplication_authorized": False,
        "job_id": 98676692652,
        "max_years_per_future_batch": 5,
        "network_called": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_PARAMETERIZED_PIPELINE_DRY_RUN_0_8_0",
        "pagination_authorized": False,
        "parameterized_pipeline_design_authorized": True,
        "pilot_plan_year_count": 1,
        "processing_live_authorized": False,
        "read_only_evidence_years": [2021],
        "recurrence_authorized": False,
        "retry_authorized": False,
        "run_id": run_id,
        "run_number": 1,
        "schedule_enabled": False,
        "schema_key_count": 52,
        "software_version": "0.8.0",
        "status": "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_PARAMETERIZED_GENERALIZATION",
        "unit_failures": 0,
        "unit_passes": 1155,
        "unit_tests": 1155,
        "workflow_event": "workflow_dispatch",
        "workflow_head_branch": "main",
    }
    _require(evidence, expected, "GENERALIZATION_EVIDENCE_DRIFT")


def _normalized_url_template(url: str, year: int) -> str:
    token = f"@Ano_Consulta={year}"
    if token not in url:
        raise HistoricalParameterizedPipelineDryRunError(f"{ERROR}_YEAR_TOKEN_MISSING")
    return url.replace(token, "@Ano_Consulta={YEAR}", 1)


def _normalized_plan(item: dict) -> dict:
    return {"year": "{YEAR}", "period": item["period"], "stages": item["stages"]}


def review(config: dict, *, root: str | Path) -> dict:
    validate_config(config)
    root = Path(root)
    meta = config["generalization_evidence"]
    evidence_path = root / meta["path"]
    raw = evidence_path.read_bytes()
    _require(_git_blob_sha(raw), meta["blob_sha"], "GENERALIZATION_EVIDENCE_BLOB_SHA")
    _validate_generalization_evidence(load_json(evidence_path), run_id=meta["run_id"])

    _require(len(PROVEN_DADOS_GERAIS_FIELDS), config["schema_key_count"], "PROVEN_SCHEMA_COUNT")
    _require(len(EXPECTED_STAGES), config["stage_count"], "STAGE_COUNT")

    plan = build_parameterized_plan(config["dry_run_years"], period=config["period"])
    _require(len(plan), len(config["dry_run_years"]), "PLAN_YEAR_COUNT")
    for item, year in zip(plan, config["dry_run_years"], strict=True):
        _require(item["year"], year, f"PLAN_{year}_YEAR")
        _require(item["period"], config["period"], f"PLAN_{year}_PERIOD")
        _require(tuple(item["stages"]), EXPECTED_STAGES, f"PLAN_{year}_STAGES")

    plan_templates = {_normalized_plan(item)["period"]: _normalized_plan(item) for item in plan}
    _require(len(plan_templates), 1, "PLAN_TEMPLATE_EQUIVALENCE")

    urls = [
        build_dados_gerais_url(
            ano=year,
            periodo=config["period"],
            uf=config["uf"],
            municipality_code=config["municipality_code"],
        )
        for year in config["dry_run_years"]
    ]
    url_templates = {_normalized_url_template(url, year) for url, year in zip(urls, config["dry_run_years"], strict=True)}
    _require(len(url_templates), 1, "SOURCE_URL_TEMPLATE_EQUIVALENCE")

    equivalence_plan = build_parameterized_plan(config["equivalence_years"], period=config["period"])
    _require([item["year"] for item in equivalence_plan], config["equivalence_years"], "EQUIVALENCE_YEARS")
    _require(all(tuple(item["stages"]) == EXPECTED_STAGES for item in equivalence_plan), True, "EQUIVALENCE_STAGE_CONTRACT")

    pilot_plan = build_parameterized_plan([config["pilot_year"]], period=config["period"])
    _require(len(pilot_plan), 1, "PILOT_PLAN_COUNT")
    _require(tuple(pilot_plan[0]["stages"]), EXPECTED_STAGES, "PILOT_STAGE_CONTRACT")

    return {
        "status": PASS,
        "gate_id": config["gate_id"],
        "network_called": False,
        "drive_called": False,
        "mutation_count": 0,
        "source_get_authorized": False,
        "drive_write_authorized": False,
        "dry_run_years": config["dry_run_years"],
        "dry_run_year_count": len(plan),
        "equivalence_years": config["equivalence_years"],
        "pilot_year": config["pilot_year"],
        "stage_count_per_year": len(EXPECTED_STAGES),
        "stage_contract_equivalent": True,
        "source_url_template_equivalent": True,
        "schema_key_count": config["schema_key_count"],
        "individual_year_workflow_duplication_authorized": False,
        "historical_collection_authorized": False,
        "batch_live_authorized": False,
        "max_years_per_future_batch": config["max_years_per_future_batch"],
        "retry_authorized": False,
        "pagination_authorized": False,
        "processing_live_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from robo_dados_publicos.sources.siope_client import PROVEN_DADOS_GERAIS_FIELDS, build_dados_gerais_url

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_PARAMETERIZED_GENERALIZATION"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_PARAMETERIZED_GENERALIZATION"


class HistoricalParameterizedGeneralizationError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise HistoricalParameterizedGeneralizationError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise HistoricalParameterizedGeneralizationError(f"{ERROR}_{code}")


def _git_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()  # noqa: S324


def validate_config(config: dict) -> dict:
    expected = {
        "batch_live_authorized": False,
        "compliance_claims_authorized": False,
        "evidence": {
            "2021_readonly": {
                "blob_sha": "6c13b93f4f95843f5449083527edd8b8faf895b8",
                "path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2021_P6_FULL_SCHEMA_READONLY_VALIDATION_RUN_1_0.8.0.json",
                "run_id": 33105190675,
            },
            "2022_gold_readback": {
                "blob_sha": "71b916f829e2aaac1c5652bd097e923f10e6dcc8",
                "path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_GOLD_DRIVE_READBACK_VERIFICATION_RUN_1_0.8.0.json",
                "run_id": 33103337072,
            },
            "2023_gold_readback": {
                "blob_sha": "e344a7d01e9226b13fd4169373cd2a5fc8aedcb8",
                "path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_GOLD_DRIVE_READBACK_VERIFICATION_RUN_1_0.8.0.json",
                "run_id": 33065919823,
            },
            "2024_gold_readback": {
                "blob_sha": "291dbd782e89552d8958eebcca69f04fb773d73a",
                "path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_GOLD_DRIVE_READBACK_VERIFICATION_RUN_1_0.8.0.json",
                "run_id": 33026528414,
            },
        },
        "full_pipeline_evidence_years": [2024, 2023, 2022],
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_PARAMETERIZED_GENERALIZATION_0_8_0",
        "historical_collection_authorized": False,
        "imputation_authorized": False,
        "individual_year_workflow_duplication_authorized": False,
        "max_years_per_future_batch": 5,
        "mode": "OFFLINE_HISTORICAL_PARAMETERIZED_GENERALIZATION_REVIEW",
        "municipality_code": 352690,
        "municipality_name": "Limeira",
        "network_called": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_PARAMETERIZED_PIPELINE_DRY_RUN_0_8_0",
        "pagination_authorized": False,
        "parameterized_pipeline_design_authorized": True,
        "period": 6,
        "processing_live_authorized": False,
        "read_only_evidence_years": [2021],
        "recurrence_authorized": False,
        "retry_authorized": False,
        "schedule_enabled": False,
        "schema_key_count": 52,
        "software_version": "0.8.0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "uf": "SP",
    }
    _require(config, expected, "CONFIG_DRIFT")
    return config


def _validate_gold_evidence(evidence: dict, *, year: int, run_id: int) -> None:
    _require(evidence.get("run_id"), run_id, f"EVIDENCE_{year}_RUN")
    _require(evidence.get("byte_identity_verified"), True, f"EVIDENCE_{year}_BYTE_IDENTITY")
    _require(evidence.get("drive_file_download_count"), 1, f"EVIDENCE_{year}_READBACK_COUNT")
    _require(evidence.get("drive_write_count"), 0, f"EVIDENCE_{year}_READBACK_WRITES")
    _require(evidence.get("metric_count"), 8, f"EVIDENCE_{year}_METRICS")
    _require(evidence.get("gold_contract"), "SIOPE_DADOS_GERAIS_LIMEIRA_ARITHMETIC_SUMMARY_GOLD_V1", f"EVIDENCE_{year}_CONTRACT")
    _require(evidence.get("compliance_claims_authorized"), False, f"EVIDENCE_{year}_COMPLIANCE")
    _require(evidence.get("imputation_performed"), False, f"EVIDENCE_{year}_IMPUTATION")
    remote_name = str(evidence.get("remote_name", ""))
    if f"__{year}_P6__352690__" not in remote_name:
        raise HistoricalParameterizedGeneralizationError(f"{ERROR}_EVIDENCE_{year}_IDENTITY")
    if not str(evidence.get("status", "")).startswith("PASS_M7_SIOPE_CLIENT_LIMEIRA"):
        raise HistoricalParameterizedGeneralizationError(f"{ERROR}_EVIDENCE_{year}_STATUS")


def _validate_readonly_evidence(evidence: dict, *, year: int, run_id: int) -> None:
    _require(evidence.get("run_id"), run_id, f"EVIDENCE_{year}_RUN")
    _require(evidence.get("generic_client_used"), True, f"EVIDENCE_{year}_GENERIC_CLIENT")
    _require(evidence.get("request_count"), 1, f"EVIDENCE_{year}_REQUEST_COUNT")
    _require(evidence.get("response_status"), 200, f"EVIDENCE_{year}_HTTP")
    _require(evidence.get("value_count"), 1, f"EVIDENCE_{year}_VALUE_COUNT")
    _require(evidence.get("selected_schema_exact"), True, f"EVIDENCE_{year}_SCHEMA")
    _require(evidence.get("selected_schema_key_count"), 52, f"EVIDENCE_{year}_SCHEMA_COUNT")
    for key in (
        "all_records_match_municipality_code",
        "all_records_match_municipality_name",
        "all_records_match_period",
        "all_records_match_state",
        "all_records_match_year",
    ):
        _require(evidence.get(key), True, f"EVIDENCE_{year}_{key.upper()}")
    _require(evidence.get("historical_collection_authorized"), False, f"EVIDENCE_{year}_COLLECTION")
    _require(evidence.get("persistence_authorized"), False, f"EVIDENCE_{year}_PERSISTENCE")
    _require(evidence.get("retry_performed"), False, f"EVIDENCE_{year}_RETRY")
    _require(evidence.get("odata_nextlink_followed"), False, f"EVIDENCE_{year}_PAGINATION")


def build_parameterized_plan(years: list[int], *, period: int = 6) -> list[dict]:
    if not years or len(years) != len(set(years)):
        raise HistoricalParameterizedGeneralizationError(f"{ERROR}_YEARS_UNIQUE_NONEMPTY")
    if years != sorted(years, reverse=True):
        raise HistoricalParameterizedGeneralizationError(f"{ERROR}_YEARS_DESCENDING")
    if len(years) > 5:
        raise HistoricalParameterizedGeneralizationError(f"{ERROR}_BATCH_LIMIT")
    if period != 6:
        raise HistoricalParameterizedGeneralizationError(f"{ERROR}_PERIOD")
    stages = (
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
    return [{"year": year, "period": period, "stages": list(stages)} for year in years]


def review(config: dict, *, root: str | Path) -> dict:
    validate_config(config)
    root = Path(root)
    for key, meta in config["evidence"].items():
        path = root / meta["path"]
        raw = path.read_bytes()
        _require(_git_blob_sha(raw), meta["blob_sha"], f"{key.upper()}_BLOB_SHA")
        evidence = load_json(path)
        year = int(key[:4])
        if key.endswith("gold_readback"):
            _validate_gold_evidence(evidence, year=year, run_id=meta["run_id"])
        else:
            _validate_readonly_evidence(evidence, year=year, run_id=meta["run_id"])

    _require(len(PROVEN_DADOS_GERAIS_FIELDS), config["schema_key_count"], "PROVEN_SCHEMA_COUNT")
    for year in [2024, 2023, 2022, 2021, 2020]:
        url = build_dados_gerais_url(
            ano=year,
            periodo=config["period"],
            uf=config["uf"],
            municipality_code=config["municipality_code"],
        )
        if f"@Ano_Consulta={year}" not in url or "$filter=COD_MUNI%20eq%20352690" not in url:
            raise HistoricalParameterizedGeneralizationError(f"{ERROR}_GENERIC_CLIENT_YEAR_PARAMETER")

    pilot_plan = build_parameterized_plan([2021])
    bounded_batch_plan = build_parameterized_plan([2020, 2019, 2018, 2017, 2016])
    return {
        "status": PASS,
        "gate_id": config["gate_id"],
        "network_called": False,
        "drive_called": False,
        "full_pipeline_evidence_years": config["full_pipeline_evidence_years"],
        "read_only_evidence_years": config["read_only_evidence_years"],
        "schema_key_count": config["schema_key_count"],
        "generic_year_parameter_verified": True,
        "individual_year_workflow_duplication_authorized": False,
        "parameterized_pipeline_design_authorized": True,
        "pilot_plan_year_count": len(pilot_plan),
        "bounded_batch_plan_year_count": len(bounded_batch_plan),
        "max_years_per_future_batch": config["max_years_per_future_batch"],
        "batch_live_authorized": False,
        "retry_authorized": False,
        "pagination_authorized": False,
        "processing_live_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }

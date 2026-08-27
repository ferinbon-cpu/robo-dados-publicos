from __future__ import annotations

import hashlib
import json
from pathlib import Path

from robo_dados_publicos.sources.siope_client import (
    PROVEN_DADOS_GERAIS_FIELDS,
    SiopeClient,
    SiopeClientPolicy,
)
from robo_dados_publicos.sources.siope_client_limeira_historical_parameterized_single_year_pilot import (
    ERROR as SINGLE_YEAR_PILOT_ERROR,
    EXPECTED_STAGES,
    HistoricalParameterizedSingleYearPilotError,
    _build_payloads,
    _put_and_readback,
    _record_from_page,
)
from robo_dados_publicos.storage.drive_rest import DriveRESTClient, OAuthCredentials, TokenProvider

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_BOUNDED_BATCH_AUTHORIZATION"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_BOUNDED_BATCH_AUTHORIZATION"


class HistoricalBoundedBatchAuthorizationError(RuntimeError):
    pass


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise HistoricalBoundedBatchAuthorizationError(f"{ERROR}_{code}")


def _translate_pilot_validation_error(exc: HistoricalParameterizedSingleYearPilotError) -> None:
    text = str(exc)
    prefix = f"{SINGLE_YEAR_PILOT_ERROR}_"
    code = text[len(prefix) :] if text.startswith(prefix) else "PILOT_HELPER"
    raise HistoricalBoundedBatchAuthorizationError(f"{ERROR}_{code}") from None


def _git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()  # noqa: S324


def validate_config(config: dict, *, root: str | Path) -> dict:
    expected = {
        "batch_live_authorized": True,
        "batch_years": [2020, 2019, 2018, 2017, 2016],
        "bounded_batch_only": True,
        "bronze_folder_id": "18yR-e6I1VCiy7XqG7Zhr0vUIJF0qA_MG",
        "compliance_claims_authorized": False,
        "create_only": True,
        "delete_authorized": False,
        "drive_download_count": 15,
        "drive_preflight_collision_checks": 15,
        "drive_write_count": 15,
        "future_batch_execution_authorized": False,
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_BOUNDED_BATCH_AUTHORIZATION_0_8_0",
        "gold_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_ARITHMETIC_SUMMARY_GOLD_V1",
        "gold_folder_id": "1hAmQNBnY6MNBtyr14ACfVfRkmWhsoRq4",
        "historical_collection_authorized": True,
        "imputation_authorized": False,
        "individual_year_workflow_duplication_authorized": False,
        "manual_confirmation_required": True,
        "max_years_per_batch": 5,
        "mime_type": "application/json",
        "mode": "BOUNDED_LIVE_PARAMETERIZED_HISTORICAL_BATCH",
        "municipality_code": 352690,
        "municipality_name": "Limeira",
        "next_state": "HISTORICAL_PARAMETERIZED_ARCHITECTURE_COMPLETE_AFTER_PASS",
        "overwrite_authorized": False,
        "pagination_authorized": False,
        "period": 6,
        "pilot_evidence": {
            "blob_sha": "7e8d9bada48a1185753cda95ab64a4ac51488eec",
            "path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_PARAMETERIZED_SINGLE_YEAR_PILOT_RUN_1_0.8.0.json",
            "run_id": 33123669920,
        },
        "recurrence_authorized": False,
        "replace_authorized": False,
        "retry_authorized": False,
        "schedule_enabled": False,
        "schema_key_count": 52,
        "silver_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_HISTORICAL_VALIDATED_RECORD_SILVER_V1",
        "silver_folder_id": "1_wl3Y90-RYKSBXUg53My5K6lxCUnIBNo",
        "single_execution_only": True,
        "software_version": "0.8.0",
        "source_get_count": 5,
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "stage_count_per_year": 9,
        "total_stage_count": 45,
        "uf": "SP",
    }
    _require(config, expected, "CONFIG_DRIFT")
    years = config["batch_years"]
    _require(len(PROVEN_DADOS_GERAIS_FIELDS), 52, "SCHEMA_ALLOWLIST_COUNT")
    _require(len(years), config["max_years_per_batch"], "BATCH_YEAR_COUNT")
    _require(len(years) <= 5, True, "BATCH_BOUND")
    _require(years, sorted(set(years), reverse=True), "BATCH_YEARS_UNIQUE_DESCENDING")
    _require(all(isinstance(year, int) and year < 2021 for year in years), True, "BATCH_YEAR_RANGE")
    _require(config["source_get_count"], len(years), "SOURCE_GET_COUNT")
    _require(config["drive_preflight_collision_checks"], len(years) * 3, "COLLISION_CHECK_COUNT")
    _require(config["drive_write_count"], len(years) * 3, "DRIVE_WRITE_COUNT")
    _require(config["drive_download_count"], len(years) * 3, "DRIVE_DOWNLOAD_COUNT")
    _require(config["total_stage_count"], len(years) * len(EXPECTED_STAGES), "TOTAL_STAGE_COUNT")

    meta = config["pilot_evidence"]
    path = Path(root) / meta["path"]
    raw = path.read_bytes()
    _require(_git_blob_sha(raw), meta["blob_sha"], "PILOT_EVIDENCE_BLOB_SHA")
    evidence = json.loads(raw.decode("utf-8"))
    _require(evidence.get("run_id"), meta["run_id"], "PILOT_EVIDENCE_RUN")
    _require(evidence.get("status"), "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_PARAMETERIZED_SINGLE_YEAR_PILOT", "PILOT_EVIDENCE_STATUS")
    _require(evidence.get("head_sha"), "bba6e85732601c7f7bd7ff343406ca0d42ae5cc3", "PILOT_EVIDENCE_HEAD")
    _require(evidence.get("pilot_year"), 2021, "PILOT_EVIDENCE_YEAR")
    _require(evidence.get("period"), 6, "PILOT_EVIDENCE_PERIOD")
    _require(evidence.get("source_get_count"), 1, "PILOT_EVIDENCE_GET")
    _require(evidence.get("schema_key_count"), 52, "PILOT_EVIDENCE_SCHEMA")
    _require(evidence.get("stage_count"), 9, "PILOT_EVIDENCE_STAGES")
    _require(evidence.get("drive_write_count"), 3, "PILOT_EVIDENCE_WRITES")
    _require(evidence.get("drive_download_count"), 3, "PILOT_EVIDENCE_READBACKS")
    _require(evidence.get("metric_count"), 8, "PILOT_EVIDENCE_METRICS")
    _require(evidence.get("batch_live_authorized"), False, "PILOT_EVIDENCE_BATCH")
    _require(evidence.get("retry_authorized"), False, "PILOT_EVIDENCE_RETRY")
    _require(evidence.get("pagination_authorized"), False, "PILOT_EVIDENCE_PAGINATION")
    _require(evidence.get("recurrence_authorized"), False, "PILOT_EVIDENCE_RECURRENCE")
    _require(evidence.get("schedule_enabled"), False, "PILOT_EVIDENCE_SCHEDULE")
    _require(evidence.get("compliance_claims_authorized"), False, "PILOT_EVIDENCE_COMPLIANCE")
    _require(evidence.get("imputation_performed"), False, "PILOT_EVIDENCE_IMPUTATION")
    return {
        "status": f"{PASS}_DESIGN",
        "batch_years": years,
        "max_years_per_batch": config["max_years_per_batch"],
        "total_stage_count": config["total_stage_count"],
    }


def _client() -> SiopeClient:
    return SiopeClient(
        policy=SiopeClientPolicy(
            timeout_seconds=60,
            max_attempts=1,
            follow_redirects=False,
            follow_nextlink=False,
        )
    )


def _preflight_all_collisions(config: dict, prepared: list[dict], drive) -> None:  # noqa: ANN001
    for item in prepared:
        payloads = item["payloads"]
        year = item["year"]
        checks = (
            (config["bronze_folder_id"], payloads["bronze_name"], f"BRONZE_{year}"),
            (config["silver_folder_id"], payloads["silver_name"], f"SILVER_{year}"),
            (config["gold_folder_id"], payloads["gold_name"], f"GOLD_{year}"),
        )
        for folder_id, name, label in checks:
            matches = drive.find_by_name(folder_id, name)
            _require(len(matches), 0, f"{label}_REMOTE_NAME_COLLISION")


def run_bounded_batch(config: dict, *, root: str | Path, siope_client=None, drive=None) -> dict:
    validate_config(config, root=root)
    if siope_client is None:
        siope_client = _client()

    prepared = []
    for year in config["batch_years"]:
        local = dict(config)
        local["pilot_year"] = year
        page = siope_client.get_dados_gerais_page(
            ano=year,
            periodo=config["period"],
            uf=config["uf"],
            municipality_code=config["municipality_code"],
            select_fields=tuple(sorted(PROVEN_DADOS_GERAIS_FIELDS)),
        )
        try:
            record = _record_from_page(local, page)
            payloads = _build_payloads(local, record, page)
        except HistoricalParameterizedSingleYearPilotError as exc:
            _translate_pilot_validation_error(exc)
        _require(payloads["metric_count"], 8, f"METRIC_COUNT_{year}")
        prepared.append({"year": year, "payloads": payloads})

    if drive is None:
        drive = DriveRESTClient(TokenProvider(OAuthCredentials.from_env()))

    # Atomic-like boundary: all source responses and output names are checked before the first create.
    _preflight_all_collisions(config, prepared, drive)

    results = []
    for item in prepared:
        year = item["year"]
        payloads = item["payloads"]
        _put_and_readback(
            drive,
            folder_id=config["bronze_folder_id"],
            name=payloads["bronze_name"],
            raw=payloads["bronze_bytes"],
            mime_type=config["mime_type"],
            label=f"BRONZE_{year}",
        )
        _put_and_readback(
            drive,
            folder_id=config["silver_folder_id"],
            name=payloads["silver_name"],
            raw=payloads["silver_bytes"],
            mime_type=config["mime_type"],
            label=f"SILVER_{year}",
        )
        _put_and_readback(
            drive,
            folder_id=config["gold_folder_id"],
            name=payloads["gold_name"],
            raw=payloads["gold_bytes"],
            mime_type=config["mime_type"],
            label=f"GOLD_{year}",
        )
        results.append(
            {
                "year": year,
                "record_sha256": payloads["record_sha256"],
                "bronze_bytes": len(payloads["bronze_bytes"]),
                "bronze_sha256": payloads["bronze_sha256"],
                "silver_bytes": len(payloads["silver_bytes"]),
                "silver_sha256": payloads["silver_sha256"],
                "gold_bytes": len(payloads["gold_bytes"]),
                "gold_sha256": payloads["gold_sha256"],
                "metric_count": payloads["metric_count"],
            }
        )

    return {
        "status": PASS,
        "gate_id": config["gate_id"],
        "batch_years": config["batch_years"],
        "batch_year_count": len(config["batch_years"]),
        "max_years_per_batch": config["max_years_per_batch"],
        "source_get_count": len(prepared),
        "source_record_count": len(prepared),
        "schema_key_count": config["schema_key_count"],
        "period": config["period"],
        "stage_count_per_year": len(EXPECTED_STAGES),
        "total_stage_count": len(prepared) * len(EXPECTED_STAGES),
        "drive_preflight_collision_checks": len(prepared) * 3,
        "drive_write_count": len(prepared) * 3,
        "drive_download_count": len(prepared) * 3,
        "create_only": True,
        "batch_live_authorized": True,
        "bounded_batch_only": True,
        "historical_collection_authorized": True,
        "future_batch_execution_authorized": False,
        "individual_year_workflow_duplication_authorized": False,
        "retry_authorized": False,
        "pagination_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "compliance_claims_authorized": False,
        "imputation_performed": False,
        "remote_file_id_persisted": False,
        "next_state": config["next_state"],
        "years": results,
    }

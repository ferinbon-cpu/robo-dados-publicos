from __future__ import annotations

import hashlib
import json
from pathlib import Path

from robo_dados_publicos.sources.siope_client import (
    PROVEN_DADOS_GERAIS_FIELDS,
    SiopeClient,
    SiopeClientError,
    SiopeClientPolicy,
)
from robo_dados_publicos.sources.siope_client_limeira_historical_parameterized_single_year_pilot import (
    ERROR as SINGLE_YEAR_PILOT_ERROR,
    HistoricalParameterizedSingleYearPilotError,
    _record_from_page,
)

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_BOUNDED_BATCH_SOURCE_PROBE"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_BOUNDED_BATCH_SOURCE_PROBE"


class HistoricalBoundedBatchSourceProbeError(RuntimeError):
    pass


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise HistoricalBoundedBatchSourceProbeError(f"{ERROR}_{code}")


def _git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()  # noqa: S324


def _pilot_code(exc: HistoricalParameterizedSingleYearPilotError) -> str:
    text = str(exc)
    prefix = f"{SINGLE_YEAR_PILOT_ERROR}_"
    return text[len(prefix) :] if text.startswith(prefix) else "PILOT_HELPER"


def validate_config(config: dict, *, root: str | Path) -> dict:
    expected = {
        "batch_live_authorized": False,
        "batch_years": [2020, 2019, 2018, 2017, 2016],
        "compliance_claims_authorized": False,
        "drive_access_authorized": False,
        "drive_write_count": 0,
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_BOUNDED_BATCH_SOURCE_PROBE_0_8_0",
        "imputation_authorized": False,
        "manual_confirmation_required": True,
        "max_years_per_probe": 5,
        "mode": "BOUNDED_LIVE_PARAMETERIZED_HISTORICAL_SOURCE_PROBE",
        "municipality_code": 352690,
        "municipality_name": "Limeira",
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_BOUNDED_BATCH_AUTHORIZATION_0_8_0",
        "pagination_authorized": False,
        "period": 6,
        "prior_failure_evidence": {
            "blob_sha": "5cd575bd0221eb7bee617edade5860966bdd6a91",
            "path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_BOUNDED_BATCH_AUTHORIZATION_RUN_1_STOP_0.8.0.json",
            "run_id": 33126863037,
        },
        "recurrence_authorized": False,
        "retry_authorized": False,
        "schedule_enabled": False,
        "schema_key_count": 52,
        "software_version": "0.8.0",
        "source_get_count": 5,
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "uf": "SP",
    }
    _require(config, expected, "CONFIG_DRIFT")
    years = config["batch_years"]
    _require(len(PROVEN_DADOS_GERAIS_FIELDS), 52, "SCHEMA_ALLOWLIST_COUNT")
    _require(years, sorted(set(years), reverse=True), "BATCH_YEARS_UNIQUE_DESCENDING")
    _require(len(years), config["max_years_per_probe"], "BATCH_YEAR_COUNT")
    _require(len(years) <= 5, True, "BATCH_BOUND")
    _require(config["source_get_count"], len(years), "SOURCE_GET_COUNT")
    _require(config["drive_access_authorized"], False, "DRIVE_ACCESS")
    _require(config["drive_write_count"], 0, "DRIVE_WRITE_COUNT")

    meta = config["prior_failure_evidence"]
    path = Path(root) / meta["path"]
    raw = path.read_bytes()
    _require(_git_blob_sha(raw), meta["blob_sha"], "PRIOR_FAILURE_EVIDENCE_BLOB_SHA")
    evidence = json.loads(raw.decode("utf-8"))
    _require(evidence.get("run_id"), meta["run_id"], "PRIOR_FAILURE_RUN")
    _require(
        evidence.get("status"),
        "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_BOUNDED_BATCH_AUTHORIZATION",
        "PRIOR_FAILURE_STATUS",
    )
    _require(
        evidence.get("error"),
        "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_BOUNDED_BATCH_AUTHORIZATION_SOURCE_RECORD_COUNT",
        "PRIOR_FAILURE_ERROR",
    )
    _require(evidence.get("writes_proven_zero_by_control_flow"), True, "PRIOR_FAILURE_ZERO_WRITES")
    return {
        "status": f"{PASS}_DESIGN",
        "batch_years": years,
        "source_get_count": len(years),
        "drive_called": False,
        "drive_write_count": 0,
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


def run_source_probe(config: dict, *, root: str | Path, siope_client=None) -> dict:
    validate_config(config, root=root)
    if siope_client is None:
        siope_client = _client()

    observations: list[dict] = []
    all_valid = True

    for year in config["batch_years"]:
        observation = {
            "year": year,
            "request_count": 0,
            "http_status": None,
            "record_count": None,
            "nextlink_present": None,
            "schema_key_count": None,
            "identity_validated": False,
            "validation_code": None,
        }
        try:
            page = siope_client.get_dados_gerais_page(
                ano=year,
                periodo=config["period"],
                uf=config["uf"],
                municipality_code=config["municipality_code"],
                select_fields=tuple(sorted(PROVEN_DADOS_GERAIS_FIELDS)),
            )
            observation.update(
                {
                    "request_count": page.request_count,
                    "http_status": page.status,
                    "record_count": len(page.records),
                    "nextlink_present": page.nextlink_present,
                }
            )
            if len(page.records) != 1:
                observation["validation_code"] = "SOURCE_RECORD_COUNT"
                all_valid = False
            else:
                observation["schema_key_count"] = len(page.records[0])
                local = dict(config)
                local["pilot_year"] = year
                try:
                    _record_from_page(local, page)
                except HistoricalParameterizedSingleYearPilotError as exc:
                    observation["validation_code"] = _pilot_code(exc)
                    all_valid = False
                else:
                    observation["identity_validated"] = True
                    observation["validation_code"] = "PASS"
        except SiopeClientError as exc:
            observation["request_count"] = int(getattr(exc, "request_count", 0) or 0)
            observation["validation_code"] = str(exc)
            all_valid = False
        observations.append(observation)

    _require(len(observations), len(config["batch_years"]), "OBSERVATION_COUNT")
    status = PASS if all_valid else ERROR
    return {
        "status": status,
        "gate_id": config["gate_id"],
        "batch_years": config["batch_years"],
        "source_get_count": sum(item["request_count"] for item in observations),
        "drive_called": False,
        "drive_write_count": 0,
        "batch_live_authorized": False,
        "retry_authorized": False,
        "pagination_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "compliance_claims_authorized": False,
        "imputation_performed": False,
        "next_gate": config["next_gate"] if all_valid else None,
        "years": observations,
    }

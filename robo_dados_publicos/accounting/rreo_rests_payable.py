from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task188_rreo_rests_payable_2026.v1.json"


class Task188Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task188Stop(code)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value))


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK188_RREO_RESTS_PAYABLE_2026_V1", "TASK188_SCHEMA")
    _stop(obj.get("mode") == "OWNER_FILE_LIBRARY_OFFLINE_MATERIALIZATION", "TASK188_MODE")
    _stop(len(obj.get("sources") or []) == 2, "TASK188_SOURCE_COUNT")
    _stop(len(obj.get("observations") or []) == 4, "TASK188_OBSERVATION_COUNT")
    _stop(obj["remote_effects"]["source_network"] is False, "TASK188_NETWORK")
    return obj


def validate_observation(row: Mapping[str, Any]) -> None:
    processed = row["processed"]
    nonprocessed = row["nonprocessed"]

    processed_balance = (
        _decimal(processed["prior_years_inscribed_brl"])
        + _decimal(processed["dec_2025_inscribed_brl"])
        - _decimal(processed["paid_brl"])
        - _decimal(processed["cancelled_brl"])
    )
    _stop(
        processed_balance == _decimal(processed["balance_brl"]),
        "TASK188_PROCESSED_ARITHMETIC",
    )

    nonprocessed_balance = (
        _decimal(nonprocessed["prior_years_inscribed_brl"])
        + _decimal(nonprocessed["dec_2025_inscribed_brl"])
        - _decimal(nonprocessed["paid_brl"])
        - _decimal(nonprocessed["cancelled_brl"])
    )
    _stop(
        nonprocessed_balance == _decimal(nonprocessed["balance_brl"]),
        "TASK188_NONPROCESSED_ARITHMETIC",
    )
    _stop(
        _decimal(row["total_balance_brl"])
        == _decimal(processed["balance_brl"]) + _decimal(nonprocessed["balance_brl"]),
        "TASK188_TOTAL_ARITHMETIC",
    )


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    contract = load_contract(path)
    keys = set()
    for row in contract["observations"]:
        validate_observation(row)
        key = str(row["observation_key"])
        _stop(key not in keys, "TASK188_DUPLICATE_KEY")
        keys.add(key)

    granular = contract["tcesp_granular_enrichment"]
    _stop(granular["task172_observed_record_count"] == 7425, "TASK188_TCE_COUNT")
    _stop(granular["raw_payload_currently_custodied"] is False, "TASK188_TCE_RAW_GUARD")
    _stop(
        granular["current_task188_transport_status"] == "SOURCE_TRANSPORT_UNAVAILABLE_NOT_NO_DATA",
        "TASK188_TCE_TRANSPORT_ADJUDICATION",
    )
    return {
        "schema": "TASK188_RREO_RESTS_PAYABLE_VALIDATION_V1",
        "status": "PASS",
        "source_count": 2,
        "observation_count": 4,
        "tcesp_granular_record_count_historical_observation": 7425,
        "network": False,
        "drive_write": False,
    }


def build_rests_payable_observations(
    path: str | Path = DEFAULT_CONTRACT,
) -> list[dict[str, Any]]:
    contract = load_contract(path)
    source_by_id = {row["source_id"]: row for row in contract["sources"]}
    out = []
    for row in contract["observations"]:
        validate_observation(row)
        source = source_by_id[row["source_id"]]
        source_material = {
            "source_id": row["source_id"],
            "observation_key": row["observation_key"],
            "processed": row["processed"],
            "nonprocessed": row["nonprocessed"],
            "total_balance_brl": row["total_balance_brl"],
        }
        source_hash = hashlib.sha256(_canonical_bytes(source_material)).hexdigest()
        observation_hash = hashlib.sha256(
            _canonical_bytes(["TASK188", row["observation_key"], source_hash])
        ).hexdigest()[:24]
        hints = list(row.get("policy_domain_hints") or [])
        out.append(
            {
                "observation_id": "ACCTOBS_RP_" + observation_hash,
                "schema": "MUNICIPAL_ACCOUNTING_OBSERVATION_V1",
                "source_id": row["source_id"],
                "source_role": contract["source_role"],
                "entity_name": "MUNICIPIO DE LIMEIRA",
                "fiscal_year": 2026,
                "stage": "OTHER_REVIEW",
                "source_stage": "RESTS_A_PAGAR_BALANCE",
                "amount_semantic": "RESTS_PAYABLE_TOTAL_BALANCE",
                "amount_brl": row["total_balance_brl"],
                "event_date": None,
                "event_month": int(row["event_month"]),
                "source_month": int(row["event_month"]),
                "source_record_hash": source_hash,
                "identity_status": "SOURCE_RECORD_ONLY",
                "transaction_keys": {},
                "programmatic_dimensions": {},
                "policy_domain_hints": hints,
                "policy_domain_hint_basis": {
                    "EDUCATION": ["SECRETARIA DE EDUCACAO"]
                } if "EDUCATION" in hints else {},
                "policy_link_status": "NOT_PROVEN",
                "policy_identity_proven": False,
                "financial_policy_identity_proven": False,
                "source_description": (
                    f"RREO Anexo 7 - {row['scope_name']} - {source['period']}"
                ),
                "history_text": None,
                "rests_payable_status": {
                    "scope_type": row["scope_type"],
                    "scope_name": row["scope_name"],
                    "period": source["period"],
                    "processed": dict(row["processed"]),
                    "nonprocessed": dict(row["nonprocessed"]),
                    "total_balance_brl": row["total_balance_brl"],
                    "source_document": source["document"],
                    "file_library_id": source["file_library_id"],
                },
                "evidence_status": "DIRECT_EXPLICIT_OFFICIAL_RREO_RECORD",
            }
        )
    return out

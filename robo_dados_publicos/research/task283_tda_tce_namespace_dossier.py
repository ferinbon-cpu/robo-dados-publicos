"""TASK283: deterministic offline dossier for the TDA→TCE commitment namespace edge."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config/task283_tda_tce_namespace_dossier.v1.json"


class Task283Stop(RuntimeError):
    """Fail-closed TASK283 validation error."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise Task283Stop(code)


def git_blob_sha(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def load_config() -> dict[str, Any]:
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    require(data.get("schema") == "TASK283_TDA_TCE_NAMESPACE_DOSSIER_V1", "CONFIG_SCHEMA")
    require(data.get("issue") == 904, "CONFIG_ISSUE")
    require(data.get("depends_on_pr") == 902, "CONFIG_DEPENDENCY")
    require(data.get("execution_class") == "T0_OFFLINE_REPLAY", "CONFIG_EXECUTION_CLASS")
    require(
        data.get("effects")
        == {
            "pncp_requests": 0,
            "tda_requests": 0,
            "tce_requests": 0,
            "drive_reads": 0,
            "drive_writes": 0,
            "publication": False,
        },
        "CONFIG_OFFLINE_EFFECTS",
    )
    require(data.get("live_acquisition_authorized_by_this_contract") is False, "LIVE_NOT_BLOCKED")
    require(data.get("payment_attribution_authorized") is False, "PAYMENT_NOT_BLOCKED")
    return data


def pinned_json(name: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or load_config()
    spec = config["pinned_repository_inputs"][name]
    path = ROOT / spec["path"]
    payload = path.read_bytes()
    require(git_blob_sha(payload) == spec["git_blob_sha"], f"PINNED_SOURCE_DRIFT_{name.upper()}")
    return json.loads(payload.decode("utf-8"))


def _task219aa_state(data: dict[str, Any]) -> dict[str, Any]:
    require(
        data.get("status") == "PASS_STRONG_MUNICIPAL_CONTRACT_TO_COMMITMENT_IDENTITY",
        "TASK219AA_STATUS",
    )
    graph = data["identity_graph"]
    require(graph["strong_contract_to_commitment_identity_proven"] is True, "TASK219AA_CHAIN")
    empenhado = next(
        row
        for row in data["operator_artifacts"]
        if row["kind"] == "OFFICIAL_TDA_EMPENHADO_XLSX_EXPORT"
    )["bounded_row"]
    require(empenhado["commitment_number"] == "03286-01", "TASK219AA_TDA_COMMITMENT")
    require(empenhado["procurement_process_typed"] == "E00010/2026", "TASK219AA_PROCUREMENT")
    reconciliation = data["historical_tcesp_reconciliation"]
    require(reconciliation["tcesp_commitment_number"] == "3286-2026", "TASK219AA_TCE_SEED")
    require(
        reconciliation["exact_tda_to_tcesp_commitment_format_identity_claim"] is False,
        "TASK219AA_FORMAT_IDENTITY_MUST_REMAIN_FALSE",
    )
    return {
        "municipal_chain": "PROVEN",
        "typed_procurement": empenhado["procurement_process_typed"],
        "tda_commitment": empenhado["commitment_number"],
        "format_identity_claim": False,
    }


def _task219ab_state(data: dict[str, Any]) -> dict[str, Any]:
    require(
        data.get("status") == "PASS_OFFICIAL_TDA_CONTRACTS_MACHINE_READABLE_EXTRACTION",
        "TASK219AB_STATUS",
    )
    row = data["contract_row"]
    require(row["normalized_contract_number"] == "45/2026", "TASK219AB_CONTRACT")
    require(row["typed_procurement_identifier"] == "E00010/2026", "TASK219AB_PROCUREMENT")
    require(data["identity_role"]["weak_join_used"] is False, "TASK219AB_WEAK_JOIN")
    return {
        "contract": row["normalized_contract_number"],
        "typed_procurement": row["typed_procurement_identifier"],
    }


def _task219h_state(data: dict[str, Any]) -> dict[str, Any]:
    chain = data["tcesp_exact_supplier_chain"]
    require(chain["unique_commitments"] == ["3286-2026"], "TASK219H_TCE_COMMITMENT")
    require(chain["candidate_row_count"] == 3, "TASK219H_ROW_COUNT")
    adjudication = data["strong_identity_adjudication"]
    require(adjudication["jom_to_tcesp_procurement_identity_proven"] is False, "TASK219H_IDENTITY")
    require(adjudication["strong_document_identifier_hit_count"] == 0, "TASK219H_STRONG_ID_HIT")
    return {
        "tce_commitment": "3286-2026",
        "observed_scoped_cohort": True,
        "procurement_identity": "UNRESOLVED",
    }


def _historical_query_state(
    x: dict[str, Any], y: dict[str, Any], z: dict[str, Any]
) -> dict[str, Any]:
    require(x["fail_closed_boundary"]["Empenho_3286_2026_queried"] is False, "TASK219X_QUERY")
    require(y["boundary"]["Empenho_3286_2026_queried"] is False, "TASK219Y_QUERY")
    require(z["boundary"]["Empenho_3286_2026_queried"] is False, "TASK219Z_QUERY")
    require(
        z["gate_result"]["status"] == "STOP_EXACT_DETAIL_SUBMIT_BINDING_NOT_UNIQUE",
        "TASK219Z_GATE_STATUS",
    )
    return {
        "task219x_query_executed": False,
        "task219y_query_executed": False,
        "task219z_query_executed": False,
        "last_gate": z["gate_result"]["status"],
    }


def _task282_state(data: dict[str, Any]) -> dict[str, Any]:
    require(data["status"] == "UNRESOLVED", "TASK282_STATUS")
    negative = data["negative_control"]
    require(negative["contract"] == "45/2026", "TASK282_CONTRACT")
    require(negative["tda_commitment"] == "03286-01", "TASK282_TDA")
    require(
        negative["tcesp_candidate_key"]
        == {
            "municipality": "Limeira",
            "entity": "PREFEITURA MUNICIPAL DE LIMEIRA",
            "original_year": 2026,
            "number": "3286",
        },
        "TASK282_TCE_KEY",
    )
    require(negative["payment_attribution_authorized"] is False, "TASK282_PAYMENT_BLOCK")
    require(data["production_identity_promoted"] is False, "TASK282_PROMOTION")
    return {
        "status": negative["status"],
        "tce_key": negative["tcesp_candidate_key"],
        "payment_attribution_authorized": False,
    }


def validate_witness(
    witness: dict[str, Any] | None, config: dict[str, Any] | None = None
) -> dict[str, Any]:
    config = config or load_config()
    contract = config["positive_witness_contract"]
    if witness is None:
        return {
            "status": "UNRESOLVED_MISSING_OFFICIAL_NAMESPACE_WITNESS",
            "payment_attribution_authorized": False,
        }

    require(isinstance(witness, dict), "WITNESS_NOT_OBJECT")
    for field in contract["provenance_required_fields"]:
        require(bool(witness.get(field)), f"WITNESS_PROVENANCE_MISSING_{field.upper()}")
    require(
        witness.get("authority_class") in contract["allowed_authority_classes"],
        "WITNESS_AUTHORITY_NOT_ALLOWED",
    )
    require(
        bool(re.fullmatch(r"[0-9a-f]{64}", str(witness["source_sha256"]))),
        "WITNESS_SOURCE_SHA256",
    )
    for field in contract["required_fields"]:
        require(field in witness, f"WITNESS_FIELD_MISSING_{field.upper()}")
        require(
            witness[field] == contract["required_values"][field],
            f"WITNESS_VALUE_MISMATCH_{field.upper()}",
        )
    require(
        not any(bool(witness.get(marker)) for marker in contract["heuristics_forbidden"]),
        "WITNESS_HEURISTIC_FORBIDDEN",
    )
    return {
        "status": "PROVEN_OFFICIAL_NAMESPACE_WITNESS",
        "payment_attribution_authorized": False,
        "witness": {
            field: witness[field]
            for field in contract["required_fields"] + contract["provenance_required_fields"]
        },
    }


def build_dossier(
    witness: dict[str, Any] | None = None, config: dict[str, Any] | None = None
) -> dict[str, Any]:
    config = config or load_config()
    aa = _task219aa_state(pinned_json("task219aa", config))
    ab = _task219ab_state(pinned_json("task219ab", config))
    h = _task219h_state(pinned_json("task219h", config))
    query_history = _historical_query_state(
        pinned_json("task219x", config),
        pinned_json("task219y", config),
        pinned_json("task219z", config),
    )
    t282 = _task282_state(pinned_json("task282", config))

    require(aa["typed_procurement"] == ab["typed_procurement"], "PROCUREMENT_CHAIN_DRIFT")
    require(aa["tda_commitment"] == config["target"]["tda_commitment"], "TDA_TARGET_DRIFT")
    require(t282["tce_key"] == config["target"]["tce_key"], "TCE_TARGET_DRIFT")

    witness_result = validate_witness(witness, config)
    require(
        witness_result["payment_attribution_authorized"] is False,
        "PAYMENT_ATTRIBUTION_MUST_REMAIN_SEPARATE",
    )

    return {
        "schema": "TASK283_TDA_TCE_NAMESPACE_DOSSIER_RESULT_V1",
        "task": "TASK_283",
        "issue": 904,
        "status": witness_result["status"],
        "municipal_chain": {
            "contract": ab["contract"],
            "typed_procurement": aa["typed_procurement"],
            "tda_commitment": aa["tda_commitment"],
            "status": aa["municipal_chain"],
        },
        "tce_candidate": {
            "commitment": h["tce_commitment"],
            "key": t282["tce_key"],
            "status": "OBSERVED_SCOPED_COHORT",
        },
        "namespace_edge": {
            "from": aa["tda_commitment"],
            "to": f'{t282["tce_key"]["number"]}-{t282["tce_key"]["original_year"]}',
            "status": witness_result["status"],
            "heuristic_normalization_allowed": False,
        },
        "historical_query_audit": query_history,
        "payment_attribution_authorized": False,
        "live_acquisition_authorized": False,
        "next_required_evidence": (
            None
            if witness_result["status"] == "PROVEN_OFFICIAL_NAMESPACE_WITNESS"
            else "OFFICIAL_TDA_TCE_NAMESPACE_WITNESS_WITH_ENTITY_AND_ORIGINAL_YEAR"
        ),
    }


def main() -> None:
    print(json.dumps(build_dossier(), ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()

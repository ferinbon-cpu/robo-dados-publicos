#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.storage.drive_rest import DriveRESTClient, OAuthCredentials, TokenProvider

BASE_IMPLEMENTATION_SHA = "4a6e271add0282689dc933a24387a69830f90465"
REPOSITORY = "ferinbon-cpu/robo-dados-publicos"
TASK = "TASK_040_LOA_SCOPED_SILVER_CREATE_ONLY_READBACK"
TARGET_FOLDER_ID = "1_wl3Y90-RYKSBXUg53My5K6lxCUnIBNo"
TARGET_NAME = "F01_LOA_JOM_2026_SCOPED_VALIDATED_STRUCTURE__3894ede7c67e__silver_v1.json"
EXPECTED_SHA256 = "3894ede7c67e60d3e12795dec3964d78baf24ff350355d98f3825dd5f81caf4c"
EVIDENCE_PATH = ROOT / "docs/evidence/TASK_039_LOA_SCOPED_SILVER_CANDIDATE_REVIEW_0.8.0.json"
WORK_DIR = ROOT / ".task040_silver_work"
RESULT_DIR = ROOT / "task-040-sanitized-evidence"
RESULT_PATH = RESULT_DIR / "result.json"

AUTHORIZATION = {
    "owner_authorized": True,
    "owner_message": "Autorizado e guarde mais 10 autorizações pra gastar futuramente",
    "authorized_local_time": "2026-09-02T12:19:00-03:00",
    "authorized_against_sha": BASE_IMPLEMENTATION_SHA,
    "scope": "EXACTLY_ONE_SCOPED_SILVER_CREATE_ONLY_PLUS_ONE_READBACK",
    "future_blanket_authorizations_accepted": False,
    "future_blanket_authorizations_reason": "Each future remote or privilege-changing operation must be scoped and pinned to the reviewed implementation SHA at execution time.",
}


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def md5_bytes(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def write_result(result: dict) -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    result = {
        "task": TASK,
        "mode": "T2_EXACT_ONE_CREATE_ONLY_SCOPED_SILVER_WITH_READBACK",
        "base_implementation_sha": BASE_IMPLEMENTATION_SHA,
        "authorization": AUTHORIZATION,
        "target": {
            "folder_id": TARGET_FOLDER_ID,
            "name": TARGET_NAME,
            "mime_type": "application/json",
        },
        "effects": {
            "public_source_get": 0,
            "drive_inventory_requests": 0,
            "drive_creates": 0,
            "drive_readbacks": 0,
            "overwrite": 0,
            "replace": 0,
            "delete": 0,
            "cleanup": 0,
            "retry": 0,
            "ocr": 0,
            "bronze": 0,
            "gold": 0,
            "serving": 0,
            "publication": 0,
        },
        "remote_file_id_persisted": False,
        "owner_decision_required": False,
    }
    created = False
    try:
        evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        if evidence.get("task") != "TASK_039_LOA_SCOPED_SILVER_CANDIDATE_REVIEW":
            raise RuntimeError("STOP_TASK040_TASK039_EVIDENCE_ID_MISMATCH")
        readiness = evidence.get("readiness") or {}
        if readiness.get("decision") != "READY_FOR_SCOPED_SILVER_CREATE_ONLY_SEPARATE_AUTH_REQUIRED":
            raise RuntimeError("STOP_TASK040_TASK039_READINESS_MISMATCH")
        candidate = evidence.get("candidate_payload") or {}
        if candidate.get("contract") != "F01_LOA_JOM_2026_SCOPED_VALIDATED_STRUCTURE_SILVER_V1":
            raise RuntimeError("STOP_TASK040_CONTRACT_MISMATCH")
        if candidate.get("scope") != "SCOPED_VALIDATED_STRUCTURE_NOT_COMPLETE_LOA_PARSE":
            raise RuntimeError("STOP_TASK040_SCOPE_MISMATCH")
        guardrails = candidate.get("guardrails") or {}
        if guardrails.get("complete_loa_parse_claim") is not False:
            raise RuntimeError("STOP_TASK040_COMPLETE_LOA_CLAIM_FORBIDDEN")
        if guardrails.get("eiti_financial_identity") != "EVIDENCIA_INSUFICIENTE":
            raise RuntimeError("STOP_TASK040_EITI_IDENTITY_WEAKENED")
        if guardrails.get("compliance_conclusion") is not False or guardrails.get("gold_authorized") is not False:
            raise RuntimeError("STOP_TASK040_DOWNSTREAM_GUARDRAIL_WEAKENED")

        payload = canonical_bytes(candidate)
        payload_sha = sha256_bytes(payload)
        payload_md5 = md5_bytes(payload)
        if payload_sha != EXPECTED_SHA256 or evidence.get("candidate_payload_sha256") != EXPECTED_SHA256:
            raise RuntimeError("STOP_TASK040_CANDIDATE_HASH_MISMATCH")

        WORK_DIR.mkdir(parents=True, exist_ok=True)
        local_payload = WORK_DIR / TARGET_NAME
        local_payload.write_bytes(payload)
        result["candidate"] = {
            "contract": candidate["contract"],
            "scope": candidate["scope"],
            "bytes": len(payload),
            "sha256": payload_sha,
            "md5": payload_md5,
            "f01_scope_partial": True,
            "complete_loa_claim": False,
            "financial_identity_eiti": "EVIDENCIA_INSUFICIENTE",
        }

        credentials = OAuthCredentials.from_env()
        client = DriveRESTClient(TokenProvider(credentials))

        inventory = client.list_children_single_page(TARGET_FOLDER_ID, page_size=1000)
        result["effects"]["drive_inventory_requests"] = 1
        if inventory.get("next_page_token"):
            raise RuntimeError("STOP_TASK040_SILVER_FOLDER_INVENTORY_PAGINATION_REQUIRED")
        existing = [x for x in (inventory.get("files") or []) if x.get("name") == TARGET_NAME]
        if existing:
            raise RuntimeError("STOP_TASK040_TARGET_NAME_COLLISION_BEFORE_WRITE")

        created_meta = client.put(local_payload, TARGET_NAME, TARGET_FOLDER_ID, mime_type="application/json")
        created = True
        result["effects"]["drive_creates"] = 1
        if created_meta.get("name") != TARGET_NAME:
            raise RuntimeError("STOP_TASK040_CREATED_NAME_MISMATCH")
        if created_meta.get("mimeType") != "application/json":
            raise RuntimeError("STOP_TASK040_CREATED_MIME_MISMATCH")
        if (created_meta.get("parents") or []) != [TARGET_FOLDER_ID]:
            raise RuntimeError("STOP_TASK040_CREATED_PARENT_MISMATCH")
        if int(created_meta.get("size") or -1) != len(payload):
            raise RuntimeError("STOP_TASK040_CREATED_SIZE_MISMATCH")
        if created_meta.get("md5Checksum") != payload_md5:
            raise RuntimeError("STOP_TASK040_CREATED_MD5_MISMATCH")

        readback_path = WORK_DIR / "readback.json"
        rb = client.get(created_meta["id"], readback_path)
        result["effects"]["drive_readbacks"] = 1
        if rb.get("bytes") != len(payload):
            raise RuntimeError("STOP_TASK040_READBACK_SIZE_MISMATCH")
        if rb.get("sha256") != EXPECTED_SHA256:
            raise RuntimeError("STOP_TASK040_READBACK_SHA256_MISMATCH")
        if readback_path.read_bytes() != payload:
            raise RuntimeError("STOP_TASK040_READBACK_BYTES_MISMATCH")

        result["readback"] = {
            "verified": True,
            "bytes": len(payload),
            "sha256": EXPECTED_SHA256,
            "md5": payload_md5,
            "byte_identity": True,
        }
        result["promotion"] = {
            "silver": True,
            "silver_scope": "SCOPED_VALIDATED_STRUCTURE_NOT_COMPLETE_LOA_PARSE",
            "gold": False,
            "serving": False,
            "publication": False,
            "f01_status": "SILVER_SCOPED_PARTIAL_VALIDATED",
        }
        result["authorization_consumed"] = True
        result["status"] = "PASS_TASK040_SCOPED_SILVER_CREATE_ONLY_READBACK_VERIFIED"
        write_result(result)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except Exception as exc:
        result["status"] = (
            "STOP_TASK040_PARTIAL_SILVER_CREATED_OWNER_DECISION_REQUIRED"
            if created else
            "STOP_TASK040_BEFORE_SILVER_CREATE"
        )
        result["error_code"] = str(exc)
        result["partial_silver_created"] = created
        result["owner_decision_required"] = created
        result["authorization_consumed"] = True
        write_result(result)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

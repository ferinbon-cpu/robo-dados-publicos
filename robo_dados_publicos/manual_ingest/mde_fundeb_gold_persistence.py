from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from robo_dados_publicos.manual_ingest.mde_fundeb_gold_preview import build_preview, load_json


class F02GoldPersistenceStop(ValueError):
    pass


def _stop(code: str) -> None:
    raise F02GoldPersistenceStop(f"STOP_F02_GOLD_PERSISTENCE_{code}")


def _sha(value: object) -> str:
    text = str(value or "").lower().strip()
    if not re.fullmatch(r"[0-9a-f]{64}", text):
        _stop("BAD_SHA256")
    return text


def validate_persistence_contract(config: dict) -> dict:
    if config.get("schema") != "F02_GOLD_PERSISTENCE_CONTRACT_V1":
        _stop("CONFIG_SCHEMA")
    if config.get("mode") != "CREATE_ONLY_GOLD_PERSISTENCE_AFTER_REVIEW":
        _stop("CONFIG_MODE")
    auth = config.get("owner_authorization")
    if not isinstance(auth, dict) or auth.get("model") != "TEN_SEQUENTIAL_BOUNDED_GATES":
        _stop("AUTH_MODEL")
    if auth.get("contract_materialization_gate") != 7 or auth.get("remote_persistence_gate") != 10:
        _stop("AUTH_GATE_DRIFT")

    candidate = config.get("candidate")
    if not isinstance(candidate, dict):
        _stop("CANDIDATE")
    _sha(candidate.get("logical_sha256"))
    _sha(candidate.get("rendered_sha256"))
    if candidate.get("rendered_bytes") != 4231:
        _stop("CANDIDATE_BYTES")
    if candidate.get("expected_values") != ["24.27", "23.60", "88.67", "96.99"]:
        _stop("CANDIDATE_VALUES")

    for name, expected_folder, expected_max in (
        ("gold_target", "03_GOLD", 1),
        ("manifest_target", "07_LOGS", 1),
    ):
        target = config.get(name)
        if not isinstance(target, dict):
            _stop("TARGET")
        if target.get("folder_name") != expected_folder:
            _stop("TARGET_FOLDER")
        if not str(target.get("folder_drive_id") or ""):
            _stop("TARGET_ID")
        if target.get("create_only") is not True or target.get("overwrite") is not False:
            _stop("TARGET_NOT_CREATE_ONLY")
        if target.get("max_creates") != expected_max or target.get("readback_required") is not True:
            _stop("TARGET_BUDGET")
    if config["manifest_target"].get("only_after_gold_readback") is not True:
        _stop("MANIFEST_ORDER")

    forbidden = config.get("forbidden")
    required = {
        "bronze_mutation","silver_mutation","source_collection","extra_gold_create",
        "overwrite","delete","move","serving","publication","site_mutation",
        "schedule","recurrence","annual_compliance_promotion",
    }
    if not isinstance(forbidden, dict) or set(forbidden) != required:
        _stop("FORBIDDEN_SET")
    if any(forbidden[key] is not True for key in required):
        _stop("FORBIDDEN_DISABLED")
    return {"status":"PASS_F02_GOLD_PERSISTENCE_CONTRACT","gold_max_creates":1,"manifest_max_creates":1}


def build_and_verify_candidate(config: dict, *, root: str | Path) -> tuple[bytes, dict]:
    validate_persistence_contract(config)
    root = Path(root)
    evidence = load_json(root / config["prerequisite"]["deepseek_review_evidence_path"])
    if evidence.get("deepseek", {}).get("counts", {}).get("blocking_findings") != config["prerequisite"]["required_deepseek_blocking_findings"]:
        _stop("DEEPSEEK_BLOCKER_DRIFT")
    if evidence.get("adjudication", {}).get("gold_preview_blockers_remaining") != 0:
        _stop("ADJUDICATION_BLOCKER")

    preview_config = load_json(root / config["prerequisite"]["gold_preview_config_path"])
    candidate, result = build_preview(preview_config, root=root)
    rendered = (json.dumps(candidate, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    expected = config["candidate"]
    if candidate.get("schema") != expected["schema"]:
        _stop("SCHEMA_DRIFT")
    if candidate.get("content_sha256") != expected["logical_sha256"]:
        _stop("LOGICAL_SHA_DRIFT")
    if hashlib.sha256(rendered).hexdigest() != expected["rendered_sha256"]:
        _stop("RENDERED_SHA_DRIFT")
    if len(rendered) != expected["rendered_bytes"]:
        _stop("RENDERED_BYTES_DRIFT")
    values = [x.get("value") for x in candidate.get("observations", [])]
    if values != expected["expected_values"]:
        _stop("VALUES_DRIFT")
    if result.get("gold_payload_persisted") is not False or result.get("drive_write_count") != 0:
        _stop("PREVIEW_EFFECT_DRIFT")
    return rendered, {
        "status":"PASS_F02_GOLD_PERSISTENCE_PREFLIGHT",
        "logical_sha256":candidate["content_sha256"],
        "rendered_sha256":hashlib.sha256(rendered).hexdigest(),
        "rendered_bytes":len(rendered),
        "gold_remote_write_performed":False,
        "manifest_remote_write_performed":False,
    }

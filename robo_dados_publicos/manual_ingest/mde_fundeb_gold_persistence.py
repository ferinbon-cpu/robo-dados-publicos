from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from robo_dados_publicos.manual_ingest.mde_fundeb_gold_preview import build_preview, load_json

EXPECTED_GOLD_FOLDER_ID = "1hAmQNBnY6MNBtyr14ACfVfRkmWhsoRq4"
EXPECTED_GOLD_FILE_NAME = "F02_MDE_FUNDEB_2026_GOLD__38232ab8e02a__gold_v1.json"
EXPECTED_LOG_FOLDER_ID = "1H2ggRDWZ3Zf5LF_ze8po8zU_Uf_IbvoU"
EXPECTED_LOG_FILE_NAME = "F02_MDE_FUNDEB_2026_GOLD_PERSISTENCE__38232ab8e02a__manifest_v1.json"


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
    if auth.get("interpretation") != "PROSPECTIVE_BOUNDED_GATES_FOR_GITHUB_API_DEEPSEEK_REVIEW_THEN_ONE_CREATE_ONLY_GOLD_PERSISTENCE":
        _stop("AUTH_INTERPRETATION_DRIFT")

    prerequisite = config.get("prerequisite")
    if not isinstance(prerequisite, dict):
        _stop("PREREQUISITE")
    dependency = prerequisite.get("gold_preview_base_dependency")
    if not isinstance(dependency, dict):
        _stop("BASE_DEPENDENCY")
    if dependency.get("path") != "robo_dados_publicos/manual_ingest/mde_fundeb_gold_preview.py":
        _stop("BASE_DEPENDENCY_PATH")
    if dependency.get("git_blob_sha") != "5e9c10872bc191dfb73b6354d361db50d84e23cf":
        _stop("BASE_DEPENDENCY_SHA")
    if prerequisite.get("persistence_pr_exact_head_deepseek_review_required") is not True:
        _stop("PERSISTENCE_REVIEW_NOT_REQUIRED")
    if prerequisite.get("persistence_pr_review_enforcement") != "ORCHESTRATOR_CHECK_BEFORE_PINNED_MERGE":
        _stop("PERSISTENCE_REVIEW_ENFORCEMENT")

    candidate = config.get("candidate")
    if not isinstance(candidate, dict):
        _stop("CANDIDATE")
    _sha(candidate.get("logical_sha256"))
    _sha(candidate.get("rendered_sha256"))
    if candidate.get("rendered_bytes") != 4231:
        _stop("CANDIDATE_BYTES")
    if candidate.get("expected_values") != ["24.27", "23.60", "88.67", "96.99"]:
        _stop("CANDIDATE_VALUES")

    target_specs = (
        ("gold_target", "03_GOLD", EXPECTED_GOLD_FOLDER_ID, EXPECTED_GOLD_FILE_NAME),
        ("manifest_target", "07_LOGS", EXPECTED_LOG_FOLDER_ID, EXPECTED_LOG_FILE_NAME),
    )
    for name, expected_folder, expected_id, expected_file in target_specs:
        target = config.get(name)
        if not isinstance(target, dict):
            _stop("TARGET")
        if target.get("folder_name") != expected_folder:
            _stop("TARGET_FOLDER")
        if target.get("folder_drive_id") != expected_id:
            _stop("TARGET_ID")
        if target.get("file_name") != expected_file:
            _stop("TARGET_FILE")
        if target.get("create_only") is not True or target.get("overwrite") is not False:
            _stop("TARGET_NOT_CREATE_ONLY")
        if target.get("max_creates") != 1 or target.get("readback_required") is not True:
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


def validate_preview_review_evidence(evidence: dict, prerequisite: dict) -> dict:
    if not isinstance(evidence, dict) or evidence.get("schema") != prerequisite.get("preview_review_evidence_schema"):
        _stop("REVIEW_EVIDENCE_SCHEMA")
    target = evidence.get("reviewed_target")
    if not isinstance(target, dict):
        _stop("REVIEW_EVIDENCE_TARGET")
    if target.get("pr") != prerequisite.get("preview_reviewed_target_pr"):
        _stop("REVIEW_EVIDENCE_PR")
    if target.get("head_sha") != prerequisite.get("preview_reviewed_target_head_sha"):
        _stop("REVIEW_EVIDENCE_HEAD")
    deepseek = evidence.get("deepseek")
    if not isinstance(deepseek, dict) or deepseek.get("review_sha256") != prerequisite.get("preview_review_sha256"):
        _stop("REVIEW_EVIDENCE_SHA")
    if deepseek.get("counts", {}).get("blocking_findings") != prerequisite.get("required_preview_blocking_findings"):
        _stop("DEEPSEEK_BLOCKER_DRIFT")
    adjudication = evidence.get("adjudication")
    if not isinstance(adjudication, dict) or adjudication.get("gold_preview_blockers_remaining") != 0:
        _stop("ADJUDICATION_BLOCKER")
    if prerequisite.get("require_preview_evidence_not_to_authorize_persistence") is not True:
        _stop("REVIEW_AUTH_POLICY")
    if adjudication.get("gold_persistence_authorized_by_this_evidence") is not False:
        _stop("REVIEW_EVIDENCE_MUST_NOT_AUTHORIZE_PERSISTENCE")
    return {"status":"PASS_F02_GOLD_PREVIEW_REVIEW_EVIDENCE","blocking_findings":0}


def _load_review_evidence(path: Path) -> dict:
    try:
        return load_json(path)
    except (OSError, UnicodeDecodeError, ValueError, TypeError) as exc:
        raise F02GoldPersistenceStop("STOP_F02_GOLD_PERSISTENCE_REVIEW_EVIDENCE_UNREADABLE") from exc


def build_and_verify_candidate(config: dict, *, root: str | Path) -> tuple[bytes, dict]:
    validate_persistence_contract(config)
    root = Path(root)
    prerequisite = config["prerequisite"]
    evidence = _load_review_evidence(root / prerequisite["preview_review_evidence_path"])
    validate_preview_review_evidence(evidence, prerequisite)

    preview_config = load_json(root / prerequisite["gold_preview_config_path"])
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

"""Pure BI-003 stable-serving planner; contains no Drive/Sheets/Looker client."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .bi_materialization import BIMaterializationError, MaterializationPlan, build_plan
from .bi_model import load_contract

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config/bi/serving.v1.json"
PASS_READBACK = "PASS_BI_SERVING_SEMANTIC_READBACK_VERIFIED"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
META_KEYS = (
    "dataset_id", "serving_contract_version", "schema_version", "snapshot_id",
    "schema_fingerprint_sha256", "canonical_matrix_sha256", "row_count", "column_count",
    "primary_key_json", "ordered_columns_json", "source_snapshot_filename",
    "source_manifest_filename", "software_version", "quality_status", "semantic_cautions_json",
)


class BIServingError(ValueError):
    """A deterministic BI-003 STOP."""


def _stop(code: str) -> None:
    raise BIServingError(f"STOP_BI_{code}")


def load_serving_contract(path: str | Path = POLICY_PATH) -> dict:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        raise BIServingError("STOP_BI_SERVING_INVALID_CONTRACT") from exc
    if (value.get("task"), value.get("tier"), value.get("parent_path"), value.get("tabs")) != (
        "BI_003", "T0_OFFLINE_IMPLEMENTATION_REVIEW", "13_BI/02_SERVING", ["DATA", "META"]
    ):
        _stop("SERVING_INVALID_CONTRACT")
    allowlist = value.get("dataset_allowlist")
    serving_names = value.get("serving_names")
    if not isinstance(allowlist, list) or len(allowlist) != 6 or len(set(allowlist)) != 6:
        _stop("SERVING_INVALID_CONTRACT")
    if serving_names != [f"{dataset_id}__SERVING" for dataset_id in allowlist]:
        _stop("SERVING_INVALID_CONTRACT")
    if value.get("active_authorization") is not None or value.get("remote_execution_authorized") is not False:
        _stop("SERVING_INVALID_CONTRACT")
    if value.get("looker_is_separate") is not True:
        _stop("SERVING_INVALID_CONTRACT")
    return value


def _field_identity(field: dict) -> dict:
    """Mirror BI-002 schema identity exactly so fingerprints cannot drift."""
    return {
        "name": field["name"],
        "data_type": field["data_type"],
        "nullable": bool(field["nullable"]),
        "enum": list(field["enum"]) if field.get("enum") else None,
        "format": field.get("format"),
    }


def schema_fingerprint(dataset_id: str, contract: dict | None = None) -> str:
    contract = contract or load_contract()
    spec = next((item for item in contract["datasets"] if item["dataset_id"] == dataset_id), None)
    if spec is None:
        _stop("SERVING_UNKNOWN_DATASET")
    bound = {
        "dataset_id": dataset_id,
        "primary_key": list(spec["primary_key"]),
        "fields": [_field_identity(field) for field in spec["fields"]],
    }
    payload = json.dumps(bound, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ServingTarget:
    materialization: MaterializationPlan
    schema_fingerprint_sha256: str
    meta: dict

    @property
    def dataset_id(self):
        return self.materialization.dataset_id

    @property
    def serving_name(self):
        return self.materialization.future_serving_name


@dataclass(frozen=True)
class ServingPlan:
    operation: str
    target: ServingTarget
    clear_grid: dict
    logical_batch_update_count: int
    automatic_retry_count: int = 0
    cleanup_on_failure: bool = False
    semantic_readback_required: bool = True


def _meta_for_plan(plan: MaterializationPlan) -> dict:
    return {
        "dataset_id": plan.dataset_id,
        "serving_contract_version": 1,
        "schema_version": 1,
        "snapshot_id": plan.snapshot_id,
        "schema_fingerprint_sha256": plan.schema_fingerprint_sha256,
        "canonical_matrix_sha256": plan.canonical_matrix_sha256,
        "row_count": plan.row_count,
        "column_count": len(plan.ordered_columns),
        "primary_key_json": json.dumps(list(plan.primary_key), separators=(",", ":")),
        "ordered_columns_json": json.dumps(list(plan.ordered_columns), separators=(",", ":")),
        "source_snapshot_filename": plan.proposed_snapshot_filename,
        "source_manifest_filename": plan.proposed_manifest_filename,
        "software_version": "0.8.0",
        "quality_status": "VALIDATED",
        "semantic_cautions_json": json.dumps(
            ["BI_DERIVED_NOT_SOURCE_OF_TRUTH", "MATCH_CANDIDATE_NE_FINANCIAL_IDENTITY"],
            separators=(",", ":"),
        ),
    }


def build_target(dataset_id: str, rows, contract: dict | None = None) -> ServingTarget:
    contract = contract or load_contract()
    try:
        plan = build_plan(dataset_id, rows, contract)
    except BIMaterializationError as exc:
        raise BIServingError("STOP_BI_SERVING_INVALID_SCHEMA") from exc
    fingerprint = schema_fingerprint(dataset_id, contract)
    if fingerprint != plan.schema_fingerprint_sha256:
        _stop("SERVING_SCHEMA_FINGERPRINT_INTERNAL_MISMATCH")
    return ServingTarget(plan, fingerprint, _meta_for_plan(plan))


def _sheets_serial(value: str, kind: str) -> float:
    if not isinstance(value, str):
        _stop("SERVING_INVALID_TYPED_VALUE")
    epoch = datetime(1899, 12, 30, tzinfo=timezone.utc)
    try:
        if kind == "date":
            parsed = datetime.combine(date.fromisoformat(value), datetime.min.time(), timezone.utc)
        else:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                _stop("SERVING_INVALID_TYPED_VALUE")
            parsed = parsed.astimezone(timezone.utc)
    except (TypeError, ValueError) as exc:
        raise BIServingError("STOP_BI_SERVING_INVALID_TYPED_VALUE") from exc
    return (parsed - epoch).total_seconds() / 86400


def serialize_cell(value: Any, data_type: str) -> dict:
    """Build locale-independent future CellData using explicit typed values."""
    if value is None:
        return {}
    if data_type == "text":
        if not isinstance(value, str):
            _stop("SERVING_INVALID_TYPED_VALUE")
        entered = {"stringValue": value}
    elif data_type == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            _stop("SERVING_INVALID_TYPED_VALUE")
        entered = {"numberValue": float(value)}
    elif data_type in {"number", "currency"}:
        if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
            _stop("SERVING_INVALID_TYPED_VALUE")
        entered = {"numberValue": float(value)}
    elif data_type == "boolean":
        if not isinstance(value, bool):
            _stop("SERVING_INVALID_TYPED_VALUE")
        entered = {"boolValue": value}
    elif data_type in {"date", "datetime"}:
        entered = {"numberValue": _sheets_serial(value, data_type)}
    else:
        _stop("SERVING_INVALID_TYPED_VALUE")
    cell = {"userEnteredValue": entered}
    patterns = {
        "date": "yyyy-mm-dd",
        "datetime": "yyyy-mm-dd hh:mm:ss",
        "currency": "0.00",
        "integer": "0",
        "number": "0.###############",
    }
    if data_type in patterns:
        number_type = "DATE" if data_type == "date" else "DATE_TIME" if data_type == "datetime" else "NUMBER"
        cell["userEnteredFormat"] = {
            "numberFormat": {"type": number_type, "pattern": patterns[data_type]}
        }
    return cell


def serialize_target(target: ServingTarget, contract: dict | None = None) -> dict:
    contract = contract or load_contract()
    spec = next(item for item in contract["datasets"] if item["dataset_id"] == target.dataset_id)
    types = [item["data_type"] for item in spec["fields"]]
    header = [
        {"userEnteredValue": {"stringValue": column}}
        for column in target.materialization.ordered_columns
    ]
    data = [header] + [
        [serialize_cell(value, kind) for value, kind in zip(row, types)]
        for row in target.materialization.rows
    ]
    meta = [[serialize_cell("key", "text"), serialize_cell("value", "text")]] + [
        [serialize_cell(key, "text"), serialize_cell(str(target.meta[key]), "text")]
        for key in META_KEYS
    ]
    return {"tabs": {"DATA": data, "META": meta}, "value_input_option": "RAW"}


def validate_existing(existing: dict, target: ServingTarget | None = None) -> None:
    if existing.get("tabs") != ["DATA", "META"]:
        _stop("SERVING_UNEXPECTED_TAB")
    if existing.get("formula_present"):
        _stop("SERVING_FORMULA_PRESENT")
    if existing.get("extra_cells"):
        _stop("SERVING_EXTRA_CELLS")
    if existing.get("headers") != list(existing.get("ordered_columns", [])):
        _stop("SERVING_EXTRA_CELLS")
    meta = existing.get("meta")
    if not isinstance(meta, dict) or set(meta) != set(META_KEYS):
        _stop("SERVING_INVALID_META")
    try:
        rebuilt = build_plan(existing["dataset_id"], existing["rows"])
    except (BIMaterializationError, KeyError, TypeError, ValueError) as exc:
        raise BIServingError("STOP_BI_SERVING_EXISTING_STATE_INVALID") from exc
    if rebuilt.canonical_matrix_sha256 != meta.get("canonical_matrix_sha256"):
        _stop("SERVING_EXISTING_STATE_INVALID")
    if target and meta.get("schema_fingerprint_sha256") != target.schema_fingerprint_sha256:
        _stop("SERVING_SCHEMA_DRIFT_REQUIRES_MIGRATION")
    expected_meta = _meta_for_plan(rebuilt)
    if meta != expected_meta:
        _stop("SERVING_INVALID_META")


def plan_serving_mutation(
    target: ServingTarget,
    existing: dict | None,
    *,
    snapshot_validated: bool,
) -> ServingPlan:
    if not snapshot_validated:
        _stop("SERVING_SNAPSHOT_NOT_VALIDATED")
    if existing is None:
        return ServingPlan(
            "CREATE_INITIAL_SERVING",
            target,
            {"rows": target.materialization.row_count + 1, "columns": len(target.materialization.ordered_columns)},
            1,
        )
    validate_existing(existing, target)
    current = existing["meta"]
    same = all(
        current[key] == target.meta[key]
        for key in ("snapshot_id", "canonical_matrix_sha256", "schema_fingerprint_sha256")
    )
    if same and existing["headers"] == list(target.materialization.ordered_columns):
        return ServingPlan(
            "NO_CHANGE_IDEMPOTENT",
            target,
            {"rows": 0, "columns": 0},
            0,
            semantic_readback_required=False,
        )
    rows = max(len(existing["rows"]), target.materialization.row_count) + 1
    columns = max(len(existing["headers"]), len(target.materialization.ordered_columns))
    return ServingPlan(
        "REPLACE_SERVING_FROM_NEW_SNAPSHOT",
        target,
        {"rows": rows, "columns": columns},
        1,
    )


def validate_remote_preflight(
    target: ServingTarget,
    *,
    parent: str,
    title: str | None = None,
    remote_matches: int,
    mime: str | None,
    snapshot_validated: bool,
    manifest_validated: bool,
) -> None:
    if parent != "13_BI/02_SERVING":
        _stop("SERVING_WRONG_PARENT")
    if title is not None and title != target.serving_name:
        _stop("SERVING_WRONG_TITLE")
    if not isinstance(remote_matches, int) or remote_matches < 0:
        _stop("SERVING_REMOTE_STATE_INVALID")
    if remote_matches > 1:
        _stop("SERVING_DUPLICATE_REMOTE_NAME")
    if remote_matches == 1 and mime != "application/vnd.google-apps.spreadsheet":
        _stop("SERVING_WRONG_MIME")
    if not snapshot_validated or not manifest_validated:
        _stop("SERVING_SNAPSHOT_NOT_VALIDATED")


def validate_serving_authorization(
    auth: dict | None,
    *,
    implementation_sha: str,
    target: ServingTarget,
) -> str:
    if not isinstance(auth, dict) or auth.get("authorized") is not True or auth.get("serving_mutation_authorized") is not True:
        _stop("SERVING_T3_NOT_AUTHORIZED")
    required = {
        "authorization_id", "authorized", "repository", "tier", "drive_root", "parent_path", "task",
        "scope", "implementation_sha", "selected_datasets", "selected_snapshots", "consumed", "test_only",
        "serving_mutation_authorized", "looker_publication_authorized",
    }
    if set(auth) != required:
        _stop("SERVING_AUTHORIZATION_MISMATCH")
    authorization_id = auth.get("authorization_id")
    if not isinstance(authorization_id, str) or not authorization_id.strip():
        _stop("SERVING_AUTHORIZATION_MISMATCH")
    if not isinstance(implementation_sha, str) or not HEX40.fullmatch(implementation_sha):
        _stop("SERVING_AUTHORIZATION_IMPLEMENTATION_SHA_INVALID")
    auth_sha = auth.get("implementation_sha")
    if not isinstance(auth_sha, str) or not HEX40.fullmatch(auth_sha):
        _stop("SERVING_AUTHORIZATION_IMPLEMENTATION_SHA_INVALID")
    expected = (
        "ferinbon-cpu/robo-dados-publicos",
        "T3_MUTATING_OR_PUBLICATION",
        "13_BI",
        "13_BI/02_SERVING",
        "BI_003_STABLE_SERVING_MATERIALIZATION",
        "STABLE_SERVING_SHEETS_FROM_PINNED_BI_SNAPSHOTS",
    )
    actual = tuple(
        auth.get(key)
        for key in ("repository", "tier", "drive_root", "parent_path", "task", "scope")
    )
    if actual != expected or auth_sha != implementation_sha:
        _stop("SERVING_AUTHORIZATION_MISMATCH")
    if auth.get("consumed") is True:
        _stop("SERVING_AUTHORIZATION_CONSUMED")
    if auth.get("test_only") is True:
        _stop("SERVING_AUTHORIZATION_TEST_ONLY")
    if auth.get("looker_publication_authorized") is not False:
        _stop("SERVING_AUTHORIZATION_INCLUDES_LOOKER")
    selected_datasets = auth.get("selected_datasets")
    selected_snapshots = auth.get("selected_snapshots")
    if not isinstance(selected_datasets, list) or target.dataset_id not in selected_datasets:
        _stop("SERVING_DATASET_NOT_AUTHORIZED")
    if not isinstance(selected_snapshots, dict) or selected_snapshots.get(target.dataset_id) != target.materialization.snapshot_id:
        _stop("SERVING_SNAPSHOT_NOT_AUTHORIZED")
    return "PASS_BI_SERVING_AUTHORIZATION_VALID"


def plan_looker_publication(*_args, **_kwargs):
    _stop("LOOKER_SEPARATE_AUTHORIZATION_REQUIRED")


def semantic_readback(target: ServingTarget, readback: dict) -> str:
    try:
        if readback.get("tabs") != ["DATA", "META"]:
            _stop("SERVING_READBACK_MISMATCH")
        if readback.get("formula_present") or readback.get("extra_cells"):
            _stop("SERVING_READBACK_MISMATCH")
        if readback.get("headers") != list(target.materialization.ordered_columns):
            _stop("SERVING_READBACK_MISMATCH")
        rebuilt = build_plan(target.dataset_id, readback["rows"])
        if rebuilt.schema_fingerprint_sha256 != target.schema_fingerprint_sha256:
            _stop("SERVING_READBACK_MISMATCH")
        if rebuilt.canonical_matrix_sha256 != target.materialization.canonical_matrix_sha256:
            _stop("SERVING_READBACK_MISMATCH")
        if readback.get("meta") != target.meta:
            _stop("SERVING_READBACK_MISMATCH")
    except BIServingError:
        raise
    except (BIMaterializationError, KeyError, TypeError, ValueError) as exc:
        raise BIServingError("STOP_BI_SERVING_READBACK_MISMATCH") from exc
    return PASS_READBACK


def serving_generation_manifest(
    plan: ServingPlan,
    authorization_id: str,
    implementation_sha: str,
) -> dict:
    if not isinstance(authorization_id, str) or not authorization_id.strip():
        _stop("SERVING_AUTHORIZATION_MISMATCH")
    if not isinstance(implementation_sha, str) or not HEX40.fullmatch(implementation_sha):
        _stop("SERVING_AUTHORIZATION_IMPLEMENTATION_SHA_INVALID")
    target = plan.target
    return {
        "dataset_id": target.dataset_id,
        "serving_name": target.serving_name,
        "selected_snapshot_id": target.materialization.snapshot_id,
        "schema_fingerprint_sha256": target.schema_fingerprint_sha256,
        "canonical_matrix_sha256": target.materialization.canonical_matrix_sha256,
        "row_count": target.materialization.row_count,
        "column_count": len(target.materialization.ordered_columns),
        "authorization_id": authorization_id,
        "implementation_sha": implementation_sha,
        "operation": plan.operation,
        "semantic_readback_verified": True,
        "generation_manifest_create_only": True,
        "overwrite_canonical_snapshot": False,
        "source_snapshot_modified": False,
        "looker_publication": False,
        "recurrence": False,
        "schedule": False,
        "filename": (
            f"{target.dataset_id}__serving_generation__"
            f"{target.materialization.snapshot_id}__manifest.json"
        ),
    }


def classify_remote_failure(*, ambiguous=False, partial_initial_creation=False) -> None:
    if partial_initial_creation:
        _stop("SERVING_PARTIAL_INITIAL_CREATION_OWNER_DECISION_REQUIRED")
    if ambiguous:
        _stop("SERVING_REMOTE_OPERATION_AMBIGUOUS_READBACK_REQUIRED")

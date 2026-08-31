"""Pure BI-002 planner and deterministic local XLSX renderer.

There is deliberately no remote transport in this module. Plans describe future
T2/T3 boundaries but never authorize or execute them.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from io import BytesIO
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from openpyxl import Workbook

from .bi_model import BIModelError, build_dataset, load_contract

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config/bi/materialization.v1.json"
PASS = "PASS_BI_MATERIALIZATION_PLAN_OFFLINE"
REPO = "ferinbon-cpu/robo-dados-publicos"
T2_TASK = "BI_002_FIRST_T2_CREATE_ONLY_MATERIALIZATION"
T2_SCOPE = "13_BI_CREATE_ONLY_SNAPSHOTS"
HEX40 = re.compile(r"^[0-9a-f]{40}$")


class BIMaterializationError(ValueError):
    pass


def _stop(code: str) -> None:
    raise BIMaterializationError(f"STOP_BI_{code}")


def load_policy(path: str | Path = POLICY_PATH) -> dict:
    try:
        policy = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        raise BIMaterializationError("STOP_BI_INVALID_SCHEMA") from exc
    if (policy.get("task"), policy.get("tier"), policy.get("future_drive_root")) != (
        "BI_002", "T0_OFFLINE_IMPLEMENTATION_REVIEW", "13_BI"
    ):
        _stop("INVALID_SCHEMA")
    auth = policy.get("authorization_contract")
    required = {
        "authorization_id", "authorized", "repository", "tier", "drive_root",
        "task", "scope", "implementation_sha", "consumed", "test_only",
    }
    if not isinstance(auth, dict) or set(auth.get("required_fields", [])) != required:
        _stop("INVALID_SCHEMA")
    return policy


def validate_future_root(root: str, policy: dict | None = None) -> str:
    policy = policy or load_policy()
    if root in policy["reserved_roots"] or (
        len(root) >= 2 and root[:2].isdigit() and int(root[:2]) <= 12
    ):
        _stop("RESERVED_ROOT")
    if root != "13_BI":
        _stop("ROOT_COLLISION")
    return PASS


def _field_identity(field: dict) -> dict:
    """Keep schema semantics in the canonical snapshot identity."""
    return {
        "name": field["name"],
        "data_type": field["data_type"],
        "nullable": bool(field["nullable"]),
        "enum": list(field["enum"]) if field.get("enum") else None,
        "format": field.get("format"),
    }


def _decimal_text(value) -> str:
    decimal_value = Decimal(str(value))
    if not decimal_value.is_finite():
        _stop("INVALID_SCHEMA")
    normalized = decimal_value.normalize()
    return format(normalized, "f")


def _typed(value, field: dict):
    """Canonical cell representation bound to the declared BI semantic type."""
    kind = field["data_type"]
    if value is None:
        return [kind, None]
    if kind == "boolean":
        return [kind, value]
    if kind == "integer":
        return [kind, str(value)]
    if kind in {"number", "currency"}:
        return [kind, _decimal_text(value)]
    if kind in {"date", "datetime", "text"}:
        return [kind, value]
    _stop("INVALID_SCHEMA")


def _schema_identity(spec: dict) -> dict:
    return {
        "dataset_id": spec["dataset_id"],
        "primary_key": list(spec["primary_key"]),
        "fields": [_field_identity(field) for field in spec["fields"]],
    }


@dataclass(frozen=True)
class MaterializationPlan:
    dataset_id: str
    source_contract: str
    rows: tuple[tuple, ...]
    ordered_columns: tuple[str, ...]
    primary_key: tuple[str, ...]
    deterministic_row_ordering: tuple[str, ...]
    row_count: int
    schema_fingerprint_sha256: str
    canonical_matrix: str
    canonical_matrix_sha256: str
    snapshot_id: str
    proposed_snapshot_filename: str
    proposed_manifest_filename: str
    future_serving_name: str
    provenance_summary: tuple[str, ...]
    governance_tier_required: str = "T2_CREATE_ONLY"
    status: str = PASS


def build_plan(dataset_id: str, rows, contract: dict | None = None) -> MaterializationPlan:
    contract = contract or load_contract()
    policy = load_policy()
    if dataset_id not in policy["dataset_allowlist"]:
        _stop("UNKNOWN_DATASET")
    try:
        validated = build_dataset(dataset_id, rows, contract)
    except BIModelError as exc:
        message = str(exc)
        if "DUPLICATE_PRIMARY_KEY" in message:
            _stop("DUPLICATE_PRIMARY_KEY")
        raise BIMaterializationError("STOP_BI_INVALID_SCHEMA") from exc

    spec = next(item for item in contract["datasets"] if item["dataset_id"] == dataset_id)
    fields = list(spec["fields"])
    columns = tuple(field["name"] for field in fields)
    schema_identity = _schema_identity(spec)
    schema_canonical = json.dumps(
        schema_identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    schema_digest = hashlib.sha256(schema_canonical.encode("utf-8")).hexdigest()
    matrix_value = {
        "schema": schema_identity,
        "schema_fingerprint_sha256": schema_digest,
        "rows": [[_typed(row[field["name"]], field) for field in fields] for row in validated],
    }
    canonical = json.dumps(
        matrix_value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    snapshot_id = digest[:24]
    values = tuple(tuple(row[col] for col in columns) for row in validated)
    provenance = tuple(
        sorted(
            {
                str(row.get("provenance_id") or row.get("provenance_reference"))
                for row in validated
            }
        )
    )
    return MaterializationPlan(
        dataset_id,
        "config/bi/analytics_output.v1.json",
        values,
        columns,
        tuple(spec["primary_key"]),
        tuple(spec["primary_key"]),
        len(values),
        schema_digest,
        canonical,
        digest,
        snapshot_id,
        f"{dataset_id}__snapshot__{snapshot_id}.xlsx",
        f"{dataset_id}__snapshot__{snapshot_id}__manifest.json",
        f"{dataset_id}__SERVING",
        provenance,
    )


def _xlsx_value(value, kind):
    if value is None:
        return None
    if kind == "date":
        return date.fromisoformat(value)
    if kind == "datetime":
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    if isinstance(value, Decimal):
        return float(value)
    return value


def render_xlsx(plan: MaterializationPlan, contract: dict | None = None) -> bytes:
    """Render reproducible bytes; ZIP metadata and workbook properties are pinned."""
    contract = contract or load_contract()
    spec = next(item for item in contract["datasets"] if item["dataset_id"] == plan.dataset_id)
    kinds = [field["data_type"] for field in spec["fields"]]
    wb = Workbook()
    ws = wb.active
    ws.title = plan.dataset_id[:31]
    ws.append(list(plan.ordered_columns))
    for row in plan.rows:
        ws.append([_xlsx_value(v, k) for v, k in zip(row, kinds)])
    fixed = datetime(2000, 1, 1, tzinfo=timezone.utc)
    wb.properties.created = fixed
    wb.properties.modified = fixed
    raw = BytesIO()
    wb.save(raw)
    source, target = ZipFile(BytesIO(raw.getvalue())), BytesIO()
    with source, ZipFile(target, "w", ZIP_DEFLATED, compresslevel=9) as out:
        for name in sorted(source.namelist()):
            info = ZipInfo(name, (2000, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            out.writestr(info, source.read(name))
    return target.getvalue()


def build_manifest(
    plan: MaterializationPlan,
    xlsx: bytes,
    *,
    input_provenance=None,
    source_hashes=None,
    generated_from_run=None,
    generated_from_batch=None,
) -> dict:
    return {
        "task": "BI_002",
        "dataset_id": plan.dataset_id,
        "schema_version": 1,
        "snapshot_id": plan.snapshot_id,
        "primary_key": list(plan.primary_key),
        "ordered_columns": list(plan.ordered_columns),
        "row_count": plan.row_count,
        "schema_fingerprint_sha256": plan.schema_fingerprint_sha256,
        "canonical_matrix_sha256": plan.canonical_matrix_sha256,
        "xlsx_bytes": len(xlsx),
        "xlsx_sha256": hashlib.sha256(xlsx).hexdigest(),
        "input_provenance": input_provenance or list(plan.provenance_summary),
        "source_hashes": source_hashes or [],
        "transformation_contract": "BI_001_SCHEMA_BOUND_TYPED_MATRIX_V2",
        "generated_from_run": generated_from_run,
        "generated_from_batch": generated_from_batch,
        "software_version": "0.8.0",
        "quality_status": "VALIDATED",
        "semantic_cautions": [
            "BI_DERIVED_NOT_SOURCE_OF_TRUTH",
            "MATCH_CANDIDATE_NE_FINANCIAL_IDENTITY",
        ],
        "future_drive_root": "13_BI",
        "future_snapshot_path": (
            f"13_BI/01_SNAPSHOTS/{plan.dataset_id}/{plan.proposed_snapshot_filename}"
        ),
        "future_serving_name": plan.future_serving_name,
        "create_only": True,
        "overwrite": False,
        "delete": False,
        "replace": False,
        "serving_mutation_authorized": False,
        "looker_publication_authorized": False,
    }


def validate_manifest(plan: MaterializationPlan, manifest: dict, xlsx: bytes) -> str:
    expected = build_manifest(
        plan,
        xlsx,
        input_provenance=manifest.get("input_provenance"),
        source_hashes=manifest.get("source_hashes"),
        generated_from_run=manifest.get("generated_from_run"),
        generated_from_batch=manifest.get("generated_from_batch"),
    )
    if manifest != expected:
        _stop("MANIFEST_MISMATCH")
    return PASS


def validate_t2_authorization(
    authorization: dict | None,
    *,
    expected_implementation_sha: str | None,
    policy: dict | None = None,
) -> str:
    """Validate a future owner authorization without embedding any active authorization."""
    policy = policy or load_policy()
    if not isinstance(authorization, dict) or authorization.get("authorized") is not True:
        _stop("T2_NOT_AUTHORIZED")
    if authorization.get("test_only") is True:
        _stop("T2_AUTHORIZATION_TEST_ONLY")
    if authorization.get("consumed") is True:
        _stop("T2_AUTHORIZATION_CONSUMED")
    if not isinstance(expected_implementation_sha, str) or not HEX40.fullmatch(
        expected_implementation_sha
    ):
        _stop("T2_AUTHORIZATION_IMPLEMENTATION_SHA_INVALID")
    if authorization.get("implementation_sha") != expected_implementation_sha:
        _stop("T2_AUTHORIZATION_IMPLEMENTATION_SHA_MISMATCH")

    contract = policy["authorization_contract"]
    expected = {
        "repository": contract["repository"],
        "tier": contract["tier"],
        "drive_root": contract["drive_root"],
        "task": contract["task"],
        "scope": contract["scope"],
    }
    observed = {key: authorization.get(key) for key in expected}
    if observed != expected:
        _stop("T2_AUTHORIZATION_SCOPE_MISMATCH")
    if not str(authorization.get("authorization_id") or "").strip():
        _stop("T2_AUTHORIZATION_ID_INVALID")
    return PASS


def future_preflight(
    plan: MaterializationPlan,
    manifest: dict,
    *,
    root="13_BI",
    remote_collision=False,
    authorization: dict | None = None,
    expected_implementation_sha: str | None = None,
) -> str:
    validate_future_root(root)
    pinned = (
        manifest.get("dataset_id"),
        manifest.get("schema_fingerprint_sha256"),
        manifest.get("canonical_matrix_sha256"),
        manifest.get("row_count"),
        manifest.get("ordered_columns"),
        manifest.get("create_only"),
        manifest.get("overwrite"),
        manifest.get("delete"),
        manifest.get("replace"),
    )
    expected = (
        plan.dataset_id,
        plan.schema_fingerprint_sha256,
        plan.canonical_matrix_sha256,
        plan.row_count,
        list(plan.ordered_columns),
        True,
        False,
        False,
        False,
    )
    if pinned != expected:
        _stop("MANIFEST_MISMATCH")
    if manifest.get("snapshot_id") != plan.snapshot_id:
        _stop("SNAPSHOT_ID_MISMATCH")
    if remote_collision:
        _stop("REMOTE_COLLISION_REQUIRES_READBACK")
    validate_t2_authorization(
        authorization,
        expected_implementation_sha=expected_implementation_sha,
    )
    return PASS


def plan_serving(*, snapshot_validated: bool, t3_authorized=False, looker_authorized=False) -> str:
    if not snapshot_validated or not t3_authorized:
        _stop("SERVING_MUTATION_NOT_AUTHORIZED")
    if looker_authorized:
        _stop("LOOKER_SEPARATE_AUTHORIZATION_REQUIRED")
    return PASS

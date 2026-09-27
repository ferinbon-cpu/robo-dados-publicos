"""BI-004 bounded first-serving executor with injected transport only."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Protocol

from .bi_serving import (
    BIServingError,
    PASS_READBACK,
    ServingTarget,
    build_target,
    plan_serving_mutation,
    semantic_readback,
    serialize_target,
    serving_generation_manifest,
    validate_remote_preflight,
)

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config/bi/serving_executor.v1.json"
PASS = "PASS_BI_004_BOUNDED_FIRST_SERVING_EXECUTOR_OFFLINE"
HEX40 = re.compile(r"^[0-9a-f]{40}$")


class BIServingExecutorError(RuntimeError):
    """Deterministic BI-004 STOP."""


def _stop(code: str) -> None:
    raise BIServingExecutorError(f"STOP_BI_SERVING_EXECUTOR_{code}")


class ServingTransport(Protocol):
    """Future transport boundary. BI-004 itself contains no Google client."""

    def discover_exact(self, *, parent_path: str, title: str) -> list[dict]:
        ...

    def create_spreadsheet(
        self, *, parent_path: str, title: str, tabs: list[str]
    ) -> dict:
        ...

    def batch_update(
        self, *, spreadsheet_id: str, payload: dict, clear_grid: dict
    ) -> dict:
        ...

    def readback(self, *, spreadsheet_id: str) -> dict:
        ...

    def create_manifest(
        self, *, parent_path: str, filename: str, content: dict
    ) -> dict:
        ...


@dataclass(frozen=True)
class ExecutorResult:
    status: str
    operation: str
    dataset_id: str
    serving_name: str
    selected_snapshot_id: str
    semantic_readback_verified: bool
    authorization_id: str
    implementation_sha: str
    discovery_read_count: int
    spreadsheet_create_count: int
    logical_batch_update_count: int
    semantic_readback_count: int
    manifest_create_count: int
    retry_count: int = 0
    delete_count: int = 0
    cleanup_count: int = 0
    looker_publication_count: int = 0

    def sanitized(self) -> dict:
        return {
            "status": self.status,
            "operation": self.operation,
            "dataset_id": self.dataset_id,
            "serving_name": self.serving_name,
            "selected_snapshot_id": self.selected_snapshot_id,
            "semantic_readback_verified": self.semantic_readback_verified,
            "authorization_id": self.authorization_id,
            "implementation_sha": self.implementation_sha,
            "discovery_read_count": self.discovery_read_count,
            "spreadsheet_create_count": self.spreadsheet_create_count,
            "logical_batch_update_count": self.logical_batch_update_count,
            "semantic_readback_count": self.semantic_readback_count,
            "manifest_create_count": self.manifest_create_count,
            "retry_count": self.retry_count,
            "delete_count": self.delete_count,
            "cleanup_count": self.cleanup_count,
            "looker_publication_count": self.looker_publication_count,
            "remote_ids_included": False,
        }


def load_executor_contract(path: str | Path = POLICY_PATH) -> dict:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        raise BIServingExecutorError(
            "STOP_BI_SERVING_EXECUTOR_INVALID_CONTRACT"
        ) from exc

    expected = (
        1,
        "BI_004",
        "T0_OFFLINE_IMPLEMENTATION_REVIEW",
        "13_BI/02_SERVING",
        "13_BI/00_MANIFESTS",
        "BI_SIOPE_SERIES",
        "BI_SIOPE_SERIES__SERVING",
        "application/vnd.google-apps.spreadsheet",
    )
    actual = (
        value.get("schema_version"),
        value.get("task"),
        value.get("tier"),
        value.get("parent_path"),
        value.get("manifest_parent_path"),
        value.get("selected_dataset"),
        value.get("serving_name"),
        value.get("google_sheets_mime"),
    )
    if actual != expected:
        _stop("INVALID_CONTRACT")
    if value.get("tabs") != ["DATA", "META"]:
        _stop("INVALID_CONTRACT")
    if value.get("remote_execution_authorized") is not False:
        _stop("INVALID_CONTRACT")
    if value.get("active_authorization") is not None:
        _stop("INVALID_CONTRACT")
    if value.get("looker_publication_authorized") is not False:
        _stop("INVALID_CONTRACT")
    if value.get("retry_authorized") is not False:
        _stop("INVALID_CONTRACT")
    if value.get("cleanup_authorized") is not False:
        _stop("INVALID_CONTRACT")
    if value.get("replace_existing_authorized_first_live") is not False:
        _stop("INVALID_CONTRACT")
    if value.get("first_live_operation_allowlist") != [
        "CREATE_INITIAL_SERVING",
        "NO_CHANGE_IDEMPOTENT",
    ]:
        _stop("INVALID_CONTRACT")
    if value.get("limits") != {
        "discovery_read_count": 1,
        "spreadsheet_create_count_max": 1,
        "logical_batch_update_count_max": 1,
        "semantic_readback_count_max": 1,
        "manifest_create_count_max": 1,
        "retry_count": 0,
        "delete_count": 0,
        "cleanup_count": 0,
        "looker_publication_count": 0,
    }:
        _stop("INVALID_CONTRACT")
    selected = value.get("selected_snapshot")
    required_snapshot_keys = {
        "snapshot_id",
        "canonical_matrix_sha256",
        "schema_fingerprint_sha256",
        "row_count",
    }
    if not isinstance(selected, dict) or set(selected) != required_snapshot_keys:
        _stop("INVALID_CONTRACT")
    return value


def _validate_target_against_pin(target: ServingTarget, contract: dict) -> None:
    if target.dataset_id != contract["selected_dataset"]:
        _stop("DATASET_NOT_PINNED")
    if target.serving_name != contract["serving_name"]:
        _stop("SERVING_NAME_MISMATCH")
    pinned = contract["selected_snapshot"]
    actual = {
        "snapshot_id": target.materialization.snapshot_id,
        "canonical_matrix_sha256": target.materialization.canonical_matrix_sha256,
        "schema_fingerprint_sha256": target.schema_fingerprint_sha256,
        "row_count": target.materialization.row_count,
    }
    if actual != pinned:
        _stop("SNAPSHOT_PIN_MISMATCH")


def validate_executor_authorization(
    auth: dict | None,
    *,
    implementation_sha: str,
    target: ServingTarget,
    contract: dict | None = None,
) -> str:
    contract = contract or load_executor_contract()
    _validate_target_against_pin(target, contract)

    if not isinstance(auth, dict) or auth.get("authorized") is not True:
        _stop("T3_NOT_AUTHORIZED")

    required = {
        "authorization_id",
        "authorized",
        "repository",
        "tier",
        "drive_root",
        "parent_path",
        "task",
        "scope",
        "implementation_sha",
        "selected_datasets",
        "selected_snapshots",
        "consumed",
        "test_only",
        "serving_mutation_authorized",
        "looker_publication_authorized",
        "first_live_proof_only",
        "replace_existing_authorized",
        "retry_authorized",
        "cleanup_authorized",
        "generation_manifest_create_only_authorized",
    }
    if set(auth) != required:
        _stop("AUTHORIZATION_MISMATCH")

    if not isinstance(implementation_sha, str) or not HEX40.fullmatch(
        implementation_sha
    ):
        _stop("IMPLEMENTATION_SHA_INVALID")
    auth_sha = auth.get("implementation_sha")
    if not isinstance(auth_sha, str) or not HEX40.fullmatch(auth_sha):
        _stop("IMPLEMENTATION_SHA_INVALID")

    expected = (
        "ferinbon-cpu/robo-dados-publicos",
        "T3_MUTATING_OR_PUBLICATION",
        "13_BI",
        contract["parent_path"],
        "BI_004_FIRST_BOUNDED_SERVING_PROOF",
        "BI_SIOPE_SERIES_CREATE_OR_IDEMPOTENT_READBACK_ONLY",
    )
    actual = tuple(
        auth.get(key)
        for key in (
            "repository",
            "tier",
            "drive_root",
            "parent_path",
            "task",
            "scope",
        )
    )
    if actual != expected or auth_sha != implementation_sha:
        _stop("AUTHORIZATION_MISMATCH")
    authorization_id = auth.get("authorization_id")
    if not isinstance(authorization_id, str) or not authorization_id.strip():
        _stop("AUTHORIZATION_MISMATCH")
    if auth.get("consumed") is True:
        _stop("AUTHORIZATION_CONSUMED")
    if auth.get("test_only") is True:
        _stop("AUTHORIZATION_TEST_ONLY")
    if auth.get("serving_mutation_authorized") is not True:
        _stop("T3_NOT_AUTHORIZED")
    if auth.get("looker_publication_authorized") is not False:
        _stop("AUTHORIZATION_INCLUDES_LOOKER")
    if auth.get("first_live_proof_only") is not True:
        _stop("AUTHORIZATION_MISMATCH")
    if auth.get("replace_existing_authorized") is not False:
        _stop("REPLACE_NOT_AUTHORIZED_FIRST_LIVE")
    if auth.get("retry_authorized") is not False:
        _stop("RETRY_NOT_AUTHORIZED")
    if auth.get("cleanup_authorized") is not False:
        _stop("CLEANUP_NOT_AUTHORIZED")
    if auth.get("generation_manifest_create_only_authorized") is not True:
        _stop("MANIFEST_NOT_AUTHORIZED")
    if auth.get("selected_datasets") != [contract["selected_dataset"]]:
        _stop("DATASET_NOT_AUTHORIZED")
    if auth.get("selected_snapshots") != {
        contract["selected_dataset"]: contract["selected_snapshot"]["snapshot_id"]
    }:
        _stop("SNAPSHOT_NOT_AUTHORIZED")
    return "PASS_BI_SERVING_EXECUTOR_AUTHORIZATION_VALID"


def _safe_transport_call(code: str, fn, **kwargs):
    try:
        return fn(**kwargs)
    except BIServingExecutorError:
        raise
    except Exception as exc:
        raise BIServingExecutorError(
            f"STOP_BI_SERVING_EXECUTOR_{code}"
        ) from exc


def _validate_discovery(matches: Any, target: ServingTarget, contract: dict) -> None:
    if not isinstance(matches, list):
        _stop("DISCOVERY_INVALID")
    if len(matches) > 1:
        _stop("DUPLICATE_REMOTE_NAME")
    if len(matches) == 1:
        item = matches[0]
        if not isinstance(item, dict):
            _stop("DISCOVERY_INVALID")
        if item.get("title") != target.serving_name:
            _stop("WRONG_TITLE")
        if item.get("mime") != contract["google_sheets_mime"]:
            _stop("WRONG_MIME")
        if not isinstance(item.get("spreadsheet_id"), str) or not item[
            "spreadsheet_id"
        ]:
            _stop("DISCOVERY_INVALID")
    validate_remote_preflight(
        target,
        parent=contract["parent_path"],
        title=target.serving_name,
        remote_matches=len(matches),
        mime=(
            matches[0].get("mime")
            if len(matches) == 1 and isinstance(matches[0], dict)
            else None
        ),
        snapshot_validated=True,
        manifest_validated=True,
    )


def execute_first_serving(
    *,
    rows: list[dict],
    transport: ServingTransport,
    authorization: dict | None,
    implementation_sha: str,
    snapshot_validated: bool,
    manifest_validated: bool,
    contract: dict | None = None,
) -> dict:
    """Execute one bounded first-serving proof through an injected transport."""
    contract = contract or load_executor_contract()
    if not snapshot_validated or not manifest_validated:
        _stop("SNAPSHOT_NOT_VALIDATED")

    try:
        target = build_target(contract["selected_dataset"], rows)
    except BIServingError as exc:
        raise BIServingExecutorError(
            "STOP_BI_SERVING_EXECUTOR_INVALID_TARGET"
        ) from exc
    _validate_target_against_pin(target, contract)
    validate_executor_authorization(
        authorization,
        implementation_sha=implementation_sha,
        target=target,
        contract=contract,
    )

    matches = _safe_transport_call(
        "DISCOVERY_FAILED_NO_RETRY",
        transport.discover_exact,
        parent_path=contract["parent_path"],
        title=target.serving_name,
    )
    _validate_discovery(matches, target, contract)

    if matches:
        spreadsheet_id = matches[0]["spreadsheet_id"]
        existing = _safe_transport_call(
            "READBACK_FAILED_NO_RETRY",
            transport.readback,
            spreadsheet_id=spreadsheet_id,
        )
        try:
            plan = plan_serving_mutation(
                target, existing, snapshot_validated=True
            )
        except BIServingError as exc:
            raise BIServingExecutorError(str(exc)) from exc

        if plan.operation == "REPLACE_SERVING_FROM_NEW_SNAPSHOT":
            _stop("REPLACE_NOT_AUTHORIZED_FIRST_LIVE")
        if plan.operation != "NO_CHANGE_IDEMPOTENT":
            _stop("UNEXPECTED_OPERATION")
        if semantic_readback(target, existing) != PASS_READBACK:
            _stop("READBACK_MISMATCH")
        result = ExecutorResult(
            status=PASS,
            operation=plan.operation,
            dataset_id=target.dataset_id,
            serving_name=target.serving_name,
            selected_snapshot_id=target.materialization.snapshot_id,
            semantic_readback_verified=True,
            authorization_id=authorization["authorization_id"],
            implementation_sha=implementation_sha,
            discovery_read_count=1,
            spreadsheet_create_count=0,
            logical_batch_update_count=0,
            semantic_readback_count=1,
            manifest_create_count=0,
        )
        return result.sanitized()

    plan = plan_serving_mutation(target, None, snapshot_validated=True)
    if plan.operation != "CREATE_INITIAL_SERVING":
        _stop("UNEXPECTED_OPERATION")

    created = _safe_transport_call(
        "CREATE_FAILED_AMBIGUOUS_OWNER_DECISION_REQUIRED",
        transport.create_spreadsheet,
        parent_path=contract["parent_path"],
        title=target.serving_name,
        tabs=list(contract["tabs"]),
    )
    if not isinstance(created, dict):
        _stop("CREATE_RESPONSE_INVALID")
    spreadsheet_id = created.get("spreadsheet_id")
    if (
        not isinstance(spreadsheet_id, str)
        or not spreadsheet_id
        or created.get("title") != target.serving_name
        or created.get("mime") != contract["google_sheets_mime"]
        or created.get("tabs") != list(contract["tabs"])
    ):
        _stop("CREATE_RESPONSE_INVALID")

    payload = serialize_target(target)
    updated = _safe_transport_call(
        "PARTIAL_INITIAL_CREATION_OWNER_DECISION_REQUIRED",
        transport.batch_update,
        spreadsheet_id=spreadsheet_id,
        payload=payload,
        clear_grid=plan.clear_grid,
    )
    if updated != {"logical_batch_update_count": 1, "retry_count": 0}:
        _stop("WRITE_RESPONSE_INVALID")

    readback = _safe_transport_call(
        "PARTIAL_INITIAL_CREATION_OWNER_DECISION_REQUIRED",
        transport.readback,
        spreadsheet_id=spreadsheet_id,
    )
    try:
        readback_status = semantic_readback(target, readback)
    except BIServingError as exc:
        raise BIServingExecutorError(
            "STOP_BI_SERVING_EXECUTOR_PARTIAL_INITIAL_CREATION_OWNER_DECISION_REQUIRED"
        ) from exc
    if readback_status != PASS_READBACK:
        _stop("PARTIAL_INITIAL_CREATION_OWNER_DECISION_REQUIRED")

    generation = serving_generation_manifest(
        plan, authorization["authorization_id"], implementation_sha
    )
    manifest_result = _safe_transport_call(
        "MANIFEST_CREATE_FAILED_OWNER_DECISION_REQUIRED",
        transport.create_manifest,
        parent_path=contract["manifest_parent_path"],
        filename=generation["filename"],
        content=generation,
    )
    if manifest_result != {
        "created": True,
        "create_only": True,
        "collision": False,
    }:
        _stop("MANIFEST_CREATE_RESPONSE_INVALID")

    result = ExecutorResult(
        status=PASS,
        operation=plan.operation,
        dataset_id=target.dataset_id,
        serving_name=target.serving_name,
        selected_snapshot_id=target.materialization.snapshot_id,
        semantic_readback_verified=True,
        authorization_id=authorization["authorization_id"],
        implementation_sha=implementation_sha,
        discovery_read_count=1,
        spreadsheet_create_count=1,
        logical_batch_update_count=1,
        semantic_readback_count=1,
        manifest_create_count=1,
    )
    return result.sanitized()

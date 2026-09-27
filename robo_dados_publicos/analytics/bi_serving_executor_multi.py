"""BI-005 generalized bounded serving executor with injected transport only.

The executor supports the six current BI datasets but one invocation may target
exactly one dataset. This module contains no Google/HTTP client and performs no
remote work unless a separately supplied transport is injected by a future,
explicitly authorized runner.
"""

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
POLICY_PATH = ROOT / "config/bi/serving_executor_multi.v1.json"
PASS = "PASS_BI_005_FINAL_SERVING_INTEGRATION_OFFLINE"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX24 = re.compile(r"^[0-9a-f]{24}$")


class BIMultiServingExecutorError(RuntimeError):
    """Deterministic BI-005 STOP."""


def _stop(code: str) -> None:
    raise BIMultiServingExecutorError(f"STOP_BI_005_{code}")


class ServingTransport(Protocol):
    """Future transport boundary. BI-005 contains no remote client."""

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
        raise BIMultiServingExecutorError("STOP_BI_005_INVALID_CONTRACT") from exc

    expected = (
        1,
        "BI_005",
        "T0_OFFLINE_IMPLEMENTATION_REVIEW",
        PASS,
        "OPTION_3_CREATE_ONLY_SNAPSHOTS_PLUS_STABLE_SERVING_SHEET",
        "396ef26cdb38f79be3c2512329bc9e848774d6f9",
        "ferinbon-cpu/robo-dados-publicos",
        "13_BI",
        "13_BI/02_SERVING",
        "13_BI/00_MANIFESTS",
        "application/vnd.google-apps.spreadsheet",
    )
    actual = (
        value.get("schema_version"),
        value.get("task"),
        value.get("tier"),
        value.get("status"),
        value.get("architecture"),
        value.get("base_main_sha"),
        value.get("repository"),
        value.get("drive_root"),
        value.get("parent_path"),
        value.get("manifest_parent_path"),
        value.get("google_sheets_mime"),
    )
    if actual != expected:
        _stop("INVALID_CONTRACT")
    if value.get("tabs") != ["DATA", "META"]:
        _stop("INVALID_CONTRACT")
    if value.get("one_dataset_per_execution") is not True:
        _stop("INVALID_CONTRACT")
    if value.get("future_live_operation_allowlist") != [
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
    for key in (
        "remote_execution_authorized",
        "looker_publication_authorized",
        "retry_authorized",
        "cleanup_authorized",
        "replace_existing_authorized",
        "multi_dataset_mutation_authorized",
    ):
        if value.get(key) is not False:
            _stop("INVALID_CONTRACT")
    if value.get("active_authorization") is not None:
        _stop("INVALID_CONTRACT")

    allowlist = value.get("dataset_allowlist")
    pins = value.get("dataset_pins")
    expected_allowlist = [
        "BI_SIOPE_SERIES",
        "BI_JORNAL_EVENTOS",
        "BI_RECONCILIACAO",
        "BI_FONTES_STATUS",
        "BI_EXECUCOES_ROBO",
        "BI_DICIONARIO",
    ]
    if allowlist != expected_allowlist or not isinstance(pins, dict):
        _stop("INVALID_CONTRACT")
    if set(pins) != set(expected_allowlist):
        _stop("INVALID_CONTRACT")
    required_pin_keys = {
        "serving_name",
        "row_count",
        "snapshot_id",
        "canonical_matrix_sha256",
        "schema_fingerprint_sha256",
    }
    for dataset_id in expected_allowlist:
        pin = pins.get(dataset_id)
        if not isinstance(pin, dict) or set(pin) != required_pin_keys:
            _stop("INVALID_CONTRACT")
        if pin["serving_name"] != f"{dataset_id}__SERVING":
            _stop("INVALID_CONTRACT")
        if isinstance(pin["row_count"], bool) or not isinstance(pin["row_count"], int) or pin["row_count"] <= 0:
            _stop("INVALID_CONTRACT")
        if not isinstance(pin["snapshot_id"], str) or not HEX24.fullmatch(pin["snapshot_id"]):
            _stop("INVALID_CONTRACT")
        if not isinstance(pin["canonical_matrix_sha256"], str) or not HEX64.fullmatch(pin["canonical_matrix_sha256"]):
            _stop("INVALID_CONTRACT")
        if not isinstance(pin["schema_fingerprint_sha256"], str) or not HEX64.fullmatch(pin["schema_fingerprint_sha256"]):
            _stop("INVALID_CONTRACT")
        if pin["snapshot_id"] != pin["canonical_matrix_sha256"][:24]:
            _stop("INVALID_CONTRACT")

    auth_contract = value.get("authorization_contract")
    if auth_contract != {
        "repository": "ferinbon-cpu/robo-dados-publicos",
        "tier": "T3_MUTATING_OR_PUBLICATION",
        "drive_root": "13_BI",
        "parent_path": "13_BI/02_SERVING",
        "task": "BI_005_BOUNDED_SERVING",
        "scope": "SINGLE_PINNED_STABLE_SERVING_FROM_IMMUTABLE_SNAPSHOT",
        "one_dataset_only": True,
        "exact_sha_required": True,
        "active_authorization_embedded": False,
    }:
        _stop("INVALID_CONTRACT")
    return value


def _dataset_pin(dataset_id: str, contract: dict) -> dict:
    if dataset_id not in contract["dataset_allowlist"]:
        _stop("UNKNOWN_DATASET")
    pin = contract["dataset_pins"].get(dataset_id)
    if not isinstance(pin, dict):
        _stop("UNKNOWN_DATASET")
    return pin


def _validate_target_against_pin(
    target: ServingTarget, dataset_id: str, contract: dict
) -> None:
    pin = _dataset_pin(dataset_id, contract)
    actual = {
        "serving_name": target.serving_name,
        "row_count": target.materialization.row_count,
        "snapshot_id": target.materialization.snapshot_id,
        "canonical_matrix_sha256": target.materialization.canonical_matrix_sha256,
        "schema_fingerprint_sha256": target.schema_fingerprint_sha256,
    }
    if actual != pin:
        _stop("SNAPSHOT_PIN_MISMATCH")


def validate_executor_authorization(
    auth: dict | None,
    *,
    implementation_sha: str,
    target: ServingTarget,
    contract: dict | None = None,
) -> str:
    contract = contract or load_executor_contract()
    _validate_target_against_pin(target, target.dataset_id, contract)

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
        "selected_serving_names",
        "consumed",
        "test_only",
        "serving_mutation_authorized",
        "looker_publication_authorized",
        "replace_existing_authorized",
        "retry_authorized",
        "cleanup_authorized",
        "generation_manifest_create_only_authorized",
    }
    if set(auth) != required:
        _stop("AUTHORIZATION_MISMATCH")
    if not isinstance(implementation_sha, str) or not HEX40.fullmatch(implementation_sha):
        _stop("IMPLEMENTATION_SHA_INVALID")
    auth_sha = auth.get("implementation_sha")
    if not isinstance(auth_sha, str) or not HEX40.fullmatch(auth_sha):
        _stop("IMPLEMENTATION_SHA_INVALID")

    ac = contract["authorization_contract"]
    expected = (
        ac["repository"],
        ac["tier"],
        ac["drive_root"],
        ac["parent_path"],
        ac["task"],
        ac["scope"],
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
    if auth.get("consumed") is not False:
        _stop("AUTHORIZATION_CONSUMED")
    if auth.get("test_only") is not False:
        _stop("AUTHORIZATION_TEST_ONLY")
    if auth.get("serving_mutation_authorized") is not True:
        _stop("T3_NOT_AUTHORIZED")
    if auth.get("looker_publication_authorized") is not False:
        _stop("AUTHORIZATION_INCLUDES_LOOKER")
    if auth.get("replace_existing_authorized") is not False:
        _stop("REPLACE_NOT_AUTHORIZED")
    if auth.get("retry_authorized") is not False:
        _stop("RETRY_NOT_AUTHORIZED")
    if auth.get("cleanup_authorized") is not False:
        _stop("CLEANUP_NOT_AUTHORIZED")
    if auth.get("generation_manifest_create_only_authorized") is not True:
        _stop("MANIFEST_NOT_AUTHORIZED")
    if auth.get("selected_datasets") != [target.dataset_id]:
        _stop("DATASET_NOT_AUTHORIZED")
    if auth.get("selected_snapshots") != {
        target.dataset_id: target.materialization.snapshot_id
    }:
        _stop("SNAPSHOT_NOT_AUTHORIZED")
    if auth.get("selected_serving_names") != [target.serving_name]:
        _stop("SERVING_NAME_NOT_AUTHORIZED")
    return "PASS_BI_005_SINGLE_DATASET_AUTHORIZATION_VALID"


def _safe_transport_call(code: str, fn, **kwargs):
    try:
        return fn(**kwargs)
    except BIMultiServingExecutorError:
        raise
    except Exception as exc:
        raise BIMultiServingExecutorError(f"STOP_BI_005_{code}") from exc


def _validate_discovery(
    matches: Any, target: ServingTarget, contract: dict
) -> None:
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
        if not isinstance(item.get("spreadsheet_id"), str) or not item["spreadsheet_id"]:
            _stop("DISCOVERY_INVALID")
    validate_remote_preflight(
        target,
        parent=contract["parent_path"],
        title=target.serving_name,
        remote_matches=len(matches),
        mime=(matches[0].get("mime") if matches else None),
        snapshot_validated=True,
        manifest_validated=True,
    )


def _generation_manifest(
    *, plan, authorization_id: str, implementation_sha: str, target: ServingTarget
) -> dict:
    value = serving_generation_manifest(plan, authorization_id, implementation_sha)
    value.update(
        {
            "task": "BI_005",
            "ordered_columns": list(target.materialization.ordered_columns),
            "primary_key": list(target.materialization.primary_key),
            "source_snapshot_filename": target.meta["source_snapshot_filename"],
            "source_snapshot_manifest_filename": target.meta["source_manifest_filename"],
            "software_version": target.meta["software_version"],
            "quality_status": target.meta["quality_status"],
            "semantic_cautions_json": target.meta["semantic_cautions_json"],
            "retry_count": 0,
            "delete_count": 0,
            "cleanup_count": 0,
            "looker_publication_count": 0,
        }
    )
    return value


def execute_serving(
    *,
    dataset_id: str,
    rows: list[dict],
    transport: ServingTransport,
    authorization: dict | None,
    implementation_sha: str,
    snapshot_validated: bool,
    manifest_validated: bool,
    contract: dict | None = None,
) -> dict:
    """Execute one bounded serving operation through an injected transport."""
    contract = contract or load_executor_contract()
    _dataset_pin(dataset_id, contract)
    if not snapshot_validated or not manifest_validated:
        _stop("SNAPSHOT_NOT_VALIDATED")

    try:
        target = build_target(dataset_id, rows)
    except BIServingError as exc:
        raise BIMultiServingExecutorError("STOP_BI_005_INVALID_TARGET") from exc
    _validate_target_against_pin(target, dataset_id, contract)
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
            plan = plan_serving_mutation(target, existing, snapshot_validated=True)
        except BIServingError as exc:
            raise BIMultiServingExecutorError(str(exc)) from exc
        if plan.operation == "REPLACE_SERVING_FROM_NEW_SNAPSHOT":
            _stop("REPLACE_NOT_AUTHORIZED")
        if plan.operation != "NO_CHANGE_IDEMPOTENT":
            _stop("UNEXPECTED_OPERATION")
        try:
            readback_status = semantic_readback(target, existing)
        except BIServingError as exc:
            raise BIMultiServingExecutorError(str(exc)) from exc
        if readback_status != PASS_READBACK:
            _stop("READBACK_MISMATCH")
        return ExecutorResult(
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
        ).sanitized()

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
        raise BIMultiServingExecutorError(
            "STOP_BI_005_PARTIAL_INITIAL_CREATION_OWNER_DECISION_REQUIRED"
        ) from exc
    if readback_status != PASS_READBACK:
        _stop("PARTIAL_INITIAL_CREATION_OWNER_DECISION_REQUIRED")

    generation = _generation_manifest(
        plan=plan,
        authorization_id=authorization["authorization_id"],
        implementation_sha=implementation_sha,
        target=target,
    )
    manifest_result = _safe_transport_call(
        "MANIFEST_CREATE_FAILED_OWNER_DECISION_REQUIRED",
        transport.create_manifest,
        parent_path=contract["manifest_parent_path"],
        filename=generation["filename"],
        content=generation,
    )
    if manifest_result != {"created": True, "create_only": True, "collision": False}:
        _stop("MANIFEST_CREATE_RESPONSE_INVALID")

    return ExecutorResult(
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
    ).sanitized()

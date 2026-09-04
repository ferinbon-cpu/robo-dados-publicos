from __future__ import annotations

from pathlib import Path
import hashlib
import json
import re
from typing import Any

from .drive_ingestion_controller import load_controller_contract
from .source_family_maturity import load_maturity_registry, execution_maturity
from .mde_fundeb import (
    F02IngestStop,
    F02SourceContract,
    validate_f02_source_bytes,
)
from .mde_fundeb_parser import normalize_f02_document, reconcile_f02
from .mde_fundeb_local_monitoring import (
    normalize_f02_local_monitoring_document,
    reconcile_f02_local_monitoring,
)


class F02KnownFamilyBundleStop(F02IngestStop):
    """Fail-closed stop for reusable known-family F02 bundles."""


REQUIRED_REMOTE_FALSE = {
    "bronze_write",
    "silver_write",
    "gold_write",
    "serving",
    "publication",
    "site",
    "overwrite",
    "delete",
    "move",
    "schedule",
    "recurrence",
}

EXPECTED_CONTROLLER_MAP = {
    "RREO_MDE": "RREO",
    "FUNDEB_LOCAL": "FUNDEB",
    "MDE_25_LOCAL": "MDE",
}


def _stop(code: str, detail: str | None = None) -> None:
    suffix = f": {detail}" if detail else ""
    raise F02KnownFamilyBundleStop(f"STOP_F02_KNOWN_BUNDLE_{code}{suffix}")


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _safe_repo_file(root: Path, value: object, *, code: str) -> Path:
    text = str(value or "").strip()
    if not text:
        _stop(code + "_MISSING")
    relative = Path(text)
    if relative.is_absolute() or ".." in relative.parts:
        _stop(code + "_UNSAFE", text)

    try:
        root_resolved = root.resolve(strict=True)
    except OSError as exc:
        raise F02KnownFamilyBundleStop(
            f"STOP_F02_KNOWN_BUNDLE_{code}_ROOT_UNREADABLE: {root}"
        ) from exc

    cursor = root_resolved
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            _stop(code + "_SYMLINK", text)

    candidate = root_resolved / relative
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise F02KnownFamilyBundleStop(
            f"STOP_F02_KNOWN_BUNDLE_{code}_UNREADABLE: {text}"
        ) from exc

    if resolved != root_resolved and root_resolved not in resolved.parents:
        _stop(code + "_ESCAPES_ROOT", text)
    if not resolved.is_file():
        _stop(code + "_NOT_FILE", text)
    return resolved


def validate_gate_contract(raw: dict[str, Any]) -> dict[str, Any]:
    if raw.get("schema") != "F02_KNOWN_FAMILY_BUNDLE_GATE_V1":
        _stop("GATE_SCHEMA")
    if raw.get("mode") != "T0_OFFLINE_KNOWN_FAMILY_BUNDLE":
        _stop("GATE_MODE")
    if raw.get("tier") != "T0":
        _stop("GATE_TIER")
    if raw.get("local_snapshot_read_authorized") is not True:
        _stop("GATE_LOCAL_SNAPSHOT_READ")
    blocked = raw.get("blocked_remote_effects")
    if not isinstance(blocked, dict) or set(blocked) != REQUIRED_REMOTE_FALSE:
        _stop("GATE_BLOCKED_EFFECT_SET")
    if any(blocked[key] is not True for key in REQUIRED_REMOTE_FALSE):
        _stop("GATE_REMOTE_EFFECT_OPEN")
    if raw.get("remote_drive_read_authorized") is not False:
        _stop("GATE_REMOTE_DRIVE_READ")
    if raw.get("new_family_or_schema_auto_authorized") is not False:
        _stop("GATE_NEW_SCHEMA_AUTO_AUTH")
    return raw


def validate_adapter_contract(raw: dict[str, Any]) -> dict[str, Any]:
    if raw.get("schema") != "F02_KNOWN_FAMILY_BUNDLE_ADAPTER_V1":
        _stop("ADAPTER_SCHEMA")
    if raw.get("mode") != "OFFLINE_KNOWN_FAMILY_BUNDLE_ADAPTER":
        _stop("ADAPTER_MODE")
    if raw.get("manifest_schema") != "F02_KNOWN_FAMILY_BATCH_MANIFEST_V1":
        _stop("MANIFEST_SCHEMA_CONTRACT")
    if raw.get("ingestion_method") != "MANUAL_SUPERVISED":
        _stop("INGESTION_METHOD")

    kinds = raw.get("allowed_batch_kinds")
    if not isinstance(kinds, dict) or set(kinds) != {"RREO_ALIGNED", "LOCAL_ONLY"}:
        _stop("BATCH_KIND_SET")
    if kinds["RREO_ALIGNED"].get("exact_families") != [
        "RREO_MDE", "FUNDEB_LOCAL", "MDE_25_LOCAL"
    ]:
        _stop("RREO_ALIGNED_FAMILY_SET")
    if kinds["LOCAL_ONLY"].get("exact_families") != ["FUNDEB_LOCAL", "MDE_25_LOCAL"]:
        _stop("LOCAL_ONLY_FAMILY_SET")
    if kinds["LOCAL_ONLY"].get("official_mde_claim_source") is not None:
        _stop("LOCAL_ONLY_OFFICIAL_SOURCE")

    alignment = raw.get("controller_alignment")
    if not isinstance(alignment, dict):
        _stop("CONTROLLER_ALIGNMENT")
    for family, controller_family in EXPECTED_CONTROLLER_MAP.items():
        if alignment.get(family) != controller_family:
            _stop("CONTROLLER_MAP", family)
    if alignment.get("individual_family_maturity_remains") != "ROUTING_ONLY_SUPERVISED_EXECUTION":
        _stop("INDIVIDUAL_MATURITY_PROMOTION")
    if alignment.get("bundle_execution_maturity") != "EXECUTION_READY_BOUNDED_MANUAL_SUPERVISED":
        _stop("BUNDLE_MATURITY")
    if not alignment.get("controller_contract_path") or not alignment.get("maturity_registry_path"):
        _stop("ALIGNMENT_PATHS")
    if not raw.get("gate_contract_path"):
        _stop("GATE_PATH")

    effects = raw.get("automatic_effects")
    if not isinstance(effects, dict) or set(effects) != REQUIRED_REMOTE_FALSE:
        _stop("AUTOMATIC_EFFECT_SET")
    if any(effects[key] is not False for key in REQUIRED_REMOTE_FALSE):
        _stop("AUTOMATIC_EFFECT_ENABLED")

    source_contract = raw.get("source_contract")
    required_true = {
        "exact_hash_required",
        "exact_bytes_required",
        "exact_pages_required",
        "full_text_layer_required",
        "stable_drive_file_id_required",
        "relative_snapshot_path_required",
        "path_traversal_forbidden",
    }
    if not isinstance(source_contract, dict):
        _stop("SOURCE_CONTRACT")
    if any(source_contract.get(key) is not True for key in required_true):
        _stop("SOURCE_CONTRACT_WEAKENED")
    return raw


def validate_controller_alignment(
    adapter: dict[str, Any], *, root: str | Path
) -> dict[str, Any]:
    root = Path(root)
    alignment = adapter["controller_alignment"]
    controller_path = _safe_repo_file(
        root, alignment["controller_contract_path"], code="CONTROLLER_PATH"
    )
    maturity_path = _safe_repo_file(
        root, alignment["maturity_registry_path"], code="MATURITY_PATH"
    )
    gate_path = _safe_repo_file(root, adapter["gate_contract_path"], code="GATE_PATH")
    validate_gate_contract(load_json(gate_path))
    controller = load_controller_contract(controller_path)
    maturity = load_maturity_registry(maturity_path)

    defaults = controller.get("family_default_routes", {})
    for source_family, controller_family in EXPECTED_CONTROLLER_MAP.items():
        if controller_family not in controller.get("known_document_families", {}):
            _stop("CONTROLLER_FAMILY_MISSING", controller_family)
        if defaults.get(controller_family) != "AUTO_INGEST":
            _stop("CONTROLLER_ROUTE_DRIFT", controller_family)
        if execution_maturity(controller_family, maturity) != "ROUTING_ONLY_SUPERVISED_EXECUTION":
            _stop("INDIVIDUAL_MATURITY_DRIFT", controller_family)

    return {
        "status": "PASS_F02_KNOWN_BUNDLE_CONTROLLER_ALIGNMENT",
        "individual_families": {
            source_family: {
                "controller_family": controller_family,
                "route": defaults[controller_family],
                "maturity": execution_maturity(controller_family, maturity),
            }
            for source_family, controller_family in EXPECTED_CONTROLLER_MAP.items()
        },
        "bundle_maturity": alignment["bundle_execution_maturity"],
    }


def _safe_relative_path(value: object) -> Path:
    text = str(value or "").strip()
    if not text:
        _stop("SNAPSHOT_PATH_MISSING")
    path = Path(text)
    if path.is_absolute() or ".." in path.parts:
        _stop("SNAPSHOT_PATH_UNSAFE", text)
    return path


def _validate_period(period: object) -> tuple[str, str]:
    if not isinstance(period, dict):
        _stop("REFERENCE_PERIOD")
    start = str(period.get("start") or "")
    end = str(period.get("end") or "")
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    if not pattern.fullmatch(start) or not pattern.fullmatch(end) or start > end:
        _stop("REFERENCE_PERIOD_VALUE")
    return start, end


def validate_batch_manifest(
    raw: dict[str, Any], adapter: dict[str, Any]
) -> dict[str, Any]:
    if raw.get("schema") != adapter["manifest_schema"]:
        _stop("MANIFEST_SCHEMA")
    if raw.get("mode") != "MANUAL_SUPERVISED_INGEST":
        _stop("MANIFEST_MODE")
    batch_id = str(raw.get("batch_id") or "").strip()
    if not batch_id:
        _stop("BATCH_ID")

    kind = str(raw.get("batch_kind") or "")
    kinds = adapter["allowed_batch_kinds"]
    if kind not in kinds:
        _stop("BATCH_KIND", kind)
    start, end = _validate_period(raw.get("reference_period"))

    sources = raw.get("sources")
    expected_families = kinds[kind]["exact_families"]
    if not isinstance(sources, list) or len(sources) != len(expected_families):
        _stop("SOURCE_COUNT")
    contracts: list[F02SourceContract] = []
    paths: dict[str, Path] = {}
    for item in sources:
        if not isinstance(item, dict):
            _stop("SOURCE_RECORD")
        try:
            contract = F02SourceContract.from_mapping(item)
        except F02IngestStop as exc:
            raise F02KnownFamilyBundleStop(str(exc)) from exc
        if contract.source_id in paths:
            _stop("DUPLICATE_SOURCE_ID", contract.source_id)
        paths[contract.source_id] = _safe_relative_path(item.get("snapshot_path"))
        contracts.append(contract)

    families = [item.family for item in contracts]
    if len(set(families)) != len(families):
        _stop("DUPLICATE_FAMILY")
    if set(families) != set(expected_families):
        _stop("EXACT_FAMILY_SET")

    effects = raw.get("remote_effects_authorized")
    if not isinstance(effects, dict) or set(effects) != REQUIRED_REMOTE_FALSE:
        _stop("REMOTE_EFFECT_SET")
    if any(effects[key] is not False for key in REQUIRED_REMOTE_FALSE):
        _stop("REMOTE_EFFECT_ENABLED")

    return {
        "raw": raw,
        "batch_id": batch_id,
        "batch_kind": kind,
        "period_start": start,
        "period_end": end,
        "contracts": tuple(contracts),
        "snapshot_paths": paths,
    }


def _read_snapshot(root: Path, relative: Path) -> bytes:
    path = _safe_repo_file(root, relative, code="SNAPSHOT_PATH")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise F02KnownFamilyBundleStop(
            f"STOP_F02_KNOWN_BUNDLE_SNAPSHOT_UNREADABLE: {relative}"
        ) from exc


def _validate_normalized_record(
    record: object,
    *,
    expected_family: str,
) -> dict[str, Any]:
    if not isinstance(record, dict):
        _stop("NORMALIZED_SCHEMA", expected_family)
    if record.get("family") != expected_family:
        _stop("NORMALIZED_FAMILY_DRIFT", expected_family)
    for key in ("authority", "period_start", "period_end"):
        if not isinstance(record.get(key), str) or not record.get(key):
            _stop("NORMALIZED_SCHEMA", f"{expected_family}:{key}")
    metrics = record.get("metrics")
    if not isinstance(metrics, dict) or not metrics:
        _stop("NORMALIZED_SCHEMA", f"{expected_family}:metrics")
    return record


def run_known_family_bundle(
    adapter: dict[str, Any],
    manifest: dict[str, Any],
    *,
    root: str | Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    adapter = validate_adapter_contract(adapter)
    root = Path(root)
    controller_alignment = validate_controller_alignment(adapter, root=root)
    plan = validate_batch_manifest(manifest, adapter)

    normalized: list[dict[str, Any]] = []
    source_evidence: list[dict[str, Any]] = []
    try:
        for contract in plan["contracts"]:
            payload = _read_snapshot(root, plan["snapshot_paths"][contract.source_id])
            verified = validate_f02_source_bytes(contract, payload)
            text = verified["text"]
            if plan["batch_kind"] == "LOCAL_ONLY":
                record = normalize_f02_local_monitoring_document(contract, text)
            else:
                record = normalize_f02_document(contract, text)
            record = _validate_normalized_record(record, expected_family=contract.family)
            normalized.append(record)
            source_evidence.append({
                "source_id": contract.source_id,
                "family": contract.family,
                "drive_file_id": contract.drive_file_id,
                "sha256": verified["sha256"],
                "bytes": verified["bytes"],
                "pages": verified["pages"],
                "snapshot_path": str(plan["snapshot_paths"][contract.source_id]),
                "status": verified["status"],
            })
    except F02KnownFamilyBundleStop:
        raise
    except F02IngestStop as exc:
        raise F02KnownFamilyBundleStop(str(exc)) from exc

    observed_periods = {
        (record.get("period_start"), record.get("period_end"))
        for record in normalized
    }
    expected_period = (plan["period_start"], plan["period_end"])
    if observed_periods != {expected_period}:
        _stop(
            "MANIFEST_PERIOD_DRIFT",
            json.dumps(
                {"expected": expected_period, "observed": sorted(observed_periods)},
                sort_keys=True,
            ),
        )

    try:
        if plan["batch_kind"] == "LOCAL_ONLY":
            reconciliation = reconcile_f02_local_monitoring(normalized)
            authority = {
                "official_mde_claim_authorized": False,
                "annual_compliance_claim_authorized": False,
                "rreo_mde_same_period_present": False,
                "interpretation": "LOCAL_MONITORING_ONLY_NOT_OFFICIAL_MDE_SUBSTITUTION",
            }
        else:
            reconciliation = reconcile_f02(normalized)
            authority = {
                "official_mde_claim_authorized": True,
                "official_mde_claim_source": "RREO_MDE",
                "annual_compliance_claim_authorized": False,
                "interpretation": "OFFICIAL_PARTIAL_PERIOD_OBSERVATION_NOT_ANNUAL_COMPLIANCE",
            }
    except F02KnownFamilyBundleStop:
        raise
    except F02IngestStop as exc:
        raise F02KnownFamilyBundleStop(str(exc)) from exc

    core = {
        "schema": "F02_KNOWN_FAMILY_BATCH_RESULT_V1",
        "batch_id": plan["batch_id"],
        "batch_kind": plan["batch_kind"],
        "reference_period": {
            "start": plan["period_start"],
            "end": plan["period_end"],
        },
        "controller_alignment": controller_alignment,
        "sources": source_evidence,
        "normalized": normalized,
        "reconciliation": reconciliation,
        "authority": authority,
        "effects": {
            "source_network_calls": 0,
            "drive_network_calls": 0,
            "bronze_writes": 0,
            "silver_writes": 0,
            "gold_writes": 0,
            "serving_writes": 0,
            "publication_writes": 0,
            "site_writes": 0,
            "overwrite": 0,
            "delete": 0,
            "move": 0,
            "schedule": 0,
            "recurrence": 0,
        },
        "status": "PASS_F02_KNOWN_FAMILY_BATCH_OFFLINE_NOT_PERSISTED",
    }
    digest = hashlib.sha256(canonical_bytes(core)).hexdigest()
    result = {"content_sha256": digest, **core}
    telemetry = {
        "status": result["status"],
        "batch_id": plan["batch_id"],
        "batch_kind": plan["batch_kind"],
        "source_count": len(normalized),
        "content_sha256": digest,
        "remote_effects": 0,
        "gold_authorized": False,
    }
    return result, telemetry

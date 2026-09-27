from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
from typing import Any
import zipfile

from robo_dados_publicos.product.publication import (
    ProductPublicationError,
    PublicationNames,
    publish_product_bundle,
    validate_bundle_integrity,
)
from robo_dados_publicos.product.siope_historical_publication_review import (
    SiopeHistoricalPublicationReviewError,
    review_publication,
)


PASS = "PASS_M8_SIOPE_HISTORICAL_PRODUCT_OUTPUT_PUBLICATION_GATE"
PASS_DRY_RUN = "PASS_M8_SIOPE_HISTORICAL_PRODUCT_OUTPUT_PUBLICATION_DRY_RUN"
ERROR = "STOP_M8_SIOPE_HISTORICAL_PRODUCT_OUTPUT_PUBLICATION"
GATE_ID = "M8_SIOPE_HISTORICAL_PRODUCT_OUTPUT_PUBLICATION_0_8_0"
REMOTE_BASENAME = "SIOPE_LIMEIRA_HISTORICAL_2016_2024_V0_8_0"
SOURCE_ARTIFACT_ID = 9684264254
SOURCE_ARTIFACT_ZIP_BYTES = 28797
SOURCE_ARTIFACT_ZIP_SHA256 = "213693b37e8a2123d1d4df4b4dec0495a5ca9536cb51b23f0549e94da72d080e"
OWNER_AUTHORIZATION_PATH = Path(
    "docs/evidence/M8_SIOPE_HISTORICAL_PRODUCT_OUTPUT_PUBLICATION_OWNER_AUTHORIZATION_0.8.0.json"
)
CLOUD_CONFIG_PATH = Path("config/cloud.json")

EXPECTED_ZIP_MEMBERS: dict[str, tuple[int, str]] = {
    "product/manifest.json": (
        1214,
        "8111dee4dee310a604e0bb9638d3fb3e1c8406c14bc4c7e1a855821329eab5d1",
    ),
    "product/report.html": (
        25974,
        "d4cde578a2ed1a544e3c3989bedbf54d602e01102339ede90f42084f27ea01e8",
    ),
    "product/report.json": (
        25586,
        "a42946e394784d7fdd10d8cecdb611075007cc4902953fa85d3adca47f268c27",
    ),
    "product/report.md": (
        24602,
        "488798af3996a2429a77379719931be102c81864d63a4f38fe259acdfa90b43d",
    ),
    "product/report.pdf": (
        21854,
        "f0e75f41bf1fef333e929b698a2e1e6b404b10f8d0ea2d4916c29063ede3a87b",
    ),
    "product/report_card.json": (
        778,
        "1cb857d4c10c3937683c823763c1e517cbceb16a39204edc30eac7f61700fa25",
    ),
    "product/table.csv": (
        23115,
        "749b8dd8f56b4ced755f634e08c9b4f8d7cd6f75c448e4c55bbfe77f6d7f8a8e",
    ),
    "result.json": (
        1200,
        "1000c052f05e25073650466034969770deaeb4dabc0fb49e0991931e599409a2",
    ),
}


class M8HistoricalPublicationGateError(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise M8HistoricalPublicationGateError(f"{ERROR}_{code}")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _load_json(path: Path, *, code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise M8HistoricalPublicationGateError(f"{ERROR}_{code}") from exc
    _require(isinstance(value, dict), f"{code}_OBJECT")
    return value


def validate_owner_authorization(*, root: str | Path) -> dict[str, Any]:
    repo_root = Path(root)
    evidence = _load_json(repo_root / OWNER_AUTHORIZATION_PATH, code="OWNER_AUTHORIZATION_READ")
    names = PublicationNames.from_basename(REMOTE_BASENAME)
    _require(
        evidence.get("schema") == "M8_SIOPE_HISTORICAL_PRODUCT_OUTPUT_PUBLICATION_OWNER_AUTHORIZATION_V1",
        "OWNER_AUTHORIZATION_SCHEMA",
    )
    _require(evidence.get("status") == "AUTHORIZED_FOR_SINGLE_T3_PUBLICATION", "OWNER_AUTHORIZATION_STATUS")
    _require(evidence.get("gate_id") == GATE_ID, "OWNER_AUTHORIZATION_GATE")
    _require(evidence.get("drive_target") == "08_OUTPUTS", "OWNER_AUTHORIZATION_TARGET")
    _require(evidence.get("required_remote_count") == 3, "OWNER_AUTHORIZATION_COUNT")
    _require(evidence.get("remote_names") == list(names.all()), "OWNER_AUTHORIZATION_NAMES")
    _require(evidence.get("create_only") is True, "OWNER_AUTHORIZATION_CREATE_ONLY")
    _require(evidence.get("manual_execution_required") is True, "OWNER_AUTHORIZATION_MANUAL")
    _require(evidence.get("single_execution") is True, "OWNER_AUTHORIZATION_SINGLE")
    _require(evidence.get("overwrite_allowed") is False, "OWNER_AUTHORIZATION_OVERWRITE")
    _require(evidence.get("delete_allowed") is False, "OWNER_AUTHORIZATION_DELETE")
    _require(evidence.get("replace_allowed") is False, "OWNER_AUTHORIZATION_REPLACE")
    _require(evidence.get("future_batch_execution_authorized") is False, "OWNER_AUTHORIZATION_FUTURE_BATCH")
    return evidence


def validate_source_zip(path: str | Path) -> dict[str, Any]:
    zip_path = Path(path)
    try:
        raw_zip = zip_path.read_bytes()
    except OSError as exc:
        raise M8HistoricalPublicationGateError(f"{ERROR}_SOURCE_ARTIFACT_READ") from exc
    _require(len(raw_zip) == SOURCE_ARTIFACT_ZIP_BYTES, "SOURCE_ARTIFACT_ZIP_BYTES")
    _require(_sha256(raw_zip) == SOURCE_ARTIFACT_ZIP_SHA256, "SOURCE_ARTIFACT_ZIP_SHA256")

    try:
        with zipfile.ZipFile(zip_path, "r") as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            _require(len(names) == len(set(names)), "SOURCE_ARTIFACT_DUPLICATE_MEMBER")
            _require(set(names) == set(EXPECTED_ZIP_MEMBERS), "SOURCE_ARTIFACT_MEMBER_SET")
            for info in infos:
                _require(not info.is_dir(), "SOURCE_ARTIFACT_DIRECTORY_MEMBER")
                _require(not (info.flag_bits & 0x1), "SOURCE_ARTIFACT_ENCRYPTED_MEMBER")
                _require(".." not in Path(info.filename).parts, "SOURCE_ARTIFACT_TRAVERSAL")
                expected_bytes, expected_sha = EXPECTED_ZIP_MEMBERS[info.filename]
                payload = archive.read(info)
                _require(len(payload) == expected_bytes, "SOURCE_ARTIFACT_MEMBER_BYTES")
                _require(_sha256(payload) == expected_sha, "SOURCE_ARTIFACT_MEMBER_SHA256")
    except (OSError, zipfile.BadZipFile) as exc:
        raise M8HistoricalPublicationGateError(f"{ERROR}_SOURCE_ARTIFACT_ZIP_INVALID") from exc

    return {
        "artifact_id": SOURCE_ARTIFACT_ID,
        "zip_bytes": SOURCE_ARTIFACT_ZIP_BYTES,
        "zip_sha256": SOURCE_ARTIFACT_ZIP_SHA256,
        "member_count": len(EXPECTED_ZIP_MEMBERS),
        "member_hash_checks": f"{len(EXPECTED_ZIP_MEMBERS)}/{len(EXPECTED_ZIP_MEMBERS)} PASS",
    }


def extract_product_bundle(source_zip: str | Path, destination: str | Path) -> Path:
    zip_path = Path(source_zip)
    bundle_dir = Path(destination) / "product"
    bundle_dir.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(zip_path, "r") as archive:
        for member in EXPECTED_ZIP_MEMBERS:
            if not member.startswith("product/"):
                continue
            payload = archive.read(member)
            target = bundle_dir / member.removeprefix("product/")
            target.write_bytes(payload)
    return bundle_dir


def prepare_publication_source(
    *,
    root: str | Path,
    source_zip: str | Path,
    work_dir: str | Path,
) -> tuple[Path, dict[str, Any]]:
    repo_root = Path(root)
    review = review_publication(root=repo_root)
    _require(
        review.get("decision") == "READY_FOR_EXPLICIT_OWNER_PUBLICATION_DECISION",
        "PUBLICATION_REVIEW_DECISION",
    )
    _require(review.get("publication_plan", {}).get("remote_writes_performed") == 0, "PUBLICATION_REVIEW_WRITES")
    _require(review.get("publication_plan", {}).get("publication_authorized") is False, "PUBLICATION_REVIEW_AUTH_STATE")
    validate_owner_authorization(root=repo_root)
    source = validate_source_zip(source_zip)
    bundle_dir = extract_product_bundle(source_zip, work_dir)
    validated = validate_bundle_integrity(bundle_dir, "READY_WITH_CAUTION")
    return bundle_dir, {
        "review_status": review.get("status"),
        "source": source,
        "report_id": validated["card"].get("report_id"),
        "report_status": validated["card"].get("status"),
    }


def output_parent_id(*, root: str | Path) -> str:
    cloud = _load_json(Path(root) / CLOUD_CONFIG_PATH, code="CLOUD_CONFIG_READ")
    value = str(cloud.get("outputs_id") or "").strip()
    _require(bool(value), "OUTPUTS_ID_REQUIRED")
    return value


def dry_run_result(*, source: dict[str, Any]) -> dict[str, Any]:
    names = PublicationNames.from_basename(REMOTE_BASENAME)
    return {
        "status": PASS_DRY_RUN,
        "gate_id": GATE_ID,
        "source_artifact_id": SOURCE_ARTIFACT_ID,
        "source_artifact_zip_sha256": source["source"]["zip_sha256"],
        "drive_target": "08_OUTPUTS",
        "would_create": 3,
        "remote_names": list(names.all()),
        "create_only": True,
        "preflight_all_names_before_first_write": True,
        "completion_manifest_written_last": True,
        "network_called": False,
        "drive_writes": 0,
        "source_collection_performed": False,
        "processing_rerun_performed": False,
        "reconciliation_rerun_performed": False,
        "future_batch_execution_authorized": False,
        "remote_identifiers_exposed": False,
        "secret_values_exposed": False,
    }


def execute_publication(
    drive,
    *,
    root: str | Path,
    source_zip: str | Path,
    published_at: str,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="m8-siope-publication-") as raw:
        bundle_dir, source = prepare_publication_source(
            root=root,
            source_zip=source_zip,
            work_dir=Path(raw),
        )
        result = publish_product_bundle(
            drive,
            output_parent_id=output_parent_id(root=root),
            bundle_dir=bundle_dir,
            remote_basename=REMOTE_BASENAME,
            expected_report_status="READY_WITH_CAUTION",
            gate_id=GATE_ID,
            published_at=published_at,
        )
    _require(result.get("created_count") == 3, "CREATED_COUNT")
    _require(result.get("completion_manifest_written_last") is True, "MANIFEST_LAST")
    _require(result.get("overwrite_performed") is False, "OVERWRITE")
    return {
        **result,
        "status": PASS,
        "source_artifact_id": SOURCE_ARTIFACT_ID,
        "source_artifact_zip_sha256": source["source"]["zip_sha256"],
        "source_collection_performed": False,
        "processing_rerun_performed": False,
        "reconciliation_rerun_performed": False,
        "retry_authorized": False,
        "pagination_authorized": False,
        "schedule_enabled": False,
        "future_batch_execution_authorized": False,
    }


__all__ = [
    "ERROR",
    "GATE_ID",
    "M8HistoricalPublicationGateError",
    "PASS",
    "PASS_DRY_RUN",
    "REMOTE_BASENAME",
    "SOURCE_ARTIFACT_ID",
    "SOURCE_ARTIFACT_ZIP_SHA256",
    "dry_run_result",
    "execute_publication",
    "extract_product_bundle",
    "output_parent_id",
    "prepare_publication_source",
    "validate_owner_authorization",
    "validate_source_zip",
]

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from robo_dados_publicos.product.publication import PublicationNames

ERROR = "STOP_M8_SIOPE_HISTORICAL_PRODUCT_OUTPUT_PUBLICATION_REVIEW"
PASS = "PASS_M8_SIOPE_HISTORICAL_PRODUCT_OUTPUT_PUBLICATION_REVIEW_OFFLINE"
REVIEW_GATE_ID = "M8_SIOPE_HISTORICAL_PRODUCT_OUTPUT_PUBLICATION_REVIEW_0_8_0"
FUTURE_PUBLICATION_GATE_ID = "M8_SIOPE_HISTORICAL_PRODUCT_OUTPUT_PUBLICATION_0_8_0"
EVIDENCE_PATH = Path("docs/evidence/M8_T1_NO_CLICK_FIRST_AUTO_RUN_0.8.0.json")
EVIDENCE_BLOB_SHA = "e8788d79ab5a397c5972c7da756944f0d3a1a70b"
POLICY_PATH = Path("config/automation_policy.v1.json")
REMOTE_BASENAME = "SIOPE_LIMEIRA_HISTORICAL_2016_2024_V0_8_0"

EXPECTED_PRODUCT_FILES = {
    "report.json": (25586, "a42946e394784d7fdd10d8cecdb611075007cc4902953fa85d3adca47f268c27"),
    "report_card.json": (778, "1cb857d4c10c3937683c823763c1e517cbceb16a39204edc30eac7f61700fa25"),
    "table.csv": (23115, "749b8dd8f56b4ced755f634e08c9b4f8d7cd6f75c448e4c55bbfe77f6d7f8a8e"),
    "report.md": (24602, "488798af3996a2429a77379719931be102c81864d63a4f38fe259acdfa90b43d"),
    "report.html": (25974, "d4cde578a2ed1a544e3c3989bedbf54d602e01102339ede90f42084f27ea01e8"),
    "report.pdf": (21854, "f0e75f41bf1fef333e929b698a2e1e6b404b10f8d0ea2d4916c29063ede3a87b"),
}
EXPECTED_BUNDLE_MANIFEST = (
    1214,
    "8111dee4dee310a604e0bb9638d3fb3e1c8406c14bc4c7e1a855821329eab5d1",
)


class SiopeHistoricalPublicationReviewError(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise SiopeHistoricalPublicationReviewError(f"{ERROR}_{code}")


def _git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()  # noqa: S324


def _load_json(path: Path, *, code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SiopeHistoricalPublicationReviewError(f"{ERROR}_{code}") from exc
    _require(isinstance(value, dict), f"{code}_OBJECT")
    return value


def _load_evidence(root: Path) -> dict[str, Any]:
    path = root / EVIDENCE_PATH
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise SiopeHistoricalPublicationReviewError(f"{ERROR}_EVIDENCE_READ") from exc
    _require(_git_blob_sha(raw) == EVIDENCE_BLOB_SHA, "EVIDENCE_BLOB_SHA")
    try:
        evidence = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SiopeHistoricalPublicationReviewError(f"{ERROR}_EVIDENCE_JSON") from exc
    _require(isinstance(evidence, dict), "EVIDENCE_OBJECT")
    return evidence


def _validate_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    _require(evidence.get("schema") == "M8_T1_NO_CLICK_FIRST_AUTO_RUN_EVIDENCE_V1", "EVIDENCE_SCHEMA")
    _require(evidence.get("software_candidate") == "0.8.0", "SOFTWARE_CANDIDATE")
    _require(evidence.get("status") == "PASS_M8_T1_NO_CLICK_FIRST_AUTO_RUN", "EVIDENCE_STATUS")

    repository = evidence.get("repository") or {}
    _require(repository.get("full_name") == "ferinbon-cpu/robo-dados-publicos", "REPOSITORY")
    _require(repository.get("visibility") == "public", "REPOSITORY_VISIBILITY")
    _require(repository.get("default_branch") == "main", "DEFAULT_BRANCH")
    _require(repository.get("main_protected") is True, "MAIN_PROTECTION")
    _require(repository.get("ruleset_id") == 21728151, "RULESET_ID")
    _require(repository.get("ruleset_name") == "main-protection-v1", "RULESET_NAME")

    activation = evidence.get("activation") or {}
    _require(activation.get("human_click_for_auto_run") is False, "AUTO_RUN_CLICK")
    _require(activation.get("trigger") == "push", "AUTO_RUN_TRIGGER")
    _require(activation.get("ref") == "refs/heads/main", "AUTO_RUN_REF")

    run = evidence.get("run") or {}
    _require(run.get("id") == 33167693804, "RUN_ID")
    _require(run.get("conclusion") == "success", "RUN_CONCLUSION")
    _require(run.get("branch") == "main", "RUN_BRANCH")

    trust = evidence.get("trust_boundary") or {}
    _require(trust.get("status") == "PASS_M8_T1_TRUST_BOUNDARY", "TRUST_STATUS")
    _require(trust.get("ref_protected") is True, "TRUST_REF_PROTECTED")
    _require(trust.get("policy_decision") == "AUTO_ALLOWED", "TRUST_POLICY")
    _require(trust.get("tier") == "T1_REMOTE_READONLY", "TRUST_TIER")
    _require(trust.get("credential_capability") == "READ_ONLY_PROVEN", "TRUST_CAPABILITY")
    _require(trust.get("source_get_count") == 0, "TRUST_SOURCE_GET")
    _require(trust.get("drive_write_count") == 0, "TRUST_DRIVE_WRITE")
    _require(trust.get("publication_authorized") is False, "TRUST_PUBLICATION")
    _require(trust.get("future_batch_execution_authorized") is False, "TRUST_FUTURE_BATCH")
    _require(trust.get("secrets_available_to_this_job") is False, "TRUST_SECRETS")

    worker = evidence.get("readonly_worker") or {}
    _require(worker.get("conclusion") == "success", "WORKER_CONCLUSION")
    oauth = worker.get("oauth_capability") or {}
    _require(oauth.get("status") == "PASS_M8_READONLY_CREDENTIAL_CAPABILITY", "OAUTH_STATUS")
    _require(oauth.get("scope") == "https://www.googleapis.com/auth/drive.readonly", "OAUTH_SCOPE")
    _require(oauth.get("scope_proof") == "oauth_refresh_and_tokeninfo_exact", "OAUTH_SCOPE_PROOF")
    _require(oauth.get("drive_api_request_count_during_capability_proof") == 0, "OAUTH_DRIVE_REQUEST")
    _require(oauth.get("secret_values_exposed") is False, "OAUTH_SECRET_EXPOSURE")

    effects = worker.get("bounded_effects") or {}
    _require(effects.get("source_get_count") == 0, "SOURCE_GET_COUNT")
    _require(effects.get("drive_lookup_count") == 9, "DRIVE_LOOKUP_COUNT")
    _require(effects.get("drive_download_count") == 9, "DRIVE_DOWNLOAD_COUNT")
    _require(effects.get("drive_write_count") == 0, "DRIVE_WRITE_COUNT")
    _require(effects.get("publication_authorized") is False, "PUBLICATION_AUTHORIZED")
    _require(effects.get("publication_status") == "LOCAL_ONLY_NOT_PUBLISHED", "PUBLICATION_STATUS")
    _require(effects.get("remote_file_id_persisted") is False, "REMOTE_ID")
    _require(effects.get("pagination_authorized") is False, "PAGINATION")
    _require(effects.get("retry_authorized") is False, "RETRY")
    _require(effects.get("recurrence_authorized") is False, "RECURRENCE")
    _require(effects.get("schedule_enabled") is False, "SCHEDULE")
    _require(effects.get("imputation_performed") is False, "IMPUTATION")
    _require(effects.get("future_batch_execution_authorized") is False, "FUTURE_BATCH")

    product = worker.get("product") or {}
    _require(product.get("status") == "PASS_M8_SIOPE_HISTORICAL_GOLD_PRODUCT_OUTPUT_READONLY", "PRODUCT_STATUS")
    _require(product.get("report_status") == "READY_WITH_CAUTION", "REPORT_STATUS")
    _require(product.get("year_count") == 9, "YEAR_COUNT")
    _require(product.get("years") == list(range(2016, 2025)), "YEARS")
    _require(product.get("gold_count") == 9, "GOLD_COUNT")
    _require(product.get("metric_row_count") == 8, "METRIC_ROWS")
    _require(product.get("gold_metric_observations") == 72, "GOLD_OBSERVATIONS")
    _require(product.get("bundle_file_count") == 7, "BUNDLE_FILE_COUNT")
    _require(product.get("next_gate") == REVIEW_GATE_ID, "NEXT_GATE")
    _require(product.get("compliance_claims_authorized") is False, "COMPLIANCE")

    qa = worker.get("qa") or {}
    _require(qa.get("unit") == "1266/1266 PASS", "QA_UNIT")
    _require(qa.get("historical") == "109/109 PASS", "QA_HISTORICAL")

    artifact = evidence.get("artifact") or {}
    _require(artifact.get("id") == 9684264254, "ARTIFACT_ID")
    _require(artifact.get("size_in_bytes") == 28797, "ARTIFACT_BYTES")
    _require(
        artifact.get("digest") == "sha256:213693b37e8a2123d1d4df4b4dec0495a5ca9536cb51b23f0549e94da72d080e",
        "ARTIFACT_DIGEST",
    )
    _require(artifact.get("expired") is False, "ARTIFACT_EXPIRED")
    _require(artifact.get("file_count") == 8, "ARTIFACT_FILE_COUNT")

    artifact_product = artifact.get("product") or {}
    manifest = artifact_product.get("manifest") or {}
    _require(manifest.get("bytes") == EXPECTED_BUNDLE_MANIFEST[0], "MANIFEST_BYTES")
    _require(manifest.get("sha256") == EXPECTED_BUNDLE_MANIFEST[1], "MANIFEST_SHA")
    _require(artifact_product.get("files_verified_against_manifest") == 6, "FILES_VERIFIED")
    _require(artifact_product.get("manifest_hash_and_byte_checks") == "6/6 PASS", "MANIFEST_CHECKS")

    files = artifact_product.get("files") or []
    _require(isinstance(files, list) and len(files) == 6, "ARTIFACT_PRODUCT_FILES")
    actual_files = {
        str(item.get("name")): (item.get("bytes"), item.get("sha256"))
        for item in files
        if isinstance(item, dict)
    }
    _require(actual_files == EXPECTED_PRODUCT_FILES, "ARTIFACT_PRODUCT_HASH_SET")

    pdf = artifact_product.get("pdf") or {}
    _require(pdf.get("pages") == 9, "PDF_PAGES")
    _require(pdf.get("encrypted") is False, "PDF_ENCRYPTED")
    _require(pdf.get("javascript") is False, "PDF_JAVASCRIPT")
    _require(pdf.get("custom_metadata") is False, "PDF_CUSTOM_METADATA")

    sensitive = artifact.get("sensitive_material_scan") or {}
    for key in (
        "google_client_id_matches",
        "google_refresh_token_matches",
        "github_token_matches",
        "private_key_matches",
        "email_matches",
        "remote_drive_file_id_occurrences",
    ):
        _require(sensitive.get(key) == 0, f"SENSITIVE_{key.upper()}")
    _require(sensitive.get("result_remote_file_id_persisted") is False, "SENSITIVE_REMOTE_ID")

    governance = evidence.get("governance") or {}
    _require(governance.get("t1_no_click_operationally_proven") is True, "GOV_T1_PROVEN")
    _require(governance.get("manual_readonly_backstop_preserved") is True, "GOV_BACKSTOP")
    _require(governance.get("t2_create_only_auto_authorized") is False, "GOV_T2")
    _require(governance.get("t3_publication_auto_authorized") is False, "GOV_T3")
    _require(governance.get("publication_authorized") is False, "GOV_PUBLICATION")
    _require(governance.get("future_batch_execution_authorized") is False, "GOV_FUTURE_BATCH")
    _require(governance.get("years_before_2016_authorized") is False, "GOV_OLDER_YEARS")

    return evidence


def _policy_gate(policy: dict[str, Any], gate_id: str) -> dict[str, Any]:
    rows = policy.get("gates") or []
    matches = [row for row in rows if isinstance(row, dict) and row.get("id") == gate_id]
    _require(len(matches) == 1, f"POLICY_GATE_{gate_id}")
    return matches[0]


def _validate_policy(root: Path) -> dict[str, Any]:
    policy = _load_json(root / POLICY_PATH, code="POLICY_JSON")
    _require(policy.get("default_decision") == "BLOCK", "POLICY_DEFAULT")
    invariants = policy.get("policy_invariants") or {}
    _require(invariants.get("publication_is_separate_gate") is True, "POLICY_PUBLICATION_SEPARATE")
    _require(invariants.get("agent_may_authorize_remote_execution") is False, "POLICY_AGENT_AUTH")
    _require(invariants.get("future_batch_execution_authorized") is False, "POLICY_FUTURE_BATCH")

    review = _policy_gate(policy, "M8_SIOPE_HISTORICAL_PRODUCT_OUTPUT_PUBLICATION_REVIEW")
    _require(review.get("tier") == "T0_OFFLINE", "POLICY_REVIEW_TIER")
    _require(review.get("auto_allowed") is True, "POLICY_REVIEW_AUTO")
    review_effects = review.get("effects") or {}
    _require(review_effects.get("source_network") is False, "POLICY_REVIEW_SOURCE")
    _require(review_effects.get("drive_reads") is False, "POLICY_REVIEW_DRIVE_READ")
    _require(review_effects.get("drive_writes") is False, "POLICY_REVIEW_DRIVE_WRITE")
    _require(review_effects.get("publication") is False, "POLICY_REVIEW_PUBLICATION")

    publication = _policy_gate(policy, "PRODUCT_OUTPUT_PUBLICATION")
    _require(publication.get("tier") == "T3_MUTATING_OR_PUBLICATION", "POLICY_PUBLICATION_TIER")
    _require(publication.get("auto_allowed") is False, "POLICY_PUBLICATION_AUTO")
    publication_effects = publication.get("effects") or {}
    _require(publication_effects.get("drive_writes") is True, "POLICY_PUBLICATION_WRITES")
    _require(publication_effects.get("publication") is True, "POLICY_PUBLICATION_EFFECT")
    _require(
        "PUBLICATION_REQUIRES_SEPARATE_EXPLICIT_AUTHORIZATION" in (publication.get("blockers") or []),
        "POLICY_PUBLICATION_BLOCKER",
    )
    return policy


def review_publication(*, root: str | Path) -> dict[str, Any]:
    repo_root = Path(root)
    evidence = _validate_evidence(_load_evidence(repo_root))
    _validate_policy(repo_root)

    names = PublicationNames.from_basename(REMOTE_BASENAME)
    table_bytes, table_sha = EXPECTED_PRODUCT_FILES["table.csv"]
    pdf_bytes, pdf_sha = EXPECTED_PRODUCT_FILES["report.pdf"]
    manifest_bytes, manifest_sha = EXPECTED_BUNDLE_MANIFEST

    return {
        "status": PASS,
        "review_gate_id": REVIEW_GATE_ID,
        "future_publication_gate_id": FUTURE_PUBLICATION_GATE_ID,
        "software_candidate": "0.8.0",
        "source_evidence": {
            "path": str(EVIDENCE_PATH),
            "git_blob_sha": EVIDENCE_BLOB_SHA,
            "run_id": evidence["run"]["id"],
            "artifact_id": evidence["artifact"]["id"],
            "artifact_digest": evidence["artifact"]["digest"],
            "manifest_bytes": manifest_bytes,
            "manifest_sha256": manifest_sha,
        },
        "product": {
            "report_id": "SIOPE_LIMEIRA_HISTORICAL_2016_2024",
            "report_status": "READY_WITH_CAUTION",
            "years": list(range(2016, 2025)),
            "year_count": 9,
            "gold_count": 9,
            "metric_row_count": 8,
            "gold_metric_observations": 72,
            "selected_publication_sources": {
                "table.csv": {"bytes": table_bytes, "sha256": table_sha},
                "report.pdf": {"bytes": pdf_bytes, "sha256": pdf_sha},
            },
            "compliance_claims_authorized": False,
        },
        "publication_plan": {
            "drive_target": "08_OUTPUTS",
            "remote_basename": REMOTE_BASENAME,
            "remote_names": {
                "google_sheet": names.sheet,
                "pdf": names.pdf,
                "completion_manifest": names.manifest,
            },
            "required_remote_count": 3,
            "publications": [
                "GOOGLE_SHEET_FROM_TABLE_CSV",
                "REPORT_PDF",
                "COMPLETION_MANIFEST_JSON",
            ],
            "create_only": True,
            "preflight_all_names_before_first_write": True,
            "collision_policy": "STOP_BEFORE_WRITES",
            "completion_manifest_written_last": True,
            "overwrite_allowed": False,
            "replace_allowed": False,
            "delete_allowed": False,
            "source_collection": "PROHIBITED",
            "processing_rerun": "PROHIBITED",
            "reconciliation_rerun": "PROHIBITED",
            "schedule": "DISABLED",
            "retry": "PROHIBITED",
            "pagination": "PROHIBITED",
            "remote_collision_preflight_observed": False,
            "remote_writes_performed": 0,
            "publication_performed": False,
            "publication_authorized": False,
            "owner_authorization_required": True,
        },
        "policy": {
            "review_tier": "T0_OFFLINE",
            "review_auto_allowed": True,
            "publication_tier": "T3_MUTATING_OR_PUBLICATION",
            "publication_auto_allowed": False,
            "agent_may_authorize_publication": False,
        },
        "decision": "READY_FOR_EXPLICIT_OWNER_PUBLICATION_DECISION",
        "next_action": "REQUEST_EXPLICIT_OWNER_AUTHORIZATION_BEFORE_ANY_M8_08_OUTPUTS_WRITE",
        "future_batch_execution_authorized": False,
        "years_before_2016_authorized": False,
    }

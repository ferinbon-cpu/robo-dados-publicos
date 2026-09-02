from __future__ import annotations

from urllib.parse import urlparse


class LiveProbeReviewStop(ValueError):
    """Fail-closed stop for TASK 029 live-probe evidence review."""


def review_live_probe(contract: dict, evidence: dict) -> dict:
    expected_sha = "2738741f0134873710f993f1abbc146a0a6b0c0e"

    if contract.get("base_sha") != expected_sha or evidence.get("base_sha") != expected_sha:
        raise LiveProbeReviewStop("STOP_TASK_029_BASE_SHA_MISMATCH")

    if contract.get("mode") != "T1_BOUNDED_LIVE_READ_ONLY" or evidence.get("mode") != "T1_BOUNDED_LIVE_READ_ONLY":
        raise LiveProbeReviewStop("STOP_TASK_029_BAD_MODE")

    auth = contract.get("authorization", {})
    evidence_auth = evidence.get("authorization", {})
    if auth.get("owner_authorized") is not True or auth.get("authorized_against_sha") != expected_sha:
        raise LiveProbeReviewStop("STOP_TASK_029_OWNER_AUTHORIZATION_MISSING")
    if evidence_auth.get("owner_authorized") is not True or evidence_auth.get("authorized_against_sha") != expected_sha:
        raise LiveProbeReviewStop("STOP_TASK_029_EVIDENCE_AUTHORIZATION_MISSING")
    if auth.get("live_initial_probe") is not True or evidence_auth.get("live_initial_probe") is not True:
        raise LiveProbeReviewStop("STOP_TASK_029_LIVE_INITIAL_PROBE_NOT_AUTHORIZED")

    forbidden_auth = (
        "candidate_followup",
        "document_download",
        "ocr",
        "drive",
        "silver",
        "gold",
        "serving",
        "publication",
    )
    if any(auth.get(key) is not False for key in forbidden_auth):
        raise LiveProbeReviewStop("STOP_TASK_029_AUTHORIZATION_TOO_BROAD")
    if evidence_auth.get("candidate_followup") is not False:
        raise LiveProbeReviewStop("STOP_TASK_029_FOLLOWUP_NOT_AUTHORIZED")

    limits = contract.get("limits", {})
    probe = evidence.get("probe", {})
    observations = probe.get("observations", [])
    expected_urls = contract.get("initial_urls", [])
    allowed_hosts = set(contract.get("allowed_hosts", []))

    if len(expected_urls) != 3 or len(observations) != 3:
        raise LiveProbeReviewStop("STOP_TASK_029_EXACT_INITIAL_SURFACE_SET_REQUIRED")
    if [item.get("url") for item in observations] != expected_urls:
        raise LiveProbeReviewStop("STOP_TASK_029_INITIAL_URL_ORDER_OR_VALUE_DRIFT")

    for item in observations:
        parsed_host = urlparse(str(item.get("url", ""))).hostname
        if parsed_host not in allowed_hosts or item.get("host") != parsed_host:
            raise LiveProbeReviewStop("STOP_TASK_029_HOST_NOT_ALLOWED")

    request_count = int(probe.get("request_count", -1))
    if request_count != len(observations) or request_count > int(limits.get("max_requests", 0)):
        raise LiveProbeReviewStop("STOP_TASK_029_REQUEST_BUDGET_MISMATCH")

    zero_probe_effects = (
        "retry_count",
        "pagination_count",
        "candidate_followup_count",
        "document_download_count",
    )
    if any(int(probe.get(key, -1)) != 0 for key in zero_probe_effects):
        raise LiveProbeReviewStop("STOP_TASK_029_UNAUTHORIZED_PROBE_EFFECT")

    blocked = [item for item in observations if item.get("classification") == "INITIAL_SURFACE_ACCESS_BLOCKED"]
    accessible = [item for item in observations if item.get("content_observed") is True]
    if len(blocked) != 2 or len(accessible) != 1:
        raise LiveProbeReviewStop("STOP_TASK_029_OBSERVED_SURFACE_SHAPE_DRIFT")

    if [item.get("transport_status") for item in observations] != [
        "HTTP_403_FORBIDDEN",
        "HTTP_200_OK",
        "HTTP_403_FORBIDDEN",
    ]:
        raise LiveProbeReviewStop("STOP_TASK_029_TRANSPORT_STATUS_DRIFT")

    if any(item.get("machine_readable_candidate_observed") is not False for item in observations):
        raise LiveProbeReviewStop("STOP_TASK_029_MACHINE_CANDIDATE_CLAIM_DRIFT")

    expected_result = "STOP_INITIAL_SURFACES_INCOMPLETE_ACCESS_BLOCKED"
    if evidence.get("result") != expected_result:
        raise LiveProbeReviewStop("STOP_TASK_029_FAIL_CLOSED_RESULT_REQUIRED")

    claims = evidence.get("claims", {})
    false_claims = (
        "all_initial_surfaces_observed",
        "machine_readable_equivalent_candidate_observed",
        "machine_readable_equivalent_proven",
        "textual_equivalent_proven",
        "absence_of_equivalent_source_proven",
        "loa_financial_identity_proven",
    )
    if any(claims.get(key) is not False for key in false_claims):
        raise LiveProbeReviewStop("STOP_TASK_029_UNSUPPORTED_CLAIM")

    effects = evidence.get("effects", {})
    if effects.get("source_network_requests") != 3:
        raise LiveProbeReviewStop("STOP_TASK_029_NETWORK_EFFECT_COUNT_DRIFT")
    zero_effects = (
        "candidate_followups",
        "document_downloads",
        "drive_reads",
        "drive_writes",
        "bronze_writes",
        "silver_writes",
        "gold_writes",
        "serving_writes",
        "site_writes",
        "publication",
        "ocr_execution",
    )
    if any(effects.get(key) != 0 for key in zero_effects):
        raise LiveProbeReviewStop("STOP_TASK_029_MUTATION_EFFECT_FORBIDDEN")
    if effects.get("schedule") is not False or effects.get("recurrence") is not False:
        raise LiveProbeReviewStop("STOP_TASK_029_SCHEDULE_OR_RECURRENCE_FORBIDDEN")

    release = evidence.get("release_boundary", {})
    if release.get("0.7.0") != "ACTIVE" or release.get("0.8.0") != "CANDIDATE" or release.get("unchanged") is not True:
        raise LiveProbeReviewStop("STOP_TASK_029_RELEASE_BOUNDARY_DRIFT")

    return {
        "status": "PASS_TASK_029_LIVE_PROBE_REVIEW_FAIL_CLOSED",
        "request_count": request_count,
        "accessible_initial_surfaces": len(accessible),
        "blocked_initial_surfaces": len(blocked),
        "machine_candidates": 0,
        "equivalence_proven": False,
        "absence_proven": False,
        "next_gate": evidence.get("next_gate"),
    }

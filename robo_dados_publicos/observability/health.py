from __future__ import annotations

from datetime import datetime, timezone

from .cards import RunCard, SourceCard, _iso8601


ALLOWED_RUN_STATUSES = {
    "PASS",
    "SUCCESS",
    "DOWNLOADED_NEW",
    "DOWNLOADED_IDENTICAL",
    "NO_CHANGE",
    "EXPECTED_ABSENCE",
}


def evaluate_source_health(
    source: SourceCard,
    run: RunCard,
    *,
    now: datetime | None = None,
) -> dict:
    """Evaluate source health without collapsing dimensions into a hidden score."""
    if source.source_id != run.source_id:
        raise ValueError("source_id mismatch between source and run cards")

    reference_now = now or datetime.now(timezone.utc)
    if reference_now.tzinfo is None:
        raise ValueError("now must include timezone")
    reference_now = reference_now.astimezone(timezone.utc)

    if source.expected_update_interval_hours is None:
        freshness_status = "NOT_CONFIGURED"
        age_hours = None
    else:
        age_hours = max(0.0, (reference_now - _iso8601(run.finished_at)).total_seconds() / 3600)
        freshness_status = (
            "PASS" if age_hours <= source.expected_update_interval_hours else "STALE"
        )

    if run.expected_absence:
        completeness_status = "NOT_APPLICABLE"
        completeness_ratio = None
    elif run.records_in is None:
        completeness_status = "UNKNOWN"
        completeness_ratio = None
    elif run.records_in == 0:
        completeness_status = "EMPTY"
        completeness_ratio = None
    elif run.records_out is None:
        completeness_status = "UNKNOWN"
        completeness_ratio = None
    else:
        completeness_ratio = run.records_out / run.records_in
        completeness_status = "PASS" if completeness_ratio >= 1.0 else "INCOMPLETE"

    consistency_status = (
        "FAIL"
        if any(warning in {"SCHEMA_CHANGE", "VALIDATION_ERROR"} for warning in run.warnings)
        else "PASS"
    )
    collection_status = "PASS" if run.status in ALLOWED_RUN_STATUSES else "FAIL"

    dimensions = {
        "freshness": {"status": freshness_status, "age_hours": age_hours},
        "completeness": {
            "status": completeness_status,
            "ratio": completeness_ratio,
            "records_in": run.records_in,
            "records_out": run.records_out,
        },
        "consistency": {"status": consistency_status, "warnings": list(run.warnings)},
        "collection": {
            "status": collection_status,
            "run_status": run.status,
            "expected_absence": run.expected_absence,
            "failure_reason": run.failure_reason,
        },
        "latency": {"status": "OBSERVED", "seconds": run.latency_seconds},
    }

    statuses = {dimension["status"] for dimension in dimensions.values()}
    if statuses & {"FAIL", "STALE", "INCOMPLETE", "EMPTY"}:
        overall_status = "FAIL"
    elif "UNKNOWN" in statuses:
        overall_status = "UNKNOWN"
    else:
        overall_status = "PASS"

    return {
        "source_id": source.source_id,
        "run_id": run.run_id,
        "overall_status": overall_status,
        "dimensions": dimensions,
    }

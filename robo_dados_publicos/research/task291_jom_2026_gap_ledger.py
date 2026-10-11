"""TASK291: deterministic 2026 custody-vs-numbering gap ledger. No network, no writes."""
from __future__ import annotations

from scripts.download_jom_2026_archive_batch import batch_map, ALREADY_PRESERVED
from robo_dados_publicos.research.task219a_jom_general_event_redigest import load_pinned_targets

# Twelve OTHER SME originals from August 2026, independent of pinned 87;
# confirmed by the SME Drive folder inventory on 2026-10-10.
SME_OTHER_ORIGINALS = tuple(range(7304, 7316))
NUMERIC_MIN = 7151
NUMERIC_MAX = 7328


def derive() -> dict:
    fixture = load_pinned_targets()  # validated fixture; 87 pinned URLs
    pinned = {int(x["edition"]) for x in fixture}
    if len(fixture) != 87 or len(pinned) != 87:
        raise ValueError("STOP_291_FIXTURE_87_DRIFT")
    if not ALREADY_PRESERVED.issubset(pinned):
        raise ValueError("STOP_291_PRIOR_PRESERVED_DRIFT")
    batches = batch_map()
    batch_ids = [int(row["edition"]) for rows in batches.values() for row in rows]
    if len(batch_ids) != 81 or len(set(batch_ids)) != 81:
        raise ValueError("STOP_291_81_BATCH_DRIFT")
    if set(batch_ids) != pinned - ALREADY_PRESERVED:
        raise ValueError("STOP_291_BATCH_COVERAGE_DRIFT")
    other = set(SME_OTHER_ORIGINALS)
    if other & pinned:
        raise ValueError("STOP_291_OTHER_OVERLAP")
    preserved = pinned | other
    if len(preserved) != 99 or min(preserved) != 7161 or max(preserved) != 7320:
        raise ValueError("STOP_291_SME_99_DRIFT")
    observed_interval = set(range(NUMERIC_MIN, NUMERIC_MAX + 1))
    missing = sorted(observed_interval - preserved)
    if len(missing) != 79:
        raise ValueError("STOP_291_GAP_COUNT_DRIFT")
    # Numeric candidates: do NOT claim publication until index and cover prove it.
    return {
        "schema": "TASK291_JOM_2026_NUMERIC_GAP_LEDGER_V1",
        "status": "NUMERIC_GAPS_ONLY_NOT_OFFICIAL_COMPLETE",
        "year": 2026,
        "custodied_identities": 99,
        "pinned_fixture_count": 87,
        "other_preexisting_sme_ids": list(SME_OTHER_ORIGINALS),
        "reference_range": [NUMERIC_MIN, NUMERIC_MAX],
        "candidate_gap_count": len(missing),
        "candidate_gaps": missing,
        "ambiguous_index_edition_numbers": [7237, 7238, 7327, 7328],
        "anomaly_note": "Portal index displays 7237/7238 in 2026-09-19/22 after 7326; don't map to 7327/7328 without PDF cover.",
        "period_after_2026_09_22": "UNINVENTORIED",
        "original_url_for_missing": None,
        "acquisition_authorized": False,
        "source": "87 official pinned URLs + twelve August originals in SME; no inferred PDF URLs",
    }

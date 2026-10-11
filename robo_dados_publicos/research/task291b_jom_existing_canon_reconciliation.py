"""TASK291B: reconcile historical canonical JOM discoveries into one offline ledger.

All evidence is read from versioned repository fixtures; there is no source
network, GitHub API, Drive access or original PDF download. The output describes
evidence already in the repo, not a 2026 exhaustive official inventory.
"""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
PINNED = ROOT / "docs/evidence/fixtures/task219/TASK_219A_CANONICAL_87_DOCUMENT_TARGETS.csv"
TASK018 = ROOT / "docs/evidence/TASK_018_JORNAL_COMPLETED_CANONICAL_CHECKPOINT_0.8.0.json"
TASK238 = ROOT / "config/lt_formation_timing_jom_direct_discovery.v3.json"
TASK238_PRIMARY = ROOT / "docs/evidence/TASK_238_JOM_PRIMARY_CONTENT_CLOSURE_0.8.0.json"
TASK248 = ROOT / "docs/evidence/TASK_248_JOM_LIVE_DELTA_CANONICAL_0.8.0.json"
LOW, HIGH = 7151, 7328
HEADER = [
    "ano", "edicao", "data_publicacao", "source_id", "url_pdf_oficial",
    "comprovacao_identidade", "fonte_repositorio", "situacao_drive_sme",
    "sha256_primario_historico", "paginas_primario_historico",
]


class ReconciliationStop(ValueError):
    pass


def demand(ok: bool, code: str) -> None:
    if not ok:
        raise ReconciliationStop(code)


def from_json(path: Path) -> dict:
    return json.loads(path.read_text("utf-8"))


def checked_entry(edition: int, date: str, source_id: str, url: str,
                  proof: str, source: str, drive: str,
                  sha: str = "", pages: str = "") -> dict:
    demand(7151 <= edition <= 7328, "STOP_291B_RANGE")
    demand(date.startswith("2026-") and len(date) == 10, "STOP_291B_DATE")
    demand(not url or (urlparse(url).scheme == "https"
                      and urlparse(url).hostname == "ecrie.com.br"
                      and urlparse(url).path.endswith(".pdf")),
           "STOP_291B_URL_NOT_OFFICIAL")
    demand(not url or bool(source_id) or proof == "TASK238_COMPLETE_JANUARY_IDENTITY_PRIMARY_URL_AND_SHA", "STOP_291B_SOURCE_ID_REQUIRED")
    demand(not sha or (len(sha) == 64 and all(c in "0123456789abcdef" for c in sha)),
           "STOP_291B_SHA_FORMAT")
    demand(not pages or (pages.isdigit() and int(pages) > 0), "STOP_291B_PAGE_FORMAT")
    return dict(zip(HEADER, [
        "2026", str(edition), date, source_id, url, proof, source,
        drive, sha, pages,
    ]))


def reconcile() -> tuple[list[dict], dict]:
    pinned = list(csv.DictReader(PINNED.open(encoding="utf-8")))
    demand(len(pinned) == 87, "STOP_291B_PINNED_COUNT")
    demand(len({int(x["edition"]) for x in pinned}) == 87, "STOP_291B_PINNED_DUP")
    old = from_json(TASK018)
    demand(old["checkpoint_status"] == "COMPLETE" and old["item_count"] == 12,
           "STOP_291B_TASK018")
    demand([x["edition"] for x in old["items"]] == list(range(7304, 7316)),
           "STOP_291B_TASK018_EDITION_DRIFT")
    raw = {}
    for item in pinned:
        edition = int(item["edition"])
        raw[edition] = checked_entry(
            edition, item["publication_date"], item["source_id"],
            item["document_url"], "TASK219A_PINNED_87",
            "docs/evidence/fixtures/task219/TASK_219A_CANONICAL_87_DOCUMENT_TARGETS.csv",
            "CUSTODIADO_SME_TASK219A_87",
        )
    for item in old["items"]:
        ed = item["edition"]
        demand(ed not in raw, "STOP_291B_018_OVERLAP")
        raw[ed] = checked_entry(
            ed, item["publication_date"], item["source_id"], item["document_url"],
            "TASK018_CANONICAL_12",
            "docs/evidence/TASK_018_JORNAL_COMPLETED_CANONICAL_CHECKPOINT_0.8.0.json",
            "CUSTODIADO_SME_PREEXISTENTE",
        )
    demand(len(raw) == 99, "STOP_291B_CUSTODY_99")
    custody = set(raw)

    jan = from_json(TASK238)["bounded_identity_inventory"]["manifest"]
    jan2026 = [x for x in jan if x["publication_date"].startswith("2026-01-")]
    demand(len(jan2026) == 22, "STOP_291B_JAN_22")
    demand([int(x["edition"]) for x in jan2026] == list(range(7151, 7173)),
           "STOP_291B_JAN_CONTIGUITY")
    missing_jan = [x for x in jan2026 if x["edition"] not in custody]
    demand([x["edition"] for x in missing_jan] == list(range(7151, 7161)),
           "STOP_291B_JAN_MISSING_TEN")
    primary = from_json(TASK238_PRIMARY)
    inspected = {int(x["edition"]): x for x in primary["primary_inspections"]}
    first = inspected[7151]
    demand(first["publication_date"] == "2026-01-06"
           and first["status"] == "CLEARED_BY_COMPLETE_PRIMARY_PDF_INSPECTION",
           "STOP_291B_7151_PRIMARY")
    for x in missing_jan:
        ed = int(x["edition"])
        p = inspected.get(ed)
        raw[ed] = checked_entry(
            ed, x["publication_date"], "",
            p["document_url"] if p else "",
            "TASK238_COMPLETE_JANUARY_IDENTITY_" +
                ("PRIMARY_URL_AND_SHA" if p else "DATE_ONLY"),
            "config/lt_formation_timing_jom_direct_discovery.v3.json" +
                (" + docs/evidence/TASK_238_JOM_PRIMARY_CONTENT_CLOSURE_0.8.0.json"
                 if p else ""),
            "NAO_CUSTODIADO_SME",
            p["sha256"] if p else "",
            str(p["pdf_page_count"]) if p else "",
        )

    delta = from_json(TASK248)
    demand(delta["status"] == "PASS_TASK247_LIVE_DELTA_CANONIZED"
           and delta["live_result"]["delta_count"] == 4, "STOP_291B_248_STATUS")
    new_rows = delta["live_result"]["delta_editions"]
    demand([int(x["edition"]) for x in new_rows] == [7321, 7322, 7323, 7324],
           "STOP_291B_248_EDITION_DRIFT")
    for x in new_rows:
        ed = x["edition"]
        demand(ed not in raw, "STOP_291B_248_OVERLAP")
        raw[ed] = checked_entry(
            ed, x["publication_date"], x["source_id"], x["document_url"],
            "TASK248_CANONICAL_LIVE_DELTA_WITH_OFFICIAL_URL",
            "docs/evidence/TASK_248_JOM_LIVE_DELTA_CANONICAL_0.8.0.json",
            "NAO_CUSTODIADO_SME",
        )
    rows = [raw[i] for i in sorted(raw)]
    demand(len(rows) == 113 and len(set(raw)) == 113, "STOP_291B_113")
    numeric = set(range(LOW, HIGH + 1))
    missing = numeric - custody
    confirmed_not_custodied = set(raw) - custody
    still_unverified = missing - confirmed_not_custodied
    demand(len(missing) == 79 and len(confirmed_not_custodied) == 14
           and len(still_unverified) == 65, "STOP_291B_79_14_65")
    official_url_waiting = [x for x in rows if x["situacao_drive_sme"] == "NAO_CUSTODIADO_SME"
                            and x["url_pdf_oficial"]]
    demand(len(official_url_waiting) == 5, "STOP_291B_5_URLS")
    overview = {
        "schema": "TASK291B_JOM_2026_HISTORICAL_RECONCILIATION_V1",
        "nature": "OFFLINE_CANONICAL_RECONCILIATION_NOT_COMPLETE_2026_INVENTORY",
        "custodied_identities": 99,
        "historically_proven_identities_not_custodied": 14,
        "known_identities": 113,
        "numeric_candidate_gap_count_before_reconciliation": 79,
        "numeric_gaps_still_without_identity_proof": 65,
        "proven_unarchived_with_direct_pdf_url": 5,
        "proven_unarchived_date_only": 9,
        "january_identified_count": 22,
        "january_custodied_count": 12,
        "january_unarchived_count": 10,
        "post_2026_09_12_uninventoried": True,
        "year_end_2026_incomplete_as_of": "2026-10-11",
        "source_pdf_get_count": 0, "index_get_count": 0, "drive_write_count": 0,
        "remaining_numeric_candidates": sorted(still_unverified),
        "known_unarchived_editions": sorted(confirmed_not_custodied),
        "official_url_known_unarchived_editions": [
            int(x["edicao"]) for x in official_url_waiting
        ],
        "interpretation": (
            "A 99-document historical PASS was a bounded snapshot, not proof "
            "that the current monthly or full-year index was exhaustive. "
            "Do not infer dates, URLs, absence or custody from sequence alone."
        ),
    }
    return rows, overview


def render_csv(rows: list[dict]) -> str:
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=HEADER, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def main() -> None:
    rows, report = reconcile()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    # This is read-only. CSV written by separately reviewed GitHub PR, never by runtime.


if __name__ == "__main__":
    main()

"""TASK291 manual one-shot JOM 2026 INDEX pilot.

Read robots.txt once plus exactly two canonical monthly index URLs (Jan, Sep).
No PDF access, no pagination GET, no redirects/retry, no Drive, no publication.
The evidence manifest is output even when a live request fails/blocks.
"""
from __future__ import annotations

import argparse
from datetime import date
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib import robotparser

from robo_dados_publicos.journal.official import JornalOficialLimeira
from robo_dados_publicos.research.task291_jom_2026_gap_ledger import derive

BASE = "https://www.limeira.sp.gov.br"
MONTHS = (1, 9)
ROBOTS_URL = BASE + "/robots.txt"
INDEX_URLS = tuple(f"{BASE}/jornaloficial/?ano=2026&mes={m}" for m in MONTHS)
USER_AGENT = "LOA-LIMEIRA-2027-JOM-Index-Audit/1.0"
ROBOTS_CAP = 256 * 1024
INDEX_CAP = 1250 * 1024


class PilotStop(RuntimeError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise PilotStop("STOP_291_REDIRECT")


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.fragments = []

    def handle_data(self, data):
        self.fragments.append(data)


def validate_manual_context(env: dict) -> None:
    if not (
        env.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
        and env.get("GITHUB_REF") == "refs/heads/main"
        and env.get("GITHUB_RUN_ATTEMPT") == "1"
        and env.get("JOM291_OWNER_CONFIRM") == "true"
        and re.fullmatch(r"[0-9a-f]{40}", env.get("GITHUB_SHA", ""))
    ):
        raise PilotStop("STOP_291_MANUAL_MAIN_OWNER_CONTEXT")


def read_bounded(opener, url: str, limit: int) -> tuple[str, bytes]:
    if url not in (ROBOTS_URL, *INDEX_URLS):
        raise PilotStop("STOP_291_URL_NOT_PINNED")
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,text/plain"}, method="GET")
    try:
        with opener.open(request, timeout=20) as response:
            code = getattr(response, "status", response.getcode())
            if code != 200 or response.geturl() != url:
                raise PilotStop("STOP_291_STATUS_OR_REDIRECT")
            ctype = (response.headers.get("Content-Type") or "").split(";", 1)[0].lower().strip()
            allowed = ("text/plain", "text/html", "application/xhtml+xml")
            if ctype not in allowed:
                raise PilotStop("STOP_291_UNEXPECTED_MIME")
            length = response.headers.get("Content-Length")
            if length is not None and int(length) > limit:
                raise PilotStop("STOP_291_DECLARED_TOO_LARGE")
            body = response.read(limit + 1)
    except HTTPError as exc:
        if url == ROBOTS_URL and exc.code == 404:
            return "ROBOTS_404", b""
        raise PilotStop(f"STOP_291_HTTP_{exc.code}") from exc
    except (URLError, OSError) as exc:
        raise PilotStop("STOP_291_TRANSPORT") from exc
    if len(body) > limit:
        raise PilotStop("STOP_291_RESPONSE_TOO_LARGE")
    return ctype, body


def text_total(html: str) -> int | None:
    collector = VisibleText()
    collector.feed(html)
    text = " ".join(collector.fragments)
    matches = set(int(x) for x in re.findall(
        r"total\s+de\s+itens\s+encontrados\s*:\s*(\d+)", text, re.I
    ))
    if len(matches) > 1:
        raise PilotStop("STOP_291_DIFFERENT_PAGE_TOTALS")
    return next(iter(matches)) if matches else None


def analyze_index(html: str, url: str, month: int) -> dict:
    if url != INDEX_URLS[MONTHS.index(month)]:
        raise PilotStop("STOP_291_MONTH_URL_DRIFT")
    if len(html.encode("utf-8")) > INDEX_CAP:
        raise PilotStop("STOP_291_INDEX_TOO_LARGE")
    declared_total = text_total(html)
    found, parser = JornalOficialLimeira._parse_html_details(html, url)
    candidates = [i for i in found if i.publication_date and i.publication_date.startswith(f"2026-{month:02d}-")]
    if len(candidates) > 30:
        raise PilotStop("STOP_291_PAGE_EDITION_BOUND")
    rows = []
    for i in candidates:
        u = urlparse(i.document_url)
        if u.scheme != "https" or u.username or u.password or u.fragment:
            raise PilotStop("STOP_291_DOCUMENT_URL_UNSAFE")
        if u.hostname not in ("ecrie.com.br", "www.limeira.sp.gov.br", "limeira.sp.gov.br"):
            raise PilotStop("STOP_291_DOCUMENT_HOST_UNRECOGNIZED")
        rows.append({
            "edition": i.edition,
            "publication_date": i.publication_date,
            "declared_url": i.document_url,
            "source_page": url,
            "url_is_pdf": i.looks_like_pdf,
            "status": "INDEX_CANDIDATE_NOT_CUSTODIED_BY_THIS_RUN",
        })
    if declared_total is None:
        status = "UNRESOLVED_TOTAL_NOT_READABLE"
    elif declared_total < len(rows):
        status = "STOP_TOTAL_LESS_THAN_MONTH_MATCHES"
    elif declared_total > len(rows):
        status = "PARTIAL_INDEX_PAGINATION_REQUIRED"
    else:
        status = "INDEX_PAGE_TOTAL_MATCHED_NOT_YET_PDF_VALIDATED"
    # Do not infer missing editions from numbers; preserve actual hrefs only.
    page_links = JornalOficialLimeira._month_pagination_candidates(parser.links, url, 2026, month)
    return {
        "month": month, "url": url,
        "authoritative_total": declared_total, "first_page_month_count": len(rows),
        "status": status, "declared_pagination_urls": page_links[:12],
        "declared_pagination_count": len(page_links),
        "items": rows,
    }


def pilot(opener) -> dict:
    ledger = derive()
    manifest = {
        "schema": "TASK291_JOM_INDEX_PILOT_V1",
        "status": "STARTED",
        "source_year": 2026,
        "robots_url": ROBOTS_URL,
        "planned_index_urls": list(INDEX_URLS),
        "network_get_attempts": 0,
        "pdf_get_attempts": 0,
        "drive_write_count": 0,
        "retry_count": 0,
        "index_results": [],
        "numeric_gap_ledger": ledger,
    }
    try:
        manifest["network_get_attempts"] += 1
        ctype, robots = read_bounded(opener, ROBOTS_URL, ROBOTS_CAP)
        if ctype == "ROBOTS_404":
            manifest["robots_status"] = "ABSENT_404"
        else:
            rp = robotparser.RobotFileParser()
            rp.parse(robots.decode("utf-8", "replace").splitlines())
            manifest["robots_status"] = "PARSED"
            if any(not rp.can_fetch(USER_AGENT, url) for url in INDEX_URLS):
                raise PilotStop("STOP_291_ROBOTS_DISALLOW")
        for month, url in zip(MONTHS, INDEX_URLS):
            manifest["network_get_attempts"] += 1
            ctype, body = read_bounded(opener, url, INDEX_CAP)
            if ctype not in ("text/html", "application/xhtml+xml"):
                raise PilotStop("STOP_291_INDEX_NOT_HTML")
            parsed = analyze_index(body.decode("utf-8", "replace"), url, month)
            manifest["index_results"].append(parsed)
        manifest["status"] = "PASS_291_INDEX_PILOT_TWO_MONTHS"
    except (PilotStop, ValueError) as exc:
        manifest["status"] = "STOP_291_INDEX_PILOT"
        manifest["failure_reason"] = str(exc)
    if manifest["network_get_attempts"] > 3:
        raise AssertionError("STOP_291_NETWORK_CAP")
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    validate_manual_context(os.environ)
    if args.out.exists():
        raise PilotStop("STOP_291_OUTPUT_EXISTS")
    opener = build_opener(NoRedirect())
    result = pilot(opener)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as output:
        json.dump(result, output, sort_keys=True, ensure_ascii=False, indent=2)
        output.write("\n")
    print(json.dumps({
        "status": result["status"],
        "network_get_attempts": result["network_get_attempts"],
        "pdf_get_attempts": 0,
        "months_returned": len(result["index_results"]),
        "stop_reason": result.get("failure_reason"),
    }, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())

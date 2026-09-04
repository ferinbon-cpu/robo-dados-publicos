from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import unicodedata
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import (
    HTTPRedirectHandler,
    Request,
    build_opener,
)


class HistoricalPpaLiveStop(RuntimeError):
    """Fail-closed TASK 104 live acquisition error."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise HistoricalPpaLiveStop(code)


def normalize_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    without_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join(without_marks.upper().split())


class _LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._href: str | None = None
        self._parts: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        self._href = dict(attrs).get("href")
        self._parts = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or self._href is None:
            return
        text = " ".join("".join(self._parts).split())
        self.links.append((self._href, text))
        self._href = None
        self._parts = []


def find_official_ppa_pdf_link(
    html: str,
    *,
    base_url: str,
    law_number: str,
    period: str,
) -> dict[str, str] | None:
    collector = _LinkCollector()
    collector.feed(html)
    law_token = normalize_text(law_number)
    period_tokens = [normalize_text(period), normalize_text(period.replace("-", "/"))]
    matches: list[dict[str, str]] = []
    for href, text in collector.links:
        normalized = normalize_text(text)
        if law_token not in normalized:
            continue
        if not any(token in normalized for token in period_tokens):
            continue
        matches.append(
            {
                "href": urljoin(base_url, href),
                "anchor_text": text,
            }
        )
    if len(matches) > 1:
        exact_pdf = [item for item in matches if urlparse(item["href"]).path.lower().endswith(".pdf")]
        if len(exact_pdf) == 1:
            return exact_pdf[0]
        raise HistoricalPpaLiveStop("TASK104_AMBIGUOUS_PPA_LINK")
    return matches[0] if matches else None


@dataclass
class _RequestBudget:
    allowed_hosts: frozenset[str]
    total_max: int
    per_period_max: int
    request_log: list[dict[str, Any]] = field(default_factory=list)
    per_period_counts: dict[str, int] = field(default_factory=dict)

    def authorize(self, period: str, url: str, *, kind: str) -> None:
        parsed = urlparse(url)
        _require(parsed.scheme == "https", "TASK104_URL_SCHEME")
        host = (parsed.hostname or "").lower()
        _require(host in self.allowed_hosts, "TASK104_HOST_OUTSIDE_ALLOWLIST")
        total_next = len(self.request_log) + 1
        period_next = self.per_period_counts.get(period, 0) + 1
        _require(total_next <= self.total_max, "TASK104_TOTAL_REQUEST_BUDGET")
        _require(period_next <= self.per_period_max, "TASK104_PERIOD_REQUEST_BUDGET")
        self.per_period_counts[period] = period_next
        self.request_log.append(
            {
                "ordinal": total_next,
                "period": period,
                "period_ordinal": period_next,
                "method": "GET",
                "host": host,
                "path": parsed.path,
                "kind": kind,
            }
        )


class _BoundedRedirectHandler(HTTPRedirectHandler):
    def __init__(self, authorize_redirect: Callable[[str], None]) -> None:
        super().__init__()
        self._authorize_redirect = authorize_redirect

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self._authorize_redirect(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class BoundedOfficialHttpClient:
    def __init__(
        self,
        *,
        allowed_hosts: set[str] | frozenset[str],
        total_max: int,
        per_period_max: int,
        timeout_seconds: int = 20,
    ) -> None:
        self.budget = _RequestBudget(
            allowed_hosts=frozenset(host.lower() for host in allowed_hosts),
            total_max=total_max,
            per_period_max=per_period_max,
        )
        self.timeout_seconds = timeout_seconds
        self._active_period: str | None = None
        self._opener = build_opener(
            _BoundedRedirectHandler(self._authorize_redirect)
        )

    @property
    def request_log(self) -> list[dict[str, Any]]:
        return list(self.budget.request_log)

    def _authorize_redirect(self, url: str) -> None:
        _require(self._active_period is not None, "TASK104_REDIRECT_WITHOUT_PERIOD")
        self.budget.authorize(self._active_period, url, kind="REDIRECT")

    def get(self, period: str, url: str) -> tuple[bytes, str, str | None]:
        self.budget.authorize(period, url, kind="INITIAL")
        self._active_period = period
        request = Request(
            url,
            method="GET",
            headers={
                "User-Agent": "ROBO_DADOS_PUBLICOS/0.8.0 TASK104 bounded-readonly",
                "Accept": "application/pdf,text/html;q=0.9,*/*;q=0.1",
            },
        )
        try:
            with self._opener.open(request, timeout=self.timeout_seconds) as response:
                final_url = response.geturl()
                parsed_final = urlparse(final_url)
                _require(
                    (parsed_final.hostname or "").lower() in self.budget.allowed_hosts,
                    "TASK104_FINAL_HOST_OUTSIDE_ALLOWLIST",
                )
                payload = response.read()
                content_type = response.headers.get("Content-Type")
                return payload, final_url, content_type
        except HTTPError as exc:
            raise HistoricalPpaLiveStop(f"TASK104_HTTP_{exc.code}") from exc
        except URLError as exc:
            raise HistoricalPpaLiveStop("TASK104_URL_ERROR") from exc
        finally:
            self._active_period = None


def _extract_pdf_text(pdf_path: Path) -> str:
    try:
        completed = subprocess.run(
            ["pdftotext", "-layout", "-enc", "UTF-8", str(pdf_path), "-"],
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise HistoricalPpaLiveStop("TASK104_PDFTOTEXT_UNAVAILABLE") from exc
    _require(completed.returncode == 0, "TASK104_PDFTOTEXT_FAILED")
    _require(bool(completed.stdout.strip()), "TASK104_PDF_TEXT_EMPTY")
    return completed.stdout


def analyze_pdf_text(
    pdf_text: str,
    *,
    period: str,
    law_number: str,
    expected_signal: str,
    source_url: str,
    final_url: str,
    source_sha256: str,
    source_bytes: int,
    discovery_anchor_text: str | None,
) -> dict[str, Any]:
    pages = pdf_text.split("\f")
    normalized_document = normalize_text(pdf_text)
    law_compact = law_number.replace(".", "")
    identity_found = (
        normalize_text(law_number) in normalized_document
        or normalize_text(law_compact) in normalized_document
    )

    signal_norm = normalize_text(expected_signal)
    matched_page_number: int | None = None
    matched_page_text: str | None = None
    matched_excerpt: str | None = None

    for number, page in enumerate(pages, start=1):
        if signal_norm not in normalize_text(page):
            continue
        matched_page_number = number
        matched_page_text = page
        lines = page.splitlines()
        matching_index = next(
            (
                index
                for index, line in enumerate(lines)
                if signal_norm in normalize_text(line)
            ),
            0,
        )
        start = max(0, matching_index - 2)
        end = min(len(lines), matching_index + 3)
        matched_excerpt = "\n".join(lines[start:end]).strip()[:1200]
        break

    signal_found = matched_page_number is not None
    if identity_found and signal_found:
        status = "PRIMARY_MATCH"
    elif signal_found:
        status = "CANDIDATE_MATCH"
    else:
        status = "STOP_SIGNAL_NOT_FOUND"

    locator = None
    if matched_page_number is not None and matched_page_text is not None:
        locator = {
            "page": matched_page_number,
            "coordinate_system": "SOURCE_PDF_PAGE_1_BASED",
            "page_text_sha256": sha256(
                matched_page_text.encode("utf-8")
            ).hexdigest(),
            "match_signal": expected_signal,
        }

    return {
        "period": period,
        "status": status,
        "source_url": source_url,
        "final_url": final_url,
        "source_bytes": source_bytes,
        "source_sha256": source_sha256,
        "law_number": law_number,
        "primary_document_identity_found_in_pdf_text": identity_found,
        "discovery_anchor_text": discovery_anchor_text,
        "expected_signal": expected_signal,
        "planning_signal_found": signal_found,
        "locator": locator,
        "direct_evidence_excerpt": matched_excerpt,
        "financial_identity_created": False,
        "implementation_proven": False,
        "causal_effect_created": False,
    }


def _period_spec(contract: dict[str, Any], period: str) -> dict[str, Any]:
    matches = [item for item in contract["periods"] if item["period"] == period]
    _require(len(matches) == 1, "TASK104_PERIOD_SPEC")
    return matches[0]


def acquire_historical_ppa_evidence(
    *,
    contract: dict[str, Any],
    runtime_dir: Path,
    client: BoundedOfficialHttpClient,
    extract_pdf_text: Callable[[Path], str] = _extract_pdf_text,
) -> dict[str, Any]:
    runtime_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []

    for period in ("2018-2021", "2022-2025"):
        spec = _period_spec(contract, period)
        law_number = "5.947" if period == "2018-2021" else "6.659"
        expected_signal = str(spec["expected_signal"])
        discovery_anchor_text: str | None = None

        try:
            if period == "2018-2021":
                index_url = next(
                    item["url"]
                    for item in spec["official_anchors"]
                    if item["role"] == "PREFEITURA_BUDGET_INDEX"
                )
                html_bytes, index_final_url, _ = client.get(period, index_url)
                html = html_bytes.decode("utf-8", errors="replace")
                link = find_official_ppa_pdf_link(
                    html,
                    base_url=index_final_url,
                    law_number=law_number,
                    period=period,
                )
                if link is None:
                    results.append(
                        {
                            "period": period,
                            "status": "NO_MATCH",
                            "reason": "PRIMARY_PPA_LINK_NOT_FOUND_IN_BOUNDED_OFFICIAL_INDEX",
                            "financial_identity_created": False,
                            "implementation_proven": False,
                            "causal_effect_created": False,
                        }
                    )
                    continue
                source_url = link["href"]
                discovery_anchor_text = link["anchor_text"]
            else:
                source_url = str(spec["primary_pdf_candidate_url"])

            pdf_bytes, final_url, content_type = client.get(period, source_url)
            _require(pdf_bytes.startswith(b"%PDF"), "TASK104_NOT_PDF_BYTES")
            source_hash = sha256(pdf_bytes).hexdigest()
            pdf_path = runtime_dir / f"ppa_{period.replace('-', '_')}.pdf"
            pdf_path.write_bytes(pdf_bytes)
            pdf_text = extract_pdf_text(pdf_path)
            result = analyze_pdf_text(
                pdf_text,
                period=period,
                law_number=law_number,
                expected_signal=expected_signal,
                source_url=source_url,
                final_url=final_url,
                source_sha256=source_hash,
                source_bytes=len(pdf_bytes),
                discovery_anchor_text=discovery_anchor_text,
            )
            result["content_type"] = content_type
            results.append(result)
        except Exception as exc:
            results.append(
                {
                    "period": period,
                    "status": "STOP_REMOTE_ACQUISITION",
                    "error_type": type(exc).__name__,
                    "error": str(exc)[:500],
                    "financial_identity_created": False,
                    "implementation_proven": False,
                    "causal_effect_created": False,
                }
            )

    primary_count = sum(item["status"] == "PRIMARY_MATCH" for item in results)
    if primary_count == 2:
        overall = "PASS_TASK104_TWO_PRIMARY_PPA_MATCHES"
    elif primary_count == 1:
        overall = "PARTIAL_TASK104_ONE_PRIMARY_PPA_MATCH"
    else:
        overall = "STOP_TASK104_NO_COMPLETE_PRIMARY_PAIR"

    return {
        "schema": "TASK_104_HISTORICAL_PPA_LIVE_RESULT_V1",
        "task": "TASK_104_SINGLE_USE_HISTORICAL_PPA_PRIMARY_EVIDENCE",
        "overall_status": overall,
        "period_results": results,
        "primary_match_count": primary_count,
        "request_count": len(client.request_log),
        "requests": client.request_log,
        "hard_boundaries": {
            "drive_reads": 0,
            "drive_writes": 0,
            "bronze_writes": 0,
            "silver_writes": 0,
            "gold_writes": 0,
            "state_registry_writes": 0,
            "queue_writes": 0,
            "serving_writes": 0,
            "publications": 0,
            "financial_identity_assertions": 0,
            "causal_effect_assertions": 0,
        },
        "retry_performed": False,
        "recurrence": False,
        "schedule": False,
        "future_execution_authorized": False,
    }


def load_contract(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    _require(
        data.get("schema") == "EITI_HISTORICAL_PPA_PRIMARY_ACQUISITION_V1",
        "TASK104_CONTRACT_SCHEMA",
    )
    return data

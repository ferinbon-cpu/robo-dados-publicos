from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import unicodedata
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class Task112Stop(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task112Stop(code)


def normalize_ocr(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^A-Za-z0-9]+", " ", text.upper())
    return " ".join(text.split())


def parse_tsv(tsv: str) -> tuple[str, list[float]]:
    lines = tsv.splitlines()
    _require(bool(lines), "TASK112_EMPTY_TSV")
    words: list[str] = []
    confidences: list[float] = []
    for line in lines[1:]:
        cols = line.split("\t")
        if len(cols) < 12:
            continue
        word = cols[11].strip()
        if not word:
            continue
        words.append(word)
        try:
            confidence = float(cols[10])
        except ValueError:
            continue
        if confidence >= 0:
            confidences.append(confidence)
    return " ".join(words), confidences


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass
class ExactSourceClient:
    initial_url: str
    allowed_host: str
    max_requests: int = 2

    def __post_init__(self) -> None:
        self.request_log: list[dict[str, Any]] = []
        self._opener = build_opener(_NoRedirect)

    def _validate(self, url: str) -> None:
        parts = urlsplit(url)
        _require(parts.scheme == "https", "TASK112_HTTPS_REQUIRED")
        _require((parts.hostname or "").lower() == self.allowed_host, "TASK112_HOST")
        _require(parts.username is None and parts.password is None, "TASK112_URL_CREDENTIALS")

    def get(self) -> tuple[bytes, str, str]:
        url = self.initial_url
        redirects = 0
        while True:
            self._validate(url)
            _require(len(self.request_log) < self.max_requests, "TASK112_REQUEST_BUDGET")
            ordinal = len(self.request_log) + 1
            self.request_log.append({
                "ordinal": ordinal,
                "method": "GET",
                "host": urlsplit(url).hostname,
                "path": urlsplit(url).path,
                "kind": "INITIAL" if ordinal == 1 else "REDIRECT",
            })
            req = Request(url, method="GET", headers={
                "User-Agent": "robo-dados-publicos-task112/0.8.0",
                "Accept": "application/pdf,*/*;q=0.1",
            })
            try:
                with self._opener.open(req, timeout=30) as response:
                    raw = response.read()
                    final_url = response.geturl()
                    content_type = response.headers.get_content_type()
                    self._validate(final_url)
                    return raw, final_url, content_type
            except HTTPError as exc:
                if exc.code not in (301, 302, 303, 307, 308):
                    raise Task112Stop(f"TASK112_HTTP_{exc.code}") from exc
                location = exc.headers.get("Location")
                _require(bool(location), "TASK112_REDIRECT_LOCATION")
                redirects += 1
                _require(redirects <= 1, "TASK112_REDIRECT_LIMIT")
                next_url = urljoin(url, location)
                self._validate(next_url)
                url = next_url
            except URLError as exc:
                raise Task112Stop("TASK112_URL_ERROR") from exc


def load_contract(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise Task112Stop("TASK112_CONTRACT_MISSING") from exc
    except json.JSONDecodeError as exc:
        raise Task112Stop("TASK112_CONTRACT_JSON") from exc
    validate_contract(data)
    return data


def validate_contract(data: dict[str, Any]) -> None:
    _require(data.get("schema") == "TASK112_REAL_PPA_OCR_CONTRACT_V1", "TASK112_SCHEMA")
    _require(data.get("mode") == "T1_SINGLE_USE_EXACT_SOURCE_OCR", "TASK112_MODE")
    source = data.get("source") or {}
    _require(
        source.get("url") == "https://www.limeira.sp.gov.br/sitenovo/downloads/0fa1a5cc5c9a1823fbf5436def00f01f.pdf",
        "TASK112_URL",
    )
    _require(source.get("allowed_host") == "www.limeira.sp.gov.br", "TASK112_ALLOWED_HOST")
    _require(source.get("method") == "GET", "TASK112_METHOD")
    _require(source.get("max_http_requests_total") == 2, "TASK112_REQUEST_MAX")
    _require(source.get("retry") is False, "TASK112_RETRY")
    _require(source.get("discovery_search") is False, "TASK112_DISCOVERY")
    document = data.get("document") or {}
    _require(document.get("period") == "2018-2021", "TASK112_PERIOD")
    _require(document.get("law_number") == "5.947", "TASK112_LAW")
    _require(document.get("max_pdf_pages") == 250, "TASK112_PAGE_MAX")
    _require(document.get("coordinate_system") == "SOURCE_PDF_PAGE_1_BASED", "TASK112_COORDINATE")
    _require(data.get("recurrence") is False, "TASK112_RECURRENCE")
    _require(data.get("schedule") is False, "TASK112_SCHEDULE")
    _require(data.get("future_execution_authorized") is False, "TASK112_FUTURE")
    boundaries = data.get("hard_boundaries") or {}
    _require(boundaries and all(value == 0 for value in boundaries.values()), "TASK112_BOUNDARY")


def render_and_ocr_page(
    source_pdf: Path,
    page: int,
    runtime_dir: Path,
) -> dict[str, Any]:
    prefix = runtime_dir / f"page-{page:04d}"
    subprocess.run(
        [
            "pdftoppm", "-f", str(page), "-l", str(page), "-singlefile",
            "-r", "300", "-gray", "-png", str(source_pdf), str(prefix),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    png = Path(str(prefix) + ".png")
    _require(png.exists(), "TASK112_RENDER_MISSING")

    proc = subprocess.run(
        ["tesseract", str(png), "stdout", "-l", "por", "--oem", "1", "--psm", "3", "tsv"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    tsv = proc.stdout
    text, confidences = parse_tsv(tsv)
    normalized = normalize_ocr(text)
    tsv_path = runtime_dir / f"page-{page:04d}.tsv"
    tsv_path.write_text(tsv, encoding="utf-8")

    return {
        "page": page,
        "coordinate_system": "SOURCE_PDF_PAGE_1_BASED",
        "normalized_text": normalized,
        "raw_text": text,
        "rendered_page_sha256": sha256(png.read_bytes()).hexdigest(),
        "ocr_tsv_sha256": sha256(tsv.encode("utf-8")).hexdigest(),
        "confidence_count": len(confidences),
        "confidence_min": min(confidences) if confidences else None,
        "confidence_max": max(confidences) if confidences else None,
        "confidence_mean": (
            sum(confidences) / len(confidences) if confidences else None
        ),
    }


def bounded_excerpt(text: str, needle: str, radius: int = 220) -> str:
    normalized_needle = normalize_ocr(needle)
    normalized_text = normalize_ocr(text)
    index = normalized_text.find(normalized_needle)
    if index < 0:
        return normalized_text[: radius * 2]
    start = max(0, index - radius)
    end = min(len(normalized_text), index + len(normalized_needle) + radius)
    return normalized_text[start:end]

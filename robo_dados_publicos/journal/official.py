from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from html.parser import HTMLParser
from urllib import robotparser
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json
import re

from robo_dados_publicos.release import USER_AGENT

_MONTHS_PT = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "março": 3, "abril": 4,
    "maio": 5, "junho": 6, "julho": 7, "agosto": 8, "setembro": 9,
    "outubro": 10, "novembro": 11, "dezembro": 12,
}
_EDITION_RE = re.compile(r"edi(?:ç|c)[aã]o\s*(?:n[ºo°.]?\s*)?(\d{3,6})", re.I)
_DATE_SLASH_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")
_DATE_PT_RE = re.compile(
    r"\b(\d{1,2})\s+de\s+([A-Za-zÀ-ÿ]+)\s+de\s+(\d{4})\b", re.I
)
_VIEW_RE = re.compile(r"visualizar\s+edi(?:ç|c)[aã]o|visualizar\s+jornal|abrir\s+edi(?:ç|c)[aã]o", re.I)
_TOTAL_RE = re.compile(r"total\s+de\s+itens\s+encontrados\s*:\s*(\d+)", re.I)
_PAGING_KEYS = {"page", "pagina", "página", "paged", "pg"}


def _norm_space(value: str) -> str:
    return " ".join(value.split())


def _parse_date(text: str) -> date | None:
    m = _DATE_SLASH_RE.search(text)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            return None
    m = _DATE_PT_RE.search(text)
    if not m:
        return None
    month_key = m.group(2).lower()
    month = _MONTHS_PT.get(month_key)
    if not month:
        return None
    try:
        return date(int(m.group(3)), month, int(m.group(1)))
    except ValueError:
        return None


@dataclass(frozen=True)
class JournalEdition:
    edition: int
    publication_date: str | None
    document_url: str
    source_page_url: str
    archive_class: str
    label: str = ""

    @property
    def source_id(self) -> str:
        return f"LIMEIRA_JO_{self.edition:05d}"

    @property
    def logical_key(self) -> str:
        return f"limeira/jornal_oficial/edicao/{self.edition}"

    @property
    def file_name(self) -> str:
        return f"limeira_jornal_oficial_edicao_{self.edition}.pdf"

    @property
    def looks_like_pdf(self) -> bool:
        return urlparse(self.document_url).path.lower().endswith(".pdf")

    def to_dict(self) -> dict:
        out = asdict(self)
        out.update({
            "source_id": self.source_id,
            "logical_key": self.logical_key,
            "file_name": self.file_name,
            "looks_like_pdf": self.looks_like_pdf,
        })
        return out

    def to_disabled_source_spec(self) -> dict:
        return {
            "source_id": self.source_id,
            "url": self.document_url,
            "logical_key": self.logical_key,
            "file_name": self.file_name,
            "enabled": False,
            "expected_content_types": ["application/pdf"],
            "cadence": "daily-discovery",
            "notes": "Discovered from official Limeira Jornal Oficial index; remains disabled until live document route/content-type validation.",
        }


class JournalIndexParser(HTMLParser):
    """Tolerant parser for the modern and legacy Limeira Jornal Oficial indexes.

    It does not guess PDF URLs. It only records links actually declared in the
    HTML. Modern pages are parsed by associating the latest visible edition/date
    with a later 'Visualizar edição' anchor. Legacy entries can be parsed from
    the anchor label itself (e.g. 'Edição 6411 - Jornal Oficial - 25 de janeiro...').
    """

    def __init__(self, base_url: str, archive_class: str = "modern"):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.archive_class = archive_class
        self.current_edition: int | None = None
        self.current_date: date | None = None
        self._anchor_href: str | None = None
        self._anchor_text: list[str] = []
        self.editions: list[JournalEdition] = []
        self.links: list[str] = []
        self.total_items: int | None = None

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        attrs = dict(attrs)
        href = attrs.get("href")
        if href:
            absolute = urljoin(self.base_url, href)
            self._anchor_href = absolute
            self.links.append(absolute)
            self._anchor_text = []

    def handle_endtag(self, tag):
        if tag.lower() != "a" or not self._anchor_href:
            return
        label = _norm_space(" ".join(self._anchor_text))
        edition = None
        publication_date = None
        em = _EDITION_RE.search(label)
        if em:
            edition = int(em.group(1))
        publication_date = _parse_date(label)

        if edition is None and _VIEW_RE.search(label):
            edition = self.current_edition
            publication_date = publication_date or self.current_date

        if edition is not None:
            self.editions.append(JournalEdition(
                edition=edition,
                publication_date=publication_date.isoformat() if publication_date else (self.current_date.isoformat() if self.current_date else None),
                document_url=self._anchor_href,
                source_page_url=self.base_url,
                archive_class=self.archive_class,
                label=label,
            ))
        self._anchor_href = None
        self._anchor_text = []

    def handle_data(self, data):
        text = _norm_space(data)
        if not text:
            return
        if self._anchor_href is not None:
            self._anchor_text.append(text)
        tm = _TOTAL_RE.search(text)
        if tm:
            self.total_items = int(tm.group(1))
        em = _EDITION_RE.search(text)
        if em:
            self.current_edition = int(em.group(1))
        parsed_date = _parse_date(text)
        if parsed_date:
            self.current_date = parsed_date

    def pagination_links(self, *, year: int | None = None, month: int | None = None) -> list[str]:
        """Return bounded crawl candidates on the same Jornal Oficial path.

        The exact pagination parameter is intentionally not hard-coded. Links
        are accepted only when the server itself emitted them and they stay on
        the same origin/path. If year/month are provided, candidates must keep
        that month context when those keys are present.
        """
        base = urlparse(self.base_url)
        out = []
        for link in self.links:
            p = urlparse(link)
            if (p.scheme, p.netloc, p.path.rstrip("/")) != (base.scheme, base.netloc, base.path.rstrip("/")):
                continue
            if link == self.base_url:
                continue
            q = parse_qs(p.query)
            if year is not None and "ano" in q and str(year) not in q["ano"]:
                continue
            if month is not None and "mes" in q and str(month) not in q["mes"]:
                continue
            if link not in out:
                out.append(link)
        return out


def _robots_url(url: str) -> str:
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc, "/robots.txt", "", "", ""))


class JornalOficialLimeira:
    MODERN_INDEX = "https://www.limeira.sp.gov.br/jornaloficial"
    LEGACY_INDEX = "https://www.limeira.sp.gov.br/imprensa/jornal-oficial-anteriores-a-01022023"

    def __init__(self, *, timeout: float = 20.0, user_agent: str = USER_AGENT, allow_insecure_localhost: bool = False):
        self.timeout = timeout
        self.user_agent = user_agent
        self.allow_insecure_localhost = allow_insecure_localhost

    @classmethod
    def modern_month_url(cls, year: int, month: int) -> str:
        if not (2000 <= int(year) <= 2100 and 1 <= int(month) <= 12):
            raise ValueError("BAD_YEAR_MONTH")
        return f"{cls.MODERN_INDEX}/?{urlencode({'ano': int(year), 'mes': int(month)})}"

    def _check_url(self, url: str):
        p = urlparse(url)
        if p.scheme not in {"https", "http"} or not p.netloc:
            raise ValueError("BAD_URL")
        if p.scheme != "https":
            local = p.hostname in {"127.0.0.1", "localhost", "::1"}
            if not (self.allow_insecure_localhost and local):
                raise ValueError("HTTPS_REQUIRED")

    def _robots_allowed(self, url: str) -> tuple[bool, str]:
        self._check_url(url)
        rp = robotparser.RobotFileParser()
        rp.set_url(_robots_url(url))
        try:
            req = Request(rp.url, headers={"User-Agent": self.user_agent})
            with urlopen(req, timeout=self.timeout) as resp:
                body = resp.read(512_000).decode("utf-8", "replace")
            rp.parse(body.splitlines())
            return bool(rp.can_fetch(self.user_agent, url)), "ROBOTS_PARSED"
        except HTTPError as exc:
            if exc.code == 404:
                return True, "ROBOTS_NOT_FOUND"
            return False, f"ROBOTS_HTTP_{exc.code}"
        except (URLError, OSError):
            # Discovery must not silently assert permission when robots cannot be read.
            return False, "ROBOTS_UNAVAILABLE"

    def _fetch_html(self, url: str) -> tuple[str, str]:
        allowed, robots_status = self._robots_allowed(url)
        if not allowed:
            raise RuntimeError(f"STOP_ROBOTS_POLICY:{robots_status}")
        req = Request(url, headers={"User-Agent": self.user_agent, "Accept": "text/html,application/xhtml+xml"})
        with urlopen(req, timeout=self.timeout) as resp:
            ctype = (resp.headers.get("Content-Type") or "").lower()
            if "html" not in ctype:
                raise RuntimeError(f"STOP_INDEX_CONTENT_TYPE:{ctype or 'UNKNOWN'}")
            raw = resp.read(5_000_000)
            final_url = resp.geturl()
        return raw.decode("utf-8", "replace"), final_url

    @staticmethod
    def _parse_html_details(html: str, source_url: str, *, archive_class: str = "modern") -> tuple[list[JournalEdition], JournalIndexParser]:
        parser = JournalIndexParser(source_url, archive_class=archive_class)
        parser.feed(html)
        deduped: dict[int, JournalEdition] = {}
        for item in parser.editions:
            old = deduped.get(item.edition)
            # Prefer a link that actually looks like a PDF, otherwise keep first seen.
            if old is None or (item.looks_like_pdf and not old.looks_like_pdf):
                deduped[item.edition] = item
        return sorted(deduped.values(), key=lambda x: x.edition, reverse=True), parser

    @staticmethod
    def parse_html(html: str, source_url: str, *, archive_class: str = "modern") -> tuple[list[JournalEdition], list[str]]:
        editions, parser = JornalOficialLimeira._parse_html_details(html, source_url, archive_class=archive_class)
        return editions, parser.links

    @staticmethod
    def _month_pagination_candidates(links: list[str], base_url: str, year: int, month: int) -> list[str]:
        base = urlparse(base_url)
        out = []
        for link in links:
            p = urlparse(link)
            if (p.scheme, p.netloc, p.path.rstrip("/")) != (base.scheme, base.netloc, base.path.rstrip("/")):
                continue
            q = parse_qs(p.query)
            keys = {k.lower() for k in q}
            if not keys.intersection(_PAGING_KEYS):
                continue
            if "ano" in q and str(year) not in q["ano"]:
                continue
            if "mes" in q and str(month) not in q["mes"]:
                continue
            if link not in out:
                out.append(link)
        return out

    def discover_page(self, url: str, *, archive_class: str = "modern") -> dict:
        html, final_url = self._fetch_html(url)
        editions, parser = self._parse_html_details(html, final_url, archive_class=archive_class)
        status = "PASS_DISCOVERY"
        if parser.total_items is not None and parser.total_items > len(editions):
            status = "PARTIAL_DISCOVERY_PAGINATION_POSSIBLE"
        return {
            "status": status,
            "requested_url": url,
            "final_url": final_url,
            "archive_class": archive_class,
            "count": len(editions),
            "reported_total_items": parser.total_items,
            "editions": [x.to_dict() for x in editions],
            "declared_links_count": len(parser.links),
        }

    def discover_month(self, year: int, month: int, *, max_pages: int = 8) -> dict:
        if max_pages < 1 or max_pages > 50:
            raise ValueError("BAD_MAX_PAGES")
        start = self.modern_month_url(year, month)
        queue = [start]
        seen = set()
        groups: list[list[JournalEdition]] = []
        reported_total = None
        page_reports = []
        while queue and len(seen) < max_pages:
            url = queue.pop(0)
            if url in seen:
                continue
            seen.add(url)
            html, final_url = self._fetch_html(url)
            editions, parser = self._parse_html_details(html, final_url, archive_class="modern")
            if reported_total is None and parser.total_items is not None:
                reported_total = parser.total_items
            # The page also shows a recent-editions block. Month discovery keeps only target-month items.
            month_items = [e for e in editions if e.publication_date and e.publication_date.startswith(f"{year:04d}-{month:02d}-")]
            groups.append(month_items)
            page_reports.append({
                "url": final_url,
                "parsed_editions": len(editions),
                "target_month_editions": len(month_items),
                "reported_total_items": parser.total_items,
            })
            for candidate in self._month_pagination_candidates(parser.links, final_url, year, month):
                if candidate not in seen and candidate not in queue:
                    queue.append(candidate)
        merged = self.merge_editions(*groups)
        if reported_total is not None and len(merged) < reported_total:
            status = "PARTIAL_DISCOVERY_PAGINATION_UNRESOLVED"
        elif queue:
            status = "PARTIAL_DISCOVERY_MAX_PAGES"
        else:
            status = "PASS_DISCOVERY"
        return {
            "status": status,
            "year": year,
            "month": month,
            "requested_url": start,
            "pages_fetched": len(seen),
            "reported_total_items": reported_total,
            "count": len(merged),
            "editions": [e.to_dict() for e in merged],
            "page_reports": page_reports,
        }

    @staticmethod
    def merge_editions(*groups: list[JournalEdition]) -> list[JournalEdition]:
        merged: dict[int, JournalEdition] = {}
        for group in groups:
            for item in group:
                old = merged.get(item.edition)
                if old is None or (item.looks_like_pdf and not old.looks_like_pdf):
                    merged[item.edition] = item
        return sorted(merged.values(), key=lambda x: x.edition, reverse=True)

    @staticmethod
    def emit_disabled_inventory(editions: list[JournalEdition], *, jurisdiction: str = "Limeira/SP") -> dict:
        return {
            "version": 1,
            "jurisdiction": jurisdiction,
            "purpose": "Generated discovery inventory. All Jornal Oficial documents remain disabled until live route/content-type validation.",
            "sources": [e.to_disabled_source_spec() for e in editions],
        }

    @staticmethod
    def write_json(payload: dict, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from html.parser import HTMLParser
from urllib.parse import quote_plus, unquote_plus, urljoin, urlparse, urlunparse
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.error import HTTPError, URLError
from urllib import robotparser
import json
import re

from robo_dados_publicos.release import RESEARCH_USER_AGENT

_SENSITIVE_QUERY_KEYS = {
    "access_token", "authorization", "auth", "code", "key", "password",
    "refresh_token", "secret", "session", "sessionid", "token",
}
_CHALLENGE_PATTERNS = (
    "captcha", "recaptcha", "hcaptcha", "verify you are human", "verify that you are human",
    "prove you are human", "não sou um robô", "nao sou um robo", "verifique que você é humano",
    "verifique que voce e humano", "cloudflare challenge", "cf-chl-",
)
_ENDPOINT_HINT_RE = re.compile(r"(?:^|[/_.-])(api|rest|json|csv|xlsx?|download|export|dadosabertos)(?:[/_.?-]|$)", re.I)


def sanitize_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.query:
        return url
    parts = []
    for part in parsed.query.split("&"):
        raw_key, separator, raw_value = part.partition("=")
        if unquote_plus(raw_key).lower() in _SENSITIVE_QUERY_KEYS:
            parts.append(f"{raw_key}={quote_plus('[REDACTED]')}")
        else:
            parts.append(part if separator else raw_key)
    return urlunparse(parsed._replace(query="&".join(parts)))


class _RecordingRedirectHandler(HTTPRedirectHandler):
    def __init__(self):
        super().__init__()
        self.history: list[dict] = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.history.append({
            "status": int(code),
            "from": sanitize_url(req.full_url),
            "to": sanitize_url(newurl),
        })
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class _SurfaceParser(HTMLParser):
    def __init__(self, base_url: str, limit: int = 80):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.limit = limit
        self.scripts: list[str] = []
        self.stylesheets: list[str] = []
        self.forms: list[dict] = []
        self.links: list[str] = []
        self.title = ""
        self._in_title = False

    @staticmethod
    def _attrs(attrs):
        return {str(k).lower(): (v or "") for k, v in attrs}

    def _append_url(self, bucket: list[str], raw: str):
        if raw and len(bucket) < self.limit:
            bucket.append(sanitize_url(urljoin(self.base_url, raw)))

    def handle_starttag(self, tag, attrs):
        a = self._attrs(attrs)
        tag = tag.lower()
        if tag == "script":
            self._append_url(self.scripts, a.get("src", ""))
        elif tag == "link" and "stylesheet" in a.get("rel", "").lower():
            self._append_url(self.stylesheets, a.get("href", ""))
        elif tag == "a":
            self._append_url(self.links, a.get("href", ""))
        elif tag == "form" and len(self.forms) < self.limit:
            action = a.get("action", "")
            self.forms.append({
                "method": (a.get("method") or "GET").upper(),
                "action": sanitize_url(urljoin(self.base_url, action)) if action else sanitize_url(self.base_url),
            })
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title and len(self.title) < 500:
            self.title += data.strip()


@dataclass(frozen=True)
class PortalProbeResult:
    status: str
    requested_url: str
    final_url: str | None
    http_status: int | None
    content_type: str | None
    html_bytes: int
    html_sha256: str | None
    redirects: tuple[dict, ...]
    robots: dict
    surface_class: str
    challenge_detected: bool
    title: str
    scripts: tuple[str, ...]
    stylesheets: tuple[str, ...]
    forms: tuple[dict, ...]
    links: tuple[str, ...]
    same_origin_links: tuple[str, ...]
    endpoint_hints: tuple[str, ...]
    notes: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


class PortalProbe:
    """Passive, non-invasive reconnaissance for public web portals.

    The probe deliberately does not solve CAPTCHAs, submit forms, execute JavaScript,
    authenticate, enumerate directories, or brute-force endpoints. It fetches robots.txt
    and a single requested public page, then inventories references already present in HTML.
    """

    def __init__(self, *, user_agent: str = RESEARCH_USER_AGENT, timeout: float = 15.0, max_bytes: int = 2_000_000, allow_insecure_localhost: bool = False):
        self.user_agent = user_agent
        self.timeout = float(timeout)
        self.max_bytes = int(max_bytes)
        self.allow_insecure_localhost = allow_insecure_localhost

    def _validate_url(self, url: str):
        p = urlparse(url)
        if p.scheme not in {"https", "http"} or not p.netloc:
            raise ValueError("PORTAL_PROBE_BAD_URL")
        if p.scheme == "http":
            is_local = p.hostname in {"127.0.0.1", "localhost", "::1"}
            if not (self.allow_insecure_localhost and is_local):
                raise ValueError("PORTAL_PROBE_HTTPS_REQUIRED")

    def _robots(self, target_url: str) -> dict:
        p = urlparse(target_url)
        robots_url = urlunparse((p.scheme, p.netloc, "/robots.txt", "", "", ""))
        req = Request(robots_url, headers={"User-Agent": self.user_agent, "Accept": "text/plain,*/*;q=0.1"})
        try:
            with build_opener().open(req, timeout=self.timeout) as resp:
                body = resp.read(min(self.max_bytes, 500_000)).decode("utf-8", "replace")
                rp = robotparser.RobotFileParser()
                rp.set_url(robots_url)
                rp.parse(body.splitlines())
                allowed = bool(rp.can_fetch(self.user_agent, target_url))
                return {
                    "url": robots_url,
                    "http_status": int(getattr(resp, "status", 200)),
                    "policy": "ALLOW" if allowed else "DISALLOW",
                }
        except HTTPError as exc:
            if exc.code == 404:
                return {"url": robots_url, "http_status": 404, "policy": "NOT_FOUND"}
            return {"url": robots_url, "http_status": int(exc.code), "policy": "UNKNOWN_HTTP_ERROR"}
        except (URLError, TimeoutError, OSError) as exc:
            return {"url": robots_url, "http_status": None, "policy": "UNKNOWN_UNREACHABLE", "error_type": type(exc).__name__}

    def probe(self, url: str) -> PortalProbeResult:
        self._validate_url(url)
        requested = sanitize_url(url)
        robots = self._robots(url)
        if robots.get("policy") == "DISALLOW":
            return PortalProbeResult(
                status="STOP_ROBOTS_DISALLOW", requested_url=requested, final_url=None,
                http_status=None, content_type=None, html_bytes=0, html_sha256=None,
                redirects=(), robots=robots, surface_class="NOT_FETCHED",
                challenge_detected=False, title="", scripts=(), stylesheets=(), forms=(), links=(),
                same_origin_links=(), endpoint_hints=(), notes=("Target page not fetched because robots.txt disallows this user agent.",),
            )

        redirects = _RecordingRedirectHandler()
        opener = build_opener(redirects)
        req = Request(url, headers={
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1",
        })
        try:
            with opener.open(req, timeout=self.timeout) as resp:
                final_url = sanitize_url(resp.geturl())
                status_code = int(getattr(resp, "status", 200))
                content_type = (resp.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower() or None
                raw = resp.read(self.max_bytes + 1)
        except HTTPError as exc:
            return PortalProbeResult(
                status="STOP_HTTP_ERROR", requested_url=requested, final_url=sanitize_url(exc.geturl()) if exc.geturl() else None,
                http_status=int(exc.code), content_type=(exc.headers.get("Content-Type") or "").split(";",1)[0].strip().lower() or None,
                html_bytes=0, html_sha256=None, redirects=tuple(redirects.history), robots=robots,
                surface_class="HTTP_ERROR", challenge_detected=False, title="", scripts=(), stylesheets=(), forms=(), links=(), same_origin_links=(), endpoint_hints=(),
                notes=(f"HTTP error {exc.code}",),
            )
        except (URLError, TimeoutError, OSError) as exc:
            return PortalProbeResult(
                status="STOP_NETWORK_ERROR", requested_url=requested, final_url=None, http_status=None, content_type=None,
                html_bytes=0, html_sha256=None, redirects=tuple(redirects.history), robots=robots,
                surface_class="NETWORK_ERROR", challenge_detected=False, title="", scripts=(), stylesheets=(), forms=(), links=(), same_origin_links=(), endpoint_hints=(),
                notes=(type(exc).__name__,),
            )

        truncated = len(raw) > self.max_bytes
        if truncated:
            raw = raw[: self.max_bytes]
        digest = sha256(raw).hexdigest()
        text = raw.decode("utf-8", "replace")
        lower = text.lower()
        challenge = any(marker in lower for marker in _CHALLENGE_PATTERNS)
        parser = _SurfaceParser(final_url)
        try:
            parser.feed(text)
        except Exception:
            # HTMLParser is tolerant, but discovery should never fail only because markup is malformed.
            pass

        origin = urlparse(final_url)
        same_origin = []
        for link in parser.links:
            lp = urlparse(link)
            if lp.scheme in {"http", "https"} and lp.netloc == origin.netloc:
                same_origin.append(link)

        candidates = parser.scripts + parser.links + [x["action"] for x in parser.forms]
        endpoint_hints = []
        for candidate in candidates:
            path_query = urlparse(candidate).path + "?" + urlparse(candidate).query
            if _ENDPOINT_HINT_RE.search(path_query) and candidate not in endpoint_hints:
                endpoint_hints.append(candidate)

        fpath = urlparse(final_url).path.lower()
        is_login_named = "login" in fpath
        has_scripts = bool(parser.scripts)
        if challenge:
            status = "STOP_HUMAN_CHALLENGE"
            surface = "HUMAN_CHALLENGE"
        else:
            status = "PASS_DISCOVERY"
            if is_login_named and has_scripts:
                surface = "SPA_ENTRY_OR_AUTH_GATE"
            elif has_scripts:
                surface = "SCRIPTED_HTML"
            else:
                surface = "STATIC_OR_SERVER_RENDERED_HTML"

        notes = []
        if robots.get("policy", "").startswith("UNKNOWN") or robots.get("policy") == "NOT_FOUND":
            notes.append("robots.txt did not provide an explicit disallow for the target; policy remains informational.")
        if is_login_named:
            notes.append("Final path contains 'login'; this may be a SPA bootstrap name and is not treated as proof that authentication is required.")
        if truncated:
            notes.append(f"HTML body truncated at {self.max_bytes} bytes.")
        if challenge:
            notes.append("Human-verification marker detected; no bypass attempted.")
        if not endpoint_hints:
            notes.append("No API/download endpoint can be proven from the static HTML alone; JavaScript network activity may still expose public data endpoints.")

        return PortalProbeResult(
            status=status,
            requested_url=requested,
            final_url=final_url,
            http_status=status_code,
            content_type=content_type,
            html_bytes=len(raw),
            html_sha256=digest,
            redirects=tuple(redirects.history),
            robots=robots,
            surface_class=surface,
            challenge_detected=challenge,
            title=parser.title.strip(),
            scripts=tuple(dict.fromkeys(parser.scripts)),
            stylesheets=tuple(dict.fromkeys(parser.stylesheets)),
            forms=tuple(parser.forms),
            links=tuple(dict.fromkeys(parser.links)),
            same_origin_links=tuple(dict.fromkeys(same_origin)),
            endpoint_hints=tuple(endpoint_hints),
            notes=tuple(notes),
        )

    @staticmethod
    def write_json(result: PortalProbeResult, path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")

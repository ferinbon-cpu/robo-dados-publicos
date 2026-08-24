from __future__ import annotations

from dataclasses import dataclass
from html import unescape
import json
import re
import socket
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class SiopeRouteDiscoveryError(RuntimeError):
    pass


@dataclass(frozen=True)
class SurfaceResponse:
    url: str
    status: int
    content_type: str
    body: str


def _network_error_code(exc: BaseException) -> str:
    if isinstance(exc, HTTPError):
        return f"STOP_SIOPE_ROUTE_HTTP_{int(exc.code)}"
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return "STOP_SIOPE_ROUTE_TIMEOUT"
    if isinstance(exc, URLError):
        reason = getattr(exc, "reason", None)
        if isinstance(reason, (TimeoutError, socket.timeout)):
            return "STOP_SIOPE_ROUTE_TIMEOUT"
        return "STOP_SIOPE_ROUTE_URL_ERROR"
    return "STOP_SIOPE_ROUTE_NETWORK_ERROR"


class PublicSurfaceClient:
    def __init__(self, *, allowed_hosts: tuple[str, ...], max_response_bytes: int, opener=urlopen):
        self.allowed_hosts = allowed_hosts
        self.max_response_bytes = max_response_bytes
        self.opener = opener

    def get(self, url: str) -> SurfaceResponse:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in self.allowed_hosts:
            raise SiopeRouteDiscoveryError("STOP_SIOPE_ROUTE_HOST_NOT_ALLOWED")
        req = Request(
            url,
            headers={
                "User-Agent": "ROBO_DADOS_PUBLICOS/0.8.0 (+public-transparency-research)",
                "Accept": "text/html,application/xhtml+xml",
            },
            method="GET",
        )
        try:
            with self.opener(req, timeout=20) as response:
                final_url = str(getattr(response, "geturl", lambda: url)())
                final = urlparse(final_url)
                if final.scheme != "https" or final.hostname not in self.allowed_hosts:
                    raise SiopeRouteDiscoveryError("STOP_SIOPE_ROUTE_REDIRECT_HOST_NOT_ALLOWED")
                status = int(getattr(response, "status", response.getcode()))
                content_type = str(response.headers.get("Content-Type", "")).split(";", 1)[0].strip().lower()
                raw = response.read(self.max_response_bytes + 1)
        except SiopeRouteDiscoveryError:
            raise
        except (HTTPError, URLError, TimeoutError, socket.timeout, OSError) as exc:
            raise SiopeRouteDiscoveryError(_network_error_code(exc)) from exc
        if len(raw) > self.max_response_bytes:
            raise SiopeRouteDiscoveryError("STOP_SIOPE_ROUTE_RESPONSE_TOO_LARGE")
        if status != 200:
            raise SiopeRouteDiscoveryError("STOP_SIOPE_ROUTE_HTTP_STATUS")
        if content_type not in {"text/html", "application/xhtml+xml"}:
            raise SiopeRouteDiscoveryError("STOP_SIOPE_ROUTE_CONTENT_TYPE")
        return SurfaceResponse(final_url, status, content_type, raw.decode("utf-8", errors="replace"))


def _normalize_html_text(html: str) -> str:
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(unescape(text).split())


def inspect_classic_surface(html: str, expected_parameters: tuple[str, ...]) -> dict:
    lowered = html.lower()
    captcha = any(marker in lowered for marker in ("g-recaptcha", "recaptcha", "captcha"))
    observed_names = set(
        unescape(value)
        for value in re.findall(r"\bname\s*=\s*['\"]([^'\"]+)['\"]", html, flags=re.IGNORECASE)
    )
    observed_expected = sorted(name for name in expected_parameters if name in observed_names or name in html)
    return {
        "surface": "CLASSIC_QUERY",
        "status": "OBSERVED",
        "captcha_detected": captcha,
        "expected_parameters_observed": observed_expected,
        "form_submitted": False,
        "acquisition_decision": (
            "BLOCK_AUTOMATED_ACQUISITION_HUMAN_CHALLENGE"
            if captcha
            else "NOT_SELECTED_FOR_AUTOMATED_ACQUISITION"
        ),
    }


def blocked_classic_surface(reason: str) -> dict:
    return {
        "surface": "CLASSIC_QUERY",
        "status": "UNAVAILABLE_OR_BLOCKED",
        "reason": reason,
        "captcha_detected": None,
        "expected_parameters_observed": [],
        "form_submitted": False,
        "acquisition_decision": "BLOCK_AUTOMATED_ACQUISITION_SURFACE_UNAVAILABLE",
    }


def inspect_antonieta_surface(html: str, *, expected_name: str, expected_path: str) -> dict:
    visible = _normalize_html_text(html)
    if expected_name not in visible and expected_name not in html:
        raise SiopeRouteDiscoveryError("STOP_SIOPE_ANTONIETA_PRODUCT_NAME_MISMATCH")
    if expected_path not in visible and expected_path not in html:
        raise SiopeRouteDiscoveryError("STOP_SIOPE_ANTONIETA_ARTIFACT_NOT_DECLARED")

    explicit_urls: list[str] = []
    basename = expected_path.rsplit("/", 1)[-1]
    for attr_value in re.findall(
        r"\b(?:href|src|data-url|data-href|download-url)\s*=\s*['\"]([^'\"]+)['\"]",
        html,
        flags=re.IGNORECASE,
    ):
        decoded = unescape(attr_value)
        if expected_path in decoded or basename in decoded:
            parsed = urlparse(decoded)
            if parsed.scheme == "https" and parsed.netloc:
                explicit_urls.append(decoded)

    explicit_urls = sorted(set(explicit_urls))
    return {
        "surface": "ANTONIETA_PRODUCT",
        "status": "OBSERVED",
        "product_name_verified": True,
        "artifact_path_declared": expected_path,
        "explicit_download_url_observed": explicit_urls[0] if len(explicit_urls) == 1 else None,
        "explicit_download_url_count": len(explicit_urls),
        "artifact_downloaded": False,
        "acquisition_decision": "CANDIDATE_REQUIRES_ARTIFACT_VERIFICATION_GATE",
    }


def _validate_config(config: dict) -> None:
    exact = {
        "schema_version": 1,
        "gate_id": "M7_SIOPE_LIMEIRA_ROUTE_DISCOVERY_GATE_0_8_0",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "active_validated_version": "0.7.0",
        "mode": "PASSIVE_ROUTE_DISCOVERY_ONLY",
        "network": "READ_ONLY_GET",
        "remote_writes": "PROHIBITED",
        "form_submission": "PROHIBITED",
        "captcha_bypass": "PROHIBITED",
        "artifact_download": "PROHIBITED",
        "source_collection": "PROHIBITED",
        "source_processing": "PROHIBITED",
        "recurrence": "PROHIBITED",
        "schedule": "DISABLED",
        "next_gate": "M7_SIOPE_ANTONIETA_ARTIFACT_VERIFICATION_GATE_0_8_0",
    }
    for key, value in exact.items():
        if config.get(key) != value:
            raise SiopeRouteDiscoveryError(f"STOP_SIOPE_ROUTE_CONFIG_{key.upper()}")
    if config.get("max_response_bytes") != 2097152:
        raise SiopeRouteDiscoveryError("STOP_SIOPE_ROUTE_CONFIG_MAX_RESPONSE_BYTES")
    hosts = config.get("allowed_hosts")
    if hosts != ["www.fnde.gov.br", "webservice.fnde.gov.br"]:
        raise SiopeRouteDiscoveryError("STOP_SIOPE_ROUTE_CONFIG_ALLOWED_HOSTS")
    surfaces = config.get("surfaces")
    expected = config.get("expected_antonieta")
    params = config.get("classic_query_parameters_observed")
    if not isinstance(surfaces, dict) or not isinstance(expected, dict) or not isinstance(params, list):
        raise SiopeRouteDiscoveryError("STOP_SIOPE_ROUTE_CONFIG_STRUCTURE")
    for url in surfaces.values():
        parsed = urlparse(str(url))
        if parsed.scheme != "https" or parsed.hostname not in hosts:
            raise SiopeRouteDiscoveryError("STOP_SIOPE_ROUTE_CONFIG_SURFACE_URL")
    if expected.get("artifact_path") != "exports/SIOPE/SIOPE_DADOS_GERAIS_SIOPE.txt.gz":
        raise SiopeRouteDiscoveryError("STOP_SIOPE_ROUTE_CONFIG_ARTIFACT_PATH")


def discover_siope_routes(config: dict, *, client: PublicSurfaceClient | None = None) -> dict:
    _validate_config(config)
    surfaces = config["surfaces"]
    expected = config["expected_antonieta"]
    params = tuple(config["classic_query_parameters_observed"])
    client = client or PublicSurfaceClient(
        allowed_hosts=tuple(config["allowed_hosts"]),
        max_response_bytes=int(config["max_response_bytes"]),
    )

    try:
        classic = client.get(surfaces["classic_query"])
        classic_result = inspect_classic_surface(classic.body, params)
    except SiopeRouteDiscoveryError as exc:
        classic_result = blocked_classic_surface(str(exc))

    # Antonieta is the preferred current automation candidate. Its declared
    # product and artifact path are required for this gate to pass.
    antonieta = client.get(surfaces["antonieta_product"])
    antonieta_result = inspect_antonieta_surface(
        antonieta.body,
        expected_name=expected["product_name"],
        expected_path=expected["artifact_path"],
    )

    return {
        "status": "PASS_M7_SIOPE_ROUTE_DISCOVERY_GATE",
        "gate_id": config["gate_id"],
        "software_version": config["software_version"],
        "network_called": True,
        "network_method": "GET_ONLY",
        "remote_writes": "NONE",
        "form_submission": False,
        "captcha_bypass": False,
        "artifact_downloaded": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "classic_query": classic_result,
        "preferred_candidate": antonieta_result,
        "acquisition_route_status": "CANDIDATE_IDENTIFIED_ARTIFACT_NOT_VERIFIED",
        "next_gate": config["next_gate"],
    }


def load_route_discovery_config(path: str | Path) -> dict:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    _validate_config(config)
    return config

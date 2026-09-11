from __future__ import annotations

import hashlib
import html.parser
import json
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


OUT = Path("probe-output/task199h_limeira_geo_public_probe.json")
MAX_BODY = 12_000_000
UA = "robo-dados-publicos/TASK199H read-only public-geoportal-audit"

SEEDS = [
    "https://limeira.geoportal.geopixel.com.br/",
    "https://limeira.geoportal.geopixel.com.br/api/pages",
    "https://limeira.geopixel.com.br/geopixelcidades3/",
]

ALLOWED_HOSTS = {
    "limeira.geoportal.geopixel.com.br",
    "limeira.geopixel.com.br",
}

API_TOKEN_RE = re.compile(
    r"(?P<url>https?://[^\"'<>\\\s]+|/(?:api|geoserver|ows|wms|wfs|rest)/[^\"'<>\\\s]*)",
    re.IGNORECASE,
)
KEYWORD_RE = re.compile(
    r"(?:api/pages|geoserver|\bwms\b|\bwfs\b|FeatureServer|MapServer|geoportal|layer|theme)",
    re.IGNORECASE,
)


class AssetParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.scripts: list[str] = []
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        d = dict(attrs)
        if tag.lower() == "script" and d.get("src"):
            self.scripts.append(d["src"])
        if tag.lower() == "link" and d.get("href"):
            self.links.append(d["href"])


def fetch(url: str, *, limit: int = MAX_BODY) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,application/json,text/javascript,application/javascript,*/*;q=0.5",
        },
        method="GET",
    )
    row = {"requested_url": url}
    try:
        with urllib.request.urlopen(req, timeout=35, context=ssl.create_default_context()) as resp:
            body = resp.read(limit + 1)
            truncated = len(body) > limit
            if truncated:
                body = body[:limit]
            row.update(
                {
                    "status": int(resp.status),
                    "final_url": resp.geturl(),
                    "content_type": resp.headers.get("Content-Type"),
                    "content_length_header": resp.headers.get("Content-Length"),
                    "bytes_captured": len(body),
                    "truncated": truncated,
                    "sha256_captured": hashlib.sha256(body).hexdigest(),
                    "body": body,
                }
            )
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read(limit + 1)
        except Exception:
            body = b""
        row.update(
            {
                "status": int(exc.code),
                "final_url": exc.geturl(),
                "content_type": exc.headers.get("Content-Type") if exc.headers else None,
                "bytes_captured": min(len(body), limit),
                "truncated": len(body) > limit,
                "sha256_captured": hashlib.sha256(body[:limit]).hexdigest(),
                "body": body[:limit],
                "error": f"HTTPError:{exc.code}",
            }
        )
    except Exception as exc:
        row.update({"status": None, "error": f"{type(exc).__name__}:{exc}", "body": b""})
    return row


def safe_text(body: bytes) -> str:
    return body.decode("utf-8", errors="replace")


def normalize_candidate(base: str, candidate: str) -> str | None:
    candidate = candidate.strip().rstrip("),;]")
    if not candidate or "{" in candidate or "}" in candidate:
        return None
    url = urllib.parse.urljoin(base, candidate)
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        return None
    if parsed.username or parsed.password:
        return None
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", parsed.query, ""))


def summarize_response(row: dict) -> dict:
    return {k: v for k, v in row.items() if k != "body"}


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "schema": "TASK199H_LIMEIRA_GEO_PUBLIC_PROBE_V1",
        "mode": "EPHEMERAL_READ_ONLY_GITHUB_ACTIONS",
        "seeds": SEEDS,
        "allowed_hosts": sorted(ALLOWED_HOSTS),
        "auth_attempted": False,
        "registration_attempted": False,
        "post_requests": 0,
        "write_requests": 0,
        "tinyfish_used": False,
        "seed_responses": [],
        "declared_assets": [],
        "asset_findings": [],
        "candidate_endpoints": [],
        "candidate_endpoint_responses": [],
    }

    seed_rows = []
    for url in SEEDS:
        row = fetch(url)
        seed_rows.append(row)
        result["seed_responses"].append(summarize_response(row))

    asset_urls: list[str] = []
    for row in seed_rows:
        body = row.get("body") or b""
        ctype = (row.get("content_type") or "").lower()
        if not body or "html" not in ctype:
            continue
        parser = AssetParser()
        try:
            parser.feed(safe_text(body))
        except Exception:
            continue
        base = row.get("final_url") or row["requested_url"]
        for raw in parser.scripts:
            url = normalize_candidate(base, raw)
            if url and url not in asset_urls:
                asset_urls.append(url)
        result["declared_assets"].append(
            {
                "source": base,
                "scripts": parser.scripts,
                "links_count": len(parser.links),
            }
        )

    # Read only scripts declared by the public HTML. No crawling and no guessed bundles.
    discovered: set[str] = set()
    for asset_url in asset_urls[:40]:
        row = fetch(asset_url)
        text = safe_text(row.get("body") or b"")
        hits = []
        if text:
            for match in API_TOKEN_RE.finditer(text):
                raw = match.group("url")
                url = normalize_candidate(row.get("final_url") or asset_url, raw)
                if url:
                    discovered.add(url)
                    hits.append(url)
            keyword_samples = []
            for m in KEYWORD_RE.finditer(text):
                start = max(0, m.start() - 160)
                end = min(len(text), m.end() + 260)
                sample = re.sub(r"\s+", " ", text[start:end])
                if sample not in keyword_samples:
                    keyword_samples.append(sample)
                if len(keyword_samples) >= 20:
                    break
        result["asset_findings"].append(
            {
                **summarize_response(row),
                "api_like_urls": sorted(set(hits))[:100],
                "keyword_samples": keyword_samples,
            }
        )

    # Keep the documented Geopixel public config endpoint in the candidate set even
    # when it was a seed, so the final summary is explicit.
    discovered.add("https://limeira.geoportal.geopixel.com.br/api/pages")
    candidates = sorted(discovered)
    result["candidate_endpoints"] = candidates

    # Probe only GET endpoints literally declared in fetched assets or the generic
    # documented public /api/pages contract. Stop at 50 to remain bounded.
    for url in candidates[:50]:
        row = fetch(url, limit=2_000_000)
        body = row.get("body") or b""
        text = safe_text(body)
        payload_summary = None
        if body and "json" in (row.get("content_type") or "").lower():
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    payload_summary = {
                        "type": "object",
                        "keys": sorted(map(str, parsed.keys()))[:100],
                        "repr_prefix": json.dumps(parsed, ensure_ascii=False)[:4000],
                    }
                elif isinstance(parsed, list):
                    payload_summary = {
                        "type": "array",
                        "length": len(parsed),
                        "repr_prefix": json.dumps(parsed[:5], ensure_ascii=False)[:4000],
                    }
            except Exception as exc:
                payload_summary = {"parse_error": f"{type(exc).__name__}:{exc}", "text_prefix": text[:2000]}
        result["candidate_endpoint_responses"].append(
            {**summarize_response(row), "payload_summary": payload_summary, "text_prefix": text[:2000] if not payload_summary else None}
        )

    # Never treat endpoint failure as proof of missing GIS evidence.
    statuses = [r.get("status") for r in result["candidate_endpoint_responses"]]
    result["status"] = (
        "PASS_PUBLIC_DATA_ENDPOINT_FOUND"
        if any(isinstance(s, int) and 200 <= s < 300 for s in statuses)
        else "STOP_NO_USABLE_PUBLIC_DATA_ENDPOINT_FOUND"
    )
    result["absence_inference_allowed"] = False
    result["next_step"] = (
        "inspect returned public layer/config data for official point/parcel geometry"
        if result["status"] == "PASS_PUBLIC_DATA_ENDPOINT_FOUND"
        else "retain five HELD schools; do not force promotion"
    )

    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "out": str(OUT)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

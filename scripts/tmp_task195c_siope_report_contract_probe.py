from __future__ import annotations

import hashlib
import html
import json
import re
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOTS = [
    "https://webservice.fnde.gov.br/siope/relatorioQuadroResumoDespesasMuni.do",
    "https://www.fnde.gov.br/siope/relatorioQuadroResumoDespesasMuni.do",
]
ALLOWED_HOSTS = {"webservice.fnde.gov.br", "www.fnde.gov.br"}
MAX_BYTES = 2_000_000
MAX_SCRIPTS = 8
OUT = Path("tmp/task195c_siope_report_contract_probe.json")


class Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.forms = []
        self.current_form = None
        self.scripts = []
        self.select_stack = []
        self.text_parts = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "form":
            self.current_form = {
                "action": a.get("action"),
                "method": (a.get("method") or "GET").upper(),
                "fields": [],
            }
            self.forms.append(self.current_form)
        elif tag in {"input", "button"} and self.current_form is not None:
            self.current_form["fields"].append({
                "tag": tag,
                "name": a.get("name"),
                "type": a.get("type"),
                "value": a.get("value"),
                "id": a.get("id"),
            })
        elif tag == "select" and self.current_form is not None:
            item = {"tag": "select", "name": a.get("name"), "id": a.get("id"), "options": []}
            self.current_form["fields"].append(item)
            self.select_stack.append(item)
        elif tag == "option" and self.select_stack:
            self.select_stack[-1]["options"].append({"value": a.get("value"), "selected": "selected" in a})
        elif tag == "script" and a.get("src"):
            self.scripts.append(a["src"])

    def handle_endtag(self, tag):
        if tag == "form":
            self.current_form = None
        elif tag == "select" and self.select_stack:
            self.select_stack.pop()

    def handle_data(self, data):
        s = " ".join(data.split())
        if s:
            self.text_parts.append(s)


def fetch(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 TASK195C-readonly-probe"})
    with urllib.request.urlopen(req, timeout=30) as r:
        final = r.geturl()
        host = urllib.parse.urlparse(final).hostname
        if host not in ALLOWED_HOSTS:
            raise RuntimeError(f"redirected outside allowed hosts: {final}")
        data = r.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise RuntimeError(f"response exceeds {MAX_BYTES} bytes")
        return {
            "requested_url": url,
            "final_url": final,
            "status": getattr(r, "status", None),
            "content_type": r.headers.get("Content-Type"),
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "data": data,
        }


def inspect_html(base_url: str, data: bytes):
    text = data.decode("utf-8", errors="replace")
    p = Parser()
    p.feed(text)
    joined = "\n".join(p.text_parts)
    markers = [
        "Dotação Atualizada", "Dotacao Atualizada", "Captcha", "captcha", "ação", "acao",
        "ano", "periodo", "munic", "cod_muni", "fase", "despesa", "relatorio",
    ]
    lines = []
    for raw in text.splitlines():
        low = raw.lower()
        if any(m.lower() in low for m in markers):
            clean = re.sub(r"\s+", " ", html.unescape(raw)).strip()
            if clean:
                lines.append(clean[:1000])
    scripts = [urllib.parse.urljoin(base_url, src) for src in p.scripts]
    scripts = [u for u in scripts if urllib.parse.urlparse(u).hostname in ALLOWED_HOSTS][:MAX_SCRIPTS]
    return {
        "forms": p.forms,
        "script_urls": scripts,
        "text_markers": {m: (m.lower() in joined.lower()) for m in markers},
        "interesting_lines": lines[:120],
    }


def main():
    result = {
        "schema": "TASK195C_SIOPE_REPORT_CONTRACT_PROBE_V1",
        "mode": "READ_ONLY_GET_NO_AUTH_NO_FORM_SUBMISSION",
        "roots": [],
        "scripts": [],
        "guards": {
            "post_requests": 0,
            "form_submissions": 0,
            "credentials": 0,
            "captcha_bypass": 0,
            "tinyfish": 0,
        },
    }
    discovered_scripts = []
    for url in ROOTS:
        item = {"url": url}
        try:
            r = fetch(url)
            item.update({k: v for k, v in r.items() if k != "data"})
            analysis = inspect_html(r["final_url"], r["data"])
            item["html"] = analysis
            discovered_scripts.extend(analysis["script_urls"])
        except Exception as e:
            item["error"] = f"{type(e).__name__}: {e}"
        result["roots"].append(item)

    seen = set()
    for url in discovered_scripts:
        if url in seen or len(result["scripts"]) >= MAX_SCRIPTS:
            continue
        seen.add(url)
        item = {"url": url}
        try:
            r = fetch(url)
            text = r["data"].decode("utf-8", errors="replace")
            item.update({k: v for k, v in r.items() if k != "data"})
            candidates = sorted(set(re.findall(r"[A-Za-z0-9_./?=&%-]{3,220}(?:\.do|\.jsp|\.js|acao=|action=)[A-Za-z0-9_./?=&%-]*", text, flags=re.I)))
            keywords = []
            for kw in ["relatorioQuadroResumoDespesas", "Dotação Atualizada", "Dotacao Atualizada", "captcha", "municipio", "periodo", "fase", "pesquisar", "atualizar"]:
                if kw.lower() in text.lower():
                    keywords.append(kw)
            item["candidate_routes"] = candidates[:100]
            item["keywords"] = keywords
        except Exception as e:
            item["error"] = f"{type(e).__name__}: {e}"
        result["scripts"].append(item)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "roots": [{k: v for k, v in x.items() if k != "html"} for x in result["roots"]],
        "forms": [x.get("html", {}).get("forms", []) for x in result["roots"]],
        "script_count": len(result["scripts"]),
        "output": str(OUT),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

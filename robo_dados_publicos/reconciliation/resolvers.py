from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from http.cookiejar import CookieJar
from io import BytesIO, StringIO
from pathlib import Path
from urllib.parse import urlencode, urljoin, urlparse
from urllib.request import HTTPCookieProcessor, Request, build_opener, urlopen
import csv
import hashlib
import json
import re
import unicodedata
import zipfile

from robo_dados_publicos.connectors.http_source import HttpSourceConnector
from robo_dados_publicos.state.registry import StateRegistry
from robo_dados_publicos.reconciliation.evidence import ReconciliationEvidenceAssembler
from robo_dados_publicos.release import RESEARCH_USER_AGENT


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ascii(value) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.lower().split())


def _digits(value) -> str:
    return re.sub(r"\D", "", str(value or ""))


def _clean(value):
    if value is None:
        return None
    text = " ".join(str(value).split()).strip()
    return text or None


def _safe_http_url(url: str, *, allow_insecure_localhost: bool = False) -> str:
    parsed = urlparse(url)
    if parsed.scheme == "https":
        return url
    if allow_insecure_localhost and parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}:
        return url
    raise ValueError("HTTPS_REQUIRED")


@dataclass(frozen=True)
class ResolutionResult:
    task_id: str
    target_source: str
    status: str
    checked_at: str
    candidates: list[dict]
    evidence: dict
    notes: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


class _LinkTextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._href = None
        self._text: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href is not None:
            self.links.append((self._href, " ".join("".join(self._text).split())))
            self._href = None
            self._text = []


class _FormParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.forms: list[dict] = []
        self.current: dict | None = None
        self.context = ""

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attrs = dict(attrs)
        if tag == "form":
            self.current = {
                "action": attrs.get("action") or "",
                "method": (attrs.get("method") or "get").lower(),
                "name": attrs.get("name") or "",
                "id": attrs.get("id") or "",
                "fields": [],
            }
            self.context = ""
            return
        if self.current is None:
            return
        if tag in {"input", "select", "textarea", "button"}:
            self.current["fields"].append({
                "tag": tag,
                "name": attrs.get("name") or "",
                "id": attrs.get("id") or "",
                "type": (attrs.get("type") or "").lower(),
                "value": attrs.get("value") or "",
                "placeholder": attrs.get("placeholder") or "",
                "title": attrs.get("title") or "",
                "context": self.context[-180:],
            })

    def handle_data(self, data):
        if self.current is not None:
            self.context += " " + data

    def handle_endtag(self, tag):
        if tag.lower() == "form" and self.current is not None:
            self.forms.append(self.current)
            self.current = None
            self.context = ""


class _TableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._row_stack: list[dict] = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "tr":
            self._row_stack.append({"cells": [], "cell": None})
        elif self._row_stack and tag in {"td", "th"}:
            self._row_stack[-1]["cell"] = []

    def handle_data(self, data):
        for row in reversed(self._row_stack):
            if row["cell"] is not None:
                row["cell"].append(data)
                break

    def handle_endtag(self, tag):
        tag = tag.lower()
        if self._row_stack and tag in {"td", "th"}:
            row = self._row_stack[-1]
            if row["cell"] is not None:
                row["cells"].append(" ".join("".join(row["cell"]).split()))
                row["cell"] = None
        elif self._row_stack and tag == "tr":
            row = self._row_stack.pop()
            if row["cell"] is not None:
                row["cells"].append(" ".join("".join(row["cell"]).split()))
            if any(cell.strip() for cell in row["cells"]):
                self.rows.append(row["cells"])


class TcespExpenseResolver:
    """Resolve TCE-SP expense tasks without extrapolating undocumented APIs.

    * 2014-2019: use the officially documented month JSON API.
    * 2020+: discover the municipality-year page first and follow the link whose
      visible text is 'Despesa Detalhada'. The resolver never guesses the ZIP URL.
    """

    REQUIRED = ("event", "commitment", "supplier_id", "supplier_name", "date", "value")
    HEADER_ALIASES = {
        "event": {"evento", "tipo_evento", "tipo_de_evento", "tp_despesa"},
        "commitment": {"nr_empenho", "numero_empenho", "numero_do_empenho", "n_empenho", "empenho"},
        "supplier_id": {"id_fornecedor", "identificador_despesa", "cpf_cnpj_ident_esp", "cpf_cnpj_ident_esp_", "nr_identificador_despesa", "cnpj_cpf"},
        "supplier_name": {"nm_fornecedor", "nome_fornecedor", "nome_do_fornecedor", "fornecedor", "ds_despesa"},
        "date": {"dt_emissao_despesa", "data_evento", "data_do_evento", "data"},
        "value": {"vl_despesa", "valor_despesa", "valor"},
        "organ": {"orgao", "orgao_nome", "ds_orgao"},
        "month": {"mes", "mes_referencia"},
    }

    def __init__(
        self,
        *,
        base_url: str = "https://transparencia.tce.sp.gov.br",
        municipality: str = "limeira",
        timeout: float = 45.0,
        allow_insecure_localhost: bool = False,
        user_agent: str = RESEARCH_USER_AGENT,
    ):
        self.base_url = base_url.rstrip("/")
        self.municipality = municipality
        self.timeout = timeout
        self.allow_insecure_localhost = allow_insecure_localhost
        self.user_agent = user_agent
        _safe_http_url(self.base_url, allow_insecure_localhost=allow_insecure_localhost)

    def _get_bytes(self, url: str) -> tuple[bytes, dict]:
        _safe_http_url(url, allow_insecure_localhost=self.allow_insecure_localhost)
        req = Request(url, headers={"User-Agent": self.user_agent}, method="GET")
        with urlopen(req, timeout=self.timeout) as resp:
            data = resp.read()
            return data, {"http_status": getattr(resp, "status", 200) or 200, "content_type": resp.headers.get("Content-Type")}

    @staticmethod
    def _flatten_json_records(payload) -> list[dict]:
        if isinstance(payload, list):
            return [x for x in payload if isinstance(x, dict)]
        if isinstance(payload, dict):
            rows = []
            for value in payload.values():
                if isinstance(value, list):
                    rows.extend(x for x in value if isinstance(x, dict))
            if rows:
                return rows
            if all(k in payload for k in ("evento", "nr_empenho")):
                return [payload]
        return []

    def _historical_year(self, year: int) -> tuple[list[dict], dict]:
        all_rows = []
        urls = []
        for month in range(1, 13):
            url = f"{self.base_url}/api/json/despesas/{self.municipality}/{year}/{month}"
            raw, meta = self._get_bytes(url)
            payload = json.loads(raw.decode("utf-8-sig"))
            rows = self._flatten_json_records(payload)
            all_rows.extend(rows)
            urls.append({"url": url, "records": len(rows), "http_status": meta["http_status"]})
        return all_rows, {"mode": "DOCUMENTED_API_2014_2019", "resources": urls}

    def _discover_current_resource(self, year: int) -> tuple[str | None, dict]:
        panel = f"{self.base_url}/municipio/{self.municipality}/{year}"
        raw, meta = self._get_bytes(panel)
        text = raw.decode("utf-8", errors="replace")
        parser = _LinkTextParser()
        parser.feed(text)
        matches = [(href, label) for href, label in parser.links if "despesa detalhada" in _ascii(label)]
        evidence = {
            "panel_url": panel,
            "http_status": meta["http_status"],
            "link_count": len(parser.links),
            "expense_detail_links": [{"href": h, "label": l} for h, l in matches],
        }
        if len(matches) != 1:
            return None, evidence
        return urljoin(panel, matches[0][0]), evidence

    @staticmethod
    def _normalized_header(value: str) -> str:
        value = _ascii(value)
        value = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
        return value

    @classmethod
    def _map_headers(cls, fieldnames: list[str] | None) -> dict[str, str]:
        if not fieldnames:
            return {}
        normalized = {cls._normalized_header(x): x for x in fieldnames if x is not None}
        mapping = {}
        for canonical, aliases in cls.HEADER_ALIASES.items():
            candidates = [normalized[a] for a in aliases if a in normalized]
            if len(candidates) == 1:
                mapping[canonical] = candidates[0]
        return mapping

    @staticmethod
    def _decode_csv(raw: bytes) -> tuple[str, str]:
        for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
            try:
                return raw.decode(enc), enc
            except UnicodeDecodeError:
                continue
        return raw.decode("latin-1", errors="replace"), "latin-1-replace"

    @classmethod
    def _parse_csv_bytes(cls, raw: bytes) -> tuple[list[dict], dict]:
        text, encoding = cls._decode_csv(raw)
        sample = text[:65536]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=";,\t|")
            delimiter = dialect.delimiter
        except csv.Error:
            delimiter = ";"
        reader = csv.DictReader(StringIO(text), delimiter=delimiter)
        mapping = cls._map_headers(reader.fieldnames)
        missing = [name for name in cls.REQUIRED if name not in mapping]
        if missing:
            return [], {
                "status": "STOP_SCHEMA_UNKNOWN",
                "encoding": encoding,
                "delimiter": delimiter,
                "fieldnames": reader.fieldnames or [],
                "mapping": mapping,
                "missing": missing,
            }
        rows = list(reader)
        return rows, {
            "status": "PASS_SCHEMA",
            "encoding": encoding,
            "delimiter": delimiter,
            "fieldnames": reader.fieldnames or [],
            "mapping": mapping,
            "records": len(rows),
        }

    def _current_year(self, year: int, work_dir: Path) -> tuple[list[dict], dict]:
        resource, discovery = self._discover_current_resource(year)
        if not resource:
            return [], {"status": "STOP_TCE_YEAR_RESOURCE_UNDISCOVERED", "discovery": discovery}
        _safe_http_url(resource, allow_insecure_localhost=self.allow_insecure_localhost)
        work_dir.mkdir(parents=True, exist_ok=True)
        archive_path = work_dir / f"tcesp_despesas_{self.municipality}_{year}.zip"
        connector = HttpSourceConnector(user_agent=self.user_agent)
        fetched = connector.download(resource, archive_path, timeout=self.timeout)
        digest = fetched.sha256 or hashlib.sha256(archive_path.read_bytes()).hexdigest()
        evidence = {
            "status": "PASS_RESOURCE_DISCOVERY",
            "mode": "MUNICIPAL_YEAR_DOWNLOAD_DISCOVERED_FROM_PANEL",
            "discovery": discovery,
            "resource_url": resource,
            "download": {
                "http_status": fetched.http_status,
                "content_type": fetched.content_type,
                "bytes_written": fetched.bytes_written,
                "sha256": digest,
            },
        }
        try:
            zf = zipfile.ZipFile(archive_path)
        except zipfile.BadZipFile:
            return [], {**evidence, "status": "STOP_UNEXPECTED_RESOURCE_FORMAT"}
        csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv") and not n.endswith("/")]
        if not csv_names:
            return [], {**evidence, "status": "STOP_SCHEMA_UNKNOWN", "zip_members": zf.namelist()}
        aggregate_rows = []
        csv_meta = []
        for name in csv_names:
            raw = zf.read(name)
            rows, meta = self._parse_csv_bytes(raw)
            csv_meta.append({"member": name, **meta})
            if meta.get("status") != "PASS_SCHEMA":
                return [], {**evidence, "status": "STOP_SCHEMA_UNKNOWN", "csv": csv_meta}
            aggregate_rows.extend(self._canonical_from_current(r, meta["mapping"]) for r in rows)
        return aggregate_rows, {**evidence, "status": "PASS_DATASET", "csv": csv_meta, "records": len(aggregate_rows)}

    @staticmethod
    def _canonical_from_historical(row: dict) -> dict:
        return {
            "organ": row.get("orgao"),
            "month": row.get("mes"),
            "event": row.get("evento"),
            "commitment": row.get("nr_empenho"),
            "supplier_id": row.get("id_fornecedor"),
            "supplier_name": row.get("nm_fornecedor"),
            "date": row.get("dt_emissao_despesa"),
            "value": row.get("vl_despesa"),
        }

    @classmethod
    def _canonical_from_current(cls, row: dict, mapping: dict[str, str]) -> dict:
        return {key: row.get(src) for key, src in mapping.items()}

    @staticmethod
    def _event_stage(event) -> str:
        e = _ascii(event)
        if "liquid" in e:
            return "LIQUIDADO"
        if "pago" in e or "pagamento" in e:
            return "PAGO"
        if "empenh" in e:
            return "EMPENHADO"
        if "anula" in e:
            return "ANULACAO"
        if "refor" in e:
            return "REFORCO"
        return "OUTRO"

    @staticmethod
    def _filter_records(rows: list[dict], *, cnpj: str | None, contractor: str | None) -> tuple[list[dict], str | None]:
        target_cnpj = _digits(cnpj)
        target_name = _ascii(contractor)
        out = []
        basis = None
        for row in rows:
            supplier_digits = _digits(row.get("supplier_id"))
            supplier_name = _ascii(row.get("supplier_name"))
            if target_cnpj:
                if supplier_digits == target_cnpj or target_cnpj in supplier_digits:
                    out.append(row)
                    basis = "CNPJ_EXACT_OR_EMBEDDED"
            elif target_name and (target_name == supplier_name or target_name in supplier_name or supplier_name in target_name):
                out.append(row)
                basis = "SUPPLIER_NAME_NORMALIZED"
        return out, basis

    def resolve(self, task: dict, *, work_dir: str | Path) -> ResolutionResult:
        if task.get("target_source") != "TCE_SP_DESPESAS":
            raise ValueError("WRONG_TARGET_SOURCE")
        keys = task.get("match_keys") or {}
        years = keys.get("candidate_years") or ([keys.get("year")] if keys.get("year") else [])
        years = sorted({int(y) for y in years if y is not None})
        if not years:
            return ResolutionResult(task["task_id"], "TCE_SP_DESPESAS", "STOP_MISSING_YEAR", _now(), [], {}, ["Tarefa sem exercício candidato."])
        cnpj = _clean(keys.get("cnpj"))
        contractor = _clean(keys.get("contractor"))
        if not cnpj and not contractor:
            return ResolutionResult(task["task_id"], "TCE_SP_DESPESAS", "STOP_MISSING_SUPPLIER_KEY", _now(), [], {}, ["Tarefa sem CNPJ/nome de fornecedor."])

        candidates = []
        evidence = {"years": {}, "resolver_contract": "API_2014_2019_OR_DISCOVERED_YEAR_DOWNLOAD_2020_PLUS"}
        for year in years:
            try:
                if 2014 <= year <= 2019:
                    raw_rows, ev = self._historical_year(year)
                    rows = [self._canonical_from_historical(r) for r in raw_rows]
                elif year >= 2020:
                    raw_rows, ev = self._current_year(year, Path(work_dir) / str(year))
                    if ev.get("status", "").startswith("STOP_"):
                        evidence["years"][str(year)] = ev
                        continue
                    rows = raw_rows
                else:
                    evidence["years"][str(year)] = {"status": "STOP_UNSUPPORTED_YEAR"}
                    continue
            except Exception as exc:
                evidence["years"][str(year)] = {"status": "RETRY_ERROR", "error_type": type(exc).__name__, "error": str(exc)[:500]}
                continue

            matched, basis = self._filter_records(rows, cnpj=cnpj, contractor=contractor)
            ev["matched_records"] = len(matched)
            evidence["years"][str(year)] = ev
            for row in matched:
                item = {**row, "year": year, "match_basis": basis, "stage": self._event_stage(row.get("event"))}
                candidates.append(item)

        stop_states = [v.get("status") for v in evidence["years"].values() if str(v.get("status", "")).startswith("STOP_")]
        retry_states = [v.get("status") for v in evidence["years"].values() if v.get("status") == "RETRY_ERROR"]
        if candidates:
            status = "MATCH_CANDIDATE"
        elif stop_states and len(stop_states) == len(evidence["years"]):
            status = stop_states[0] if len(set(stop_states)) == 1 else "STOP_SOURCE_CONTRACT_UNRESOLVED"
        elif retry_states and len(retry_states) == len(evidence["years"]):
            status = "RETRY_ERROR"
        else:
            status = "NO_MATCH"

        notes = [
            "Correspondência de fornecedor no TCE-SP não prova vínculo com o contrato publicado.",
            "Empenho/liquidação/pagamento só podem ser atribuídos ao objeto após gate de identidade V16/V17.",
        ]
        return ResolutionResult(task["task_id"], "TCE_SP_DESPESAS", status, _now(), candidates, evidence, notes)


class LimeiraContractsResolver:
    """Adaptive, fail-closed resolver for the municipal contracts public search.

    The live portal's search fields are public, but their machine field names are not
    treated as stable documentation. This resolver first inspects the actual HTML form;
    it submits only when year + contract/supplier fields can be unambiguously inferred.
    """

    TOKENS = {
        "year": ("ano", "exercicio", "year"),
        "contract": ("contrato", "documento", "numero", "nro", "nr"),
        "supplier": ("fornecedor", "contratada", "empresa"),
        "object": ("objeto",),
    }

    def __init__(
        self,
        *,
        search_url: str = "https://serv42.limeira.sp.gov.br/ncweb/cns_contratos_web_mestre/",
        timeout: float = 30.0,
        allow_insecure_localhost: bool = False,
        user_agent: str = RESEARCH_USER_AGENT,
    ):
        self.search_url = search_url
        self.timeout = timeout
        self.allow_insecure_localhost = allow_insecure_localhost
        self.user_agent = user_agent
        self._opener = build_opener(HTTPCookieProcessor(CookieJar()))
        _safe_http_url(search_url, allow_insecure_localhost=allow_insecure_localhost)

    def _request(self, url: str, *, method: str = "GET", params: dict | None = None) -> tuple[bytes, dict]:
        _safe_http_url(url, allow_insecure_localhost=self.allow_insecure_localhost)
        params = params or {}
        headers = {"User-Agent": self.user_agent}
        data = None
        if method.upper() == "GET":
            if params:
                url = url + ("&" if "?" in url else "?") + urlencode(params)
        elif method.upper() == "POST":
            data = urlencode(params).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            raise ValueError("UNSUPPORTED_FORM_METHOD")
        req = Request(url, data=data, headers=headers, method=method.upper())
        with self._opener.open(req, timeout=self.timeout) as resp:
            return resp.read(), {"url": resp.geturl(), "http_status": getattr(resp, "status", 200) or 200, "content_type": resp.headers.get("Content-Type")}

    @staticmethod
    def _decode_html(raw: bytes, content_type: str | None) -> str:
        declared = _ascii(content_type)
        if "iso-8859-1" in declared or "latin-1" in declared:
            return raw.decode("latin-1", errors="replace")
        return raw.decode("utf-8", errors="replace")

    @staticmethod
    def _discover_autosubmit_relay(html: str) -> tuple[dict | None, dict]:
        parser = _FormParser()
        parser.feed(html)
        candidates = []
        for form in parser.forms:
            form_name = form.get("name") or form.get("id")
            fields = [f for f in form.get("fields", []) if f.get("name")]
            hidden_only = bool(fields) and all(f.get("type") == "hidden" for f in fields)
            values = {f["name"]: f.get("value", "") for f in fields}
            explicit_submit = bool(form_name and re.search(rf"document\.{re.escape(form_name)}\.submit\s*\(\s*\)", html))
            is_scriptcase_search = values.get("nmgp_opcao") == "pesq" and "script_case_session" in values and "script_case_init" in values
            meta = {
                "form_name": form_name,
                "method": form.get("method"),
                "action": form.get("action"),
                "field_names": sorted(values),
                "hidden_only": hidden_only,
                "explicit_submit": explicit_submit,
                "scriptcase_search_relay": is_scriptcase_search,
            }
            candidates.append(meta)
            if hidden_only and explicit_submit and is_scriptcase_search and form.get("method") == "post":
                meta["params"] = values
        viable = [x for x in candidates if "params" in x]
        evidence = {"forms": len(parser.forms), "candidates": [{k: v for k, v in x.items() if k != "params"} for x in candidates]}
        if len(viable) != 1:
            evidence["status"] = "NO_PROVEN_AUTOSUBMIT_RELAY"
            return None, evidence
        selected = viable[0]
        evidence["status"] = "PASS_PROVEN_AUTOSUBMIT_RELAY"
        evidence["selected"] = {k: v for k, v in selected.items() if k != "params"}
        return selected, evidence

    @classmethod
    def _field_score(cls, field: dict, kind: str) -> int:
        blob = _ascii(" ".join([field.get("name", ""), field.get("id", ""), field.get("placeholder", ""), field.get("title", ""), field.get("context", "")]))
        score = sum(3 for tok in cls.TOKENS[kind] if tok in _ascii(field.get("name", "") + " " + field.get("id", "")))
        score += sum(1 for tok in cls.TOKENS[kind] if tok in blob)
        if field.get("type") in {"hidden", "submit", "button", "image"} and kind in {"year", "contract", "supplier", "object"}:
            score -= 4
        return score

    @classmethod
    def _pick_field(cls, fields: list[dict], kind: str, *, html: str = "") -> tuple[dict | None, dict]:
        scored = sorted(((cls._field_score(f, kind), f) for f in fields if f.get("name")), key=lambda x: x[0], reverse=True)
        positive = [(s, f) for s, f in scored if s > 0]
        if not positive:
            return None, {"kind": kind, "status": "NOT_FOUND"}
        top_score = positive[0][0]
        top = [f for s, f in positive if s == top_score]
        if len(top) != 1:
            names = {str(f.get("name") or "") for f in top}
            bases = {name.removesuffix("_autocomp") for name in names}
            if len(top) == 2 and len(bases) == 1:
                base = next(iter(bases))
                base_field = next((f for f in top if f.get("name") == base), None)
                companion = next((f for f in top if f.get("name") == f"{base}_autocomp"), None)
                base_id = re.escape(str((base_field or {}).get("id") or ""))
                companion_id = re.escape(str((companion or {}).get("id") or ""))
                js_copies_to_base = bool(
                    base_field
                    and companion
                    and base_id
                    and companion_id
                    and re.search(rf'["\']#{companion_id}["\']', html)
                    and re.search(rf'["\']#{base_id}["\']\)\.val\s*\(', html)
                )
                if js_copies_to_base:
                    selected = dict(base_field)
                    selected["paired_field_names"] = [companion["name"]]
                    return selected, {
                        "kind": kind,
                        "status": "FOUND_SCRIPTCASE_AUTOCOMPLETE_PAIR",
                        "score": top_score,
                        "field": base,
                        "companion_field": companion["name"],
                    }
            return None, {"kind": kind, "status": "AMBIGUOUS", "top_score": top_score, "fields": [f.get("name") for f in top]}
        return top[0], {"kind": kind, "status": "FOUND", "score": top_score, "field": top[0].get("name")}

    def _discover_form(self, html: str) -> tuple[dict | None, dict]:
        parser = _FormParser()
        parser.feed(html)
        evidence = {"forms": len(parser.forms), "candidates": []}
        viable = []
        for idx, form in enumerate(parser.forms):
            year, ymeta = self._pick_field(form["fields"], "year", html=html)
            contract, cmeta = self._pick_field(form["fields"], "contract", html=html)
            supplier, smeta = self._pick_field(form["fields"], "supplier", html=html)
            obj, ometa = self._pick_field(form["fields"], "object", html=html)
            meta = {"index": idx, "method": form["method"], "action": form["action"], "year": ymeta, "contract": cmeta, "supplier": smeta, "object": ometa}
            evidence["candidates"].append(meta)
            if year and (contract or supplier):
                viable.append((form, {"year": year, "contract": contract, "supplier": supplier, "object": obj}, meta))
        if len(viable) != 1:
            evidence["status"] = "STOP_CONTRACT_FORM_UNPROVEN"
            evidence["viable_forms"] = len(viable)
            return None, evidence
        form, mapping, meta = viable[0]
        evidence["status"] = "PASS_FORM_DISCOVERY"
        evidence["selected"] = meta
        return {"form": form, "mapping": mapping}, evidence

    @staticmethod
    def _contract_stem(value) -> str | None:
        if not value:
            return None
        m = re.search(r"\d+", str(value))
        return m.group(0) if m else _clean(value)

    @classmethod
    def has_minimum_search_key(cls, task: dict) -> bool:
        """Return whether the public form can receive a bounded search.

        The live form can be submitted by contract number or supplier name. CNPJ,
        object and process remain corroborating signals, but are not used alone to
        broaden the search.
        """
        keys = task.get("match_keys") or {}
        return bool(cls._contract_stem(keys.get("contract_number")) or _clean(keys.get("contractor")))

    @staticmethod
    def _candidate_rows(rows: list[list[str]], keys: dict) -> list[dict]:
        contract_raw = _ascii(keys.get("contract_number"))
        stem = _ascii(LimeiraContractsResolver._contract_stem(keys.get("contract_number")))
        cnpj = _digits(keys.get("cnpj"))
        supplier = _ascii(keys.get("contractor"))
        year = str(keys.get("year") or "")
        out = []
        for idx, cells in enumerate(rows):
            joined = " | ".join(cells)
            text = _ascii(joined)
            digits = _digits(joined)
            signals = []
            if contract_raw and contract_raw in text:
                signals.append("CONTRACT_FULL")
            elif stem and re.search(rf"(?<!\d){re.escape(stem)}(?!\d)", text) and (not year or year in text):
                signals.append("CONTRACT_STEM_PLUS_YEAR")
            if cnpj and cnpj in digits:
                signals.append("CNPJ")
            if supplier and supplier in text:
                signals.append("SUPPLIER_NAME")
            if "CNPJ" in signals or "CONTRACT_FULL" in signals or "CONTRACT_STEM_PLUS_YEAR" in signals:
                out.append({"row_index": idx, "cells": cells, "match_signals": signals})
        return out

    def resolve(self, task: dict, *, work_dir: str | Path | None = None) -> ResolutionResult:
        if task.get("target_source") != "LIMEIRA_CONTRATOS":
            raise ValueError("WRONG_TARGET_SOURCE")
        keys = task.get("match_keys") or {}
        raw, landing_meta = self._request(self.search_url)
        html = self._decode_html(raw, landing_meta.get("content_type"))
        discovered, form_evidence = self._discover_form(html)
        evidence = {"landing": landing_meta, "form_discovery": form_evidence}
        if not discovered:
            return ResolutionResult(task["task_id"], "LIMEIRA_CONTRATOS", "STOP_CONTRACT_FORM_UNPROVEN", _now(), [], evidence, ["Nenhuma submissão foi feita porque o contrato do formulário não ficou inequívoco."])

        contract_key = self._contract_stem(keys.get("contract_number"))
        supplier_key = _clean(keys.get("contractor"))
        if not contract_key and not supplier_key:
            return ResolutionResult(
                task["task_id"],
                "LIMEIRA_CONTRATOS",
                "STOP_MISSING_CONTRACT_OR_SUPPLIER_KEY",
                _now(),
                [],
                evidence,
                ["A tarefa não contém número de contrato nem nome de fornecedor; nenhuma busca ampla por objeto foi submetida."],
            )

        form = discovered["form"]
        mapping = discovered["mapping"]
        params = {}
        for field in form["fields"]:
            name = field.get("name")
            if not name:
                continue
            if field.get("type") == "hidden" and field.get("value"):
                params[name] = field["value"]
            if field.get("type") in {"submit", "button"} and "pesquis" in _ascii(field.get("value")):
                params[name] = field.get("value")
        def set_mapped_value(field: dict | None, value) -> None:
            if not field or value is None:
                return
            params[field["name"]] = str(value)
            for companion_name in field.get("paired_field_names", []):
                params[companion_name] = str(value)

        if mapping.get("year") and keys.get("year"):
            set_mapped_value(mapping["year"], keys["year"])
        if mapping.get("contract") and contract_key:
            set_mapped_value(mapping["contract"], contract_key)
        elif mapping.get("supplier") and supplier_key:
            set_mapped_value(mapping["supplier"], supplier_key)

        action = urljoin(self.search_url, form.get("action") or self.search_url)
        method = (form.get("method") or "get").upper()
        result_raw, result_meta = self._request(action, method=method, params=params)
        result_html = self._decode_html(result_raw, result_meta.get("content_type"))
        table = _TableParser()
        table.feed(result_html)
        evidence["submission"] = {
            "method": method,
            "action": action,
            "http_status": result_meta["http_status"],
            "result_url": result_meta["url"],
            "submitted_field_names": sorted(params),
            "table_rows": len(table.rows),
        }
        if not table.rows:
            relay, relay_evidence = self._discover_autosubmit_relay(result_html)
            evidence["submission"]["autosubmit_relay"] = relay_evidence
            if relay:
                relay_action = urljoin(result_meta["url"], relay.get("action") or result_meta["url"])
                if urlparse(relay_action).netloc != urlparse(self.search_url).netloc:
                    return ResolutionResult(task["task_id"], "LIMEIRA_CONTRATOS", "STOP_CONTRACT_RELAY_ORIGIN_UNPROVEN", _now(), [], evidence, ["O relay do resultado apontou para origem diferente e não foi seguido."])
                relay_raw, relay_meta = self._request(relay_action, method="POST", params=relay["params"])
                result_html = self._decode_html(relay_raw, relay_meta.get("content_type"))
                table = _TableParser()
                table.feed(result_html)
                evidence["submission"]["relay_followup"] = {
                    "method": "POST",
                    "action": relay_action,
                    "http_status": relay_meta["http_status"],
                    "result_url": relay_meta["url"],
                    "submitted_field_names": sorted(relay["params"]),
                    "table_rows": len(table.rows),
                }
        if not table.rows:
            return ResolutionResult(task["task_id"], "LIMEIRA_CONTRATOS", "STOP_CONTRACT_RESULT_SCHEMA_UNPROVEN", _now(), [], evidence, ["A busca foi executada, mas o resultado não expôs tabela interpretável."])
        candidates = self._candidate_rows(table.rows, keys)
        status = "MATCH_CANDIDATE" if candidates else "NO_MATCH"
        notes = ["Registro municipal candidato não prova execução financeira; vínculo posterior continua sujeito aos gates V16/V17."]
        return ResolutionResult(task["task_id"], "LIMEIRA_CONTRATOS", status, _now(), candidates, evidence, notes)


class ReconciliationExecutor:
    IMPLEMENTED_TARGETS = {"LIMEIRA_CONTRATOS", "TCE_SP_DESPESAS"}

    def __init__(self, *, contracts_resolver: LimeiraContractsResolver | None = None, tce_resolver: TcespExpenseResolver | None = None):
        self.contracts = contracts_resolver or LimeiraContractsResolver()
        self.tce = tce_resolver or TcespExpenseResolver()

    def execute_task(self, task: dict, *, work_dir: str | Path) -> ResolutionResult:
        target = task.get("target_source")
        if target == "LIMEIRA_CONTRATOS":
            return self.contracts.resolve(task, work_dir=work_dir)
        if target == "TCE_SP_DESPESAS":
            return self.tce.resolve(task, work_dir=work_dir)
        return ResolutionResult(task["task_id"], str(target), "BLOCKED_RESOLVER_NOT_IMPLEMENTED", _now(), [], {}, ["Resolver ainda não implementado para este target_source."])

    def run_queue(
        self,
        state_db: str | Path,
        *,
        work_dir: str | Path,
        limit: int = 10,
        targets: list[str] | None = None,
        task_ids: list[str] | None = None,
        dry_run: bool = False,
    ) -> dict:
        targets_set = set(targets or self.IMPLEMENTED_TARGETS)
        task_ids_set = set(task_ids) if task_ids is not None else None
        with StateRegistry(state_db) as st:
            ready = [t for t in st.list_reconciliation_tasks(status="READY_SEARCH") if t["target_source"] in targets_set]
            if task_ids_set is not None:
                ready = [t for t in ready if t["task_id"] in task_ids_set]
            ready = ready[: max(0, int(limit))]
            if dry_run:
                return {
                    "status": "PASS_RECONCILIATION_EXECUTOR_DRY_RUN",
                    "selected": len(ready),
                    "tasks": [{"task_id": t["task_id"], "target_source": t["target_source"], "task_type": t["task_type"]} for t in ready],
                }
            results = []
            for task in ready:
                st.update_reconciliation_task(task["task_id"], "RUNNING", {"started_at": _now()})
                try:
                    result = self.execute_task(task, work_dir=Path(work_dir) / task["task_id"])
                except Exception as exc:
                    result = ResolutionResult(
                        task["task_id"], task["target_source"], "RETRY_ERROR", _now(), [],
                        {"error_type": type(exc).__name__, "error": str(exc)[:1000]},
                        ["Falha operacional; nenhuma identidade foi promovida."],
                    )
                st.update_reconciliation_task(task["task_id"], result.status, result.to_dict())
                edges = ReconciliationEvidenceAssembler().assemble(task, result.to_dict())
                for edge in edges:
                    st.upsert_reconciliation_evidence(edge)
                st.event("RECONCILIATION_RESOLVED", {"task_id": task["task_id"], "target_source": task["target_source"], "status": result.status, "evidence_edges": len(edges)})
                payload=result.to_dict(); payload["evidence_edges"]=[e.to_dict() for e in edges]
                results.append(payload)
        counts = {}
        for r in results:
            counts[r["status"]] = counts.get(r["status"], 0) + 1
        return {"status": "PASS_RECONCILIATION_EXECUTION", "selected": len(ready), "results": results, "status_counts": counts}

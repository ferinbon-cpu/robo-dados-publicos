from __future__ import annotations

import hashlib
import json
import re
import socket
from dataclasses import dataclass
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

BASE_URL = "https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata"
RESOURCE = "Dados_Gerais_Siope"
RESOURCE_SIGNATURE = "Dados_Gerais_Siope(Ano_Consulta=@Ano_Consulta,Num_Peri=@Num_Peri,Sig_UF=@Sig_UF)"
ERROR = "STOP_SIOPE_CLIENT"
PASS = "PASS_SIOPE_CLIENT"

PROVEN_DADOS_GERAIS_FIELDS = frozenset(
    {
        "COD_DIGIT",
        "COD_MUNI",
        "COD_UF",
        "COD_VERIFIC",
        "DAT_DECL",
        "DES_DIFE_METO_CALC",
        "DES_JUST_PROB_BALA",
        "DS_JUST_RETIFICACAO",
        "DS_NOTA_RODAPE_FUNDEB",
        "DS_NOTA_RODAPE_RREO",
        "IDN_ASSU_RESP_MTDO_APUR",
        "IDN_DECL_RETI",
        "IDN_METO_LIMI_CONS",
        "IDN_METO_SIOPE_IGUA_TC",
        "IDN_POSS_CERT_TC",
        "IDN_POSS_DECI_JUDI",
        "IDN_TIPO_DECL",
        "NOM_MUNI",
        "NUM_ANO",
        "NUM_CIDE",
        "NUM_CP_FUNDEF",
        "NUM_FPE",
        "NUM_FPM",
        "NUM_FUNDEF",
        "NUM_ICMS",
        "NUM_IPI_EXPO",
        "NUM_IPVA_FUNDEB",
        "NUM_ITCMD_FUNDEB",
        "NUM_ITR",
        "NUM_LC",
        "NUM_PERI",
        "NUM_POPU",
        "NUM_RECI",
        "NUM_SOLI",
        "SIG_UF",
        "TIPO",
        "VAL_DESP_DOTA_ATUA",
        "VAL_DESP_EMPE",
        "VAL_DESP_LIQU",
        "VAL_DESP_ORCA",
        "VAL_DESP_PAGA",
        "VAL_PIB",
        "VAL_PIB_PERCAPTO",
        "VAL_RECE_ORCA",
        "VAL_RECE_PREV_ATUA",
        "VAL_RECE_REAL",
        "VAL_TRANSMISSAO",
        "VL_DESP_DOTA_ATUA_EDU",
        "VL_DESP_EMPE_EDU",
        "VL_DESP_LIQU_EDU",
        "VL_DESP_ORCA_EDU",
        "VL_DESP_PAGA_EDU",
    }
)
_SAFE_UF = re.compile(r"^[A-Z]{2}$")
_SAFE_FIELD = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")


class SiopeClientError(RuntimeError):
    def __init__(self, message: str, *, request_count: int = 0):
        super().__init__(message)
        self.request_count = request_count


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def _default_open(req: Request, timeout: int):
    return build_opener(_NoRedirectHandler()).open(req, timeout=timeout)


def _urlerror_is_timeout(exc: URLError) -> bool:
    return isinstance(getattr(exc, "reason", None), (TimeoutError, socket.timeout))


@dataclass(frozen=True)
class SiopeClientPolicy:
    timeout_seconds: int = 60
    max_response_bytes: int = 2 * 1024 * 1024
    max_attempts: int = 1
    follow_redirects: bool = False
    follow_nextlink: bool = False

    def validate(self) -> None:
        if not (1 <= self.timeout_seconds <= 90):
            raise SiopeClientError(f"{ERROR}_POLICY_TIMEOUT")
        if not (1024 <= self.max_response_bytes <= 4 * 1024 * 1024):
            raise SiopeClientError(f"{ERROR}_POLICY_RESPONSE_LIMIT")
        if self.max_attempts != 1:
            raise SiopeClientError(f"{ERROR}_POLICY_RETRY_NOT_AUTHORIZED")
        if self.follow_redirects:
            raise SiopeClientError(f"{ERROR}_POLICY_REDIRECT_NOT_AUTHORIZED")
        if self.follow_nextlink:
            raise SiopeClientError(f"{ERROR}_POLICY_PAGINATION_NOT_AUTHORIZED")


@dataclass(frozen=True)
class SiopePage:
    records: list[dict]
    status: int
    content_type: str
    response_byte_count: int
    odata_context_present: bool
    nextlink_present: bool
    request_count: int
    response_sha256: str


def build_dados_gerais_url(
    *,
    ano: int,
    periodo: int,
    uf: str,
    municipality_code: int | None = None,
    select_fields: tuple[str, ...] | list[str] | None = None,
) -> str:
    if not isinstance(ano, int) or not (2000 <= ano <= 2100):
        raise SiopeClientError(f"{ERROR}_YEAR")
    if not isinstance(periodo, int) or not (1 <= periodo <= 6):
        raise SiopeClientError(f"{ERROR}_PERIOD")
    uf = str(uf).strip().upper()
    if not _SAFE_UF.fullmatch(uf):
        raise SiopeClientError(f"{ERROR}_UF")

    if municipality_code is not None:
        if not isinstance(municipality_code, int) or not (100000 <= municipality_code <= 999999):
            raise SiopeClientError(f"{ERROR}_MUNICIPALITY_CODE")

    fields: list[str] = []
    if select_fields:
        fields = list(select_fields)
        if len(fields) != len(set(fields)):
            raise SiopeClientError(f"{ERROR}_SELECT_DUPLICATE")
        for field in fields:
            if not isinstance(field, str) or not _SAFE_FIELD.fullmatch(field):
                raise SiopeClientError(f"{ERROR}_SELECT_FIELD_SYNTAX")
            if field not in PROVEN_DADOS_GERAIS_FIELDS:
                raise SiopeClientError(f"{ERROR}_SELECT_FIELD_UNPROVEN")

    parts = [
        f"@Ano_Consulta={ano}",
        f"@Num_Peri={periodo}",
        f"@Sig_UF='{uf}'",
    ]
    if municipality_code is not None:
        parts.append(f"$filter=COD_MUNI%20eq%20{municipality_code}")
    if fields:
        parts.append("$select=" + ",".join(fields))
    parts.append("$format=json")
    return f"{BASE_URL}/{RESOURCE_SIGNATURE}?" + "&".join(parts)


class SiopeClient:
    def __init__(
        self,
        *,
        policy: SiopeClientPolicy | None = None,
        opener: Callable[[Request, int], object] | None = None,
    ):
        self.policy = policy or SiopeClientPolicy()
        self.policy.validate()
        self._opener = opener or _default_open

    def get_dados_gerais_page(
        self,
        *,
        ano: int,
        periodo: int,
        uf: str,
        municipality_code: int | None = None,
        select_fields: tuple[str, ...] | list[str] | None = None,
    ) -> SiopePage:
        url = build_dados_gerais_url(
            ano=ano,
            periodo=periodo,
            uf=uf,
            municipality_code=municipality_code,
            select_fields=select_fields,
        )
        req = Request(
            url,
            headers={
                "User-Agent": "ROBO_DADOS_PUBLICOS/0.8.0 (+public-transparency-research)",
                "Accept": "application/json,application/odata+json;q=0.9",
                "Cache-Control": "no-cache",
            },
            method="GET",
        )
        max_bytes = self.policy.max_response_bytes
        try:
            response = self._opener(req, self.policy.timeout_seconds)
            with response:
                final_url = str(getattr(response, "url", None) or response.geturl())
                if final_url != url:
                    raise SiopeClientError(f"{ERROR}_REDIRECT_OR_URL_DRIFT", request_count=1)
                status = int(getattr(response, "status", None) or response.getcode())
                content_type = str(response.headers.get("Content-Type", "")).split(";", 1)[0].strip().lower()
                raw = response.read(max_bytes + 1)
        except SiopeClientError:
            raise
        except HTTPError as exc:
            code = int(getattr(exc, "code", 0) or 0)
            if 300 <= code < 400:
                raise SiopeClientError(f"{ERROR}_REDIRECT_BLOCKED", request_count=1) from None
            raise SiopeClientError(f"{ERROR}_HTTP_{code}", request_count=1) from None
        except (TimeoutError, socket.timeout):
            raise SiopeClientError(f"{ERROR}_TIMEOUT", request_count=1) from None
        except URLError as exc:
            code = "TIMEOUT" if _urlerror_is_timeout(exc) else "NETWORK"
            raise SiopeClientError(f"{ERROR}_{code}", request_count=1) from None
        except OSError:
            raise SiopeClientError(f"{ERROR}_NETWORK", request_count=1) from None

        if len(raw) > max_bytes:
            raise SiopeClientError(f"{ERROR}_RESPONSE_TOO_LARGE", request_count=1)
        if status != 200:
            raise SiopeClientError(f"{ERROR}_HTTP_STATUS", request_count=1)
        if content_type not in {"application/json", "application/odata+json"}:
            raise SiopeClientError(f"{ERROR}_CONTENT_TYPE", request_count=1)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise SiopeClientError(f"{ERROR}_INVALID_JSON", request_count=1) from None
        if not isinstance(payload, dict):
            raise SiopeClientError(f"{ERROR}_TOP_LEVEL_OBJECT_REQUIRED", request_count=1)
        value = payload.get("value")
        if not isinstance(value, list):
            raise SiopeClientError(f"{ERROR}_VALUE_LIST_REQUIRED", request_count=1)
        if any(not isinstance(record, dict) for record in value):
            raise SiopeClientError(f"{ERROR}_RECORD_OBJECT_REQUIRED", request_count=1)

        nextlink_present = "@odata.nextLink" in payload
        if nextlink_present and not self.policy.follow_nextlink:
            raise SiopeClientError(f"{ERROR}_NEXTLINK_REQUIRES_FUTURE_AUTHORIZATION", request_count=1)

        return SiopePage(
            records=value,
            status=status,
            content_type=content_type,
            response_byte_count=len(raw),
            odata_context_present="@odata.context" in payload,
            nextlink_present=nextlink_present,
            request_count=1,
            response_sha256=hashlib.sha256(raw).hexdigest(),
        )

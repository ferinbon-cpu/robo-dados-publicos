from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

from .siope_download_route_discovery import (
    ReadOnlyDeclaredResourceClient,
    SiopeDownloadRouteDiscoveryError,
)

ERROR = "STOP_SIOPE_PUBLIC_INDEXED_GET_CONTRACT"


class SiopePublicIndexedGetContractError(RuntimeError):
    def __init__(self, message: str, *, diagnostics: dict | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


def _validate_config(config: dict) -> None:
    exact = {
        "gate_id": "M7_SIOPE_PUBLIC_INDEXED_GET_CONTRACT_GATE_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "mode": "EXACT_PUBLICLY_INDEXED_GET_CONTRACT_VERIFICATION",
        "expected_path": "/siope/dadosInformadosMunicipio.do",
        "expected_page_heading": "Dados Informados pelos Municípios",
        "success_condition": "INDEXED_GET_ROUTE_RETURNS_EXPECTED_PUBLIC_SIOPE_SURFACE",
        "next_gate_if_no_human_challenge": "M7_SIOPE_PUBLIC_GET_RUNTIME_ROUTE_DIAGNOSTICS_0_8_0",
        "next_gate_if_human_challenge": "M7_SIOPE_MANUAL_ASSISTED_ACQUISITION_DESIGN_0_8_0",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
    }
    for key, value in exact.items():
        if config.get(key) != value:
            raise SiopePublicIndexedGetContractError(f"{ERROR}_CONFIG_{key.upper()}")
    if config.get("allowed_hosts") != ["www.fnde.gov.br"]:
        raise SiopePublicIndexedGetContractError(f"{ERROR}_CONFIG_ALLOWED_HOSTS")
    if config.get("expected_query_keys") != [
        "acao", "admin", "cod_muni", "cod_uf", "num_ano", "num_peri", "pag", "tp_relatorio"
    ]:
        raise SiopePublicIndexedGetContractError(f"{ERROR}_CONFIG_QUERY_KEYS")
    if config.get("expected_loading_markers") != ["Buscando planilhas", "Buscando dados"]:
        raise SiopePublicIndexedGetContractError(f"{ERROR}_CONFIG_LOADING_MARKERS")
    if config.get("captcha_component_markers") != ["captcha", "recaptcha", "g-recaptcha", "hcaptcha"]:
        raise SiopePublicIndexedGetContractError(f"{ERROR}_CONFIG_CAPTCHA_COMPONENT_MARKERS")
    if config.get("human_challenge_required_markers") != ["É necessário validar o captcha"]:
        raise SiopePublicIndexedGetContractError(f"{ERROR}_CONFIG_HUMAN_CHALLENGE_MARKERS")
    if config.get("limits") != {"max_response_bytes": 1048576}:
        raise SiopePublicIndexedGetContractError(f"{ERROR}_CONFIG_LIMITS")
    rules = config.get("verification_rules") or {}
    if rules != {
        "methods": ["GET"],
        "send_exact_indexed_example_only": True,
        "send_pilot_limeira_values": False,
        "submit_forms": False,
        "bypass_captcha": False,
        "authenticate": False,
        "capture_credentials": False,
        "capture_cookies": False,
        "persist_response_body": False,
        "persist_query_values": False,
        "download_artifacts": False,
        "head_request": False,
    }:
        raise SiopePublicIndexedGetContractError(f"{ERROR}_CONFIG_RULES")

    raw = str(config.get("public_indexed_example_url", ""))
    parsed = urlparse(raw)
    if parsed.scheme != "https" or parsed.hostname != "www.fnde.gov.br" or parsed.path != config["expected_path"]:
        raise SiopePublicIndexedGetContractError(f"{ERROR}_CONFIG_EXAMPLE_URL")
    keys = sorted({key for key, _ in parse_qsl(parsed.query, keep_blank_values=True)})
    if keys != config["expected_query_keys"]:
        raise SiopePublicIndexedGetContractError(f"{ERROR}_CONFIG_EXAMPLE_QUERY_KEYS")


def load_public_indexed_get_contract_config(path: str | Path) -> dict:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    _validate_config(config)
    return config


def _marker_present(body: str, markers: list[str]) -> bool:
    lower = body.casefold()
    return any(marker.casefold() in lower for marker in markers)


def _surface(url: str) -> dict:
    parsed = urlparse(url)
    keys = sorted({key[:128] for key, _ in parse_qsl(parsed.query, keep_blank_values=True) if key})
    return {
        "scheme": parsed.scheme,
        "host": parsed.hostname or "",
        "path": parsed.path or "/",
        "query_present": bool(parsed.query),
        "query_keys": keys,
    }


def verify_public_indexed_get_contract(config: dict, *, client: ReadOnlyDeclaredResourceClient | None = None) -> dict:
    _validate_config(config)
    allowed_hosts = tuple(config["allowed_hosts"])
    client = client or ReadOnlyDeclaredResourceClient(allowed_hosts=allowed_hosts)
    try:
        response = client.get_text(
            config["public_indexed_example_url"],
            max_bytes=int(config["limits"]["max_response_bytes"]),
            allowed_content_types=("text/html", "application/xhtml+xml"),
        )
    except SiopeDownloadRouteDiscoveryError as exc:
        raise SiopePublicIndexedGetContractError(f"{ERROR}_{exc}") from None

    final = _surface(response.url)
    common_diagnostics = {
        "network_called": True,
        "response_status": response.status,
        "content_type": response.content_type,
        "response_byte_count": response.byte_count,
        "final_surface": final,
    }
    if final["path"] != config["expected_path"]:
        raise SiopePublicIndexedGetContractError(
            f"{ERROR}_FINAL_PATH",
            diagnostics=common_diagnostics,
        )
    if final["query_keys"] != config["expected_query_keys"]:
        raise SiopePublicIndexedGetContractError(
            f"{ERROR}_FINAL_QUERY_KEYS",
            diagnostics=common_diagnostics,
        )

    body = response.body
    lower = body.casefold()
    heading_present = config["expected_page_heading"].casefold() in lower
    loading = {
        marker: marker.casefold() in lower
        for marker in config["expected_loading_markers"]
    }
    stable_surface_markers_present = all(loading.values())
    if not heading_present and not stable_surface_markers_present:
        raise SiopePublicIndexedGetContractError(
            f"{ERROR}_UNEXPECTED_SURFACE",
            diagnostics={
                **common_diagnostics,
                "expected_heading_present": False,
                "stable_loading_marker_count": sum(1 for present in loading.values() if present),
                "stable_loading_marker_total": len(loading),
            },
        )

    captcha_component = _marker_present(body, config["captcha_component_markers"])
    challenge_required = _marker_present(body, config["human_challenge_required_markers"])
    if not challenge_required:
        challenge_required = "validar o captcha" in lower
    next_gate = config["next_gate_if_human_challenge"] if challenge_required else config["next_gate_if_no_human_challenge"]
    return {
        "status": "PASS_M7_SIOPE_PUBLIC_INDEXED_GET_CONTRACT_GATE",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "contract_status": "EXPECTED_PUBLIC_SIOPE_SURFACE_OBSERVED",
        "network_called": True,
        "network_method": "GET_ONLY",
        "indexed_example_query_sent": True,
        "pilot_limeira_values_sent": False,
        "response_status": response.status,
        "content_type": response.content_type,
        "response_byte_count": response.byte_count,
        "final_surface": final,
        "expected_heading_present": heading_present,
        "surface_identity_basis": "HEADING" if heading_present else "ASCII_LOADING_MARKERS",
        "loading_markers_present": loading,
        "captcha_component_present": captcha_component,
        "human_challenge_required_message_present": challenge_required,
        "human_challenge_active": challenge_required,
        "form_submission": False,
        "captcha_bypass": False,
        "authentication_performed": False,
        "credentials_captured": False,
        "cookies_captured": False,
        "response_body_persisted": False,
        "query_values_persisted": False,
        "artifact_downloaded": False,
        "head_request_performed": False,
        "remote_writes": "NONE",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": next_gate,
    }

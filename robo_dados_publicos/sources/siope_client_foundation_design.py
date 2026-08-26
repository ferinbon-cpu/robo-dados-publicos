from __future__ import annotations

from robo_dados_publicos.sources.siope_client import (
    PROVEN_DADOS_GERAIS_FIELDS,
    SiopeClientError,
    SiopeClientPolicy,
    build_dados_gerais_url,
)

ERROR = "STOP_M7_SIOPE_CLIENT_FOUNDATION_DESIGN"
PASS = "PASS_M7_SIOPE_CLIENT_FOUNDATION_DESIGN"


class SiopeClientFoundationDesignError(RuntimeError):
    pass


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeClientFoundationDesignError(f"{ERROR}_{code}")


def run_design(config: dict) -> dict:
    exact = {
        "gate_id": "M7_SIOPE_CLIENT_FOUNDATION_DESIGN_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "mode": "OFFLINE_SIOPE_CLIENT_FOUNDATION_FROM_PROVEN_LIMEIRA_CONTRACT",
        "network_called": False,
        "proven_resource": "Dados_Gerais_Siope",
        "allowed_operational_resources": ["Dados_Gerais_Siope"],
        "parameter_aliases": ["Ano_Consulta", "Num_Peri", "Sig_UF"],
        "server_side_municipality_filter": "COD_MUNI eq <six_digit_code>",
        "format": "json",
        "url_space_encoding": "%20",
        "retry_status": "DESIGNED_NOT_AUTHORIZED",
        "pagination_status": "DETECTED_NOT_AUTHORIZED",
        "cache_status": "PLANNED_NOT_IMPLEMENTED",
        "crosswalk_status": "PLANNED_NOT_IMPLEMENTED",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_LIVE_VALIDATION_0_8_0",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, key.upper())

    _require(
        config.get("pinned_pilot_review_gate"),
        "M7_SIOPE_OFFICIAL_OLINDA_LIMEIRA_PILOT_READONLY_GET_REVIEW_0_8_0",
        "PINNED_REVIEW",
    )
    _require(
        config.get("selected_identity_fields"),
        ["COD_MUNI", "NOM_MUNI", "NUM_ANO", "NUM_PERI", "SIG_UF"],
        "IDENTITY_FIELDS",
    )
    _require(
        config.get("live_validation"),
        {
            "ano": 2024,
            "periodo": 6,
            "uf": "SP",
            "municipality_code": 352690,
            "expected_municipality_name": "LIMEIRA",
            "request_count": 1,
            "max_value_count": 1,
            "persist_records": False,
            "follow_redirects": False,
            "follow_nextlink": False,
            "max_attempts": 1,
            "timeout_seconds": 60,
        },
        "LIVE_VALIDATION",
    )
    expected_url = (
        "https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata/"
        "Dados_Gerais_Siope(Ano_Consulta=@Ano_Consulta,Num_Peri=@Num_Peri,Sig_UF=@Sig_UF)"
        "?@Ano_Consulta=2024&@Num_Peri=6&@Sig_UF='SP'"
        "&$filter=COD_MUNI%20eq%20352690"
        "&$select=COD_MUNI,NOM_MUNI,NUM_ANO,NUM_PERI,SIG_UF"
        "&$format=json"
    )
    _require(config.get("expected_proven_limeira_url"), expected_url, "PROVEN_URL")
    try:
        built = build_dados_gerais_url(
            ano=2024,
            periodo=6,
            uf="SP",
            municipality_code=352690,
            select_fields=tuple(config["selected_identity_fields"]),
        )
        SiopeClientPolicy(
            timeout_seconds=60,
            max_response_bytes=65536,
            max_attempts=1,
            follow_redirects=False,
            follow_nextlink=False,
        ).validate()
    except SiopeClientError as exc:
        raise SiopeClientFoundationDesignError(f"{ERROR}_CLIENT_{exc}") from None

    _require(built, expected_url, "BUILDER_DOES_NOT_REPRODUCE_PROVEN_URL")
    if "+" in built or "%20" not in built:
        raise SiopeClientFoundationDesignError(f"{ERROR}_ENCODING")
    if not set(config["selected_identity_fields"]).issubset(PROVEN_DADOS_GERAIS_FIELDS):
        raise SiopeClientFoundationDesignError(f"{ERROR}_UNPROVEN_FIELD")

    return {
        "status": PASS,
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "mode": config["mode"],
        "network_called": False,
        "builder_reproduces_proven_limeira_url": True,
        "resource_allowlist_count": 1,
        "proven_schema_field_count": len(PROVEN_DADOS_GERAIS_FIELDS),
        "selected_identity_field_count": len(config["selected_identity_fields"]),
        "percent20_filter_encoding_enforced": True,
        "plus_filter_encoding_rejected": True,
        "max_attempts": 1,
        "redirects_allowed": False,
        "pagination_follow_allowed": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }

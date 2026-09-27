from __future__ import annotations

import hashlib
import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

from robo_dados_publicos.sources.siope_client_limeira_historical_2023_p6_silver_drive_persistence import (
    HistoricalSilverDrivePersistenceError,
    _build_silver_payload,
    load_json as load_silver_json,
)

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_GOLD_TRANSFORM_PREVIEW"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_GOLD_TRANSFORM_PREVIEW"
PERCENT_QUANTUM = Decimal("0.0001")
PER_CAPITA_QUANTUM = Decimal("0.01")


class HistoricalGoldTransformPreviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise HistoricalGoldTransformPreviewError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise HistoricalGoldTransformPreviewError(f"{ERROR}_{code}")


def _canonical_bytes(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _decimal_field(data: dict, field: str, *, positive: bool = False) -> Decimal:
    value = data.get(field)
    if value is None or isinstance(value, bool):
        raise HistoricalGoldTransformPreviewError(f"{ERROR}_{field}_VALUE")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise HistoricalGoldTransformPreviewError(f"{ERROR}_{field}_VALUE") from exc
    if not number.is_finite() or number < 0 or (positive and number <= 0):
        raise HistoricalGoldTransformPreviewError(f"{ERROR}_{field}_RANGE")
    return number


def _pct(numerator: Decimal, denominator: Decimal) -> str:
    if denominator <= 0:
        raise HistoricalGoldTransformPreviewError(f"{ERROR}_ZERO_DENOMINATOR")
    return str((numerator / denominator * Decimal("100")).quantize(PERCENT_QUANTUM, rounding=ROUND_HALF_UP))


def _per_capita(amount: Decimal, population: Decimal) -> str:
    if population <= 0:
        raise HistoricalGoldTransformPreviewError(f"{ERROR}_ZERO_POPULATION")
    return str((amount / population).quantize(PER_CAPITA_QUANTUM, rounding=ROUND_HALF_UP))


def validate_config(config: dict) -> dict:
    expected = {
        "compliance_claims_authorized": False,
        "drive_network_authorized": False,
        "drive_write_count": 0,
        "expected_gold_payload_bytes": 1623,
        "expected_gold_payload_sha256": "a4da994fd2a04ef0b3133d9a20855e6809922f19366075d48aab3296ca488272",
        "expected_metric_ids": [
            "receita_realizada_sobre_previsao_atualizada_pct",
            "despesa_paga_sobre_dotacao_atualizada_pct",
            "despesa_educacao_paga_sobre_dotacao_atualizada_educacao_pct",
            "participacao_educacao_na_despesa_empenhada_pct",
            "participacao_educacao_na_despesa_liquidada_pct",
            "participacao_educacao_na_despesa_paga_pct",
            "despesa_total_paga_por_habitante",
            "despesa_educacao_paga_por_habitante",
        ],
        "expected_record_count": 1,
        "expected_schema_key_count": 52,
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_GOLD_TRANSFORM_PREVIEW_0_8_0",
        "gold_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_ARITHMETIC_SUMMARY_GOLD_V1",
        "gold_persistence_authorized": False,
        "gold_remote_write_authorized": False,
        "historical_collection_authorized": False,
        "imputation_authorized": False,
        "manual_confirmation_required": True,
        "mode": "OFFLINE_PINNED_VERIFIED_HISTORICAL_SILVER_ARITHMETIC_GOLD_PREVIEW",
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_GOLD_TRANSFORM_REVIEW_0_8_0",
        "processing_authorized": False,
        "readback_review_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_SILVER_DRIVE_READBACK_REVIEW_0_8_0",
        "record_sha256": "8b63fd15413c3ab9ca5f82749ea5d89e5a1c92b06e7b80cb6def7af60b769919",
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "semantic_scope": "DERIVED_ARITHMETIC_ONLY_FROM_SIOPE_DADOS_GERAIS",
        "silver_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_HISTORICAL_VALIDATED_RECORD_SILVER_V1",
        "silver_payload_bytes": 1830,
        "silver_payload_sha256": "6d5c6a96f7a0b57b06ad6a6b7078a46ba58ef5fd1242f08c3de8c7aa5f2c87fb",
        "silver_persistence_config_path": "config/source_expansion.siope_client_limeira_historical_2023_p6_silver_drive_persistence.json",
        "software_version": "0.8.0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "source_network_authorized": False,
    }
    _require(config, expected, "CONFIG_DRIFT")
    return {
        "compliance_claims_authorized": False,
        "drive_network_called": False,
        "drive_write_count": 0,
        "gold_persistence_authorized": False,
        "gold_remote_write_authorized": False,
        "historical_collection_authorized": False,
        "imputation_performed": False,
        "network_called": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "source_network_called": False,
        "status": f"{PASS}_DESIGN",
    }


def build_preview(config: dict, *, root: str | Path) -> tuple[dict, dict]:
    validate_config(config)
    root_path = Path(root)
    try:
        silver_config = load_silver_json(root_path / config["silver_persistence_config_path"])
        silver_payload = _build_silver_payload(silver_config, root=root_path)
    except (HistoricalSilverDrivePersistenceError, OSError, json.JSONDecodeError) as exc:
        raise HistoricalGoldTransformPreviewError(f"{ERROR}_SILVER_PREREQUISITE") from exc

    silver_bytes = _canonical_bytes(silver_payload)
    _require(len(silver_bytes), config["silver_payload_bytes"], "SILVER_BYTES")
    _require(hashlib.sha256(silver_bytes).hexdigest(), config["silver_payload_sha256"], "SILVER_SHA256")
    _require(silver_payload.get("silver_contract"), config["silver_contract"], "SILVER_CONTRACT")
    _require(silver_payload.get("schema_key_count"), 52, "SILVER_SCHEMA")
    _require(silver_payload.get("provenance", {}).get("record_sha256"), config["record_sha256"], "RECORD_SHA256")

    data = silver_payload.get("data")
    if not isinstance(data, dict) or len(data) != 52:
        raise HistoricalGoldTransformPreviewError(f"{ERROR}_SILVER_DATA_SCHEMA")
    _require(data.get("COD_MUNI"), 352690, "MUNICIPALITY")
    _require(data.get("NOM_MUNI"), "Limeira", "MUNICIPALITY_NAME")
    _require(data.get("SIG_UF"), "SP", "STATE")
    _require(data.get("NUM_ANO"), 2023, "YEAR")
    _require(data.get("NUM_PERI"), 6, "PERIOD")

    facts = {
        "VAL_RECE_PREV_ATUA": _decimal_field(data, "VAL_RECE_PREV_ATUA", positive=True),
        "VAL_RECE_REAL": _decimal_field(data, "VAL_RECE_REAL"),
        "VAL_DESP_DOTA_ATUA": _decimal_field(data, "VAL_DESP_DOTA_ATUA", positive=True),
        "VAL_DESP_EMPE": _decimal_field(data, "VAL_DESP_EMPE", positive=True),
        "VAL_DESP_LIQU": _decimal_field(data, "VAL_DESP_LIQU", positive=True),
        "VAL_DESP_PAGA": _decimal_field(data, "VAL_DESP_PAGA", positive=True),
        "VL_DESP_DOTA_ATUA_EDU": _decimal_field(data, "VL_DESP_DOTA_ATUA_EDU", positive=True),
        "VL_DESP_EMPE_EDU": _decimal_field(data, "VL_DESP_EMPE_EDU"),
        "VL_DESP_LIQU_EDU": _decimal_field(data, "VL_DESP_LIQU_EDU"),
        "VL_DESP_PAGA_EDU": _decimal_field(data, "VL_DESP_PAGA_EDU"),
        "NUM_POPU": _decimal_field(data, "NUM_POPU", positive=True),
    }

    metrics = {
        "receita_realizada_sobre_previsao_atualizada_pct": _pct(facts["VAL_RECE_REAL"], facts["VAL_RECE_PREV_ATUA"]),
        "despesa_paga_sobre_dotacao_atualizada_pct": _pct(facts["VAL_DESP_PAGA"], facts["VAL_DESP_DOTA_ATUA"]),
        "despesa_educacao_paga_sobre_dotacao_atualizada_educacao_pct": _pct(facts["VL_DESP_PAGA_EDU"], facts["VL_DESP_DOTA_ATUA_EDU"]),
        "participacao_educacao_na_despesa_empenhada_pct": _pct(facts["VL_DESP_EMPE_EDU"], facts["VAL_DESP_EMPE"]),
        "participacao_educacao_na_despesa_liquidada_pct": _pct(facts["VL_DESP_LIQU_EDU"], facts["VAL_DESP_LIQU"]),
        "participacao_educacao_na_despesa_paga_pct": _pct(facts["VL_DESP_PAGA_EDU"], facts["VAL_DESP_PAGA"]),
        "despesa_total_paga_por_habitante": _per_capita(facts["VAL_DESP_PAGA"], facts["NUM_POPU"]),
        "despesa_educacao_paga_por_habitante": _per_capita(facts["VL_DESP_PAGA_EDU"], facts["NUM_POPU"]),
    }
    _require(list(metrics), config["expected_metric_ids"], "METRIC_IDS")

    gold_payload = {
        "gold_contract": config["gold_contract"],
        "identity": dict(silver_payload["identity"]),
        "input_facts": {key: str(value) for key, value in facts.items()},
        "metrics": metrics,
        "provenance": {
            "record_sha256": config["record_sha256"],
            "silver_contract": config["silver_contract"],
            "silver_payload_sha256": config["silver_payload_sha256"],
            "source_id": config["source_id"],
        },
        "semantic_scope": {
            "fiscal_audit_conclusion": False,
            "fundeb_compliance_conclusion": False,
            "imputation_performed": False,
            "kind": config["semantic_scope"],
            "mde_compliance_conclusion": False,
        },
        "software_version": config["software_version"],
    }
    gold_bytes = _canonical_bytes(gold_payload)
    gold_sha256 = hashlib.sha256(gold_bytes).hexdigest()
    _require(len(gold_bytes), config["expected_gold_payload_bytes"], "GOLD_BYTES")
    _require(gold_sha256, config["expected_gold_payload_sha256"], "GOLD_SHA256")

    result = {
        "compliance_claims_authorized": False,
        "drive_network_called": False,
        "drive_write_count": 0,
        "gate_id": config["gate_id"],
        "gold_contract": config["gold_contract"],
        "gold_payload_bytes": len(gold_bytes),
        "gold_payload_persisted": False,
        "gold_payload_sha256": gold_sha256,
        "gold_persistence_authorized": False,
        "gold_remote_write_authorized": False,
        "historical_collection_authorized": False,
        "imputation_performed": False,
        "metric_count": len(metrics),
        "metrics": metrics,
        "network_called": False,
        "next_gate": config["next_gate"],
        "processing_authorized": False,
        "record_count": 1,
        "record_sha256": config["record_sha256"],
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "schema_key_count": 52,
        "semantic_scope": config["semantic_scope"],
        "silver_payload_sha256": config["silver_payload_sha256"],
        "source_network_called": False,
        "status": PASS,
    }
    return gold_payload, result

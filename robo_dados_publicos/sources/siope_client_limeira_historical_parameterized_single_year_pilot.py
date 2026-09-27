from __future__ import annotations

import hashlib
import json
import tempfile
import unicodedata
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

from robo_dados_publicos.sources.siope_client import (
    PROVEN_DADOS_GERAIS_FIELDS,
    SiopeClient,
    SiopeClientPolicy,
)
from robo_dados_publicos.storage.drive_rest import DriveRESTClient, OAuthCredentials, TokenProvider

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_PARAMETERIZED_SINGLE_YEAR_PILOT"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_PARAMETERIZED_SINGLE_YEAR_PILOT"
PERCENT_QUANTUM = Decimal("0.0001")
PER_CAPITA_QUANTUM = Decimal("0.01")
EXPECTED_STAGES = (
    "SOURCE_CAPTURE",
    "BRONZE_CREATE_ONLY",
    "BRONZE_READBACK",
    "SILVER_LOSSLESS",
    "SILVER_CREATE_ONLY",
    "SILVER_READBACK",
    "GOLD_ARITHMETIC",
    "GOLD_CREATE_ONLY",
    "GOLD_READBACK",
)


class HistoricalParameterizedSingleYearPilotError(RuntimeError):
    pass


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise HistoricalParameterizedSingleYearPilotError(f"{ERROR}_{code}")


def _canonical_bytes(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()  # noqa: S324


def _normalize_name(value) -> str:  # noqa: ANN001
    text = unicodedata.normalize("NFKD", str(value).strip())
    return "".join(ch for ch in text if not unicodedata.combining(ch)).upper()


def _as_int(value, code: str) -> int:  # noqa: ANN001
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        raise HistoricalParameterizedSingleYearPilotError(f"{ERROR}_{code}") from None


def _decimal_field(data: dict, field: str, *, positive: bool = False) -> Decimal:
    value = data.get(field)
    if value is None or isinstance(value, bool):
        raise HistoricalParameterizedSingleYearPilotError(f"{ERROR}_{field}_VALUE")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise HistoricalParameterizedSingleYearPilotError(f"{ERROR}_{field}_VALUE") from None
    if not number.is_finite() or number < 0 or (positive and number <= 0):
        raise HistoricalParameterizedSingleYearPilotError(f"{ERROR}_{field}_RANGE")
    return number


def _pct(numerator: Decimal, denominator: Decimal) -> str:
    if denominator <= 0:
        raise HistoricalParameterizedSingleYearPilotError(f"{ERROR}_ZERO_DENOMINATOR")
    return str((numerator / denominator * Decimal("100")).quantize(PERCENT_QUANTUM, rounding=ROUND_HALF_UP))


def _per_capita(amount: Decimal, population: Decimal) -> str:
    if population <= 0:
        raise HistoricalParameterizedSingleYearPilotError(f"{ERROR}_ZERO_POPULATION")
    return str((amount / population).quantize(PER_CAPITA_QUANTUM, rounding=ROUND_HALF_UP))


def validate_config(config: dict, *, root: str | Path) -> dict:
    expected = {
        "batch_live_authorized": False,
        "bronze_folder_id": "18yR-e6I1VCiy7XqG7Zhr0vUIJF0qA_MG",
        "compliance_claims_authorized": False,
        "create_only": True,
        "delete_authorized": False,
        "drive_download_count": 3,
        "drive_write_count": 3,
        "dry_run_evidence": {
            "blob_sha": "241ebfd22f123ae891fcba013a0061d3ac70efd6",
            "path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_PARAMETERIZED_PIPELINE_DRY_RUN_RUN_1_0.8.0.json",
            "run_id": 33119681850,
        },
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_PARAMETERIZED_SINGLE_YEAR_PILOT_0_8_0",
        "gold_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_ARITHMETIC_SUMMARY_GOLD_V1",
        "gold_folder_id": "1hAmQNBnY6MNBtyr14ACfVfRkmWhsoRq4",
        "historical_collection_authorized": False,
        "imputation_authorized": False,
        "individual_year_workflow_duplication_authorized": False,
        "manual_confirmation_required": True,
        "mime_type": "application/json",
        "mode": "BOUNDED_LIVE_PARAMETERIZED_SINGLE_YEAR_END_TO_END_PILOT",
        "municipality_code": 352690,
        "municipality_name": "Limeira",
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_BOUNDED_BATCH_AUTHORIZATION_0_8_0",
        "overwrite_authorized": False,
        "pagination_authorized": False,
        "period": 6,
        "pilot_year": 2021,
        "recurrence_authorized": False,
        "replace_authorized": False,
        "retry_authorized": False,
        "schedule_enabled": False,
        "schema_key_count": 52,
        "silver_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_HISTORICAL_VALIDATED_RECORD_SILVER_V1",
        "silver_folder_id": "1_wl3Y90-RYKSBXUg53My5K6lxCUnIBNo",
        "software_version": "0.8.0",
        "source_get_count": 1,
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "stage_count": 9,
        "uf": "SP",
    }
    _require(config, expected, "CONFIG_DRIFT")
    _require(len(PROVEN_DADOS_GERAIS_FIELDS), 52, "SCHEMA_ALLOWLIST_COUNT")
    meta = config["dry_run_evidence"]
    path = Path(root) / meta["path"]
    raw = path.read_bytes()
    _require(_git_blob_sha(raw), meta["blob_sha"], "DRY_RUN_EVIDENCE_BLOB_SHA")
    evidence = json.loads(raw.decode("utf-8"))
    _require(evidence.get("run_id"), meta["run_id"], "DRY_RUN_EVIDENCE_RUN")
    _require(evidence.get("status"), "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_PARAMETERIZED_PIPELINE_DRY_RUN", "DRY_RUN_EVIDENCE_STATUS")
    _require(evidence.get("pilot_year"), config["pilot_year"], "DRY_RUN_EVIDENCE_PILOT_YEAR")
    _require(evidence.get("stage_count_per_year"), 9, "DRY_RUN_EVIDENCE_STAGE_COUNT")
    _require(evidence.get("stage_contract_equivalent"), True, "DRY_RUN_EVIDENCE_STAGE_EQUIVALENCE")
    _require(evidence.get("source_url_template_equivalent"), True, "DRY_RUN_EVIDENCE_URL_EQUIVALENCE")
    _require(evidence.get("network_called"), False, "DRY_RUN_EVIDENCE_NETWORK")
    _require(evidence.get("drive_called"), False, "DRY_RUN_EVIDENCE_DRIVE")
    _require(evidence.get("mutation_count"), 0, "DRY_RUN_EVIDENCE_MUTATION")
    _require(evidence.get("batch_live_authorized"), False, "DRY_RUN_EVIDENCE_BATCH")
    return {"status": f"{PASS}_DESIGN", "pilot_year": config["pilot_year"], "stage_count": len(EXPECTED_STAGES)}


def _record_from_page(config: dict, page) -> dict:  # noqa: ANN001
    _require(page.request_count, 1, "SOURCE_REQUEST_COUNT")
    _require(page.status, 200, "SOURCE_HTTP")
    _require(page.nextlink_present, False, "SOURCE_NEXTLINK")
    _require(len(page.records), 1, "SOURCE_RECORD_COUNT")
    record = page.records[0]
    _require(set(record), set(PROVEN_DADOS_GERAIS_FIELDS), "SOURCE_SCHEMA")
    _require(_as_int(record.get("COD_MUNI"), "COD_MUNI"), config["municipality_code"], "SOURCE_MUNICIPALITY")
    _require(_normalize_name(record.get("NOM_MUNI")), _normalize_name(config["municipality_name"]), "SOURCE_MUNICIPALITY_NAME")
    _require(_as_int(record.get("NUM_ANO"), "NUM_ANO"), config["pilot_year"], "SOURCE_YEAR")
    _require(_as_int(record.get("NUM_PERI"), "NUM_PERI"), config["period"], "SOURCE_PERIOD")
    _require(str(record.get("SIG_UF", "")).strip().upper(), config["uf"], "SOURCE_UF")
    return record


def _build_payloads(config: dict, record: dict, page) -> dict:  # noqa: ANN001
    record_bytes = _canonical_bytes(record)
    record_sha256 = hashlib.sha256(record_bytes).hexdigest()
    manifest = {
        "bronze_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_HISTORICAL_SINGLE_RECORD_V1",
        "historical_collection_authorized": False,
        "municipality_code": config["municipality_code"],
        "nextlink_url_persisted": False,
        "period": config["period"],
        "processing_authorized": False,
        "record_count": 1,
        "record_sha256": record_sha256,
        "recurrence_authorized": False,
        "resource": "Dados_Gerais_Siope",
        "response_byte_count": page.response_byte_count,
        "response_envelope_persisted": False,
        "response_sha256": page.response_sha256,
        "schema_key_count": 52,
        "software_version": config["software_version"],
        "source_id": config["source_id"],
        "state": config["uf"],
        "year": config["pilot_year"],
    }
    bronze = {
        "bronze_bundle_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_HISTORICAL_SINGLE_RECORD_DRIVE_BUNDLE_V1",
        "manifest": manifest,
        "record": record,
    }
    bronze_bytes = _canonical_bytes(bronze)
    bronze_sha256 = hashlib.sha256(bronze_bytes).hexdigest()

    identity = {
        "municipality_code": config["municipality_code"],
        "municipality_name": config["municipality_name"],
        "period": config["period"],
        "resource": "Dados_Gerais_Siope",
        "state": config["uf"],
        "year": config["pilot_year"],
    }
    silver = {
        "data": record,
        "identity": identity,
        "provenance": {
            "bronze_contract": manifest["bronze_contract"],
            "record_sha256": record_sha256,
            "source_bundle_sha256": bronze_sha256,
            "source_id": config["source_id"],
        },
        "schema_key_count": 52,
        "silver_contract": config["silver_contract"],
        "software_version": config["software_version"],
    }
    silver_bytes = _canonical_bytes(silver)
    _require(_canonical_bytes(silver["data"]), record_bytes, "SILVER_LOSSLESS")
    silver_sha256 = hashlib.sha256(silver_bytes).hexdigest()

    data = silver["data"]
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
    gold = {
        "gold_contract": config["gold_contract"],
        "identity": identity,
        "input_facts": {key: str(value) for key, value in facts.items()},
        "metrics": metrics,
        "provenance": {
            "record_sha256": record_sha256,
            "silver_contract": config["silver_contract"],
            "silver_payload_sha256": silver_sha256,
            "source_id": config["source_id"],
        },
        "semantic_scope": {
            "fiscal_audit_conclusion": False,
            "fundeb_compliance_conclusion": False,
            "imputation_performed": False,
            "kind": "DERIVED_ARITHMETIC_ONLY_FROM_SIOPE_DADOS_GERAIS",
            "mde_compliance_conclusion": False,
        },
        "software_version": config["software_version"],
    }
    gold_bytes = _canonical_bytes(gold)
    gold_sha256 = hashlib.sha256(gold_bytes).hexdigest()

    prefix = f"{config['source_id']}__Dados_Gerais_Siope__Limeira_SP__{config['pilot_year']}_P{config['period']}__{config['municipality_code']}"
    return {
        "record_sha256": record_sha256,
        "bronze": bronze,
        "bronze_bytes": bronze_bytes,
        "bronze_sha256": bronze_sha256,
        "bronze_name": f"{prefix}__{record_sha256[:12]}__bundle.json",
        "silver": silver,
        "silver_bytes": silver_bytes,
        "silver_sha256": silver_sha256,
        "silver_name": f"{prefix}__{silver_sha256[:12]}__silver_v1.json",
        "gold": gold,
        "gold_bytes": gold_bytes,
        "gold_sha256": gold_sha256,
        "gold_name": f"{prefix}__{gold_sha256[:12]}__gold_v1.json",
        "metric_count": len(metrics),
    }


def _preflight_no_collisions(config: dict, payloads: dict, drive) -> None:  # noqa: ANN001
    checks = (
        (config["bronze_folder_id"], payloads["bronze_name"], "BRONZE"),
        (config["silver_folder_id"], payloads["silver_name"], "SILVER"),
        (config["gold_folder_id"], payloads["gold_name"], "GOLD"),
    )
    for folder_id, name, label in checks:
        matches = drive.find_by_name(folder_id, name)
        _require(len(matches), 0, f"{label}_REMOTE_NAME_COLLISION")


def _put_and_readback(drive, *, folder_id: str, name: str, raw: bytes, mime_type: str, label: str) -> None:  # noqa: ANN001
    expected_sha = hashlib.sha256(raw).hexdigest()
    expected_md5 = hashlib.md5(raw).hexdigest()  # noqa: S324
    with tempfile.TemporaryDirectory() as td:
        local = Path(td) / f"{label.lower()}.json"
        local.write_bytes(raw)
        uploaded = drive.put(local, name, folder_id, mime_type)
        _require(uploaded.get("name"), name, f"{label}_UPLOAD_NAME")
        _require(uploaded.get("mimeType"), mime_type, f"{label}_UPLOAD_MIME")
        _require(str(uploaded.get("size")), str(len(raw)), f"{label}_UPLOAD_SIZE")
        _require(uploaded.get("md5Checksum"), expected_md5, f"{label}_UPLOAD_MD5")
        file_id = uploaded.get("id")
        if not isinstance(file_id, str) or not file_id:
            raise HistoricalParameterizedSingleYearPilotError(f"{ERROR}_{label}_UPLOAD_ID")
        out = Path(td) / f"{label.lower()}_readback.json"
        downloaded = drive.get(file_id, out)
        actual = out.read_bytes()
    _require(downloaded.get("bytes"), len(raw), f"{label}_READBACK_BYTES")
    _require(downloaded.get("sha256"), expected_sha, f"{label}_READBACK_SHA")
    _require(actual, raw, f"{label}_READBACK_IDENTITY")


def run_pilot(config: dict, *, root: str | Path, siope_client=None, drive=None) -> dict:
    validate_config(config, root=root)
    if siope_client is None:
        siope_client = SiopeClient(
            policy=SiopeClientPolicy(
                timeout_seconds=60,
                max_response_bytes=262144,
                max_attempts=1,
                follow_redirects=False,
                follow_nextlink=False,
            )
        )
    page = siope_client.get_dados_gerais_page(
        ano=config["pilot_year"],
        periodo=config["period"],
        uf=config["uf"],
        municipality_code=config["municipality_code"],
        select_fields=tuple(sorted(PROVEN_DADOS_GERAIS_FIELDS)),
    )
    record = _record_from_page(config, page)
    payloads = _build_payloads(config, record, page)

    if drive is None:
        drive = DriveRESTClient(TokenProvider(OAuthCredentials.from_env()))
    _preflight_no_collisions(config, payloads, drive)
    _put_and_readback(drive, folder_id=config["bronze_folder_id"], name=payloads["bronze_name"], raw=payloads["bronze_bytes"], mime_type=config["mime_type"], label="BRONZE")
    _put_and_readback(drive, folder_id=config["silver_folder_id"], name=payloads["silver_name"], raw=payloads["silver_bytes"], mime_type=config["mime_type"], label="SILVER")
    _put_and_readback(drive, folder_id=config["gold_folder_id"], name=payloads["gold_name"], raw=payloads["gold_bytes"], mime_type=config["mime_type"], label="GOLD")

    return {
        "status": PASS,
        "gate_id": config["gate_id"],
        "pilot_year": config["pilot_year"],
        "period": config["period"],
        "stage_count": 9,
        "stages_completed": list(EXPECTED_STAGES),
        "source_get_count": 1,
        "source_record_count": 1,
        "schema_key_count": 52,
        "drive_preflight_collision_checks": 3,
        "drive_write_count": 3,
        "drive_download_count": 3,
        "create_only": True,
        "record_sha256": payloads["record_sha256"],
        "bronze_sha256": payloads["bronze_sha256"],
        "silver_sha256": payloads["silver_sha256"],
        "gold_sha256": payloads["gold_sha256"],
        "bronze_bytes": len(payloads["bronze_bytes"]),
        "silver_bytes": len(payloads["silver_bytes"]),
        "gold_bytes": len(payloads["gold_bytes"]),
        "metric_count": payloads["metric_count"],
        "remote_file_id_persisted": False,
        "batch_live_authorized": False,
        "historical_collection_authorized": False,
        "individual_year_workflow_duplication_authorized": False,
        "retry_authorized": False,
        "pagination_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "imputation_performed": False,
        "compliance_claims_authorized": False,
        "next_gate": config["next_gate"],
    }

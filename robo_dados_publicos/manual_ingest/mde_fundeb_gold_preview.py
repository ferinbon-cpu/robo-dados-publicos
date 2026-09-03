from __future__ import annotations
from decimal import Decimal, InvalidOperation
from pathlib import Path
import hashlib, json, re

class F02GoldPreviewStop(ValueError):
    """Fail-closed stop for the F02 Gold preview."""

def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def _require_sha256(value: object, label: str) -> str:
    digest=str(value or "").lower().strip()
    if not re.fullmatch(r"[0-9a-f]{64}",digest): raise F02GoldPreviewStop(f"STOP_F02_GOLD_BAD_SHA256: {label}")
    return digest

def _decimal(value: object, label: str) -> Decimal:
    try: number=Decimal(str(value))
    except (InvalidOperation,ValueError) as exc: raise F02GoldPreviewStop(f"STOP_F02_GOLD_NON_NUMERIC: {label}") from exc
    if not number.is_finite() or number<0: raise F02GoldPreviewStop(f"STOP_F02_GOLD_INVALID_NUMERIC: {label}")
    return number

def validate_config(raw: dict) -> dict:
    if raw.get("schema")!="F02_GOLD_PREVIEW_CONFIG_V1": raise F02GoldPreviewStop("STOP_F02_GOLD_CONFIG_SCHEMA")
    if raw.get("mode")!="OFFLINE_GOLD_PREVIEW": raise F02GoldPreviewStop("STOP_F02_GOLD_CONFIG_MODE")
    inputs=raw.get("silver_inputs")
    if not isinstance(inputs,list) or len(inputs)!=2: raise F02GoldPreviewStop("STOP_F02_GOLD_EXACTLY_TWO_SILVERS")
    ids=[str(i.get("input_id","")).strip() for i in inputs]
    if set(ids)!={"F02_SILVER_JAN_APR","F02_SILVER_JAN_MAY_LOCAL"} or len(set(ids))!=2: raise F02GoldPreviewStop("STOP_F02_GOLD_SILVER_ID_SET")
    for item in inputs:
        for key in ("drive_file_id","file_name","expected_bytes","expected_sha256","expected_logical_sha256","expected_schema","expected_status","local_snapshot_path"):
            if item.get(key) in (None,""): raise F02GoldPreviewStop(f"STOP_F02_GOLD_INPUT_MISSING: {item.get('input_id')}:{key}")
        if int(item["expected_bytes"])<=0: raise F02GoldPreviewStop("STOP_F02_GOLD_BAD_BYTES")
        _require_sha256(item["expected_sha256"],f"{item['input_id']}.file"); _require_sha256(item["expected_logical_sha256"],f"{item['input_id']}.logical")
    obs=raw.get("required_observations")
    if not isinstance(obs,list) or len(obs)!=4: raise F02GoldPreviewStop("STOP_F02_GOLD_EXACTLY_FOUR_OBSERVATIONS")
    if len({x.get("observation_id") for x in obs})!=4: raise F02GoldPreviewStop("STOP_F02_GOLD_DUPLICATE_OBSERVATION_ID")
    for item in obs:
        for key in ("metric","period_start","period_end","authority","claim_class","source_input_id","source_family"):
            if item.get(key) in (None,""): raise F02GoldPreviewStop(f"STOP_F02_GOLD_OBSERVATION_MISSING: {item.get('observation_id')}:{key}")
        if item["source_input_id"] not in ids: raise F02GoldPreviewStop("STOP_F02_GOLD_OBSERVATION_UNKNOWN_INPUT")
    semantic=raw.get("semantic_policy")
    for key in ("allow_imputation","allow_period_collapsing","allow_authority_collapsing","allow_annual_compliance_claim","allow_local_mde_as_official"):
        if not isinstance(semantic,dict) or semantic.get(key) is not False: raise F02GoldPreviewStop("STOP_F02_GOLD_SEMANTIC_PERMISSION")
    if semantic.get("require_source_silver_identity_per_observation") is not True: raise F02GoldPreviewStop("STOP_F02_GOLD_PROVENANCE_NOT_REQUIRED")
    effects=raw.get("effects")
    if not isinstance(effects,dict) or effects.get("drive_write_count")!=0: raise F02GoldPreviewStop("STOP_F02_GOLD_EFFECTS")
    for key,value in effects.items():
        if key!="drive_write_count" and value is not False: raise F02GoldPreviewStop(f"STOP_F02_GOLD_EFFECT_ENABLED: {key}")
    return {"status":"PASS_F02_GOLD_PREVIEW_CONFIG","silver_input_count":2,"observation_count":4}

def validate_silver_snapshot(spec: dict,path: str|Path)->dict:
    payload=Path(path).read_bytes(); digest=hashlib.sha256(payload).hexdigest()
    if len(payload)!=int(spec["expected_bytes"]): raise F02GoldPreviewStop("STOP_F02_GOLD_SILVER_BYTES_DRIFT")
    if digest!=spec["expected_sha256"]: raise F02GoldPreviewStop("STOP_F02_GOLD_SILVER_FILE_SHA_DRIFT")
    data=json.loads(payload.decode("utf-8"))
    if data.get("content_sha256")!=spec["expected_logical_sha256"]: raise F02GoldPreviewStop("STOP_F02_GOLD_SILVER_LOGICAL_SHA_DRIFT")
    if data.get("schema")!=spec["expected_schema"]: raise F02GoldPreviewStop("STOP_F02_GOLD_SILVER_SCHEMA_DRIFT")
    if data.get("status")!=spec["expected_status"]: raise F02GoldPreviewStop("STOP_F02_GOLD_SILVER_STATUS_DRIFT")
    if not isinstance(data.get("normalized"),list) or not data["normalized"]: raise F02GoldPreviewStop("STOP_F02_GOLD_SILVER_NORMALIZED_MISSING")
    return {"spec":spec,"data":data,"file_sha256":digest,"bytes":len(payload)}

def _one_family(silver:dict,family:str)->dict:
    matches=[x for x in silver["data"]["normalized"] if x.get("family")==family]
    if len(matches)!=1: raise F02GoldPreviewStop(f"STOP_F02_GOLD_FAMILY_CARDINALITY: family={family};observed={len(matches)}")
    return matches[0]

def build_preview(config:dict,*,root:str|Path)->tuple[dict,dict]:
    validate_config(config); root=Path(root); silvers={}
    for spec in config["silver_inputs"]: silvers[spec["input_id"]]=validate_silver_snapshot(spec,root/spec["local_snapshot_path"])
    observations=[]
    for required in config["required_observations"]:
        silver=silvers[required["source_input_id"]]; record=_one_family(silver,required["source_family"])
        if record.get("period_start")!=required["period_start"] or record.get("period_end")!=required["period_end"]: raise F02GoldPreviewStop("STOP_F02_GOLD_PERIOD_DRIFT")
        if record.get("authority")!=required["authority"]: raise F02GoldPreviewStop("STOP_F02_GOLD_AUTHORITY_DRIFT")
        metrics=record.get("metrics")
        if not isinstance(metrics,dict) or required["metric"] not in metrics: raise F02GoldPreviewStop("STOP_F02_GOLD_METRIC_MISSING")
        value=metrics[required["metric"]]; _decimal(value,required["observation_id"]); spec=silver["spec"]
        observations.append({"observation_id":required["observation_id"],"metric":required["metric"],"value":str(value),"period_start":required["period_start"],"period_end":required["period_end"],"authority":required["authority"],"claim_class":required["claim_class"],"source_family":required["source_family"],"source_silver":{"input_id":required["source_input_id"],"drive_file_id":spec["drive_file_id"],"file_sha256":silver["file_sha256"],"logical_content_sha256":spec["expected_logical_sha256"]},"annual_compliance_claim_authorized":False,"imputation_performed":False,"period_or_authority_collapsed":False})
    if len({x["observation_id"] for x in observations})!=4: raise F02GoldPreviewStop("STOP_F02_GOLD_OUTPUT_OBSERVATION_DRIFT")
    core={"schema":"F02_MDE_FUNDEB_GOLD_PREVIEW_V1","batch":config["batch"],"kind":"TYPED_OBSERVATIONS_PRESERVE_PERIOD_AUTHORITY_AND_PROVENANCE","observations":observations,"semantic_scope":{"annual_compliance_conclusion":False,"local_mde_substitutes_official_rreo":False,"imputation_performed":False,"period_collapsing_performed":False,"authority_collapsing_performed":False},"effects":{"source_network_calls":0,"drive_network_calls":0,"drive_writes":0,"gold_writes":0,"serving_writes":0,"publication_writes":0,"site_writes":0,"delete":0,"move":0,"overwrite":0},"status":"PASS_F02_GOLD_PREVIEW_NOT_PERSISTED"}
    digest=hashlib.sha256(canonical_bytes(core)).hexdigest(); candidate={"content_sha256":digest,**core}
    return candidate,{"status":candidate["status"],"observation_count":4,"gold_payload_sha256":digest,"gold_payload_persisted":False,"gold_remote_write_authorized":False,"annual_compliance_claim_authorized":False,"network_called":False,"drive_write_count":0}

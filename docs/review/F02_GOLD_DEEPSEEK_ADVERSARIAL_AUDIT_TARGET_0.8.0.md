# F02 Gold — DeepSeek adversarial audit target — 0.8.0

Status: **AUDIT_TARGET_ONLY — NO GOLD PERSISTENCE**

This file exists only to put the complete F02 Gold review surface into one PR diff for the already-configured automatic DeepSeek reviewer. It makes no operational change.

## Pinned repository state

- main before this audit PR: `952c5b5d77cdca2024f26f2680ff999835c91139`
- Gold implementation PR already merged: #370
- merged implementation head: `28b586e424c5afe4941cf313d336e87530aa3921`
- review-request issue: #371
- expected Gold preview logical SHA-256 from the already-built offline candidate: `38232ab8e02a3afc5444d3ef8f6276f056f29a001d62b2b2dc1d571a0a79e90d`
- expected rendered candidate SHA-256: `e2ef3f4eef403730f54c8f8ddfd5dcbf3facd5131a6cedd0cb356ffce7354fe1`

## Pinned Silver identities

Jan–Apr official-partial Silver:
- Drive ID: `1YmINhBM_jE2BnsYrVN5BuZMv5mE4ElmP`
- bytes: 7269
- file SHA-256: `fe76d088143e61b9f0d5b1f611757bee924b5a2c95abae5fa5908b1b85b742f9`
- logical SHA-256: `72cc2cb29990809c043877ef8b0ef19d61f1064b093ef58fdb8fcc0f87386c81`

Jan–May local-monitoring Silver:
- Drive ID: `10GNOfBEKJOgRNS0Ord2asR2UdwKc1gse`
- bytes: 6769
- file SHA-256: `ec1cb12dec7349cd391ed12ad9654d598136781acca0138bf6bc286f35827a42`
- logical SHA-256: `d244b94d04f954c01771d9a416d97814fd163a0ecb693003677becfde06bf1a1`

## Adversarial objectives

Attempt to prove a concrete failure path for each item, not merely propose extra process:

1. local MDE 23.60% can become an official MDE claim;
2. Jan–Apr 24.27% and Jan–May 23.60% can be collapsed without visible authority/period mismatch;
3. RREO 88.67% and local 96.99% can become one undifferentiated FUNDEB-compliance series;
4. missing May RREO can be imputed, forward-filled, inferred or substituted;
5. any partial observation can become an annual compliance conclusion;
6. tampered Silver bytes/logical hash can still produce Gold;
7. Gold preview can cause network/Drive/Gold/serving/publication/site/delete/move/overwrite effects;
8. emitted Gold observations can lose enough provenance to become non-reproducible;
9. configuration fields can be altered in combinations not covered by current tests to bypass a guard;
10. any claim-class/authority combination is semantically inconsistent or under-validated;
11. any type/shape edge case can trigger permissive behavior instead of fail-closed;
12. any realistic downstream consumer could misread the schema despite the current fields.

Look for additional material defects outside this list.

## Required adjudication semantics

The project adjudicator will evaluate findings under the merged protocol below. DeepSeek is encouraged to disagree, but a reviewer preference is not retroactive owner authorization or a retroactive blocker.

### External review adjudication protocol

# External Review Adjudication Protocol

Status: **governance protocol**  
Project: `robo-dados-publicos`  
Applies from: `0.8.0` candidate onward

## Purpose

This protocol defines how findings from an external reviewer, model, agent, auditor, or human reviewer are evaluated before they become project requirements.

The goal is to preserve the value of adversarial review without allowing a reviewer to silently redefine authorization, provenance, execution scope, or promotion rules after the fact.

## Roles and authority

The project separates four roles:

1. **Owner** — grants or withholds execution authorization and is the authority for owner intent.
2. **Architect/adjudicator** — maps the owner's authorization to the repository's existing contracts, evaluates reviewer findings, and determines whether a finding is a blocker, hardening opportunity, or rejected requirement.
3. **Executor** — implements the bounded change or run exactly within the materialized contract.
4. **External reviewer** — performs adversarial review and may identify defects, missing evidence, unsafe assumptions, or useful hardening opportunities.

An external reviewer is intentionally independent, but is **not** an independent source of owner authorization and does not automatically have veto power over a change.

## Authority hierarchy

When sources disagree, use the following order:

1. explicit current owner authorization;
2. repository governance and already-materialized task/run contract;
3. executable gates, tests, and pinned evidence;
4. architectural conventions established by merged history;
5. external reviewer recommendation.

A lower-ranked source may reveal that a higher-ranked source has been implemented incorrectly, but it may not rewrite the higher-ranked source retroactively.

## Review finding classes

Every material reviewer finding should be adjudicated into one of these classes.

| Class | Meaning | Required treatment |
|---|---|---|
| `BLOCKER_REQUIREMENT_VIOLATION` | Existing requirement, authorization boundary, invariant, or gate is violated | Stop; fix before merge or execution |
| `BLOCKER_EVIDENCE_GAP` | A claim cannot be supported by the available evidence | Stop the claim; obtain evidence or narrow the claim |
| `HARDENING_RISK` | Real technical risk is not yet an explicit requirement | Prefer implementing a proportional fail-closed guard/test; not automatically retroactive |
| `ARCHITECTURAL_IMPROVEMENT` | Useful maintainability, reuse, observability, or auditability improvement | Adopt when proportional and separately reviewable |
| `NEW_GOVERNANCE_PROPOSAL` | Reviewer proposes a new authorization, provenance, approval, signature, issue, or process rule | Evaluate prospectively; never treat as a retroactive blocker solely because the reviewer proposed it |
| `ALREADY_COVERED` | Existing code, gate, test, or evidence already addresses the concern | Record/reply with the covering control; no new requirement |
| `REJECTED_UNSUPPORTED_REQUIREMENT` | Proposed requirement conflicts with or is unsupported by current governance | Reject explicitly; do not fabricate evidence to satisfy it |

## Non-retroactivity rule

A reviewer must not create a new historical fact.

Therefore the project must not:

- create a post-hoc issue and describe it as prior authorization;
- add a signature after execution and claim it existed before execution;
- reinterpret a broad or unrelated owner instruction as authorization for an already-completed effect;
- backfill an approval timestamp, reviewer identity, or evidence chain that did not exist;
- promote a reviewer preference into a pre-existing mandatory requirement without a prospective governance change.

If a new governance rule is valuable, it may be adopted **for future gates** with an explicit effective point.

## Evidence-first adjudication

Reviewer findings about executed behavior should be tested against the strongest available evidence, preferably:

- exact commit/head SHA;
- task or execution contract committed before the effect;
- workflow source at execution time;
- immutable or pinned evidence payloads;
- reproducible hashes;
- independent offline verifiers;
- CI results and regression tests;
- explicit counters for prohibited effects.

When evidence disproves a reviewer concern, classify it as `ALREADY_COVERED` or `REJECTED_UNSUPPORTED_REQUIREMENT` rather than adding redundant process.

When evidence is insufficient, the correct response is to reduce the claim or fail closed, not to invent missing evidence.

## Authorization adjudication

External review may test whether an execution exceeded its authorized scope, but external review cannot itself authorize or de-authorize an already-defined owner instruction.

For one-shot bounded operations, the preferred chain is:

`owner authorization -> pre-run materialized contract -> bounded execution -> pinned evidence -> authorization consumed`

A reviewer may block the chain if it demonstrates that one of these links is missing, inconsistent, or violated.

A reviewer may recommend a stronger future chain, such as an additional approval artifact, but that recommendation becomes binding only after the project adopts it prospectively.

## Security and fail-closed rule

Security-relevant reviewer findings receive conservative treatment.

If the reviewer identifies a plausible path to:

- exceed a network request budget;
- contact a non-allowlisted origin;
- perform an unauthorized write;
- retry automatically when retry is not authorized;
- publish, promote, or assert an identity without sufficient evidence;
- bypass a pinned head or expected SHA;

then the preferred resolution is an executable fail-closed guard plus a regression test, not merely explanatory prose.

## Reviewer independence

Reviewers should be encouraged to disagree with the implementation. A healthy result may include rejected findings.

The project must avoid both failure modes:

- **rubber-stamp review** — accepting the implementation without serious challenge;
- **reviewer capture** — accepting every reviewer demand even when it invents requirements or conflicts with established governance.

The target is evidence-based adjudication.

## Required adjudication record for disputed findings

When a reviewer maintains a material blocker after implementation changes, record at least:

- the reviewer finding;
- the applicable existing requirement or absence of one;
- the relevant evidence/control;
- the classification from this protocol;
- the decision: `ACCEPT`, `HARDEN`, `DEFER_PROSPECTIVELY`, or `REJECT`;
- whether the decision changes any future gate.

The record may live in the PR description, review thread, task evidence, or a dedicated governance artifact as appropriate.

## Example: new signature requirement after a bounded run

If a reviewer argues after execution that the owner should have signed an issue before the run:

- if the repository already required that signature before execution and it is absent, classify as `BLOCKER_REQUIREMENT_VIOLATION`;
- if no such requirement existed and the actual owner authorization plus pre-run contract are preserved, classify the demand as `NEW_GOVERNANCE_PROPOSAL`;
- do not manufacture a retroactive signature;
- evaluate whether to require such a signature for future gates.

## Merge rule

This protocol does not weaken existing CI, branch, expected-head, authorization, or evidence requirements.

A reviewer finding marked `BLOCKER_*` remains blocking until resolved or formally reclassified with evidence. A reviewer finding does not become a blocker merely because it is strongly worded or repeated.

## Design principle

**Use adversarial review to discover defects and convert real risks into executable invariants; never convert reviewer preference into fictional provenance.**


## Gold contract under review

# F02 MDE/FUNDEB Gold preview contract — 0.8.0

## Purpose

Build a deterministic offline Gold **preview** from two already-promoted, byte-verified F02 Silver artifacts. The preview curates typed observations; it does not persist Gold.

## Pinned Silver inputs

The config pins exact Drive IDs, byte sizes, file SHA-256, logical content SHA-256, schema and status for:
- Jan–Apr/2026 F02 Silver with same-period RREO;
- Jan–May/2026 F02 local-monitoring Silver without same-period RREO.

Any drift is a STOP.

## Semantic boundary

Gold is not a license to erase provenance. The preview emits exactly four observations:

1. MDE Jan–Apr official partial RREO observation;
2. MDE Jan–May local monitoring observation;
3. FUNDEB professionals Jan–Apr official partial RREO observation;
4. FUNDEB professionals Jan–May local monitoring observation.

Every observation must retain exact period, authority, claim class, source Silver identity, source metric and value.

The following are forbidden:
- treating Jan–May local MDE as official MDE;
- annual compliance conclusions from partial data;
- combining Jan–Apr and Jan–May as the same period;
- combining RREO authority with local-monitoring authority;
- imputation, forward fill or inferred May RREO;
- replacing an observation with a derived comparison across incompatible periods/authorities.

## Fail-closed rules

STOP on:
- Silver file hash, byte length, logical hash, schema or status drift;
- missing expected normalized family;
- missing/non-numeric/non-finite/negative metric;
- source period drift;
- authority drift;
- observation-set drift;
- duplicated observation IDs;
- any semantic-policy permission becoming true;
- any remote/write/persistence/serving/publication/site/delete/move/overwrite/recurrence/schedule permission becoming true.

## Operational boundary

This gate is offline only. It makes zero Drive calls and zero writes.

A passing preview authorizes only review of the Gold candidate and its evidence. A create-only write into `03_GOLD` requires a later, separately reviewed owner gate.


## Gold config under review

```json
{
  "schema": "F02_GOLD_PREVIEW_CONFIG_V1",
  "mode": "OFFLINE_GOLD_PREVIEW",
  "batch": "F02_MDE_FUNDEB_2026_GOLD_PREVIEW",
  "silver_inputs": [
    {
      "input_id": "F02_SILVER_JAN_APR",
      "drive_file_id": "1YmINhBM_jE2BnsYrVN5BuZMv5mE4ElmP",
      "file_name": "F02_MDE_FUNDEB_2026_JAN_ABR__72cc2cb29990__silver_v1.json",
      "expected_bytes": 7269,
      "expected_sha256": "fe76d088143e61b9f0d5b1f611757bee924b5a2c95abae5fa5908b1b85b742f9",
      "expected_logical_sha256": "72cc2cb29990809c043877ef8b0ef19d61f1064b093ef58fdb8fcc0f87386c81",
      "expected_schema": "F02_MDE_FUNDEB_SILVER_V1",
      "expected_status": "SILVER_SCOPED_VALIDATED",
      "local_snapshot_path": "docs/evidence/f02_gold_preview/F02_MDE_FUNDEB_2026_JAN_ABR__72cc2cb29990__silver_v1.json"
    },
    {
      "input_id": "F02_SILVER_JAN_MAY_LOCAL",
      "drive_file_id": "10GNOfBEKJOgRNS0Ord2asR2UdwKc1gse",
      "file_name": "F02_LOCAL_MONITORING_2026_JAN_MAY__d244b94d04f9__silver_v1.json",
      "expected_bytes": 6769,
      "expected_sha256": "ec1cb12dec7349cd391ed12ad9654d598136781acca0138bf6bc286f35827a42",
      "expected_logical_sha256": "d244b94d04f954c01771d9a416d97814fd163a0ecb693003677becfde06bf1a1",
      "expected_schema": "F02_LOCAL_MONITORING_SILVER_V1",
      "expected_status": "SILVER_PROMOTED_VALIDATED_LOCAL_MONITORING_ONLY",
      "local_snapshot_path": "docs/evidence/f02_gold_preview/F02_LOCAL_MONITORING_2026_JAN_MAY__d244b94d04f9__silver_v1.json"
    }
  ],
  "required_observations": [
    {
      "observation_id": "MDE_OFFICIAL_PARTIAL_2026_JAN_APR",
      "metric": "mde_percent",
      "period_start": "2026-01-01",
      "period_end": "2026-04-30",
      "authority": "OFFICIAL_MDE_PRIMARY",
      "claim_class": "OFFICIAL_PARTIAL_OBSERVATION_NOT_ANNUAL_COMPLIANCE",
      "source_input_id": "F02_SILVER_JAN_APR",
      "source_family": "RREO_MDE"
    },
    {
      "observation_id": "MDE_LOCAL_MONITORING_2026_JAN_MAY",
      "metric": "education_expense_liquidated_percent",
      "period_start": "2026-01-01",
      "period_end": "2026-05-31",
      "authority": "AUXILIARY_LOCAL_MONITORING",
      "claim_class": "LOCAL_MONITORING_ONLY_NOT_OFFICIAL_MDE",
      "source_input_id": "F02_SILVER_JAN_MAY_LOCAL",
      "source_family": "MDE_25_LOCAL"
    },
    {
      "observation_id": "FUNDEB_PROFESSIONALS_OFFICIAL_PARTIAL_2026_JAN_APR",
      "metric": "fundeb_professionals_percent",
      "period_start": "2026-01-01",
      "period_end": "2026-04-30",
      "authority": "OFFICIAL_MDE_PRIMARY",
      "claim_class": "OFFICIAL_PARTIAL_OBSERVATION_NOT_ANNUAL_COMPLIANCE",
      "source_input_id": "F02_SILVER_JAN_APR",
      "source_family": "RREO_MDE"
    },
    {
      "observation_id": "FUNDEB_PROFESSIONALS_LOCAL_MONITORING_2026_JAN_MAY",
      "metric": "fundeb_professionals_liquidated_percent_local",
      "period_start": "2026-01-01",
      "period_end": "2026-05-31",
      "authority": "LOCAL_MONITORING_NO_OFFICIAL_RREO_PERIOD_MATCH",
      "claim_class": "LOCAL_MONITORING_ONLY_NOT_OFFICIAL_COMPLIANCE",
      "source_input_id": "F02_SILVER_JAN_MAY_LOCAL",
      "source_family": "FUNDEB_LOCAL"
    }
  ],
  "semantic_policy": {
    "allow_imputation": false,
    "allow_period_collapsing": false,
    "allow_authority_collapsing": false,
    "allow_annual_compliance_claim": false,
    "allow_local_mde_as_official": false,
    "require_source_silver_identity_per_observation": true
  },
  "effects": {
    "source_network_authorized": false,
    "drive_network_authorized": false,
    "drive_write_count": 0,
    "gold_persistence_authorized": false,
    "serving_authorized": false,
    "publication_authorized": false,
    "site_mutation_authorized": false,
    "delete_authorized": false,
    "move_authorized": false,
    "overwrite_authorized": false,
    "recurrence_authorized": false,
    "schedule_enabled": false
  }
}

```

## Gold builder under review

```python
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

```

## Gold tests under review

```python
import copy,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from robo_dados_publicos.manual_ingest.mde_fundeb_gold_preview import F02GoldPreviewStop,build_preview,load_json,validate_config
ROOT=Path(__file__).resolve().parents[1]; CONFIG=ROOT/"config/manual_supervised_ingest_f02_gold_preview.v1.json"
class Tests(unittest.TestCase):
 def test_config(self): self.assertEqual(validate_config(load_json(CONFIG))["observation_count"],4)
 def test_exact_values_and_boundaries(self):
  c,r=build_preview(load_json(CONFIG),root=ROOT); self.assertEqual([x["value"] for x in c["observations"]],["24.27","23.60","88.67","96.99"]); self.assertFalse(r["gold_payload_persisted"]); self.assertEqual(r["drive_write_count"],0)
  by={x["observation_id"]:x for x in c["observations"]}; self.assertEqual(by["MDE_OFFICIAL_PARTIAL_2026_JAN_APR"]["period_end"],"2026-04-30"); self.assertEqual(by["MDE_LOCAL_MONITORING_2026_JAN_MAY"]["period_end"],"2026-05-31")
  for x in c["observations"]: self.assertFalse(x["annual_compliance_claim_authorized"]); self.assertFalse(x["imputation_performed"]); self.assertFalse(x["period_or_authority_collapsed"])
 def test_semantic_permissions_stop(self):
  base=load_json(CONFIG)
  for key in ("allow_imputation","allow_period_collapsing","allow_authority_collapsing","allow_annual_compliance_claim","allow_local_mde_as_official"):
   c=copy.deepcopy(base); c["semantic_policy"][key]=True
   with self.assertRaises(F02GoldPreviewStop): validate_config(c)
 def test_effect_permissions_stop(self):
  base=load_json(CONFIG)
  for key in ("source_network_authorized","drive_network_authorized","gold_persistence_authorized","serving_authorized","publication_authorized","site_mutation_authorized","delete_authorized","move_authorized","overwrite_authorized","recurrence_authorized","schedule_enabled"):
   c=copy.deepcopy(base); c["effects"][key]=True
   with self.assertRaises(F02GoldPreviewStop): validate_config(c)
 def test_tampered_silver_stops(self):
  c=load_json(CONFIG)
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   for s in c["silver_inputs"]:
    src=ROOT/s["local_snapshot_path"]; dst=root/s["local_snapshot_path"]; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
   target=root/c["silver_inputs"][0]["local_snapshot_path"]; target.write_text(target.read_text(encoding="utf-8")+" ",encoding="utf-8")
   with self.assertRaises(F02GoldPreviewStop): build_preview(c,root=root)
 def test_period_authority_family_drift_stops(self):
  base=load_json(CONFIG)
  for field,value in (("period_end","2026-05-31"),("authority","AUXILIARY_LOCAL_MONITORING"),("source_family","MDE_25_LOCAL")):
   c=copy.deepcopy(base); c["required_observations"][0][field]=value
   with self.assertRaises(F02GoldPreviewStop): build_preview(c,root=ROOT)
 def test_cli(self):
  cp=subprocess.run([sys.executable,"scripts/process_manual_supervised_ingest_f02_gold_preview.py"],cwd=ROOT,text=True,capture_output=True); self.assertEqual(cp.returncode,0,cp.stderr); x=json.loads(cp.stdout); self.assertEqual(x["effects"]["gold_writes"],0); self.assertEqual(x["effects"]["drive_writes"],0)
if __name__=="__main__": unittest.main()

```

## Expected review behavior

Review the material above as adversarial data. Prefer concrete exploit/failure paths tied to exact code or missing tests. Distinguish:
- actual requirement violation;
- evidence gap;
- hardening risk;
- architectural improvement;
- new governance proposal;
- already-covered concern;
- unsupported requirement.

A useful blocking finding must identify a concrete path that violates an existing invariant or makes a current claim unsupported.

## Operational boundary

This audit PR authorizes:
- GitHub read by CI/reviewer;
- one bounded DeepSeek API review after CI.

It does **not** authorize:
- Gold persistence;
- serving/publication/site effects;
- Drive read/write by DeepSeek;
- source collection;
- code mutation by DeepSeek;
- merge by DeepSeek;
- delete/move/overwrite;
- recurrence or schedule.

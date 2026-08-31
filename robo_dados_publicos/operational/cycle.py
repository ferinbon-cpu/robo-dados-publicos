from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from robo_dados_publicos.core.models import AnswerContract
from robo_dados_publicos.operational.model import SOURCE_AUTHORIZATION_STATES, STAGES, StageResult
from robo_dados_publicos.product.bundle import build_product_report, write_product_bundle


STOP_PREFIX = "STOP_"
COMPARISONS = (
    "FIRST_RUN", "NO_CHANGE", "SOURCE_CHANGED", "NEW_SOURCE_OBJECT",
    "PROCESSING_CHANGED", "NEW_RECONCILIATION_CANDIDATE", "STOP_STATE_CHANGED",
)


def _canonical_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def compare_runs(current: dict, prior: dict | None) -> list[str]:
    """Classify deterministic differences without assigning a cause."""
    if prior is None:
        return ["FIRST_RUN"]
    if current.get("profile_id") != prior.get("profile_id"):
        return ["NEW_SOURCE_OBJECT"]
    changes = []
    if current.get("source_identities") != prior.get("source_identities"):
        changes.append("NEW_SOURCE_OBJECT")
    if current.get("source_hashes") != prior.get("source_hashes"):
        changes.append("SOURCE_CHANGED")
    if current.get("processed_object_counts") != prior.get("processed_object_counts") or current.get("gold_event_counts") != prior.get("gold_event_counts"):
        changes.append("PROCESSING_CHANGED")
    if current.get("reconciliation_task_counts") != prior.get("reconciliation_task_counts") or current.get("reconciliation_result_counts_by_status") != prior.get("reconciliation_result_counts_by_status"):
        changes.append("NEW_RECONCILIATION_CANDIDATE")
    if current.get("stop_reasons") != prior.get("stop_reasons"):
        changes.append("STOP_STATE_CHANGED")
    return changes or ["NO_CHANGE"]


class OperationalCycle:
    """Offline composition only; TASK 017 deliberately has no transport dependency."""

    def __init__(self, config: dict):
        self.config = config

    @classmethod
    def from_file(cls, path: str | Path) -> "OperationalCycle":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def _validate(self) -> list[str]:
        c = self.config
        errors = []
        if c.get("profile_id") != "LIMEIRA_OPERATIONAL_PILOT_V1": errors.append("PROFILE_UNPROVEN")
        if c.get("tier") != "T0_OFFLINE": errors.append("TIER_NOT_OFFLINE")
        if c.get("source_mode") != "PINNED_REUSE": errors.append("LIVE_MODE_REQUIRES_OWNER_AUTHORIZATION")
        if c.get("source", {}).get("authorization_state", "BLOCKED_AUTHORIZATION_REQUIRED") not in SOURCE_AUTHORIZATION_STATES: errors.append("SOURCE_AUTHORIZATION_UNKNOWN")
        effects = c.get("effects", {})
        if any(effects.get(k) for k in ("network_requests", "drive_reads", "drive_writes", "source_collection", "live_reconciliation")): errors.append("REMOTE_EFFECT_REQUESTED")
        if c.get("recurrence") != "DISABLED" or c.get("schedule") != "DISABLED": errors.append("RECURRENCE_OR_SCHEDULE_FORBIDDEN")
        if c.get("persistence_policy") != "CREATE_ONLY_LOCAL": errors.append("MUTATING_PERSISTENCE_FORBIDDEN")
        return errors

    def run(self, output_dir: str | Path, *, prior: dict | None = None, started_at: str | None = None) -> dict:
        output_dir = Path(output_dir)
        if output_dir.exists():
            return self._stopped("OUTPUT_COLLISION_CREATE_ONLY", started_at=started_at)
        errors = self._validate()
        if errors:
            return self._stopped(*errors, started_at=started_at)
        output_dir.mkdir(parents=True)
        c, source, counts = self.config, self.config["source"], self.config["pinned_reference"]
        evidence = c["evidence_references"]
        stages = [
            StageResult("PREFLIGHT", "PASS", True, [c["profile_id"]], ["T0_OFFLINE_VALIDATED"], evidence),
            StageResult("SOURCE_SELECTION", "PASS", True, [source["source_id"]], [source["source_id"]], evidence),
            StageResult("ACQUISITION_OR_REUSE", "SKIPPED_ALREADY_PROVEN", False, [source["sha256"]], [source["sha256"]], evidence, ["HISTORICAL_PINNED_REFERENCE_NOT_FRESH_COLLECTION"]),
            StageResult("PROCESSING", "SKIPPED_ALREADY_PROVEN", False, [source["sha256"]], [c["processing_identity"]], evidence, ["PINNED_COUNTS_REUSED_NOT_RECOMPUTED"]),
            StageResult("RECONCILIATION", "EVIDENCIA_INSUFICIENTE", False, [c["processing_identity"]], ["MATCH_CANDIDATE_NOT_FINANCIAL_IDENTITY"], evidence, ["LIVE_RECONCILIATION_NOT_EXECUTED"]),
            StageResult("OBSERVABILITY", "PASS", True, [source["source_id"]], ["SOURCE_CARD_7310"], evidence),
        ]
        snapshot = {
            "profile_id": c["profile_id"], "software_active": c["release_boundary"]["active"],
            "candidate_version": c["release_boundary"]["candidate"],
            "source_identities": [source["source_id"]], "source_hashes": [source["sha256"]],
            "processed_object_counts": {"pages": counts["pages"], "extracted_characters": counts["extracted_characters"], "rag_chunks": counts["rag_chunks"]},
            "gold_event_counts": counts["gold_events"], "reconciliation_task_counts": counts["reconciliation_tasks"],
            "reconciliation_result_counts_by_status": {"MATCH_CANDIDATE": 0, "NO_MATCH": 0}, "stop_reasons": [],
        }
        run_id = "OPC-" + _canonical_hash(snapshot)[:16].upper()
        generated_at = started_at or datetime.now(timezone.utc).isoformat()
        report = build_product_report([
            AnswerContract("ANSWERED", f"Referência histórica examinada: {source['source_id']}", f"{counts['pages']} páginas; {counts['extracted_characters']} caracteres; {counts['gold_events']} eventos; {counts['rag_chunks']} chunks; {counts['reconciliation_tasks']} tarefas", "Nenhuma reconciliação ao vivo tentada; MATCH_CANDIDATE não é identidade financeira.", "Resultados fixados já provados, não uma coleta nova.", "EVIDENCIA_INSUFICIENTE e NOT_EXECUTED permanecem explícitos.", tuple(evidence)),
            AnswerContract("EVIDENCIA_INSUFICIENTE", "0 resultados de reconciliação ao vivo", "", "MATCH_CANDIDATE", "Nenhuma identidade financeira promovida.", "LIVE_ONE_SHOT_AUTHORIZED exige autorização posterior do proprietário.", tuple(evidence)),
        ], report_id=run_id, title="Resumo do ciclo operacional controlado", scope="Prova offline PINNED_REUSE", generated_at=generated_at, limitations=("PROVEN FACT é referência histórica fixada.", "Apresentação não é evidência."), software_version=c["release_boundary"]["active"])
        manifest = write_product_bundle(report, output_dir / "product")
        product_hashes = {x["name"]: x["sha256"] for x in manifest["files"]}
        snapshot.update({"run_id": run_id, "started_at": generated_at, "product_artifact_hashes": product_hashes})
        snapshot["comparison"] = compare_runs(snapshot, prior)
        stages.extend([
            StageResult("PRODUCT_BUILD", "PASS", True, [run_id], list(product_hashes), evidence),
            StageResult("OPERATIONAL_SUMMARY", "PASS", True, [run_id], ["operational_result.json", "operational_summary.md"], evidence),
        ])
        result = {**snapshot, "status": "PASS", "source_mode": "PINNED_REUSE", "source_authorization_state": source["authorization_state"], "pinned_reference": counts, "reconciliation_safety": c["reconciliation"], "effects": c["effects"], "stages": [x.to_dict() for x in stages], "output_files": ["operational_result.json", "operational_summary.md", "product/"]}
        summary = self._markdown(result)
        (output_dir / "operational_summary.md").write_text(summary, encoding="utf-8")
        (output_dir / "operational_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return result

    def _stopped(self, *reasons: str, started_at: str | None = None) -> dict:
        first = StageResult("PREFLIGHT", "STOP_AUTHORIZATION_REQUIRED", True, warnings_stops=list(reasons))
        rest = [StageResult(stage, "STOP_DEPENDENCY", False, warnings_stops=["UPSTREAM_STOP"]) for stage in STAGES[1:]]
        return {"status": first.status, "started_at": started_at, "stop_reasons": list(reasons), "effects": {"network_requests": 0, "drive_reads": 0, "drive_writes": 0, "source_collection": 0, "live_reconciliation": 0}, "stages": [x.to_dict() for x in [first, *rest]]}

    @staticmethod
    def _markdown(r: dict) -> str:
        p = r["pinned_reference"]
        return f"""# Operational summary — {r['profile_id']}

> **PROVEN FACT (historical pinned reference):** this is not a fresh collection. Presentation is not evidence.

- **Examined:** `{r['source_identities'][0]}` (`PINNED_REUSE`)
- **Anything new:** no; `{r['comparison'][0]}`
- **Processed reference:** {p['pages']} pages / {p['extracted_characters']} extracted characters
- **Structured events:** {p['gold_events']}
- **RAG chunks:** {p['rag_chunks']}
- **Reconciliation tasks/candidates:** {p['reconciliation_tasks']}
- **Reconciliations attempted:** 0 (`NOT_EXECUTED`)
- **MATCH_CANDIDATE:** 0; never promoted to financial identity
- **Could not be proven:** live/current source state (`EVIDENCIA_INSUFICIENTE`)
- **STOP conditions:** none in this offline composition
- **Outputs:** `operational_result.json`, `operational_summary.md`, `product/`
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from robo_dados_publicos.core.models import AnswerContract
from robo_dados_publicos.operational.model import STAGES, StageResult
from robo_dados_publicos.product.bundle import build_product_report, write_product_bundle


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_CONTRACTS = {
    "sources": "config/sources.jornal_oficial_7310_gate.json",
    "processing": "config/processing.jornal_oficial_7310_gate.json",
    "reconciliation": "config/reconciliation.first_contract_gate.json",
    "observability": "config/observability.jornal_oficial_7310.json",
    "pending": "docs/evidence/TASK_011_FNDE_AUTHORITATIVE_REQUESTS_PENDING_0.8.0.json",
}
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

    def __init__(self, config: dict, *, repository_root: str | Path = REPOSITORY_ROOT):
        self.config = config
        self.repository_root = Path(repository_root)

    @classmethod
    def from_file(cls, path: str | Path) -> "OperationalCycle":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def _canonical_contracts_match(self) -> bool:
        """Cross-check copied profile values; canonical files are never repaired."""
        try:
            contracts = {
                name: json.loads((self.repository_root / path).read_text(encoding="utf-8"))
                for name, path in CANONICAL_CONTRACTS.items()
            }
        except (OSError, json.JSONDecodeError):
            return False
        c = self.config
        source = c.get("source", {})
        pinned = c.get("pinned_reference", {})
        reconciliation = c.get("reconciliation", {})
        source_contracts = contracts["sources"].get("sources", [])
        if len(source_contracts) != 1:
            return False
        canonical_source = source_contracts[0]
        processing = contracts["processing"]
        canonical_reconciliation = contracts["reconciliation"]
        source_id = "LIMEIRA_JORNAL_OFICIAL_EDICAO_7310"
        source_hash = "78a23262023f6233cb59fdc78f1fadc196d0a7bbd52c418bbdd9244229f46680"
        expected = (
            source.get("source_id") == source_id == canonical_source.get("source_id") == processing.get("source_id"),
            source.get("sha256") == source_hash == canonical_source.get("expected_sha256") == processing.get("source_sha256"),
            source.get("edition") == 7310 == processing.get("edition"),
            c.get("processing_identity") == "LIMEIRA_JO_07310_78A23262023F" == processing.get("output_prefix"),
            pinned.get("pages") == 76 == processing.get("expected_pages"),
            pinned.get("extracted_characters") == 195540 == processing.get("expected_total_extracted_chars"),
            pinned.get("gold_events") == 53 == processing.get("expected_gold_events"),
            pinned.get("rag_chunks") == 148 == processing.get("expected_rag_chunks"),
            pinned.get("reconciliation_tasks") == 68 == processing.get("expected_reconciliation_tasks"),
            contracts["observability"].get("source_card", {}).get("source_id") == source_id,
        )
        reconciliation_fields = (
            "allowed_targets", "limit", "required_selected", "initial_status",
            "selection_policy", "financial_identity_auto_promotion",
        )
        reconciliation_match = all(
            reconciliation.get(field) == canonical_reconciliation.get(field)
            for field in reconciliation_fields
        )
        referenced_contracts = [
            CANONICAL_CONTRACTS[name]
            for name in ("sources", "processing", "reconciliation", "observability")
        ]
        return all(expected) and reconciliation_match and c.get("evidence_references") == referenced_contracts

    def _release_boundary_matches(self) -> bool:
        try:
            pending = json.loads((self.repository_root / CANONICAL_CONTRACTS["pending"]).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        canonical = pending.get("canonical_state", {})
        boundary = self.config.get("release_boundary", {})
        expected = {
            "active": "0.7.0",
            "active_status": canonical.get("release_0_7_0"),
            "candidate": "0.8.0",
            "candidate_status": canonical.get("release_0_8_0"),
            "year_2025": canonical.get("year_2025"),
            "S1_NUM_POPU": canonical.get("S1_NUM_POPU"),
            "S2_FINANCIAL_ALIAS_BRIDGE": canonical.get("S2_FINANCIAL_ALIAS_BRIDGE"),
            "annual_closure_status": canonical.get("annual_closure_status"),
            "semantic_comparability_status": canonical.get("semantic_comparability_status"),
            "closed_annual_series": canonical.get("closed_annual_series"),
            "gold_2025": canonical.get("gold_2025"),
            "year_2026": canonical.get("year_2026"),
        }
        response_states = {
            request.get("blocker_id"): request.get("response_status")
            for request in pending.get("requests", [])
        }
        expected.update({
            "B1": response_states.get("B1_NUM_POPU"),
            "B2": response_states.get("B2_DOTACAO_EDU"),
            "B3": response_states.get("B3_EFFECTIVE_DECLARATION"),
        })
        fixed = {
            "active": "0.7.0", "active_status": "ACTIVE",
            "candidate": "0.8.0", "candidate_status": "CANDIDATE",
            "year_2025": "PROVEN_STRUCTURAL_RECENT",
            "S1_NUM_POPU": "NOT_PROVEN", "S2_FINANCIAL_ALIAS_BRIDGE": "NOT_PROVEN",
            "annual_closure_status": "UNKNOWN", "semantic_comparability_status": "UNKNOWN",
            "closed_annual_series": "2016-2024", "gold_2025": "UNKNOWN/BLOCKED",
            "year_2026": "UNPROVEN_CURRENT_YEAR", "B1": "PENDING", "B2": "PENDING", "B3": "PENDING",
        }
        return expected == fixed and boundary == {key: fixed[key] for key in boundary} and set(boundary) == set(fixed)

    def _validate(self) -> list[tuple[str, str]]:
        c = self.config
        errors = []
        structural_stop = "STOP_CONTRACT_UNPROVEN"
        authorization_stop = "STOP_AUTHORIZATION_REQUIRED"
        if c.get("profile_id") != "LIMEIRA_OPERATIONAL_PILOT_V1": errors.append((structural_stop, "PROFILE_UNPROVEN"))
        if c.get("tier") != "T0_OFFLINE": errors.append((structural_stop, "TIER_NOT_OFFLINE"))
        if c.get("source_mode") != "PINNED_REUSE": errors.append((authorization_stop, "LIVE_MODE_REQUIRES_OWNER_AUTHORIZATION"))
        if c.get("source", {}).get("authorization_state") != "PINNED_REUSE": errors.append((authorization_stop, "PINNED_REUSE_AUTHORIZATION_INCONSISTENT"))
        if c.get("live_one_shot_authorized") is not False: errors.append((authorization_stop, "LIVE_ONE_SHOT_MUST_REMAIN_BLOCKED"))
        if c.get("default_live_authorization_state") != "BLOCKED_AUTHORIZATION_REQUIRED": errors.append((authorization_stop, "DEFAULT_LIVE_AUTHORIZATION_MUST_BLOCK"))
        effects = c.get("effects", {})
        if any(effects.get(k) for k in ("network_requests", "drive_reads", "drive_writes", "source_collection", "live_reconciliation")): errors.append((authorization_stop, "REMOTE_EFFECT_REQUESTED"))
        if c.get("recurrence") != "DISABLED" or c.get("schedule") != "DISABLED": errors.append((authorization_stop, "RECURRENCE_OR_SCHEDULE_FORBIDDEN"))
        if c.get("persistence_policy") != "CREATE_ONLY_LOCAL": errors.append((authorization_stop, "MUTATING_PERSISTENCE_FORBIDDEN"))
        if not self._canonical_contracts_match(): errors.append((structural_stop, "PINNED_EVIDENCE_CONTRACT_DRIFT"))
        if not self._release_boundary_matches(): errors.append((structural_stop, "CANONICAL_RELEASE_STATE_DRIFT"))
        return errors

    def run(self, output_dir: str | Path, *, prior: dict | None = None, started_at: str | None = None) -> dict:
        output_dir = Path(output_dir)
        if output_dir.exists():
            return self._stopped("STOP_CONTRACT_UNPROVEN", "OUTPUT_COLLISION_CREATE_ONLY", started_at=started_at)
        errors = self._validate()
        if errors:
            status = "STOP_CONTRACT_UNPROVEN" if any(item[0] == "STOP_CONTRACT_UNPROVEN" for item in errors) else errors[0][0]
            return self._stopped(status, *(item[1] for item in errors), started_at=started_at)
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

    def _stopped(self, status: str, *reasons: str, started_at: str | None = None) -> dict:
        first = StageResult("PREFLIGHT", status, True, warnings_stops=list(reasons))
        rest = [StageResult(stage, "STOP_DEPENDENCY", False, warnings_stops=["UPSTREAM_STOP"]) for stage in STAGES[1:]]
        return {"status": first.status, "started_at": started_at, "stop_reasons": list(reasons), "effects": {"network_requests": 0, "drive_reads": 0, "drive_writes": 0, "source_collection": 0, "live_reconciliation": 0}, "stages": [x.to_dict() for x in [first, *rest]]}

    @staticmethod
    def _markdown(r: dict) -> str:
        p = r["pinned_reference"]
        comparison = r["comparison"]
        if comparison == ["FIRST_RUN"]:
            comparison_text = "First compatible comparison baseline; no new/no-change claim is made."
        elif comparison == ["NO_CHANGE"]:
            comparison_text = "Anything new: no deterministic change detected."
        else:
            comparison_text = "Changes detected: " + ", ".join(comparison)
        return f"""# Operational summary — {r['profile_id']}

> **PROVEN FACT (historical pinned reference):** this is not a fresh collection. Presentation is not evidence.

- **Examined:** `{r['source_identities'][0]}` (`PINNED_REUSE`)
- **Run comparison:** {comparison_text}
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

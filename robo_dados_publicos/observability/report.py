from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .cards import MetricCard, RunCard, SourceCard
from .health import evaluate_source_health


SCHEMA_VERSION = 1
PASS_PREFIXES = ("PASS",)
STOP_PREFIXES = ("STOP", "FAIL", "ERROR")


def _status(value: Any) -> str:
    return str(value or "UNKNOWN").strip().upper()


def _health(value: Any) -> str:
    status = _status(value)
    if status.startswith(PASS_PREFIXES):
        return "HEALTHY"
    if status.startswith(STOP_PREFIXES):
        return "STOPPED"
    if status in {"NOT_CONFIGURED", "DISABLED", "NONE", "UNKNOWN"}:
        return "NOT_CONFIGURED"
    return "ATTENTION"


def _bool_checks(payload: dict[str, Any]) -> tuple[int, int, list[str]]:
    checks = payload.get("checks")
    if not isinstance(checks, dict):
        return 0, 0, []
    boolean_checks = {str(name): value for name, value in checks.items() if isinstance(value, bool)}
    failed = sorted(name for name, value in boolean_checks.items() if not value)
    return sum(boolean_checks.values()), len(boolean_checks), failed


def _source_execution(payload: dict[str, Any]) -> dict[str, Any]:
    collection = payload.get("source_collection")
    if not isinstance(collection, dict):
        return {
            "card_type": "SOURCE_EXECUTION",
            "status": "NOT_CONFIGURED",
            "health": "NOT_CONFIGURED",
            "enabled_sources": 0,
            "result_count": 0,
            "results": [],
        }

    inventory = collection.get("inventory") if isinstance(collection.get("inventory"), dict) else {}
    results: list[dict[str, Any]] = []
    for item in collection.get("results") or []:
        if not isinstance(item, dict):
            continue
        results.append(
            {
                "source_id": item.get("source_id"),
                "status": _status(item.get("status")),
                "http_status": item.get("http_status"),
                "content_type": item.get("content_type"),
                "bytes": item.get("bytes"),
                "integrity_verified": bool(item.get("sha256")),
            }
        )

    status = _status(collection.get("status"))
    return {
        "card_type": "SOURCE_EXECUTION",
        "status": status,
        "health": _health(status),
        "enabled_sources": int(inventory.get("enabled") or len(results)),
        "result_count": len(results),
        "results": results,
    }


def _runtime_source_id(source_execution: dict[str, Any]) -> str:
    results = source_execution.get("results") or []
    if len(results) == 1 and results[0].get("source_id"):
        return str(results[0]["source_id"])
    return "RUNTIME_INFRASTRUCTURE"


def _run_card(payload: dict[str, Any], source_execution: dict[str, Any]) -> RunCard | None:
    started_at = payload.get("started_at")
    finished_at = payload.get("finished_at")
    run_id = payload.get("run_id")
    software_version = payload.get("software_version")
    if not all(isinstance(value, str) and value.strip() for value in (started_at, finished_at, software_version)):
        return None
    passed, total, failed = _bool_checks(payload)
    status = _status(payload.get("status"))
    return RunCard(
        run_id=str(run_id if run_id is not None else "UNPUBLISHED_RUN"),
        source_id=_runtime_source_id(source_execution),
        software_version=str(software_version),
        started_at=str(started_at),
        finished_at=str(finished_at),
        status="PASS" if status.startswith(PASS_PREFIXES) else status,
        warnings=tuple(f"GATE_CHECK_FAILED:{name}" for name in failed),
        failure_reason="" if status.startswith(PASS_PREFIXES) else status,
        expected_absence=False,
    )


def _metric_definitions() -> dict[str, MetricCard]:
    cards = (
        MetricCard(
            metric_id="gate_checks_pass_rate",
            name="Taxa de checks aprovados",
            definition="Proporção de checks booleanos do gate que foram aprovados.",
            formula="checks_passed / checks_total",
            unit="ratio",
            source_fields=("checks",),
            null_semantics="NULL significa que o gate não forneceu checks booleanos; não equivale a zero.",
            limitations=("Não substitui a leitura individual dos checks.",),
        ),
        MetricCard(
            metric_id="enabled_sources",
            name="Fontes habilitadas na execução",
            definition="Quantidade de fontes explicitamente habilitadas no inventário da execução.",
            formula="source_collection.inventory.enabled",
            unit="count",
            source_fields=("source_collection.inventory.enabled",),
            null_semantics="Ausência de source_collection significa fonte não configurada, não zero observado.",
        ),
        MetricCard(
            metric_id="source_results",
            name="Resultados de fonte",
            definition="Quantidade de resultados de coleta expostos pela projeção sanitizada.",
            formula="len(source_collection.results)",
            unit="count",
            source_fields=("source_collection.results",),
            null_semantics="Ausência de source_collection significa fonte não configurada.",
        ),
        MetricCard(
            metric_id="append_only_log_created",
            name="Log append-only criado",
            definition="Indica se o gate confirmou criação do log append-only autorizado.",
            formula="bool(append_only_log_created)",
            unit="boolean",
            source_fields=("append_only_log_created",),
            null_semantics="Ausência ou falso não prova falha isoladamente; deve ser interpretada com o status do gate.",
        ),
        MetricCard(
            metric_id="run_latency_seconds",
            name="Latência da execução",
            definition="Duração observada entre início e fim da execução persistente.",
            formula="finished_at - started_at",
            unit="seconds",
            source_fields=("started_at", "finished_at"),
            null_semantics="NULL significa timestamps insuficientes para calcular duração.",
        ),
    )
    return {card.metric_id: card for card in cards}


def _metric_observations(
    payload: dict[str, Any],
    source_execution: dict[str, Any],
    run_card: RunCard | None,
) -> list[dict[str, Any]]:
    passed, total, _ = _bool_checks(payload)
    values = {
        "gate_checks_pass_rate": round(passed / total, 4) if total else None,
        "enabled_sources": source_execution.get("enabled_sources", 0),
        "source_results": source_execution.get("result_count", 0),
        "append_only_log_created": bool(payload.get("append_only_log_created")),
        "run_latency_seconds": run_card.latency_seconds if run_card else None,
    }
    definitions = _metric_definitions()
    observations: list[dict[str, Any]] = []
    for metric_id, card in definitions.items():
        value = values[metric_id]
        if metric_id == "gate_checks_pass_rate":
            status = "PASS" if value == 1.0 else ("NOT_AVAILABLE" if value is None else "ATTENTION")
        elif metric_id == "append_only_log_created":
            status = "PASS" if value is True else "ATTENTION"
        else:
            status = "OBSERVED" if value is not None else "NOT_AVAILABLE"
        observations.append({"card": card.to_dict(), "value": value, "status": status})
    return observations


def load_source_card_config(path: str | Path) -> SourceCard:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("source_card"), dict):
        raise ValueError("source card config must contain a source_card object")
    return SourceCard.from_mapping(payload["source_card"])


def build_observability_report(
    payload: dict[str, Any],
    *,
    source_card: SourceCard | None = None,
) -> dict[str, Any]:
    """Build an allowlist-only operator report from sanitized gate evidence."""
    if not isinstance(payload, dict):
        raise TypeError("payload must be a JSON object")

    source_execution = _source_execution(payload)
    run_card = _run_card(payload, source_execution)
    passed, total, failed = _bool_checks(payload)
    gate_status = _status(payload.get("status"))

    run_projection: dict[str, Any] = {
        "card_type": "RUN",
        "status": gate_status,
        "health": _health(gate_status),
        "software_version": payload.get("software_version"),
        "release_status": payload.get("release_status"),
        "state_source": payload.get("state_source"),
        "state_remote_mode": payload.get("state_remote_mode"),
        "append_only_log_created": bool(payload.get("append_only_log_created")),
        "started_at": payload.get("started_at"),
        "finished_at": payload.get("finished_at"),
        "checks_passed": passed,
        "checks_total": total,
        "failed_checks": failed,
    }
    if run_card is not None:
        run_projection["run_contract"] = run_card.to_dict()

    health = None
    source_contract = source_card.to_dict() if source_card is not None else None
    if source_card is not None and run_card is not None and source_card.source_id == run_card.source_id:
        health = evaluate_source_health(source_card, run_card)

    secret_safe = payload.get("secret_values_exposed") is False
    remote_safe = payload.get("remote_identifiers_exposed") is False
    privacy_status = "PASS" if secret_safe and remote_safe else "STOP_UNSAFE_INPUT_CONTRACT"

    if privacy_status != "PASS" or gate_status.startswith(STOP_PREFIXES):
        overall_health = "STOPPED"
    elif gate_status.startswith(PASS_PREFIXES):
        overall_health = "HEALTHY"
    else:
        overall_health = "ATTENTION"

    report = {
        "schema_version": SCHEMA_VERSION,
        "report_type": "RUN_OBSERVABILITY",
        "overall_health": overall_health,
        "run": run_projection,
        "source_contract": source_contract,
        "source_execution": source_execution,
        "health_dimensions": health,
        "metrics": _metric_observations(payload, source_execution, run_card),
        "privacy": {
            "status": privacy_status,
            "secret_values_exposed": not secret_safe,
            "remote_identifiers_exposed": not remote_safe,
            "allowlist_projection": True,
        },
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    run = report["run"]
    source = report["source_execution"]
    lines = [
        "# Relatório de observabilidade — ROBO_DADOS_PUBLICOS",
        "",
        f"**Saúde geral:** `{report['overall_health']}`  ",
        f"**Gate:** `{run['status']}`  ",
        f"**Software:** `{run.get('software_version') or 'não informado'}` / `{run.get('release_status') or 'não informado'}`  ",
        f"**Checks:** `{run['checks_passed']}/{run['checks_total']}`  ",
        f"**Estado remoto:** `{run.get('state_remote_mode') or 'não informado'}`  ",
        f"**Log append-only criado:** `{'sim' if run['append_only_log_created'] else 'não'}`  ",
        "",
        "## Fonte na execução",
        "",
        f"- status: `{source['status']}`",
        f"- saúde: `{source['health']}`",
        f"- fontes habilitadas: `{source['enabled_sources']}`",
        f"- resultados: `{source['result_count']}`",
    ]
    if report.get("source_contract"):
        contract = report["source_contract"]
        lines.extend(
            [
                "",
                "## Contrato da fonte",
                "",
                f"- source_id: `{contract['source_id']}`",
                f"- instituição: {contract['institution']}",
                f"- periodicidade: `{contract['periodicity']}`",
                f"- limiar de atualização: `{contract.get('expected_update_interval_hours')}`",
            ]
        )
    if report.get("health_dimensions"):
        lines.extend(["", "## Saúde multidimensional", ""])
        for name, dimension in report["health_dimensions"]["dimensions"].items():
            lines.append(f"- **{name}:** `{dimension['status']}`")
    lines.extend(
        [
            "",
            "## Métricas",
            "",
            "| Métrica | Valor | Unidade | Status |",
            "|---|---:|---|---|",
        ]
    )
    for observation in report["metrics"]:
        card = observation["card"]
        value = "n/d" if observation["value"] is None else str(observation["value"]).lower()
        lines.append(f"| `{card['metric_id']}` | {value} | {card['unit']} | `{observation['status']}` |")
    lines.extend(
        [
            "",
            "## Privacidade e proveniência",
            "",
            f"- contrato de privacidade: `{report['privacy']['status']}`",
            "- projeção por lista permitida: `sim`",
            "- credenciais, hashes e identificadores remotos: `não incluídos`",
            "",
            "> Relatório derivado de evidência sanitizada do gate. Não consulta a origem, não altera Bronze/Silver/Gold/Bancos/Logs e não substitui os logs append-only privados.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report_bundle(
    payload: dict[str, Any],
    output_dir: str | Path,
    *,
    source_card: SourceCard | None = None,
) -> dict[str, Any]:
    output = Path(output_dir)
    cards = output / "cards"
    cards.mkdir(parents=True, exist_ok=True)
    report = build_observability_report(payload, source_card=source_card)
    files: dict[Path, Any] = {
        output / "report.json": report,
        cards / "run.json": report["run"],
        cards / "source_execution.json": report["source_execution"],
        cards / "metrics.json": report["metrics"],
        cards / "health.json": report["health_dimensions"],
    }
    if report.get("source_contract") is not None:
        files[cards / "source_contract.json"] = report["source_contract"]
    for path, content in files.items():
        path.write_text(json.dumps(content, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "report.md").write_text(render_markdown(report), encoding="utf-8")
    return report

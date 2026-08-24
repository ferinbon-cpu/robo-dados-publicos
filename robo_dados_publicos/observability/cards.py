from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json


SCHEMA_VERSION = 1
PASS_PREFIXES = ("PASS",)
STOP_PREFIXES = ("STOP", "FAIL", "ERROR")


def _status(value) -> str:
    return str(value or "UNKNOWN").strip().upper()


def _health(value) -> str:
    status = _status(value)
    if status.startswith(PASS_PREFIXES):
        return "HEALTHY"
    if status.startswith(STOP_PREFIXES):
        return "STOPPED"
    if status in {"NOT_CONFIGURED", "DISABLED", "NONE", "UNKNOWN"}:
        return "NOT_CONFIGURED"
    return "ATTENTION"


def _duration_seconds(started_at, finished_at):
    if not started_at or not finished_at:
        return None
    try:
        started = datetime.fromisoformat(str(started_at).replace("Z", "+00:00"))
        finished = datetime.fromisoformat(str(finished_at).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return round(max(0.0, (finished - started).total_seconds()), 3)


def _bool_checks(payload: dict) -> tuple[int, int]:
    checks = payload.get("checks")
    if not isinstance(checks, dict):
        return 0, 0
    values = [value for value in checks.values() if isinstance(value, bool)]
    return sum(values), len(values)


def _source_card(payload: dict) -> dict:
    source = payload.get("source_collection")
    if not isinstance(source, dict):
        return {
            "card_type": "SOURCE",
            "status": "NOT_CONFIGURED",
            "health": "NOT_CONFIGURED",
            "enabled_sources": 0,
            "results": [],
        }
    inventory = source.get("inventory") if isinstance(source.get("inventory"), dict) else {}
    results = []
    for item in source.get("results") or []:
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
    status = _status(source.get("status"))
    return {
        "card_type": "SOURCE",
        "status": status,
        "health": _health(status),
        "enabled_sources": int(inventory.get("enabled") or len(results)),
        "result_count": len(results),
        "results": results,
    }


def _run_card(payload: dict) -> dict:
    status = _status(payload.get("status"))
    passed, total = _bool_checks(payload)
    return {
        "card_type": "RUN",
        "status": status,
        "health": _health(status),
        "software_version": payload.get("software_version"),
        "release_status": payload.get("release_status"),
        "state_source": payload.get("state_source"),
        "state_remote_mode": payload.get("state_remote_mode"),
        "append_only_log_created": bool(payload.get("append_only_log_created")),
        "started_at": payload.get("started_at"),
        "finished_at": payload.get("finished_at"),
        "duration_seconds": _duration_seconds(payload.get("started_at"), payload.get("finished_at")),
        "checks_passed": passed,
        "checks_total": total,
    }


def _metric_cards(payload: dict, source_card: dict, run_card: dict) -> list[dict]:
    metrics = [
        {
            "metric_id": "gate_checks_pass_rate",
            "value": (
                round(run_card["checks_passed"] / run_card["checks_total"], 4)
                if run_card["checks_total"] else None
            ),
            "unit": "ratio",
            "status": "PASS" if run_card["checks_total"] and run_card["checks_passed"] == run_card["checks_total"] else "NOT_AVAILABLE",
        },
        {
            "metric_id": "enabled_sources",
            "value": source_card["enabled_sources"],
            "unit": "count",
            "status": source_card["health"],
        },
        {
            "metric_id": "source_results",
            "value": source_card.get("result_count", 0),
            "unit": "count",
            "status": source_card["health"],
        },
        {
            "metric_id": "append_only_log_created",
            "value": run_card["append_only_log_created"],
            "unit": "boolean",
            "status": "PASS" if run_card["append_only_log_created"] else "NOT_AVAILABLE",
        },
    ]
    return metrics


def build_observability_report(payload: dict) -> dict:
    """Build an allowlist-only report; arbitrary input keys never propagate."""
    if not isinstance(payload, dict):
        raise TypeError("payload must be a JSON object")
    source_card = _source_card(payload)
    run_card = _run_card(payload)
    secret_safe = payload.get("secret_values_exposed") is False
    remote_safe = payload.get("remote_identifiers_exposed") is False
    report = {
        "schema_version": SCHEMA_VERSION,
        "report_type": "RUN_OBSERVABILITY",
        "overall_health": run_card["health"],
        "run": run_card,
        "source": source_card,
        "metrics": _metric_cards(payload, source_card, run_card),
        "privacy": {
            "secret_values_exposed": not secret_safe,
            "remote_identifiers_exposed": not remote_safe,
            "allowlist_projection": True,
        },
    }
    if not secret_safe or not remote_safe:
        report["overall_health"] = "STOPPED"
        report["privacy"]["status"] = "STOP_UNSAFE_INPUT_CONTRACT"
    else:
        report["privacy"]["status"] = "PASS"
    return report


def render_markdown(report: dict) -> str:
    run = report["run"]
    source = report["source"]
    lines = [
        "# Relatório de observabilidade — ROBO_DADOS_PUBLICOS",
        "",
        f"**Saúde geral:** `{report['overall_health']}`  ",
        f"**Execução:** `{run['status']}`  ",
        f"**Software:** `{run.get('software_version') or 'não informado'}` / `{run.get('release_status') or 'não informado'}`  ",
        f"**Estado remoto:** `{run.get('state_remote_mode') or 'não informado'}`  ",
        f"**Log append-only criado:** `{'sim' if run['append_only_log_created'] else 'não'}`  ",
        "",
        "## Fonte",
        "",
        f"- status: `{source['status']}`",
        f"- saúde: `{source['health']}`",
        f"- fontes habilitadas: `{source['enabled_sources']}`",
        f"- resultados: `{source.get('result_count', 0)}`",
        "",
        "## Métricas",
        "",
        "| Métrica | Valor | Unidade | Status |",
        "|---|---:|---|---|",
    ]
    for metric in report["metrics"]:
        value = "n/d" if metric["value"] is None else str(metric["value"]).lower()
        lines.append(f"| `{metric['metric_id']}` | {value} | {metric['unit']} | `{metric['status']}` |")
    lines.extend(
        [
            "",
            "## Privacidade e proveniência",
            "",
            f"- contrato de privacidade: `{report['privacy']['status']}`",
            "- projeção por lista permitida: `sim`",
            "- credenciais e identificadores remotos: `não incluídos`",
            "",
            "> Este relatório é derivado da evidência sanitizada do gate. Ele não consulta a origem, não altera Bronze/Silver/Gold e não substitui os logs append-only do Drive.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report_bundle(payload: dict, output_dir: str | Path) -> dict:
    output = Path(output_dir)
    cards = output / "cards"
    cards.mkdir(parents=True, exist_ok=True)
    report = build_observability_report(payload)
    files = {
        output / "report.json": report,
        cards / "run.json": report["run"],
        cards / "source.json": report["source"],
        cards / "metrics.json": report["metrics"],
    }
    for path, content in files.items():
        path.write_text(json.dumps(content, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "report.md").write_text(render_markdown(report), encoding="utf-8")
    return report

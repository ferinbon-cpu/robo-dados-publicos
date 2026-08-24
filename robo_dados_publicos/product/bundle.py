from __future__ import annotations

import csv
import hashlib
import html
import io
import json
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

from robo_dados_publicos.core.models import AnswerContract
from robo_dados_publicos.product.contracts import ReportCard
from robo_dados_publicos.release import SOFTWARE_VERSION


PRODUCT_FIELDS = (
    "status",
    "DADO",
    "CÁLCULO",
    "CORRESPONDÊNCIA",
    "INTERPRETAÇÃO",
    "CAUTELA",
    "FONTES",
)

OUTPUT_FORMATS = (
    "application/json",
    "text/csv",
    "text/markdown",
    "text/html",
    "application/pdf",
)

_ALLOWED_ANSWER_STATUSES = {"ANSWERED", "EVIDENCIA_INSUFICIENTE"}
_SENSITIVE_QUERY_MARKERS = (
    "token",
    "secret",
    "password",
    "passwd",
    "credential",
    "authorization",
    "auth",
    "api_key",
    "apikey",
    "access_key",
    "signature",
    "sig",
)


def _text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def sanitize_source_reference(source: str) -> str:
    """Redact credential-like URL query values while retaining public provenance."""
    value = _text(source)
    if not value:
        return ""
    try:
        parts = urlsplit(value)
    except ValueError:
        return value
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        return value
    pairs = []
    for key, val in parse_qsl(parts.query, keep_blank_values=True):
        lowered = key.casefold()
        if any(marker in lowered for marker in _SENSITIVE_QUERY_MARKERS):
            val = "REDACTED"
        pairs.append((key, val))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(pairs, doseq=True), ""))


def _row(answer: AnswerContract) -> dict[str, str]:
    if answer.status not in _ALLOWED_ANSWER_STATUSES:
        raise ValueError(f"ANSWER_STATUS_UNSUPPORTED: {answer.status}")
    sources = tuple(filter(None, (sanitize_source_reference(x) for x in answer.fontes)))
    return {
        "status": answer.status,
        "DADO": _text(answer.dado),
        "CÁLCULO": _text(answer.calculo),
        "CORRESPONDÊNCIA": _text(answer.correspondencia),
        "INTERPRETAÇÃO": _text(answer.interpretacao),
        "CAUTELA": _text(answer.cautela),
        "FONTES": " | ".join(sources),
    }


def _report_status(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "NO_DATA"
    if all(row["status"] == "EVIDENCIA_INSUFICIENTE" for row in rows):
        return "EVIDENCIA_INSUFICIENTE"
    if any(row["status"] == "EVIDENCIA_INSUFICIENTE" or row["CAUTELA"] for row in rows):
        return "READY_WITH_CAUTION"
    return "READY"


def build_product_report(
    answers: Iterable[AnswerContract],
    *,
    report_id: str,
    title: str,
    scope: str,
    generated_at: str,
    limitations: Iterable[str] = (),
    notes: str = "",
    software_version: str = SOFTWARE_VERSION,
) -> dict:
    rows = [_row(answer) for answer in answers]
    card = ReportCard(
        report_id=_text(report_id),
        title=_text(title),
        scope=_text(scope),
        software_version=_text(software_version),
        generated_at=_text(generated_at),
        status=_report_status(rows),
        row_count=len(rows),
        formats=OUTPUT_FORMATS,
        limitations=tuple(_text(x) for x in limitations if _text(x)),
        notes=_text(notes),
    )
    return {
        "schema_version": 1,
        "report_type": "MINIMAL_PRODUCT_OUTPUT",
        "report_card": card.to_dict(),
        "columns": list(PRODUCT_FIELDS),
        "rows": rows,
        "semantics": {
            "presentation_is_evidence": False,
            "zero_is_not_missing": True,
            "evidence_insufficient_is_explicit": True,
            "sources_are_provenance_references": True,
        },
    }


def render_csv(report: dict) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(PRODUCT_FIELDS), extrasaction="ignore")
    writer.writeheader()
    for row in report.get("rows", []):
        writer.writerow(row)
    return stream.getvalue()


def render_markdown(report: dict) -> str:
    card = report["report_card"]
    lines = [
        f"# {card['title']}",
        "",
        f"**Relatório:** `{card['report_id']}`  ",
        f"**Escopo:** {card['scope']}  ",
        f"**Status:** `{card['status']}`  ",
        f"**Linhas:** {card['row_count']}  ",
        f"**Software:** `{card['software_version']}`  ",
        f"**Gerado em:** {card['generated_at']}",
        "",
        "> A apresentação não substitui a evidência de origem. Cálculo, cautela e fontes permanecem explícitos.",
        "",
    ]
    if card.get("limitations"):
        lines.extend(["## Limitações", ""])
        lines.extend(f"- {x}" for x in card["limitations"])
        lines.append("")
    if card.get("notes"):
        lines.extend(["## Notas", "", card["notes"], ""])
    if not report.get("rows"):
        lines.extend(["## Resultados", "", "`NO_DATA` — nenhuma linha foi fornecida ao gerador.", ""])
        return "\n".join(lines)
    lines.extend(["## Resultados", ""])
    labels = PRODUCT_FIELDS[1:]
    for idx, row in enumerate(report["rows"], start=1):
        lines.extend([f"### {idx}. {row['status']}", ""])
        for label in labels:
            value = row.get(label, "") or "—"
            lines.append(f"**{label}:** {value}")
            lines.append("")
    return "\n".join(lines)


def render_html(report: dict) -> str:
    card = report["report_card"]
    esc = lambda x: html.escape(_text(x), quote=True)
    sections = []
    for idx, row in enumerate(report.get("rows", []), start=1):
        fields = "".join(
            f"<dt>{esc(label)}</dt><dd>{esc(row.get(label, '') or '—')}</dd>"
            for label in PRODUCT_FIELDS[1:]
        )
        sections.append(
            f"<section><h2>{idx}. {esc(row['status'])}</h2><dl>{fields}</dl></section>"
        )
    if not sections:
        sections.append("<section><h2>Resultados</h2><p><code>NO_DATA</code> — nenhuma linha foi fornecida ao gerador.</p></section>")
    limitations = "".join(f"<li>{esc(x)}</li>" for x in card.get("limitations", []))
    limitations_block = f"<section><h2>Limitações</h2><ul>{limitations}</ul></section>" if limitations else ""
    notes_block = f"<section><h2>Notas</h2><p>{esc(card.get('notes', ''))}</p></section>" if card.get("notes") else ""
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(card['title'])}</title>
<style>
body{{font-family:system-ui,-apple-system,sans-serif;max-width:980px;margin:32px auto;padding:0 20px;line-height:1.5}}
header,section{{border:1px solid #ddd;border-radius:10px;padding:18px;margin:16px 0}}
dt{{font-weight:700;margin-top:10px}}dd{{margin:2px 0 0 0;white-space:pre-wrap}}code{{font-family:ui-monospace,monospace}}
</style>
</head>
<body>
<header><h1>{esc(card['title'])}</h1><p><strong>Status:</strong> <code>{esc(card['status'])}</code> · <strong>Linhas:</strong> {card['row_count']} · <strong>Software:</strong> <code>{esc(card['software_version'])}</code></p><p><strong>Escopo:</strong> {esc(card['scope'])}<br><strong>Gerado em:</strong> {esc(card['generated_at'])}</p><p>A apresentação não substitui a evidência de origem.</p></header>
{limitations_block}{notes_block}{''.join(sections)}
</body></html>
"""


def _pdf_canvas(*args, **kwargs):
    kwargs["invariant"] = 1
    return rl_canvas.Canvas(*args, **kwargs)


def render_pdf(report: dict, destination: str | Path) -> Path:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(
        str(destination),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=report["report_card"]["title"],
        author="ROBO_DADOS_PUBLICOS",
    )
    card = report["report_card"]
    story = [
        Paragraph(html.escape(card["title"]), styles["Title"]),
        Spacer(1, 5 * mm),
        Paragraph(f"<b>Status:</b> {html.escape(card['status'])}", styles["BodyText"]),
        Paragraph(f"<b>Escopo:</b> {html.escape(card['scope'])}", styles["BodyText"]),
        Paragraph(f"<b>Software:</b> {html.escape(card['software_version'])}", styles["BodyText"]),
        Paragraph(f"<b>Gerado em:</b> {html.escape(card['generated_at'])}", styles["BodyText"]),
        Spacer(1, 4 * mm),
        Paragraph("A apresentação não substitui a evidência de origem. Cálculo, cautela e fontes permanecem explícitos.", styles["Italic"]),
        Spacer(1, 5 * mm),
    ]
    if card.get("limitations"):
        story.append(Paragraph("Limitações", styles["Heading2"]))
        for item in card["limitations"]:
            story.append(Paragraph("• " + html.escape(item), styles["BodyText"]))
        story.append(Spacer(1, 4 * mm))
    rows = report.get("rows", [])
    if not rows:
        story.append(Paragraph("NO_DATA — nenhuma linha foi fornecida ao gerador.", styles["BodyText"]))
    for idx, row in enumerate(rows, start=1):
        if idx > 1:
            story.append(PageBreak())
        story.append(Paragraph(f"{idx}. {html.escape(row['status'])}", styles["Heading2"]))
        for label in PRODUCT_FIELDS[1:]:
            value = row.get(label, "") or "—"
            safe_value = html.escape(value).replace("\n", "<br/>")
            story.append(Paragraph(f"<b>{html.escape(label)}:</b> {safe_value}", styles["BodyText"]))
            story.append(Spacer(1, 1.5 * mm))
    doc.build(story, canvasmaker=_pdf_canvas)
    return destination


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_product_bundle(report: dict, output_dir: str | Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "report.json": json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        "report_card.json": json.dumps(report["report_card"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        "table.csv": render_csv(report),
        "report.md": render_markdown(report) + "\n",
        "report.html": render_html(report),
    }
    for name, content in files.items():
        (output_dir / name).write_text(content, encoding="utf-8", newline="")
    render_pdf(report, output_dir / "report.pdf")

    inventory = []
    for name in (*files.keys(), "report.pdf"):
        path = output_dir / name
        inventory.append(
            {
                "name": name,
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    manifest = {
        "schema_version": 1,
        "bundle_type": "MINIMAL_PRODUCT_OUTPUT",
        "report_id": report["report_card"]["report_id"],
        "software_version": report["report_card"]["software_version"],
        "status": report["report_card"]["status"],
        "files": inventory,
        "drive_target": "08_OUTPUTS",
        "google_sheets_import_source": "table.csv",
        "publication_status": "LOCAL_ONLY_NOT_PUBLISHED",
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest

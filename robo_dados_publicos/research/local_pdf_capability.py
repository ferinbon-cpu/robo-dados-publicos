from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


class LocalPdfCapabilityStop(RuntimeError):
    """Fail-closed local-only PDF capability probe error."""


def _minimal_pdf_bytes(text: str) -> bytes:
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 18 Tf 72 720 Td ({safe}) Tj ET\n".encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"endstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(f"{index} 0 obj\n".encode("ascii"))
        out.extend(obj)
        out.extend(b"\nendobj\n")
    xref = len(out)
    out.extend(f"xref\n0 {len(objects)+1}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        out.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    out.extend(
        (
            f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\n"
            f"startxref\n{xref}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(out)


def write_synthetic_pdf(path: Path, text: str) -> None:
    path.write_bytes(_minimal_pdf_bytes(text))


def _json_request(method: str, url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    if not url.startswith("http://127.0.0.1:"):
        raise LocalPdfCapabilityStop("TASK105_NON_LOOPBACK_HTTP_BLOCKED")
    raw = None
    headers = {}
    if payload is not None:
        raw = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    request = Request(url, data=raw, headers=headers, method=method)
    try:
        with urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8")
    except URLError as exc:
        raise LocalPdfCapabilityStop("TASK105_LOOPBACK_WEBDRIVER_ERROR") from exc
    data = json.loads(body)
    if isinstance(data, dict) and isinstance(data.get("value"), dict):
        error = data["value"].get("error")
        if error:
            raise LocalPdfCapabilityStop(f"TASK105_WEBDRIVER:{error}")
    return data


def _ax_strings(nodes: list[dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for node in nodes:
        for key in ("name", "value", "description"):
            item = node.get(key)
            if isinstance(item, dict):
                value = item.get("value")
                if isinstance(value, str) and value.strip():
                    values.append(value.strip())
    return values


def probe_runner_capabilities() -> dict[str, Any]:
    commands = (
        "pdftotext",
        "pdfinfo",
        "pdftoppm",
        "mutool",
        "qpdf",
        "gs",
        "libreoffice",
        "google-chrome",
        "chromium",
        "chromedriver",
        "strings",
    )
    modules = (
        "pypdf",
        "PyPDF2",
        "fitz",
        "pdfplumber",
        "pdfminer",
        "selenium",
    )
    return {
        "schema": "TASK105_RUNNER_PDF_CAPABILITY_PROBE_V1",
        "commands": {name: shutil.which(name) for name in commands},
        "python_modules": {
            name: importlib.util.find_spec(name) is not None for name in modules
        },
    }


def probe_chrome_pdf_accessibility(
    *,
    marker: str = "TASK105_SYNTHETIC_PDF_MARKER_78421",
) -> dict[str, Any]:
    chromedriver = shutil.which("chromedriver")
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if not chromedriver or not chrome:
        return {
            "status": "UNAVAILABLE",
            "chromedriver": chromedriver,
            "chrome": chrome,
            "marker": marker,
            "marker_in_ax": False,
            "marker_in_source": False,
            "marker_in_body_inner_text": False,
        }

    port = 9515
    process = subprocess.Popen(
        [chromedriver, f"--port={port}", "--allowed-ips=127.0.0.1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    session_id: str | None = None
    try:
        deadline = time.time() + 8
        ready = False
        while time.time() < deadline:
            try:
                status = _json_request("GET", f"http://127.0.0.1:{port}/status")
                if status.get("value", {}).get("ready"):
                    ready = True
                    break
            except LocalPdfCapabilityStop:
                time.sleep(0.1)
        if not ready:
            raise LocalPdfCapabilityStop("TASK105_CHROMEDRIVER_NOT_READY")

        session = _json_request(
            "POST",
            f"http://127.0.0.1:{port}/session",
            {
                "capabilities": {
                    "alwaysMatch": {
                        "browserName": "chrome",
                        "goog:chromeOptions": {
                            "binary": chrome,
                            "args": [
                                "--headless",
                                "--no-sandbox",
                                "--disable-dev-shm-usage",
                                "--disable-gpu",
                                "--allow-file-access-from-files",
                                "--force-renderer-accessibility",
                            ],
                        },
                    }
                }
            },
        )
        value = session.get("value", {})
        session_id = value.get("sessionId") or session.get("sessionId")
        if not session_id:
            raise LocalPdfCapabilityStop("TASK105_WEBDRIVER_NO_SESSION_ID")

        with tempfile.TemporaryDirectory() as td:
            pdf = Path(td) / "synthetic.pdf"
            write_synthetic_pdf(pdf, marker)
            _json_request(
                "POST",
                f"http://127.0.0.1:{port}/session/{session_id}/url",
                {"url": pdf.resolve().as_uri()},
            )
            time.sleep(1.5)

            source_response = _json_request(
                "GET",
                f"http://127.0.0.1:{port}/session/{session_id}/source",
            )
            source = source_response.get("value")
            if not isinstance(source, str):
                source = ""

            inner = _json_request(
                "POST",
                f"http://127.0.0.1:{port}/session/{session_id}/execute/sync",
                {"script": "return document.body ? document.body.innerText : '';", "args": []},
            ).get("value")
            if not isinstance(inner, str):
                inner = ""

            ax = _json_request(
                "POST",
                f"http://127.0.0.1:{port}/session/{session_id}/goog/cdp/execute",
                {"cmd": "Accessibility.getFullAXTree", "params": {}},
            )
            nodes = ax.get("value", {}).get("nodes", [])
            if not isinstance(nodes, list):
                nodes = []
            strings = _ax_strings(nodes)

            return {
                "status": "PROBED",
                "chromedriver": chromedriver,
                "chrome": chrome,
                "marker": marker,
                "marker_in_ax": any(marker in item for item in strings),
                "marker_in_source": marker in source,
                "marker_in_body_inner_text": marker in inner,
                "ax_string_count": len(strings),
                "ax_strings_sample": strings[:40],
                "source_prefix": source[:500],
                "body_inner_text_prefix": inner[:500],
            }
    finally:
        if session_id is not None:
            try:
                _json_request(
                    "DELETE",
                    f"http://127.0.0.1:{port}/session/{session_id}",
                )
            except Exception:
                pass
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def prove_pypdf_text_extraction(
    *,
    marker: str = "TASK105_PYPDF_TEXT_MARKER_91743",
) -> dict[str, Any]:
    """Prove local deterministic PDF text extraction using the pinned pypdf dependency."""
    try:
        from io import BytesIO
        from pypdf import PdfReader
    except ImportError:
        return {
            "schema": "TASK105_LOCAL_PDF_PARSER_PROOF_V1",
            "parser": "pypdf",
            "status": "UNAVAILABLE",
            "marker": marker,
            "marker_in_text": False,
            "page_count": 0,
            "extracted_text": "",
        }

    raw = _minimal_pdf_bytes(marker)
    try:
        reader = PdfReader(BytesIO(raw))
        pages = [(page.extract_text() or "") for page in reader.pages]
    except Exception as exc:
        raise LocalPdfCapabilityStop("TASK105_PYPDF_EXTRACTION_ERROR") from exc

    extracted = "\n".join(pages)
    marker_in_text = marker in extracted
    if not marker_in_text:
        raise LocalPdfCapabilityStop("TASK105_PYPDF_MARKER_NOT_RECOVERED")

    return {
        "schema": "TASK105_LOCAL_PDF_PARSER_PROOF_V1",
        "parser": "pypdf",
        "status": "PROVEN",
        "marker": marker,
        "marker_in_text": True,
        "page_count": len(pages),
        "extracted_text": extracted,
    }


def extract_pdf_text_pypdf(pdf_path: Path) -> str:
    """Extract page-preserving text locally with the pinned pypdf dependency."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise LocalPdfCapabilityStop("TASK106_PYPDF_UNAVAILABLE") from exc

    try:
        reader = PdfReader(str(pdf_path))
        pages = [(page.extract_text() or "") for page in reader.pages]
    except Exception as exc:
        raise LocalPdfCapabilityStop("TASK106_PYPDF_EXTRACTION_ERROR") from exc

    text = "\f".join(pages)
    if not text.strip():
        raise LocalPdfCapabilityStop("TASK106_PDF_TEXT_EMPTY")
    return text

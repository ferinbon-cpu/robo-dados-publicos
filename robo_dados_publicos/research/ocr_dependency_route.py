from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class OcrDependencyRouteStop(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise OcrDependencyRouteStop(code)


def validate_ocr_dependency_route(data: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(data, dict), "TASK110_OBJECT")
    _require(data.get("schema") == "PPA_2018_2021_OCR_DEPENDENCY_ROUTE_V1", "TASK110_SCHEMA")
    _require(data.get("mode") == "T0_OFFLINE_DEPENDENCY_ROUTE_DESIGN_ONLY", "TASK110_MODE")
    target = data.get("target") or {}
    _require(target.get("period") == "2018-2021", "TASK110_PERIOD")
    _require(target.get("law_number") == "5.947/2017", "TASK110_LAW")
    _require(
        target.get("official_pdf_url")
        == "https://www.limeira.sp.gov.br/sitenovo/downloads/0fa1a5cc5c9a1823fbf5436def00f01f.pdf",
        "TASK110_SOURCE_URL",
    )

    runner = data.get("runner") or {}
    _require(runner == {"os_image": "ubuntu-24.04", "architecture": "amd64"}, "TASK110_RUNNER")

    route = data.get("canonical_route") or {}
    renderer = route.get("renderer") or {}
    _require(renderer.get("package") == "poppler-utils", "TASK110_RENDERER_PACKAGE")
    _require(renderer.get("version") == "24.02.0-1ubuntu9.9", "TASK110_RENDERER_VERSION")
    _require(renderer.get("executable") == "pdftoppm", "TASK110_RENDERER_EXECUTABLE")
    ocr = route.get("ocr_engine") or {}
    _require(ocr.get("package") == "tesseract-ocr", "TASK110_OCR_PACKAGE")
    _require(ocr.get("version") == "5.3.4-1build5", "TASK110_OCR_VERSION")
    lang = ocr.get("language_package") or {}
    _require(lang.get("package") == "tesseract-ocr-por", "TASK110_LANG_PACKAGE")
    _require(lang.get("version") == "1:4.1.0-2", "TASK110_LANG_VERSION")
    _require(lang.get("language_code") == "por", "TASK110_LANG_CODE")
    _require("tsv" in (ocr.get("command_template") or []), "TASK110_TSV_OUTPUT")

    rejected = {item.get("route") for item in data.get("explicitly_rejected_routes") or []}
    _require(
        {"CHROME_ACCESSIBILITY_ONLY", "PYTESSERACT_WRAPPER", "OCRMYPDF", "PYMUPDF_RENDERER", "OPENCV_PREPROCESSING"}
        <= rejected,
        "TASK110_REJECTED_ROUTES",
    )

    synthetic = data.get("task111_synthetic_gate") or {}
    _require(synthetic.get("authorized_now") is False, "TASK110_TASK111_NOT_AUTHORIZED")
    _require(synthetic.get("real_source_reads") == 0, "TASK110_TASK111_SOURCE_READS")
    _require(synthetic.get("real_source_ocr") is False, "TASK110_TASK111_REAL_OCR")
    _require(
        synthetic.get("dependency_install_allowlist")
        == [
            "poppler-utils=24.02.0-1ubuntu9.9",
            "tesseract-ocr=5.3.4-1build5",
            "tesseract-ocr-por=1:4.1.0-2",
        ],
        "TASK110_INSTALL_ALLOWLIST",
    )

    future = data.get("future_real_source_gate") or {}
    _require(future.get("authorized_now") is False, "TASK110_REAL_SOURCE_NOT_AUTHORIZED")
    _require(future.get("requires_task111_pass") is True, "TASK110_REQUIRES_TASK111")
    _require(future.get("exact_source_only") is True, "TASK110_EXACT_SOURCE")
    _require(future.get("discovery_search_allowed") is False, "TASK110_NO_DISCOVERY")
    _require(future.get("retry") is False, "TASK110_NO_RETRY")
    _require(future.get("max_pdf_pages") == 250, "TASK110_PAGE_BOUND")

    remote = data.get("remote_effects") or {}
    _require(remote and all(value is False for value in remote.values()), "TASK110_REMOTE_EFFECT")

    return {
        "status": "PASS_TASK110_OCR_DEPENDENCY_ROUTE_DESIGN",
        "canonical_route": "POPPLER_TESSERACT_POR_TSV",
        "package_count": 3,
        "real_source_authorized": False,
        "task111_authorized": False,
        "remote_effects": 0,
    }


def load_and_validate_ocr_dependency_route(path: str | Path) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise OcrDependencyRouteStop("TASK110_INPUT_MISSING") from exc
    except json.JSONDecodeError as exc:
        raise OcrDependencyRouteStop("TASK110_INPUT_JSON") from exc
    return validate_ocr_dependency_route(data)

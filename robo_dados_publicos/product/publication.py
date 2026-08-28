from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import tempfile
from typing import Any

from openpyxl import Workbook


GOOGLE_SHEETS_MIME = "application/vnd.google-apps.spreadsheet"
CSV_MIME = "text/csv"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PDF_MIME = "application/pdf"
JSON_MIME = "application/json"


class ProductPublicationError(RuntimeError):
    def __init__(self, code: str, *, created_count: int = 0):
        super().__init__(code)
        self.code = code
        self.created_count = created_count


@dataclass(frozen=True)
class PublicationNames:
    sheet: str
    pdf: str
    manifest: str

    @classmethod
    def from_basename(cls, basename: str) -> "PublicationNames":
        value = str(basename).strip()
        if not value or not re.fullmatch(r"[A-Za-z0-9_.-]{8,120}", value):
            raise ProductPublicationError("STOP_PRODUCT_PUBLICATION_BASENAME_INVALID")
        return cls(
            sheet=f"{value}_TABELA",
            pdf=f"{value}.pdf",
            manifest=f"{value}_publication_manifest.json",
        )

    def all(self) -> tuple[str, str, str]:
        return (self.sheet, self.pdf, self.manifest)


def _json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        raise ProductPublicationError("STOP_PRODUCT_BUNDLE_JSON_INVALID") from exc
    if not isinstance(value, dict):
        raise ProductPublicationError("STOP_PRODUCT_BUNDLE_JSON_MAPPING_REQUIRED")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalize_cell(value: str) -> str:
    return str(value).replace("\r\n", "\n").replace("\r", "\n")


def _csv_matrix(
    path: Path,
    *,
    error_code: str,
    created_count: int = 0,
) -> list[list[str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = [[_normalize_cell(cell) for cell in row] for row in csv.reader(handle)]
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        raise ProductPublicationError(error_code, created_count=created_count) from exc
    if not rows or not rows[0]:
        raise ProductPublicationError(error_code, created_count=created_count)
    width = len(rows[0])
    if width <= 0 or any(len(row) != width for row in rows):
        raise ProductPublicationError(error_code, created_count=created_count)
    return rows


def _write_xlsx(matrix: list[list[str]], destination: Path) -> None:
    try:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Tabela"
        for row in matrix:
            sheet.append(row)
        workbook.save(destination)
        workbook.close()
    except Exception as exc:
        raise ProductPublicationError("STOP_PRODUCT_TABLE_XLSX_BUILD") from exc


def validate_bundle_integrity(bundle_dir: str | Path, expected_report_status: str) -> dict:
    """Validate the entire local product bundle before any remote request."""
    root = Path(bundle_dir)
    report = _json(root / "report.json")
    card = _json(root / "report_card.json")
    manifest = _json(root / "manifest.json")

    if report.get("report_card") != card:
        raise ProductPublicationError("STOP_PRODUCT_REPORT_CARD_MISMATCH")
    if card.get("status") != expected_report_status:
        raise ProductPublicationError("STOP_PRODUCT_REPORT_STATUS_MISMATCH")
    if manifest.get("report_id") != card.get("report_id"):
        raise ProductPublicationError("STOP_PRODUCT_MANIFEST_REPORT_ID_MISMATCH")
    if manifest.get("software_version") != card.get("software_version"):
        raise ProductPublicationError("STOP_PRODUCT_MANIFEST_VERSION_MISMATCH")
    if manifest.get("publication_status") != "LOCAL_ONLY_NOT_PUBLISHED":
        raise ProductPublicationError("STOP_PRODUCT_BUNDLE_ALREADY_MARKED_PUBLISHED")
    if manifest.get("drive_target") != "08_OUTPUTS":
        raise ProductPublicationError("STOP_PRODUCT_DRIVE_TARGET_MISMATCH")
    if manifest.get("google_sheets_import_source") != "table.csv":
        raise ProductPublicationError("STOP_PRODUCT_SHEET_SOURCE_MISMATCH")

    files = manifest.get("files")
    if not isinstance(files, list) or len(files) != 6:
        raise ProductPublicationError("STOP_PRODUCT_MANIFEST_FILE_COUNT")
    names = {item.get("name") for item in files if isinstance(item, dict)}
    required = {"report.json", "report_card.json", "table.csv", "report.md", "report.html", "report.pdf"}
    if names != required:
        raise ProductPublicationError("STOP_PRODUCT_MANIFEST_FILE_SET")

    for item in files:
        if not isinstance(item, dict):
            raise ProductPublicationError("STOP_PRODUCT_MANIFEST_ENTRY_INVALID")
        path = root / str(item.get("name", ""))
        if not path.is_file():
            raise ProductPublicationError("STOP_PRODUCT_BUNDLE_FILE_MISSING")
        if path.stat().st_size != item.get("bytes"):
            raise ProductPublicationError("STOP_PRODUCT_BUNDLE_SIZE_MISMATCH")
        if _sha256(path) != item.get("sha256"):
            raise ProductPublicationError("STOP_PRODUCT_BUNDLE_HASH_MISMATCH")

    # Parse the canonical table before any remote request. This catches malformed
    # local CSV and yields the exact matrix later required from Sheet readback.
    table_matrix = _csv_matrix(
        root / "table.csv",
        error_code="STOP_PRODUCT_TABLE_CSV_INVALID",
    )
    return {"report": report, "card": card, "manifest": manifest, "table_matrix": table_matrix}


def _verify_parent(meta: dict, parent_id: str) -> bool:
    parents = meta.get("parents") or []
    return isinstance(parents, list) and parent_id in parents


def _remote_meta(drive, file_id: str, *, created_count: int) -> dict:
    try:
        meta = drive.metadata(file_id)
    except Exception as exc:
        raise ProductPublicationError(
            "STOP_PRODUCT_PUBLICATION_REMOTE_VERIFY",
            created_count=created_count,
        ) from exc
    if not isinstance(meta, dict):
        raise ProductPublicationError(
            "STOP_PRODUCT_PUBLICATION_REMOTE_METADATA_INVALID",
            created_count=created_count,
        )
    return meta


def _publication_manifest_payload(
    *,
    gate_id: str,
    published_at: str,
    card: dict,
    names: PublicationNames,
    bundle_dir: Path,
) -> dict[str, Any]:
    try:
        parsed = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProductPublicationError("STOP_PRODUCT_PUBLICATION_TIMESTAMP_INVALID") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ProductPublicationError("STOP_PRODUCT_PUBLICATION_TIMESTAMP_TIMEZONE_REQUIRED")
    return {
        "schema_version": 1,
        "publication_type": "M6_CONTROLLED_PRODUCT_OUTPUT",
        "gate_id": gate_id,
        "published_at": published_at,
        "report_id": card.get("report_id"),
        "software_version": card.get("software_version"),
        "report_status": card.get("status"),
        "drive_target": "08_OUTPUTS",
        "remote_names": {
            "google_sheet": names.sheet,
            "pdf": names.pdf,
            "completion_manifest": names.manifest,
        },
        "local_integrity": {
            "table_csv_sha256": _sha256(bundle_dir / "table.csv"),
            "report_pdf_sha256": _sha256(bundle_dir / "report.pdf"),
            "bundle_manifest_sha256": _sha256(bundle_dir / "manifest.json"),
        },
        "sheet_import_transport": "XLSX_LOCALE_INDEPENDENT",
        "sheet_semantic_readback_required": True,
        "completion_marker_written_last": True,
        "remote_identifiers_recorded": False,
        "overwrite_allowed": False,
    }


def publish_product_bundle(
    drive,
    *,
    output_parent_id: str,
    bundle_dir: str | Path,
    remote_basename: str,
    expected_report_status: str,
    gate_id: str,
    published_at: str,
) -> dict:
    """Publish exactly one Sheet, one PDF and one completion manifest.

    All local integrity and remote inventory checks happen before the first
    write. The canonical CSV is parsed locally, converted to XLSX to avoid
    locale-dependent delimiter inference, imported as a Google Sheet, then
    exported back to CSV and compared cell-for-cell with the canonical matrix.
    PDF and completion manifest are created only after that semantic readback
    passes. Exact-name collisions stop the gate. Existing files are never
    updated or deleted. The publication manifest is intentionally created last.
    """
    if not str(output_parent_id).strip():
        raise ProductPublicationError("STOP_PRODUCT_OUTPUT_PARENT_REQUIRED")
    names = PublicationNames.from_basename(remote_basename)
    root = Path(bundle_dir)
    validated = validate_bundle_integrity(root, expected_report_status)
    card = validated["card"]
    canonical_matrix = validated["table_matrix"]

    try:
        import_formats = drive.import_formats()
    except Exception as exc:
        raise ProductPublicationError("STOP_PRODUCT_IMPORT_FORMAT_DISCOVERY") from exc
    supported = import_formats.get(XLSX_MIME) or []
    if GOOGLE_SHEETS_MIME not in supported:
        raise ProductPublicationError("STOP_PRODUCT_XLSX_TO_SHEETS_NOT_SUPPORTED")

    try:
        children = drive.list_children(output_parent_id)
    except Exception as exc:
        raise ProductPublicationError("STOP_PRODUCT_OUTPUTS_INVENTORY_READ") from exc
    existing_names = {item.get("name") for item in children if isinstance(item, dict)}
    collisions = sorted(set(names.all()) & existing_names)
    if collisions:
        raise ProductPublicationError("STOP_PRODUCT_OUTPUT_NAME_COLLISION")

    # Precompute the completion marker before writes so timestamp and local
    # hashes cannot fail after remote mutation has started.
    publication_manifest = _publication_manifest_payload(
        gate_id=gate_id,
        published_at=published_at,
        card=card,
        names=names,
        bundle_dir=root,
    )
    publication_manifest_path = root / "publication_manifest.json"
    publication_manifest_path.write_text(
        json.dumps(publication_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    created = 0
    try:
        with tempfile.TemporaryDirectory(prefix="product-sheet-import-") as raw_temp:
            temp_root = Path(raw_temp)
            xlsx_path = temp_root / "table.xlsx"
            readback_csv_path = temp_root / "sheet_readback.csv"
            _write_xlsx(canonical_matrix, xlsx_path)

            sheet = drive.put_converted(
                xlsx_path,
                names.sheet,
                output_parent_id,
                XLSX_MIME,
                GOOGLE_SHEETS_MIME,
            )
            created += 1
            sheet_id = str(sheet.get("id") or "")
            if not sheet_id:
                raise ProductPublicationError("STOP_PRODUCT_SHEET_ID_MISSING", created_count=created)
            sheet_meta = _remote_meta(drive, sheet_id, created_count=created)
            if (
                sheet_meta.get("name") != names.sheet
                or sheet_meta.get("mimeType") != GOOGLE_SHEETS_MIME
                or not _verify_parent(sheet_meta, output_parent_id)
            ):
                raise ProductPublicationError("STOP_PRODUCT_SHEET_VERIFY", created_count=created)

            try:
                drive.export(sheet_id, readback_csv_path, CSV_MIME)
            except Exception as exc:
                raise ProductPublicationError(
                    "STOP_PRODUCT_SHEET_READBACK_EXPORT",
                    created_count=created,
                ) from exc
            observed_matrix = _csv_matrix(
                readback_csv_path,
                error_code="STOP_PRODUCT_SHEET_READBACK_INVALID",
                created_count=created,
            )
            if observed_matrix != canonical_matrix:
                raise ProductPublicationError(
                    "STOP_PRODUCT_SHEET_CONTENT_VERIFY",
                    created_count=created,
                )

        pdf_path = root / "report.pdf"
        pdf = drive.put(pdf_path, names.pdf, output_parent_id, PDF_MIME)
        created += 1
        pdf_id = str(pdf.get("id") or "")
        if not pdf_id:
            raise ProductPublicationError("STOP_PRODUCT_PDF_ID_MISSING", created_count=created)
        pdf_meta = _remote_meta(drive, pdf_id, created_count=created)
        if (
            pdf_meta.get("name") != names.pdf
            or pdf_meta.get("mimeType") != PDF_MIME
            or not _verify_parent(pdf_meta, output_parent_id)
            or int(pdf_meta.get("size") or -1) != pdf_path.stat().st_size
        ):
            raise ProductPublicationError("STOP_PRODUCT_PDF_VERIFY", created_count=created)

        completion_path = publication_manifest_path
        receipt = drive.put(completion_path, names.manifest, output_parent_id, JSON_MIME)
        created += 1
        receipt_id = str(receipt.get("id") or "")
        if not receipt_id:
            raise ProductPublicationError("STOP_PRODUCT_MANIFEST_ID_MISSING", created_count=created)
        receipt_meta = _remote_meta(drive, receipt_id, created_count=created)
        if (
            receipt_meta.get("name") != names.manifest
            or receipt_meta.get("mimeType") != JSON_MIME
            or not _verify_parent(receipt_meta, output_parent_id)
            or int(receipt_meta.get("size") or -1) != completion_path.stat().st_size
        ):
            raise ProductPublicationError("STOP_PRODUCT_MANIFEST_VERIFY", created_count=created)
    except ProductPublicationError:
        raise
    except Exception as exc:
        raise ProductPublicationError(
            "STOP_PRODUCT_PUBLICATION_REMOTE_OPERATION",
            created_count=created,
        ) from exc

    return {
        "status": "PASS_M6_PRODUCT_OUTPUT_PUBLICATION_GATE",
        "gate_id": gate_id,
        "report_id": card.get("report_id"),
        "report_status": card.get("status"),
        "drive_target": "08_OUTPUTS",
        "created_count": created,
        "google_sheet_created": True,
        "sheet_import_transport": "XLSX_LOCALE_INDEPENDENT",
        "sheet_semantic_readback_verified": True,
        "sheet_rows": len(canonical_matrix),
        "sheet_columns": len(canonical_matrix[0]),
        "pdf_created": True,
        "completion_manifest_created": True,
        "completion_manifest_written_last": True,
        "overwrite_performed": False,
        "remote_identifiers_exposed": False,
        "secret_values_exposed": False,
        "remote_names": list(names.all()),
    }

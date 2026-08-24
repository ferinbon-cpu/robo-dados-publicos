#!/usr/bin/env python3
"""One-time controlled publication gate for the 0.7.0 product candidate.

Publishes exactly three items in the configured 08_OUTPUTS folder:
- Google Sheet imported from table.csv;
- report.pdf;
- completion manifest JSON, written last.

No source collection, processing or reconciliation is executed here.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.core.models import AnswerContract
from robo_dados_publicos.product import build_product_report, write_product_bundle
from robo_dados_publicos.product.publication import (
    ProductPublicationError,
    PublicationNames,
    publish_product_bundle,
    validate_bundle_integrity,
)
from robo_dados_publicos.release import (
    ACTIVE_VALIDATED_VERSION,
    CURRENT_CANDIDATE_VERSION,
    NEXT_ACTION,
    RELEASE_STATUS,
    SOFTWARE_VERSION,
)
from robo_dados_publicos.storage.drive_rest import DriveRESTClient, OAuthCredentials, TokenProvider


EXPECTED_GATE_ID = "M6_FIRST_PRODUCT_OUTPUT_PUBLICATION_GATE_0_7_0"
EXPECTED_NEXT_ACTION = "M6_PRODUCT_OUTPUT_CONTROLLED_PUBLICATION_GATE_0_7_0"
EXPECTED_PUBLICATIONS = [
    "GOOGLE_SHEET_FROM_TABLE_CSV",
    "REPORT_PDF",
    "COMPLETION_MANIFEST_JSON",
]


def _stop(code: str, *, created_count: int = 0) -> tuple[dict, int]:
    return {
        "status": code,
        "created_count": created_count,
        "partial_write_possible": created_count > 0,
        "remote_identifiers_exposed": False,
        "secret_values_exposed": False,
    }, 16


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _answers(payload) -> list[AnswerContract]:
    items = payload.get("answers", []) if isinstance(payload, dict) else payload
    if not isinstance(items, list) or not items:
        raise ProductPublicationError("STOP_PRODUCT_GATE_ANSWERS_REQUIRED")
    out = []
    for item in items:
        if not isinstance(item, dict):
            raise ProductPublicationError("STOP_PRODUCT_GATE_ANSWER_MAPPING_REQUIRED")
        sources = item.get("FONTES", item.get("fontes", []))
        if isinstance(sources, str):
            sources = [sources]
        if not isinstance(sources, list):
            raise ProductPublicationError("STOP_PRODUCT_GATE_SOURCES_INVALID")
        out.append(
            AnswerContract(
                status=str(item.get("status", "")),
                dado=str(item.get("DADO", item.get("dado", "")) or ""),
                calculo=str(item.get("CÁLCULO", item.get("calculo", "")) or ""),
                correspondencia=str(item.get("CORRESPONDÊNCIA", item.get("correspondencia", "")) or ""),
                interpretacao=str(item.get("INTERPRETAÇÃO", item.get("interpretacao", "")) or ""),
                cautela=str(item.get("CAUTELA", item.get("cautela", "")) or ""),
                fontes=tuple(str(value) for value in sources),
            )
        )
    return out


def _validate_gate(gate: dict) -> None:
    if not isinstance(gate, dict):
        raise ProductPublicationError("STOP_PRODUCT_GATE_CONFIG_INVALID")
    exact = {
        "gate_id": EXPECTED_GATE_ID,
        "software_version": "0.7.0",
        "release_status": "CANDIDATE",
        "active_validated_version": "0.6.3",
        "parent_config_key": "outputs_id",
        "drive_target": "08_OUTPUTS",
        "required_remote_count": 3,
        "allow_overwrite": False,
        "collision_policy": "STOP_BEFORE_WRITES",
        "completion_manifest_written_last": True,
        "source_collection": "PROHIBITED",
        "processing_rerun": "PROHIBITED",
        "reconciliation_rerun": "PROHIBITED",
        "schedule": "DISABLED",
    }
    for key, value in exact.items():
        if gate.get(key) != value:
            raise ProductPublicationError(f"STOP_PRODUCT_GATE_CONTRACT_{key.upper()}")
    if gate.get("publications") != EXPECTED_PUBLICATIONS:
        raise ProductPublicationError("STOP_PRODUCT_GATE_PUBLICATIONS_SCOPE")
    report = gate.get("report")
    if not isinstance(report, dict):
        raise ProductPublicationError("STOP_PRODUCT_GATE_REPORT_CONFIG")
    for key in ("report_id", "title", "scope", "generated_at", "expected_status"):
        if not str(report.get(key, "")).strip():
            raise ProductPublicationError(f"STOP_PRODUCT_GATE_REPORT_{key.upper()}")
    if report.get("expected_status") != "READY_WITH_CAUTION":
        raise ProductPublicationError("STOP_PRODUCT_GATE_EXPECTED_STATUS")
    PublicationNames.from_basename(str(gate.get("remote_basename", "")))


def _validate_release_identity() -> None:
    if not (
        SOFTWARE_VERSION == "0.7.0"
        and RELEASE_STATUS == "CANDIDATE"
        and ACTIVE_VALIDATED_VERSION == "0.6.3"
        and CURRENT_CANDIDATE_VERSION == "0.7.0"
        and NEXT_ACTION == EXPECTED_NEXT_ACTION
    ):
        raise ProductPublicationError("STOP_PRODUCT_GATE_RELEASE_IDENTITY")


def _build_bundle(gate: dict, work_dir: Path) -> tuple[Path, dict]:
    answers_path = ROOT / str(gate["answers_file"])
    answers = _answers(_load_json(answers_path))
    report_cfg = gate["report"]
    report = build_product_report(
        answers,
        report_id=report_cfg["report_id"],
        title=report_cfg["title"],
        scope=report_cfg["scope"],
        generated_at=report_cfg["generated_at"],
        limitations=report_cfg.get("limitations", []),
        notes=report_cfg.get("notes", ""),
    )
    bundle_dir = work_dir / "product_bundle"
    write_product_bundle(report, bundle_dir)
    validate_bundle_integrity(bundle_dir, report_cfg["expected_status"])
    return bundle_dir, report


def run_gate(gate_config: str | Path, *, dry_run: bool = False) -> tuple[dict, int]:
    try:
        _validate_release_identity()
        gate_path = Path(gate_config)
        if not gate_path.is_absolute():
            gate_path = ROOT / gate_path
        gate = _load_json(gate_path)
        _validate_gate(gate)
        cloud = _load_json(ROOT / "config" / "cloud.json")
        output_parent_id = str(cloud.get(gate["parent_config_key"], "")).strip()
        if not output_parent_id:
            raise ProductPublicationError("STOP_PRODUCT_OUTPUT_PARENT_NOT_CONFIGURED")

        with tempfile.TemporaryDirectory(prefix="robo-product-gate-") as raw:
            bundle_dir, report = _build_bundle(gate, Path(raw))
            if dry_run:
                return {
                    "status": "PASS_M6_PRODUCT_OUTPUT_PUBLICATION_DRY_RUN",
                    "gate_id": gate["gate_id"],
                    "report_id": report["report_card"]["report_id"],
                    "report_status": report["report_card"]["status"],
                    "would_create": 3,
                    "drive_target": "08_OUTPUTS",
                    "remote_identifiers_exposed": False,
                    "secret_values_exposed": False,
                    "network_called": False,
                    "remote_writes": "NONE",
                }, 0

            credentials = OAuthCredentials.from_env()
            drive = DriveRESTClient(TokenProvider(credentials))
            result = publish_product_bundle(
                drive,
                output_parent_id=output_parent_id,
                bundle_dir=bundle_dir,
                remote_basename=gate["remote_basename"],
                expected_report_status=gate["report"]["expected_status"],
                gate_id=gate["gate_id"],
                published_at=datetime.now(timezone.utc).isoformat(),
            )
            return result, 0
    except ProductPublicationError as exc:
        return _stop(exc.code, created_count=exc.created_count)
    except RuntimeError as exc:
        # OAuthCredentials.from_env uses a RuntimeError. Never echo its text,
        # because generic future runtime errors could contain operational data.
        return _stop("STOP_PRODUCT_PUBLICATION_RUNTIME")
    except Exception:
        return _stop("STOP_PRODUCT_PUBLICATION_UNEXPECTED")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--gate-config",
        default="config/product_output.first_publication_gate.json",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    payload, code = run_gate(args.gate_config, dry_run=args.dry_run)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())

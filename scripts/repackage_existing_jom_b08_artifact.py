"""TASK290: validated, strictly bounded split of existing GitHub B08 artifact.

Never fetch the official site, access Drive, or publish. Source acquisition is
the one existing GitHub Actions artifact handled by the manual workflow.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT)

from scripts.download_jom_2026_archive_batch import batch_map
from scripts.download_jom_loa2027_pilot import inspect_pdf

RUN_ID = 38076191781
SOURCE_ARTIFACT = "jom2026-originais-B08-manifesto"
SOURCE_SHA = "9ebfb5c1d26f570429c40790842cae928b29b8ed"
EDITIONS = (7270, 7271, 7272, 7273, 7283, 7284, 7287, 7288, 7289)
CHUNK_BYTES = 90 * 1024 * 1024
MAX_PDF_BYTES = 200 * 1024 * 1024


class StopB08(RuntimeError):
    pass


def validate_context(env: dict) -> None:
    expected = (
        env.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
        and env.get("GITHUB_REF") == "refs/heads/main"
        and env.get("GITHUB_RUN_ATTEMPT") == "1"
        and env.get("B08_OWNER_CONFIRM") == "true"
        and env.get("B08_SOURCE_RUN") == str(RUN_ID)
        and bool(re.fullmatch(r"[a-f0-9]{40}", env.get("GITHUB_SHA", "")))
    )
    if not expected:
        raise StopB08("STOP_B08_MANUAL_MAIN_CONFIRMATION")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stage(source: Path, target: Path) -> dict:
    if target.exists():
        raise StopB08("STOP_B08_OUTPUT_EXISTS")
    if not source.is_dir():
        raise StopB08("STOP_B08_SOURCE_MISSING")
    try:
        manifest = json.loads((source / "manifest.json").read_text("utf-8"))
    except (OSError, ValueError):
        raise StopB08("STOP_B08_MANIFEST_UNREADABLE")

    expected_rows = batch_map()["B08"]
    if tuple(int(x["edition"]) for x in expected_rows) != EDITIONS:
        raise StopB08("STOP_B08_PINNED_ID_DRIFT")
    if not (
        manifest.get("schema") == "LOA2027_JOM_2026_BATCH_9_ORIGINALS_V1"
        and manifest.get("batch") == "B08"
        and manifest.get("github_sha") == SOURCE_SHA
        and manifest.get("validated_count") == 9
        and manifest.get("failed_count") == 0
        and manifest.get("source_get_attempts") == 9
        and manifest.get("drive_write_count") == 0
        and manifest.get("publication_count") == 0
    ):
        raise StopB08("STOP_B08_RUN_PROVENANCE")

    rows_list = manifest.get("documents", [])
    if len(rows_list) != 9 or len({x.get("edition") for x in rows_list}) != 9:
        raise StopB08("STOP_B08_MANIFEST_CARDINALITY")
    rows = {int(x["edition"]): x for x in rows_list}
    if set(rows) != set(EDITIONS):
        raise StopB08("STOP_B08_EDITION_DRIFT")
    originals = source / "originals"
    expected_files = {f"JOM_{e}_2026_ORIGINAL.pdf" for e in EDITIONS}
    if not originals.is_dir() or {x.name for x in originals.iterdir()} != expected_files:
        raise StopB08("STOP_B08_FILES_DRIFT")

    verified = []
    for expected in expected_rows:
        edition = int(expected["edition"])
        row = rows[edition]
        name = f"JOM_{edition}_2026_ORIGINAL.pdf"
        path = originals / name
        if not (
            row.get("file_name") == name
            and row.get("status") == "VALIDATED_ORIGINAL"
            and row.get("url") == expected["document_url"]
            and row.get("source_id") == expected["source_id"]
            and row.get("request_attempts") == 1
            and row.get("cover_edition_verified") is True
        ):
            raise StopB08(f"STOP_B08_DOCUMENT_METADATA_{edition}")
        size = path.stat().st_size
        if not (0 < size <= MAX_PDF_BYTES and row.get("bytes") == size):
            raise StopB08(f"STOP_B08_SIZE_{edition}")
        digest = sha256_file(path)
        if digest != row.get("sha256"):
            raise StopB08(f"STOP_B08_HASH_{edition}")
        if inspect_pdf(path, edition) != row.get("pages"):
            raise StopB08(f"STOP_B08_PDF_COVER_PAGES_{edition}")
        verified.append((edition, path, row, size))

    # All nine verified before *any* output. Generated artifacts never alter
    # original bytes; large PDFs get independently SHA-proved binary pieces.
    target.mkdir(parents=True, exist_ok=False)
    parts_total = 0
    for edition, path, row, size in verified:
        parts = (size + CHUNK_BYTES - 1) // CHUNK_BYTES
        if not 1 <= parts <= 3:
            raise StopB08("STOP_B08_CHUNK_BOUND")
        with path.open("rb") as stream:
            for i in range(1, parts + 1):
                dst = target / str(edition) / f"part{i:02d}"
                dst.mkdir(parents=True)
                name = path.name if parts == 1 else f"{path.name}.part{i:02d}"
                chunk = stream.read(CHUNK_BYTES)
                if not chunk or len(chunk) > CHUNK_BYTES:
                    raise StopB08("STOP_B08_CHUNK_BYTES")
                (dst / name).write_bytes(chunk)
                (dst / "manifest_excerpt.json").write_text(
                    json.dumps({
                        "schema": "LOA2027_TASK290_B08_SPLIT_V1",
                        "source_run_id": RUN_ID,
                        "source_artifact": SOURCE_ARTIFACT,
                        "source_head_sha": SOURCE_SHA,
                        "original_file": path.name,
                        "original_size": size,
                        "original_sha256": row["sha256"],
                        "edition": edition,
                        "total_parts": parts,
                        "part_number": i,
                        "part_size": len(chunk),
                        "part_sha256": hashlib.sha256(chunk).hexdigest(),
                        "source_document": row,
                        "original_bytes_reconstruct_by_order": True,
                    }, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                parts_total += 1
            if stream.read(1):
                raise StopB08("STOP_B08_UNEXPECTED_TRAILING_BYTES")
    return {"status": "PASS_B08_9_VALIDATED", "editions": list(EDITIONS),
            "parts_created": parts_total, "source_site_gets": 0,
            "drive_writes": 0, "source_run_id": RUN_ID}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    validate_context(os.environ)
    print(json.dumps(stage(args.source, args.out), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

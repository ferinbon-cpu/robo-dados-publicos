#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.manual_ingest.budget_journal_bounded_acquisition import (
    DriveCustodyStore,
    ExactPinnedHttpTransport,
    run_acquisition,
)
from robo_dados_publicos.storage.drive_rest import (
    DriveRESTClient,
    OAuthCredentials,
    TokenProvider,
)

BASE_IMPLEMENTATION_SHA = "2ffb26131a568790e841f56d6cf1432b1563db1c"
CONTRACT_PATH = ROOT / "config/budget_laws_journal_bounded_acquisition.v1.json"


def main() -> int:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    authorization = {
        "task": "TASK_032_BUDGET_JOURNAL_BOUNDED_ACQUISITION",
        "repository": "ferinbon-cpu/robo-dados-publicos",
        "branch": "main",
        "implementation_sha": BASE_IMPLEMENTATION_SHA,
        "source": "LIMEIRA_JORNAL_OFICIAL",
        "operation": "EXACT_3_JOM_PDF_GETS_CREATE_ONLY_CUSTODY_READBACK",
        "target_folder_id": "1CdL4T1CVIPqNph3f5xHbiU8KgxgPpkl5",
        "max_source_gets": 3,
        "max_drive_inventory_requests": 1,
        "max_drive_creates": 3,
        "max_drive_readbacks": 3,
        "automatic_retry": False,
        "overwrite": False,
        "replace": False,
        "delete": False,
        "cleanup": False,
        "ocr": False,
        "parser": False,
        "bronze": False,
        "silver": False,
        "gold": False,
        "serving": False,
        "publication": False,
        "schedule": False,
        "recurrence": False,
        "owner_authorized": True,
        "consumed": False,
    }

    credentials = OAuthCredentials.from_env()
    client = DriveRESTClient(TokenProvider(credentials))
    result = run_acquisition(
        contract=contract,
        source=ExactPinnedHttpTransport(),
        store=DriveCustodyStore(client),
        authorization=authorization,
        expected_sha=BASE_IMPLEMENTATION_SHA,
        work_dir=ROOT / ".task033_jom_work",
        offline_test_mode=False,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("status") == "PASS_TASK_032_JOM_EXACT_3_SOURCE_CUSTODY_READBACK_VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())

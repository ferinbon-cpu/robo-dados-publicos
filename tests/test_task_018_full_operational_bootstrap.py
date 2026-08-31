import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.operational.bootstrap_adapters import (
    DiscoveryContractError,
    DriveCreateOnlyStore,
    JornalSourceAdapter,
    JournalProcessorAdapter,
)
from robo_dados_publicos.operational.bootstrap_batch import (
    BootstrapBatch,
    Budget,
    deduplicate_discovery,
    reserve_one_shot,
    validate_canonical_projection,
)
from robo_dados_publicos.state.registry import StateRegistry

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads(
    (ROOT / "config/operational_bootstrap.full.v1.json").read_text(encoding="utf-8")
)


def auth(identity="b" * 40):
    value = json.loads(
        (
            ROOT
            / "docs/evidence/TASK_018_FULL_OPERATIONAL_BOOTSTRAP_OWNER_AUTHORIZATION_0.8.0.json"
        ).read_text(encoding="utf-8")
    )
    value.update(
        {
            "authorized": True,
            "status": "AUTHORIZED",
            "single_batch_authorized": True,
            "implementation_merge_sha": "a" * 40,
            "authorization_sha": identity,
        }
    )
    for key in (
        "source_read_authorized",
        "drive_read_authorized",
        "drive_create_only_authorized",
        "processing_authorized",
        "reconciliation_read_authorized",
        "product_generation_authorized",
        "product_publication_create_only_authorized",
    ):
        value[key] = True
    return value


def row(key, host="ecrie.com.br", url=None):
    return {
        "source_id": "LIMEIRA_JO_" + key.upper(),
        "logical_key": key,
        "file_name": key + ".pdf",
        "url": url or f"https://{host}/{key}.pdf",
        "allowed_hosts": [
            "ecrie.com.br",
            "limeira.sp.gov.br",
            "www.limeira.sp.gov.br",
        ],
        "publication_date": "2026-08-01",
        "source_page_url": "https://www.limeira.sp.gov.br/jornaloficial",
        "archive_class": "modern",
        "edition": 7311,
    }


def reconciliation_task(task_id="t1", target="LIMEIRA_CONTRATOS"):
    return {
        "task_id": task_id,
        "origin_event_id": "event-" + task_id,
        "origin_source_id": "LIMEIRA_JO_07311",
        "target_source": target,
        "task_type": "CONTRACT_LOOKUP",
        "status": "READY_SEARCH",
        "priority": 10,
        "rationale": "synthetic",
        "match_keys": {
            "year": 2026,
            "contract_number": "1/2026",
            "contractor": "Synthetic Ltd",
        },
        "search_hints": {},
        "minimum_link_confidence": "MEDIUM",
        "identity_rule": "SYNTHETIC_NO_PROMOTION",
    }


class Ocr(Exception):
    status = "STOP_OCR_REQUIRED"


class Source:
    def __init__(self, rows, telemetry=None, payloads=None, staged=False):
        self.rows = rows
        self.gets = []
        self.telemetry = telemetry or {"robots_get_count": 1, "index_get_count": 1}
        self.payloads = payloads or {}
        self.is_staged = staged

    def discover(self, family, maximum_pages):
        return self.rows, self.telemetry

    def get(self, url, maximum_bytes):
        self.gets.append(url)
        data = self.payloads.get(url, b"%PDF synthetic " + url.encode())
        host = url.split("/")[2]
        return data, {
            "https": True,
            "final_host": host,
            "content_type": "application/pdf",
            "remote_get_count": 0 if self.is_staged else 1,
        }


class Store:
    def __init__(self):
        self.objects = {}
        self.creates = []
        self.readbacks = []
        self.remote_ids = {}

    @staticmethod
    def _name(logical_key, suffix=""):
        return logical_key.replace("/", "_") + suffix

    def lookup(self, destination, logical_key, suffix=""):
        value = self.objects.get((destination, self._name(logical_key, suffix)))
        return dict(value) if value else None

    def create(self, destination, name, data, metadata):
        digest = hashlib.sha256(data).hexdigest()
        key = (destination, name)
        if key in self.objects:
            if self.objects[key]["sha256"] != digest:
                raise RuntimeError("STOP_CREATE_ONLY_INVARIANT")
            status = "REUSED_IDENTICAL"
        else:
            self.objects[key] = {
                "data": data,
                "sha256": digest,
                "bytes": len(data),
                **metadata,
            }
            self.creates.append(key)
            status = "CREATED"
        self.readback(destination, name)
        return {"status": status, "sha256": digest, "bytes": len(data), "name": name}

    def readback(self, destination, name):
        self.readbacks.append((destination, name))
        value = self.objects.get((destination, name))
        if not value:
            raise RuntimeError("STOP_MANIFEST_INTEGRITY")
        return {"name": name, "sha256": value["sha256"], "bytes": value["bytes"]}

    def get_by_id(self, file_id, *, cache_key="remote"):
        return dict(self.remote_ids[file_id])


class Processor:
    def __init__(self, fail_once=None, tasks=None, many=0):
        self.fail_once = fail_once
        self.tasks = tasks or []
        self.many = many

    def process(self, item, data):
        if self.fail_once == item["logical_key"]:
            self.fail_once = None
            raise Ocr()
        layers = {
            "Silver": [(item["source_id"] + "_silver.jsonl", b"{}")],
            "Gold": [(item["source_id"] + "_tasks.jsonl", b"{}")],
            "RAG": [(item["source_id"] + "_rag.jsonl", b"{}")],
            "Documentos": [],
        }
        if self.many:
            layers = {
                "Silver": [
                    (f"{item['source_id']}_{i}.json", b"{}") for i in range(self.many)
                ]
            }
        return {
            "layers": layers,
            "tasks": list(self.tasks),
            "metrics": {"status": "PASS_PROCESSING"},
        }


class Reconciler:
    def __init__(self):
        self.calls = []

    def execute(self, task, work_dir, maximum_requests):
        self.calls.append(task["task_id"])
        return {"task_id": task["task_id"], "status": "MATCH_CANDIDATE"}, 1


class FakeJournal:
    timeout = 1
    user_agent = "synthetic"

    def __init__(self, report):
        self.report = report

    def discover_month(self, year, month, max_pages):
        return dict(self.report)


class Task018Tests(unittest.TestCase):
    def run_batch(self, rows, **kwargs):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        source = kwargs.pop("source", None) or Source(rows)
        store = kwargs.pop("store", None) or Store()
        processor = kwargs.pop("processor", None) or Processor()
        reconciler = kwargs.pop("reconciler", None)
        config = kwargs.pop("config", None) or CONFIG
        authorization = kwargs.pop("authorization", None) or auth()
        validator = kwargs.pop("validator", None) or (lambda c: True)
        execution = kwargs.pop("execution", None)
        batch = BootstrapBatch(
            config,
            source,
            store,
            processor,
            reconciler=reconciler,
            canonical_validator=validator,
        )
        result = batch.run(
            Path(td.name) / "out",
            authorization,
            execution=execution,
            **kwargs,
        )
        return result, source, store, Path(td.name) / "out"

    def test_pending_authorization_and_canonical_drift_are_zero_effect(self):
        result, source, store, out = self.run_batch(
            [row("a")], authorization={"authorized": False}
        )
        self.assertEqual("STOP_OWNER_AUTHORIZATION_REQUIRED", result["status"])
        self.assertEqual([], source.gets)
        self.assertEqual([], store.creates)
        self.assertTrue((out.parent / "task-018-audit/operational_result.json").is_file())

        result, source, store, _ = self.run_batch([row("a")], validator=lambda c: False)
        self.assertEqual("STOP_CANONICAL_POLICY_DRIFT", result["status"])
        self.assertEqual(([], []), (source.gets, store.creates))

    def test_complete_canonical_projection_and_truthful_discovery_ceiling(self):
        self.assertTrue(validate_canonical_projection(CONFIG))
        expected = {
            "active": "0.7.0",
            "active_status": "ACTIVE",
            "candidate": "0.8.0",
            "candidate_status": "CANDIDATE",
            "closed_annual_series": "2016-2024",
            "year_2025": "PROVEN_STRUCTURAL_RECENT",
            "S1_NUM_POPU": "NOT_PROVEN",
            "S2_FINANCIAL_ALIAS_BRIDGE": "NOT_PROVEN",
            "annual_closure_status": "UNKNOWN",
            "semantic_comparability_status": "UNKNOWN",
            "gold_2025": "UNKNOWN/BLOCKED",
            "year_2026": "UNPROVEN_CURRENT_YEAR",
            "B1": "PENDING",
            "B2": "PENDING",
            "B3": "PENDING",
        }
        self.assertEqual(expected, CONFIG["release_boundary"])
        self.assertEqual(50, CONFIG["hard_safety_ceilings"]["maximum_index_discovery_pages"])

    def test_discovery_requires_exact_pass_and_reports_page_telemetry(self):
        adapter = JornalSourceAdapter(
            journal=FakeJournal(
                {
                    "status": "PARTIAL_DISCOVERY_MAX_PAGES",
                    "year": 2026,
                    "month": 8,
                    "pages_fetched": 50,
                    "editions": [],
                }
            )
        )
        with self.assertRaises(DiscoveryContractError):
            adapter.discover({"year": 2026, "month": 8, "allowed_hosts": ["ecrie.com.br"]}, 50)

        edition = {
            "source_id": "LIMEIRA_JO_07311",
            "logical_key": "a",
            "file_name": "a.pdf",
            "document_url": "https://ecrie.com.br/a.pdf",
            "publication_date": "2026-08-01",
            "edition": 7311,
            "source_page_url": "https://www.limeira.sp.gov.br/jornaloficial",
            "archive_class": "modern",
        }
        adapter = JornalSourceAdapter(
            journal=FakeJournal(
                {
                    "status": "PASS_DISCOVERY",
                    "year": 2026,
                    "month": 8,
                    "pages_fetched": 3,
                    "editions": [edition],
                }
            )
        )
        rows, telemetry = adapter.discover(
            {"year": 2026, "month": 8, "allowed_hosts": ["ecrie.com.br"]}, 50
        )
        self.assertEqual(1, len(rows))
        self.assertEqual(3, telemetry["robots_get_count"])
        self.assertEqual(3, telemetry["index_get_count"])

    def test_discovery_ambiguity_is_explicit(self):
        accepted, ambiguous = deduplicate_discovery(
            [
                row("same", url="https://ecrie.com.br/a.pdf"),
                row("same", url="https://ecrie.com.br/b.pdf"),
            ]
        )
        self.assertEqual([], accepted)
        self.assertEqual("STOP_DISCOVERY_AMBIGUITY", ambiguous[0]["status"])

    def test_t1_failure_is_carried_and_oversize_is_item_local(self):
        result, _, _, _ = self.run_batch(
            [],
            initial_items=[{**row("bad"), "status": "STOP_DOCUMENT_FETCH"}],
            discovered_count=1,
        )
        self.assertEqual("STOP_DOCUMENT_FETCH", result["items"][0]["status"])

        config = json.loads(json.dumps(CONFIG))
        config["hard_safety_ceilings"]["maximum_bytes_per_document"] = 20
        payloads = {
            row("large")["url"]: b"%PDF" + b"x" * 30,
            row("later")["url"]: b"%PDF ok",
        }
        source = Source([row("large"), row("later")], payloads=payloads)
        result, source, _, _ = self.run_batch(
            [row("large"), row("later")], config=config, source=source
        )
        states = {x["logical_key"]: x["status"] for x in result["items"]}
        self.assertEqual("STOP_DOCUMENT_TOO_LARGE", states["large"])
        self.assertEqual("PASS_ITEM", states["later"])
        self.assertEqual(2, len(source.gets))

    def test_unknown_host_is_blocked_and_ocr_does_not_kill_independent_items(self):
        result, _, _, _ = self.run_batch(
            [row("good"), row("unknown", host="surprise.example")]
        )
        states = {x["logical_key"]: x["status"] for x in result["items"]}
        self.assertEqual("PASS_ITEM", states["good"])
        self.assertEqual("STOP_DOCUMENT_HOST_UNPROVEN", states["unknown"])

        result, _, _, _ = self.run_batch(
            [row("a"), row("ocr"), row("z")], processor=Processor(fail_once="ocr")
        )
        states = {x["logical_key"]: x["status"] for x in result["items"]}
        self.assertEqual("COMPLETE", result["status"])
        self.assertEqual("STOP_OCR_REQUIRED", states["ocr"])
        self.assertEqual("PASS_ITEM", states["z"])

    def test_actual_t1_telemetry_is_seeded_and_all_get_categories_share_budget(self):
        budget = Budget(CONFIG["hard_safety_ceilings"])
        budget.add_gets("robots_get_count", 2)
        budget.add_gets("index_get_count", 3)
        budget.before_document()
        budget.add_gets("reconciliation_get_count", 4)
        self.assertEqual(10, budget.counts["total_remote_get_count"])

        staged = Source([row("a")], telemetry={"robots_get_count": 0, "index_get_count": 0}, staged=True)
        data = b"%PDF synthetic https://ecrie.com.br/a.pdf"
        store = Store()
        store.objects[("Bronze", "a.pdf")] = {
            "data": data,
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "source_url": "https://ecrie.com.br/a.pdf",
        }
        result, _, _, _ = self.run_batch(
            [row("a")],
            source=staged,
            store=store,
            initial_telemetry={
                "robots_get_count": 1,
                "index_get_count": 1,
                "document_get_count": 1,
                "reconciliation_get_count": 0,
                "source_bytes": len(data),
                "drive_create_operations": 1,
            },
        )
        self.assertEqual(1, result["telemetry"]["document_get_count"])
        self.assertEqual(3, result["telemetry"]["total_remote_get_count"])

    def test_create_budget_and_reconciliation_budget_are_enforced(self):
        config = json.loads(json.dumps(CONFIG))
        config["hard_safety_ceilings"]["maximum_drive_create_operations"] = 2
        result, _, store, _ = self.run_batch(
            [row("a")], processor=Processor(many=5), config=config
        )
        self.assertEqual("PARTIAL_BATCH_SAFETY_BUDGET_REACHED", result["status"])
        self.assertLessEqual(len(store.creates), 2)

        config = json.loads(json.dumps(CONFIG))
        config["hard_safety_ceilings"]["maximum_live_reconciliation_requests"] = 2
        reconciler = Reconciler()
        tasks = [reconciliation_task(f"t{i}") for i in range(3)]
        result, _, _, _ = self.run_batch(
            [row("a")],
            processor=Processor(tasks=tasks),
            reconciler=reconciler,
            config=config,
        )
        self.assertEqual("PARTIAL_BATCH_SAFETY_BUDGET_REACHED", result["status"])
        self.assertEqual(["t0", "t1"], reconciler.calls)

    def test_reconciliation_tasks_use_state_registry_and_bancos_only_for_sqlite_snapshot(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        state_path = Path(td.name) / "state.sqlite"
        result, _, store, _ = self.run_batch(
            [row("a")],
            processor=Processor(tasks=[reconciliation_task("state-task")]),
            reconciler=Reconciler(),
            state_path=state_path,
        )
        with StateRegistry(state_path) as state:
            tasks = state.list_reconciliation_tasks()
        self.assertEqual(1, len([x for x in tasks if x["task_id"] == "state-task"]))
        self.assertTrue(
            any(d == "Bancos" and n.endswith("__ROBOT_STATE.sqlite") for d, n in store.creates)
        )
        self.assertFalse(any(d == "Bancos" and n.endswith(".jsonl") for d, n in store.creates))
        self.assertIn(result["state_snapshot"]["status"], {"CREATED", "REUSED_IDENTICAL"})

    def test_existing_bronze_resumes_and_private_remote_id_does_not_leak(self):
        store = Store()
        data = b"%PDF synthetic https://ecrie.com.br/a.pdf"
        store.objects[("Bronze", "a.pdf")] = {
            "data": data,
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "source_url": "https://ecrie.com.br/a.pdf",
        }
        result, source, store, _ = self.run_batch([row("a")], store=store)
        self.assertEqual([], source.gets)
        self.assertEqual("REUSED_IDENTICAL", result["items"][0]["bronze_state"])
        self.assertIn(("Silver", "LIMEIRA_JO_A_silver.jsonl"), store.creates)
        self.assertNotIn(("Bronze", "a.pdf"), store.creates)

        store = Store()
        remote = b"%PDF already proven"
        store.remote_ids["opaque"] = {
            "data": remote,
            "sha256": hashlib.sha256(remote).hexdigest(),
            "bytes": len(remote),
        }
        known = row("known")
        known["bronze_remote_id"] = "opaque"
        known["expected_sha256"] = hashlib.sha256(remote).hexdigest()
        result, source, _, _ = self.run_batch([known], store=store)
        self.assertEqual([], source.gets)
        self.assertNotIn("bronze_remote_id", json.dumps(result))

    def test_one_shot_reservation_and_run_attempt_policy(self):
        store = Store()
        execution = {"github_run_id": "100", "github_run_attempt": "1"}
        first = reserve_one_shot(store, auth(), execution)
        second = reserve_one_shot(store, auth(), execution)
        rerun = reserve_one_shot(
            Store(), auth(), {"github_run_id": "100", "github_run_attempt": "2"}
        )
        self.assertEqual("PASS_BATCH_ONE_SHOT_RESERVED", first["status"])
        self.assertEqual("STOP_BATCH_AUTHORIZATION_CONSUMED", second["status"])
        self.assertEqual("STOP_BATCH_AUTHORIZATION_CONSUMED", rerun["status"])

    def test_publication_is_create_only_manifest_last_and_readback_verified(self):
        result, _, store, out = self.run_batch([row("a")])
        before = len(store.creates)
        BootstrapBatch(CONFIG, None, store, None).publish(out, result)
        outputs = [x for x in store.creates[before:] if x[0] == "Outputs"]
        self.assertTrue(outputs[-1][1].endswith("manifest.json"))
        self.assertTrue(all(("Outputs", name) in store.readbacks for _, name in outputs))
        self.assertTrue(result["publication"]["final_readback_required"])
        self.assertEqual("COMPLETE", result["publication"]["batch_status"])

    def test_workflow_and_runner_enforce_pre_t1_reservation_and_proven_secrets(self):
        workflow = (
            ROOT / ".github/workflows/task-018-full-operational-bootstrap.yml"
        ).read_text(encoding="utf-8")
        for secret in (
            "GOOGLE_DRIVE_CLIENT_ID",
            "GOOGLE_DRIVE_CLIENT_SECRET",
            "GOOGLE_DRIVE_REFRESH_TOKEN",
        ):
            self.assertIn(secret, workflow)
        self.assertNotIn("GOOGLE_CLIENT_ID", workflow)
        self.assertLess(workflow.index("T2_RESERVE_ONE_SHOT"), workflow.index("T1_DISCOVER_AND_COLLECT"))
        self.assertLess(workflow.index("T1_DISCOVER_AND_COLLECT"), workflow.index("T2_CREATE_ONLY_PERSIST_AND_PROCESS"))
        self.assertLess(workflow.index("T2_CREATE_ONLY_PERSIST_AND_PROCESS"), workflow.index("T3_CREATE_ONLY_PRODUCT_PUBLICATION"))

        runner = (
            ROOT / "scripts/github_task_018_full_operational_bootstrap.py"
        ).read_text(encoding="utf-8")
        self.assertIn("GITHUB_RUN_ATTEMPT", runner)
        self.assertIn('!= "1"', runner)
        self.assertIn("deduplicate_discovery(rows)", runner)
        self.assertLess(runner.index("deduplicate_discovery(rows)"), runner.index("source.get("))
        self.assertIn("collection_failures", runner)
        self.assertIn("initial_telemetry=initial_telemetry", runner)

    def test_processor_keeps_task_jsonl_out_of_bancos_and_fixture_is_synthetic(self):
        self.assertEqual("Gold", JournalProcessorAdapter.LAYERS["reconciliation_tasks.jsonl"])
        text = (ROOT / "tests/fixtures/task_018_bootstrap/README.txt").read_text(encoding="utf-8")
        for phrase in (
            "SYNTHETIC",
            "NOT FROM LIVE SOURCES",
            "NO REAL PERSONAL DATA",
            "NO PROMOTION EFFECT",
        ):
            self.assertIn(phrase, text)
        self.assertFalse(CONFIG["schedule"])
        self.assertFalse(CONFIG["recurrence"])
        self.assertFalse(CONFIG["automatic_retry"])
        self.assertEqual("PROHIBITED", CONFIG["reconciliation"]["financial_identity_auto_promotion"])

    def test_product_contains_task017_identities_and_detailed_summary(self):
        result, _, _, out = self.run_batch(
            [row("a")],
            execution={
                "github_run_id": "synthetic",
                "github_run_attempt": "1",
                "execution_sha": "c" * 40,
            },
        )
        self.assertTrue(result["snapshot_id"].startswith("SNAP-"))
        self.assertTrue(result["run_id"].startswith("RUN-"))
        self.assertTrue(result["batch_id"].startswith("BATCH-"))
        summary = (out / "operational_summary.md").read_text(encoding="utf-8")
        for term in (
            "families_considered",
            "discovered",
            "bronze_created",
            "processed",
            "derived",
            "item_local_failures",
            "reconciliation_tasks",
            "state_snapshot",
            "budget",
            "checkpoint",
            "publication",
        ):
            self.assertIn(term, summary)


if __name__ == "__main__":
    unittest.main()

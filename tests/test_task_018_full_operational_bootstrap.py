import json
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.operational.bootstrap_batch import BootstrapBatch, eligibility_inventory

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config/operational_bootstrap.full.v1.json").read_text())


def auth():
    value = json.loads((ROOT / "docs/evidence/TASK_018_FULL_OPERATIONAL_BOOTSTRAP_OWNER_AUTHORIZATION_0.8.0.json").read_text())
    value["authorized"] = True; value["status"] = "AUTHORIZED"; value["implementation_merge_sha"] = "a" * 40
    for key in ("source_read_authorized", "drive_read_authorized", "drive_create_only_authorized", "processing_authorized", "reconciliation_read_authorized", "product_generation_authorized", "product_publication_create_only_authorized"):
        value[key] = True
    return value


class OcrError(Exception): status = "STOP_OCR_REQUIRED"


class Source:
    def __init__(self, rows): self.rows, self.gets, self.discoveries = rows, [], []
    def discover(self, family, maximum_pages): self.discoveries.append(family["source_family"]); return self.rows
    def get(self, url, maximum_bytes):
        self.gets.append(url); data = b"bad" if "bad" in url else b"%PDF synthetic " + url.encode()
        return data, {"https": True, "final_host": "limeira.sp.gov.br", "content_type": "application/pdf"}


class Store:
    def __init__(self): self.objects, self.creates, self.readbacks = {}, [], []
    def lookup(self, destination, logical_key): return self.objects.get((destination, logical_key))
    def create(self, destination, name, data, metadata):
        logical = metadata.get("logical_key", name.rsplit(".", 1)[0])
        key = (destination, logical)
        if key in self.objects: raise AssertionError("overwrite attempted")
        record = dict(metadata); record["sha256"] = metadata.get("sha256")
        self.objects[key] = record; self.creates.append((destination, name)); return record
    def readback(self, destination, name): self.readbacks.append((destination, name)); return {}


class Processor:
    def process(self, item, data):
        if "ocr" in item["logical_key"]: raise OcrError()
        return {"layers": {"Silver": [(item["logical_key"] + ".json", b"{}")], "RAG": [(item["logical_key"] + ".jsonl", b"{}")], "Gold": []}}


def row(key, suffix=None):
    return {"source_id": "LIMEIRA_JORNAL_OFICIAL_" + key.upper(), "logical_key": key, "url": "https://limeira.sp.gov.br/" + (suffix or key) + ".pdf", "allowed_hosts": ["limeira.sp.gov.br"], "publication_date": "2026-01-01"}


class TestTask018(unittest.TestCase):
    def run_batch(self, rows, store=None, config=None):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        source, store = Source(rows), store or Store()
        result = BootstrapBatch(config or CONFIG, source, store, Processor()).run(Path(td.name) / "out", auth())
        return result, source, store, Path(td.name) / "out"

    def test_inventory_is_contract_driven_and_tda_and_2025_blocked(self):
        inventory = eligibility_inventory(CONFIG); classes = {x["source_family"]: x["classification"] for x in inventory}
        self.assertEqual("ELIGIBLE_LIVE_COLLECTION", classes["LIMEIRA_JORNAL_OFICIAL"])
        self.assertEqual("BLOCKED_CONTRACT_UNPROVEN", classes["LIMEIRA_TDA_PORTAL"])
        self.assertEqual("BLOCKED_SEMANTIC_UNPROVEN", classes["SIOPE_2025"])
        result, source, _, _ = self.run_batch([row("one")])
        self.assertEqual(["LIMEIRA_JORNAL_OFICIAL"], source.discoveries)
        self.assertNotIn("TDA", json.dumps(source.gets).upper())
        self.assertNotIn("SIOPE", json.dumps(source.gets).upper())

    def test_drains_multiple_and_item_local_failures_continue(self):
        result, source, store, out = self.run_batch([row("one"), row("ocr"), row("bad", "bad"), row("later")])
        self.assertEqual("COMPLETE", result["status"])
        self.assertEqual({"one": "PASS_ITEM", "ocr": "STOP_OCR_REQUIRED", "bad": "STOP_DOCUMENT_NOT_PDF", "later": "PASS_ITEM"}, {x["logical_key"]: x["status"] for x in result["items"]})
        self.assertEqual(4, len(source.gets)); self.assertTrue((out / "product/manifest.json").is_file())
        self.assertTrue((out / "operational_result.json").is_file())
        self.assertIn(("Quarantine", "ocr.json"), store.creates)

    def test_authorization_or_canonical_drift_stops_before_all_effects(self):
        source, store = Source([row("one")]), Store()
        with tempfile.TemporaryDirectory() as td:
            result = BootstrapBatch(CONFIG, source, store, Processor()).run(Path(td) / "out", {"authorized": False})
        self.assertEqual("STOP_OWNER_AUTHORIZATION_REQUIRED", result["status"]); self.assertEqual([], source.gets); self.assertEqual([], store.creates)
        with tempfile.TemporaryDirectory() as td:
            result = BootstrapBatch(CONFIG, source, store, Processor()).run(Path(td) / "out", auth(), preflight_ok=False)
        self.assertEqual("STOP_CANONICAL_POLICY_DRIFT", result["status"]); self.assertEqual([], source.gets)

    def test_dedupe_exact_skip_and_collision_never_overwrite(self):
        store = Store(); store.objects[("Bronze", "known")] = {"sha256": "abc"}; store.objects[("Bronze", "collision")] = {"sha256": "old"}
        known, collision = row("known"), row("collision"); known["expected_sha256"] = "abc"; collision["expected_sha256"] = "new"
        result, source, store, _ = self.run_batch([known, collision, row("new")], store)
        self.assertEqual(["STOP_DOCUMENT_HASH_COLLISION", "SKIPPED_ALREADY_PROVEN", "PASS_ITEM"], [x["status"] for x in result["items"]])
        self.assertEqual(1, len(source.gets)); self.assertEqual("old", store.objects[("Bronze", "collision")]["sha256"])

    def test_safety_budget_is_partial_with_checkpoint(self):
        config = json.loads(json.dumps(CONFIG)); config["hard_safety_ceilings"]["maximum_documents"] = 2
        result, _, _, _ = self.run_batch([row("a"), row("b"), row("c")], config=config)
        self.assertEqual("PARTIAL_BATCH_SAFETY_BUDGET_REACHED", result["status"]); self.assertEqual(["c"], result["checkpoint"]["remaining_logical_keys"])

    def test_second_batch_skips_proven_source_objects(self):
        store = Store(); first, _, store, _ = self.run_batch([row("a"), row("b")], store)
        rows = [row("a"), row("b")]
        for item in first["items"]: rows[[x["logical_key"] for x in rows].index(item["logical_key"])]["expected_sha256"] = item["sha256"]
        second, source, _, _ = self.run_batch(rows, store)
        self.assertEqual(["SKIPPED_ALREADY_PROVEN"] * 2, [x["status"] for x in second["items"]]); self.assertEqual([], source.gets)

    def test_policy_no_mutation_retry_recurrence_or_fake_promotion(self):
        self.assertEqual({"create_only": True, "overwrite": False, "replace": False, "delete": False}, CONFIG["mutation_policy"])
        self.assertFalse(CONFIG["schedule"]); self.assertFalse(CONFIG["recurrence"]); self.assertFalse(CONFIG["automatic_retry"])
        self.assertEqual("PROHIBITED", CONFIG["reconciliation"]["financial_identity_auto_promotion"])
        self.assertEqual("UNKNOWN/BLOCKED", CONFIG["release_boundary"]["gold_2025"])

    def test_fixture_disclaimer(self):
        text = (ROOT / "tests/fixtures/task_018_bootstrap/README.txt").read_text()
        for phrase in ("SYNTHETIC", "NOT FROM LIVE SOURCES", "NO REAL PERSONAL DATA", "NO PROMOTION EFFECT"): self.assertIn(phrase, text)


if __name__ == "__main__": unittest.main()

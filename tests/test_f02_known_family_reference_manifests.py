from __future__ import annotations

import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.f02_known_family_bundle import (
    load_json,
    validate_adapter_contract,
    validate_batch_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "config/f02_known_family_bundle_adapter.v1.json"
APR_MANIFEST = ROOT / "docs/evidence/f02_known_family/F02_REAL_PROVEN_2026_JAN_APR_REFERENCE_MANIFEST.json"
MAY_MANIFEST = ROOT / "docs/evidence/f02_known_family/F02_REAL_PROVEN_2026_JAN_MAY_REFERENCE_MANIFEST.json"
APR_SILVER = ROOT / "docs/evidence/f02_gold_preview/F02_MDE_FUNDEB_2026_JAN_ABR__72cc2cb29990__silver_v1.json"
MAY_SILVER = ROOT / "docs/evidence/f02_gold_preview/F02_LOCAL_MONITORING_2026_JAN_MAY__d244b94d04f9__silver_v1.json"


class F02KnownFamilyReferenceManifestTests(unittest.TestCase):
    def setUp(self):
        self.adapter = validate_adapter_contract(load_json(ADAPTER))

    def test_reference_manifests_are_data_only_and_contract_valid(self):
        apr = validate_batch_manifest(load_json(APR_MANIFEST), self.adapter)
        may = validate_batch_manifest(load_json(MAY_MANIFEST), self.adapter)
        self.assertEqual(apr["batch_kind"], "RREO_ALIGNED")
        self.assertEqual(apr["period_end"], "2026-04-30")
        self.assertEqual(may["batch_kind"], "LOCAL_ONLY")
        self.assertEqual(may["period_end"], "2026-05-31")
        for raw in (load_json(APR_MANIFEST), load_json(MAY_MANIFEST)):
            self.assertTrue(all(value is False for value in raw["remote_effects_authorized"].values()))
            for item in raw["sources"]:
                self.assertTrue(item["snapshot_path"].startswith("runtime/f02/"))
                self.assertFalse(Path(item["snapshot_path"]).is_absolute())

    def test_april_manifest_matches_proven_silver_source_custody(self):
        manifest = load_json(APR_MANIFEST)
        silver = load_json(APR_SILVER)
        bronze = silver["bronze"]
        for source in manifest["sources"]:
            observed = bronze[source["family"]]
            self.assertEqual(source["drive_file_id"], observed["inbox_drive_file_id"])
            self.assertEqual(source["expected_sha256"], observed["sha256"])
            self.assertEqual(source["expected_bytes"], observed["bytes"])
            self.assertTrue(observed["readback_byte_identity"])
        self.assertEqual(silver["status"], "SILVER_SCOPED_VALIDATED")

    def test_may_manifest_matches_proven_silver_source_custody(self):
        manifest = load_json(MAY_MANIFEST)
        silver = load_json(MAY_SILVER)
        by_family = {
            item["family"]: item
            for item in silver["promotion_provenance"]["bronze_sources"]
        }
        for source in manifest["sources"]:
            observed = by_family[source["family"]]
            self.assertEqual(source["drive_file_id"], observed["inbox_drive_file_id"])
            self.assertEqual(source["expected_sha256"], observed["sha256"])
            self.assertEqual(source["expected_bytes"], observed["bytes"])
            self.assertTrue(observed["readback_byte_identity"])
        self.assertEqual(
            silver["status"],
            "SILVER_PROMOTED_VALIDATED_LOCAL_MONITORING_ONLY",
        )

    def test_examples_preserve_official_vs_local_semantics(self):
        apr = load_json(APR_MANIFEST)
        may = load_json(MAY_MANIFEST)
        self.assertIn("RREO_MDE", {x["family"] for x in apr["sources"]})
        self.assertNotIn("RREO_MDE", {x["family"] for x in may["sources"]})
        self.assertEqual(
            {x["family"] for x in may["sources"]},
            {"FUNDEB_LOCAL", "MDE_25_LOCAL"},
        )


if __name__ == "__main__":
    unittest.main()

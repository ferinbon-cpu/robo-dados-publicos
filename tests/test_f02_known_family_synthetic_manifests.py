from __future__ import annotations

import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.f02_known_family_bundle import (
    load_json,
    validate_adapter_contract,
    validate_batch_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "config/f02_known_family_bundle_adapter.v1.json"
ALIGNED = ROOT / "docs/evidence/f02_known_family/F02_SYNTHETIC_RREO_ALIGNED_EXAMPLE.json"
LOCAL = ROOT / "docs/evidence/f02_known_family/F02_SYNTHETIC_LOCAL_ONLY_EXAMPLE.json"


class F02KnownFamilySyntheticManifestTests(unittest.TestCase):
    def setUp(self):
        self.adapter = validate_adapter_contract(load_json(ADAPTER))

    def test_synthetic_examples_validate_without_real_custody_identifiers(self):
        aligned = validate_batch_manifest(load_json(ALIGNED), self.adapter)
        local = validate_batch_manifest(load_json(LOCAL), self.adapter)
        self.assertEqual(aligned["batch_kind"], "RREO_ALIGNED")
        self.assertEqual(local["batch_kind"], "LOCAL_ONLY")
        for path in (ALIGNED, LOCAL):
            raw = load_json(path)
            rendered = path.read_text(encoding="utf-8")
            self.assertNotIn("2026-", rendered)
            for source in raw["sources"]:
                self.assertTrue(source["drive_file_id"].startswith("synthetic-drive-"))
                self.assertTrue(source["source_id"].startswith("SYNTH_"))
                self.assertTrue(source["snapshot_path"].startswith("runtime/f02/synthetic/"))
            self.assertTrue(all(value is False for value in raw["remote_effects_authorized"].values()))

    def test_local_only_example_cannot_claim_rreo_family(self):
        local = load_json(LOCAL)
        self.assertEqual(
            {item["family"] for item in local["sources"]},
            {"FUNDEB_LOCAL", "MDE_25_LOCAL"},
        )


if __name__ == "__main__":
    unittest.main()

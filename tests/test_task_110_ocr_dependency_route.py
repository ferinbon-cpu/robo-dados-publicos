from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from robo_dados_publicos.research.ocr_dependency_route import (
    OcrDependencyRouteStop,
    load_and_validate_ocr_dependency_route,
    validate_ocr_dependency_route,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/ppa_2018_2021_ocr_dependency_route.v1.json"


class TestTask110OcrDependencyRoute(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_canonical_contract_passes_t0_only(self):
        result = load_and_validate_ocr_dependency_route(CONTRACT)
        self.assertEqual("PASS_TASK110_OCR_DEPENDENCY_ROUTE_DESIGN", result["status"])
        self.assertEqual("POPPLER_TESSERACT_POR_TSV", result["canonical_route"])
        self.assertFalse(result["real_source_authorized"])
        self.assertFalse(result["task111_authorized"])
        self.assertEqual(0, result["remote_effects"])

    def test_package_version_drift_fails_closed(self):
        for section, key, bad in (
            (self.data["canonical_route"]["renderer"], "version", "latest"),
            (self.data["canonical_route"]["ocr_engine"], "version", "latest"),
            (self.data["canonical_route"]["ocr_engine"]["language_package"], "version", "latest"),
        ):
            data = copy.deepcopy(self.data)
            target = data
            if section is self.data["canonical_route"]["renderer"]:
                target = data["canonical_route"]["renderer"]
            elif section is self.data["canonical_route"]["ocr_engine"]:
                target = data["canonical_route"]["ocr_engine"]
            else:
                target = data["canonical_route"]["ocr_engine"]["language_package"]
            target[key] = bad
            with self.assertRaises(OcrDependencyRouteStop):
                validate_ocr_dependency_route(data)

    def test_real_source_cannot_be_authorized_in_design_task(self):
        data = copy.deepcopy(self.data)
        data["future_real_source_gate"]["authorized_now"] = True
        with self.assertRaisesRegex(OcrDependencyRouteStop, "REAL_SOURCE_NOT_AUTHORIZED"):
            validate_ocr_dependency_route(data)

    def test_task111_install_cannot_be_authorized_in_task110(self):
        data = copy.deepcopy(self.data)
        data["task111_synthetic_gate"]["authorized_now"] = True
        with self.assertRaisesRegex(OcrDependencyRouteStop, "TASK111_NOT_AUTHORIZED"):
            validate_ocr_dependency_route(data)

    def test_dependency_allowlist_cannot_expand(self):
        data = copy.deepcopy(self.data)
        data["task111_synthetic_gate"]["dependency_install_allowlist"].append("ocrmypdf")
        with self.assertRaisesRegex(OcrDependencyRouteStop, "INSTALL_ALLOWLIST"):
            validate_ocr_dependency_route(data)

    def test_remote_effect_enablement_fails_closed(self):
        data = copy.deepcopy(self.data)
        data["remote_effects"]["package_network"] = True
        with self.assertRaisesRegex(OcrDependencyRouteStop, "REMOTE_EFFECT"):
            validate_ocr_dependency_route(data)


if __name__ == "__main__":
    unittest.main()

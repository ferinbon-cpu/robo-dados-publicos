from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.github_siope_2025_official_alias_documentary_discovery_design_gate import (
    DocumentaryDiscoveryDesignError,
    validate_design,
)

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "config" / "siope_2025_official_alias_documentary_discovery_design.v1.json"
TASK007 = ROOT / "config" / "siope_2025_official_documentary_proof.v1.json"
TASK008 = ROOT / "config" / "siope_2025_alias_finality_audit.v1.json"
TASK009D = ROOT / "config" / "siope_2025_route_dead_end_consolidation.v1.json"
SIOPE_CLIENT = ROOT / "robo_dados_publicos" / "sources" / "siope_client.py"
GATE = ROOT / "scripts" / "github_siope_2025_official_alias_documentary_discovery_design_gate.py"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Task009EOfficialAliasDocumentaryDiscoveryDesignTests(unittest.TestCase):
    def setUp(self) -> None:
        self.design = _load(DESIGN)
        self.task007 = _load(TASK007)
        self.task008 = _load(TASK008)
        self.task009d = _load(TASK009D)
        self.client = SIOPE_CLIENT.read_text(encoding="utf-8")

    def validate(self, *, design=None, task007=None, task008=None, task009d=None, client=None) -> None:
        validate_design(
            self.design if design is None else design,
            self.task007 if task007 is None else task007,
            self.task008 if task008 is None else task008,
            self.task009d if task009d is None else task009d,
            self.client if client is None else client,
        )

    def test_pinned_design_passes(self) -> None:
        self.validate()

    def test_cli_reports_t0_and_no_remote_authorization(self) -> None:
        proc = subprocess.run([sys.executable, str(GATE)], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["source_get_count"], 0)
        self.assertFalse(result["remote_execution_authorized"])
        self.assertEqual(result["questions"], ["S1_NUM_POPU", "S2_FINANCIAL_ALIAS_BRIDGE"])
        self.assertEqual(result["future_document_open_budget"], 12)
        self.assertEqual(result["gold_2025"], "UNKNOWN")

    def test_enabling_future_t1_or_network_capability_fails_closed(self) -> None:
        design = copy.deepcopy(self.design)
        design["future_t1_template"]["authorized"] = True
        with self.assertRaises(DocumentaryDiscoveryDesignError):
            self.validate(design=design)
        for key in (
            "retry_authorized",
            "authentication_authorized",
            "cookies_authorized",
            "oauth_authorized",
            "credential_use_authorized",
            "sharepoint_401_route_reuse_authorized",
            "antonieta_login_authorized",
            "limeira_financial_data_query_authorized",
            "binary_package_download_authorized",
            "source_data_collection_authorized",
            "gold_computation_authorized",
            "semantic_promotion_in_same_execution_authorized",
            "closure_promotion_in_same_execution_authorized",
            "drive_access_authorized",
        ):
            design = copy.deepcopy(self.design)
            design["future_t1_template"][key] = True
            with self.assertRaises(DocumentaryDiscoveryDesignError):
                self.validate(design=design)

    def test_nonofficial_host_or_broadened_authority_fails_closed(self) -> None:
        design = copy.deepcopy(self.design)
        design["future_t1_template"]["allowed_hosts"].append("example.com")
        with self.assertRaises(DocumentaryDiscoveryDesignError):
            self.validate(design=design)
        design = copy.deepcopy(self.design)
        design["future_t1_template"]["allowed_authorities"].append("THIRD_PARTY")
        with self.assertRaises(DocumentaryDiscoveryDesignError):
            self.validate(design=design)

    def test_sharepoint_retry_and_login_remain_blocked(self) -> None:
        design = copy.deepcopy(self.design)
        design["blocked_targets_and_actions"].remove("RETRY_ALREADY_NEGATIVE_SHAREPOINT_ROUTE")
        with self.assertRaises(DocumentaryDiscoveryDesignError):
            self.validate(design=design)
        design = copy.deepcopy(self.design)
        design["blocked_targets_and_actions"].remove("AUTOMATE_GOV_BR_LOGIN")
        with self.assertRaises(DocumentaryDiscoveryDesignError):
            self.validate(design=design)

    def test_num_popu_cannot_be_promoted_without_official_source_and_vintage(self) -> None:
        task007 = copy.deepcopy(self.task007)
        pop = next(row for row in task007["gate_b_field_semantics"]["field_assessment"] if row["odata_field"] == "NUM_POPU")
        pop["historical_definition_found"] = True
        with self.assertRaises(DocumentaryDiscoveryDesignError):
            self.validate(task007=task007)
        design = copy.deepcopy(self.design)
        design["repo_resident_baseline"]["num_popu_definition_status"] = "PROVEN"
        with self.assertRaises(DocumentaryDiscoveryDesignError):
            self.validate(design=design)

    def test_alias_identity_cannot_be_promoted_from_existing_material(self) -> None:
        task007 = copy.deepcopy(self.task007)
        task007["gate_b_field_semantics"]["field_assessment"][0]["2025_alias_identity_proven"] = True
        with self.assertRaises(DocumentaryDiscoveryDesignError):
            self.validate(task007=task007)
        task008 = copy.deepcopy(self.task008)
        task008["gate_a_alias_metadata"]["current_2025_alias_bridge_status"] = "PROVEN"
        with self.assertRaises(DocumentaryDiscoveryDesignError):
            self.validate(task008=task008)

    def test_schema_presence_is_not_definition(self) -> None:
        self.assertIn('"NUM_POPU"', self.client)
        client = self.client.replace('"NUM_POPU",', '')
        with self.assertRaises(DocumentaryDiscoveryDesignError):
            self.validate(client=client)
        design = copy.deepcopy(self.design)
        design["admissible_evidence"]["not_sufficient_alone"].remove("CURRENT_52_FIELD_SCHEMA_PRESENCE_WITHOUT_DEFINITION")
        with self.assertRaises(DocumentaryDiscoveryDesignError):
            self.validate(design=design)

    def test_semantic_gold_closure_series_and_2026_promotions_fail_closed(self) -> None:
        for key, value in (
            ("annual_closure_status", "PROVEN_CLOSED"),
            ("semantic_comparability_status", "PROVEN"),
            ("gold_metrics_status", "PROVEN"),
            ("closed_annual_series_last_year", 2025),
            ("year_2026_status", "PROVEN"),
        ):
            design = copy.deepcopy(self.design)
            design["semantic_guards"][key] = value
            with self.assertRaises(DocumentaryDiscoveryDesignError):
                self.validate(design=design)

    def test_discovery_questions_and_budget_are_exact(self) -> None:
        design = copy.deepcopy(self.design)
        design["discovery_questions"].append({"id": "S3_DATA_COLLECTION"})
        with self.assertRaises(DocumentaryDiscoveryDesignError):
            self.validate(design=design)
        design = copy.deepcopy(self.design)
        design["future_t1_template"]["maximum_official_document_opens"] = 100
        with self.assertRaises(DocumentaryDiscoveryDesignError):
            self.validate(design=design)

    def test_task009d_negative_boundaries_must_remain_pinned(self) -> None:
        task009d = copy.deepcopy(self.task009d)
        task009d["route_inventory"][0]["repeat_probe_authorized"] = True
        with self.assertRaises(DocumentaryDiscoveryDesignError):
            self.validate(task009d=task009d)
        task009d = copy.deepcopy(self.task009d)
        task009d["decision"] = "REMOTE_ALLOWED"
        with self.assertRaises(DocumentaryDiscoveryDesignError):
            self.validate(task009d=task009d)


if __name__ == "__main__":
    unittest.main()

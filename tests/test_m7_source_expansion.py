import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.sources.expansion import (
    LIFECYCLE_STATES,
    SourceExpansionContract,
    SourceExpansionError,
    load_source_expansion_gate,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_limeira_0_8_0.json"
WORKFLOW = ROOT / ".github" / "workflows" / "robo-dados-publicos.yml"


class TestM7SourceExpansion(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.gate = load_source_expansion_gate(CONFIG)

    def test_lifecycle_order_is_explicit_and_stops_before_recurrence(self):
        self.assertEqual(
            (
                "DISCOVERED",
                "CONTRACT_VALIDATED",
                "ONE_TIME_AUTHORIZED",
                "LIVE_VALIDATED",
                "RECURRENCE_ELIGIBLE",
            ),
            LIFECYCLE_STATES,
        )

    def test_siope_limeira_is_the_only_design_pilot(self):
        source = self.gate.source
        self.assertEqual("FNDE", source.institution)
        self.assertEqual("SIOPE", source.system)
        self.assertEqual("Limeira", source.pilot.municipality)
        self.assertEqual("SP", source.pilot.state)
        self.assertEqual("352690", source.pilot.municipality_code)
        self.assertEqual(2024, source.pilot.year)

    def test_public_surface_is_https_and_official(self):
        source = self.gate.source
        self.assertEqual(
            "https://webservice.fnde.gov.br/siope/dadosInformadosMunicipio.do",
            source.public_surface_url,
        )
        self.assertTrue(source.official_description_url.startswith("https://www.gov.br/fnde/"))
        self.assertEqual("CITIZEN_NO_PASSWORD", source.public_access)

    def test_design_stops_at_contract_validated(self):
        source = self.gate.source
        self.assertEqual("CONTRACT_VALIDATED", source.lifecycle_state)
        self.assertEqual("UNPROVEN", source.acquisition_route_status)
        self.assertEqual("UNPROVEN", source.schema_status)
        self.assertEqual("UNPROVEN", source.content_type_status)
        self.assertFalse(source.can_collect)
        self.assertFalse(source.can_schedule)

    def test_design_gate_prohibits_network_collection_processing_and_writes(self):
        self.assertEqual("DESIGN_ONLY", self.gate.mode)
        self.assertEqual("PROHIBITED", self.gate.network)
        self.assertEqual("PROHIBITED", self.gate.remote_writes)
        self.assertEqual("PROHIBITED", self.gate.source_collection)
        self.assertEqual("PROHIBITED", self.gate.source_processing)
        self.assertEqual("PROHIBITED", self.gate.recurrence)
        self.assertEqual("DISABLED", self.gate.schedule)

    def test_one_time_authorization_requires_proven_route_schema_and_content_type(self):
        raw = dict(self.raw["source"])
        raw.update({
            "lifecycle_state": "ONE_TIME_AUTHORIZED",
            "collection_authorization": "ONE_TIME_AUTHORIZED",
        })
        with self.assertRaisesRegex(SourceExpansionError, "REQUIRES_PROVEN_ROUTE_SCHEMA_CONTENT_TYPE"):
            SourceExpansionContract.from_mapping(raw)

    def test_recurrence_eligibility_does_not_enable_schedule(self):
        raw = dict(self.raw["source"])
        raw.update({
            "lifecycle_state": "RECURRENCE_ELIGIBLE",
            "acquisition_route_status": "PROVEN",
            "schema_status": "PROVEN",
            "content_type_status": "PROVEN",
            "collection_authorization": "ONE_TIME_AUTHORIZED",
            "recurrence_authorization": "ELIGIBLE_NOT_AUTHORIZED",
            "schedule": "DISABLED",
        })
        source = SourceExpansionContract.from_mapping(raw)
        self.assertTrue(source.can_collect)
        self.assertFalse(source.can_schedule)

    def test_schedule_requires_explicit_recurrence_authorization(self):
        raw = dict(self.raw["source"])
        raw.update({
            "lifecycle_state": "RECURRENCE_ELIGIBLE",
            "acquisition_route_status": "PROVEN",
            "schema_status": "PROVEN",
            "content_type_status": "PROVEN",
            "collection_authorization": "ONE_TIME_AUTHORIZED",
            "recurrence_authorization": "ELIGIBLE_NOT_AUTHORIZED",
            "schedule": "ENABLED",
        })
        with self.assertRaisesRegex(SourceExpansionError, "SCHEDULE_REQUIRES_RECURRENCE_AUTHORIZATION"):
            SourceExpansionContract.from_mapping(raw)

    def test_gate_script_is_offline_and_sanitized(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "github_source_expansion_design_gate.py")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, proc.returncode, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual("PASS_M7_SOURCE_EXPANSION_DESIGN_GATE", payload["status"])
        self.assertFalse(payload["network_called"])
        self.assertEqual("NONE", payload["remote_writes"])
        self.assertFalse(payload["collection_authorized"])
        self.assertFalse(payload["recurrence_authorized"])
        self.assertFalse(payload["schedule_enabled"])

    def test_production_workflow_cannot_reach_siope_expansion(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertNotIn("source_expansion.siope_limeira_0_8_0.json", text)
        self.assertNotIn("github_source_expansion_design_gate.py", text)
        self.assertNotIn("confirm_source_expansion", text)
        self.assertNotIn("dadosInformadosMunicipio", text)

    def test_bad_http_surface_fails_closed(self):
        raw = dict(self.raw["source"])
        raw["public_surface_url"] = "http://example.invalid/siope"
        with self.assertRaisesRegex(SourceExpansionError, "HTTPS_REQUIRED"):
            SourceExpansionContract.from_mapping(raw)

    def test_tampered_design_gate_cannot_authorize_collection(self):
        tampered = dict(self.raw)
        tampered_source = dict(tampered["source"])
        tampered_source.update({
            "lifecycle_state": "ONE_TIME_AUTHORIZED",
            "acquisition_route_status": "PROVEN",
            "schema_status": "PROVEN",
            "content_type_status": "PROVEN",
            "collection_authorization": "ONE_TIME_AUTHORIZED",
        })
        tampered["source"] = tampered_source
        with tempfile.TemporaryDirectory() as raw_dir:
            path = Path(raw_dir) / "gate.json"
            path.write_text(json.dumps(tampered), encoding="utf-8")
            with self.assertRaisesRegex(SourceExpansionError, "DESIGN_MUST_STOP_AT_CONTRACT_VALIDATED"):
                load_source_expansion_gate(path)


if __name__ == "__main__":
    unittest.main()

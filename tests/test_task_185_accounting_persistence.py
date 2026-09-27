import io
import json
import unittest
import zipfile

from robo_dados_publicos.accounting.task185_persistence import (
    Task185Stop,
    build_custody_manifest_plan,
    inspect_zip_bytes,
    load_contract,
    validate_stage_a_design,
)


IMPLEMENTATION_SHA = "a" * 40
RETRIEVED_AT = "2026-09-06T12:00:00-03:00"
AUTH_REF = "docs/evidence/TASK_185_STAGE_B_AUTHORIZATION_EXAMPLE.json"


def _csv_bytes(*, remove_header=None, extra_header=None, rows=2, delimiter=";"):
    headers = list(load_contract()["csv_schema"]["required_headers"])
    if remove_header:
        headers.remove(remove_header)
    if extra_header:
        headers.append(extra_header)

    values = {
        "tp_despesa": "Empenhado",
        "nr_empenho": "1234",
        "identificador_despesa": "EXP-2026-0001",
        "ds_despesa": "Teste estrutural",
        "dt_emissao_despesa": "2026-01-02",
        "vl_despesa": "100,00",
        "ds_funcao_governo": "Educação",
        "ds_subfuncao_governo": "Ensino Fundamental",
        "cd_programa": "2001",
        "ds_programa": "Educação",
        "cd_acao": "2010",
        "ds_acao": "Manutenção",
        "ds_fonte_recurso": "Tesouro",
        "ds_cd_aplicacao_fixo": "2200000",
        "ds_modalidade_lic": "Pregão",
        "ds_elemento": "Serviços",
        "historico_despesa": "Fixture sintética apenas para testar parser.",
    }
    if extra_header:
        values[extra_header] = "EXTRA"

    out = io.StringIO()
    out.write(delimiter.join(headers) + "\n")
    for index in range(rows):
        row = []
        for header in headers:
            value = str(values.get(header, ""))
            if delimiter == ";" and ";" in value:
                value = '"' + value.replace('"', '""') + '"'
            row.append(value)
        out.write(delimiter.join(row) + "\n")
    return out.getvalue().encode("utf-8")


def _zip_bytes(csv_payload, *, member="despesas-limeira-2026.csv", extra_member=False):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(member, csv_payload)
        if extra_member:
            archive.writestr("README.txt", b"metadata")
    return out.getvalue()


class TestTask185AccountingPersistenceStageA(unittest.TestCase):
    def test_stage_a_design_is_offline_and_bound_to_exact_upstream_contracts(self):
        result = validate_stage_a_design()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            result["source_url"],
            "https://transparencia.tce.sp.gov.br/sites/default/files/csv/despesas-limeira-2026.zip",
        )
        self.assertEqual(result["expected_member"], "despesas-limeira-2026.csv")
        self.assertEqual(result["required_header_count"], 17)
        self.assertEqual(result["historical_row_count"], 39780)
        self.assertFalse(result["historical_row_count_is_future_requirement"])
        self.assertTrue(result["stage_b_authorization_required"])
        self.assertFalse(result["network"])
        self.assertFalse(result["drive_write"])
        self.assertFalse(result["serving"])
        self.assertFalse(result["publication"])

    def test_contract_pins_create_only_existing_bronze_folder_and_fresh_authorization(self):
        contract = load_contract()
        custody = contract["custody"]
        auth = contract["stage_b_authorization"]
        self.assertEqual(custody["target_layer"], "01_BRONZE")
        self.assertEqual(custody["target_folder_id"], "1cgG2YiVm14DYEqAJGFpB7GOKaRloIqUC")
        self.assertTrue(custody["create_only"])
        self.assertFalse(custody["overwrite"])
        self.assertFalse(custody["delete"])
        self.assertFalse(custody["drive_write_authorized_in_stage_a"])
        self.assertTrue(auth["required"])
        self.assertFalse(auth["prior_task172_authorization_reusable"])
        self.assertTrue(auth["authorization_artifact_required_before_network"])
        self.assertEqual(auth["bind_max_requests"], 1)

    def test_structural_zip_fixture_passes_without_becoming_real_accounting_evidence(self):
        payload = _zip_bytes(_csv_bytes(rows=3))
        got = inspect_zip_bytes(payload)
        self.assertEqual(got["record_count"], 3)
        self.assertEqual(got["member_name"], "despesas-limeira-2026.csv")
        self.assertEqual(got["csv_delimiter"], ";")
        self.assertEqual(len(got["zip_sha256"]), 64)
        self.assertEqual(len(got["csv_sha256"]), 64)
        self.assertFalse(got["record_count_must_equal_historical"])
        self.assertFalse(got["network_performed"])
        self.assertFalse(got["drive_write_performed"])
        self.assertNotEqual(got["record_count"], 39780)

    def test_extra_source_column_is_recorded_not_promoted_to_proven_schema(self):
        payload = _zip_bytes(_csv_bytes(extra_header="new_future_column"))
        got = inspect_zip_bytes(payload)
        self.assertEqual(got["extra_headers"], ["new_future_column"])
        self.assertNotIn("new_future_column", load_contract()["csv_schema"]["required_headers"])

    def test_missing_required_column_fails_closed(self):
        payload = _zip_bytes(_csv_bytes(remove_header="nr_empenho"))
        with self.assertRaises(Task185Stop):
            inspect_zip_bytes(payload)

    def test_wrong_member_name_fails_closed(self):
        payload = _zip_bytes(_csv_bytes(), member="despesas-outra-cidade-2026.csv")
        with self.assertRaisesRegex(Task185Stop, "TASK185_EXPECTED_MEMBER"):
            inspect_zip_bytes(payload)

    def test_non_zip_fails_closed(self):
        with self.assertRaisesRegex(Task185Stop, "TASK185_NOT_ZIP"):
            inspect_zip_bytes(b"not a zip")

    def test_manifest_plan_is_hash_named_create_only_and_does_not_write(self):
        inspection = inspect_zip_bytes(_zip_bytes(_csv_bytes()))
        plan = build_custody_manifest_plan(
            inspection,
            retrieved_at=RETRIEVED_AT,
            authorization_artifact=AUTH_REF,
            implementation_sha=IMPLEMENTATION_SHA,
        )
        self.assertIn(inspection["zip_sha256"], plan["artifact_names"]["zip"])
        self.assertIn(inspection["csv_sha256"], plan["artifact_names"]["csv"])
        self.assertIn(inspection["zip_sha256"], plan["artifact_names"]["manifest"])
        self.assertEqual(plan["custody_folder_id"], "1cgG2YiVm14DYEqAJGFpB7GOKaRloIqUC")
        self.assertTrue(plan["create_only"])
        self.assertEqual(plan["collision_policy"], "STOP_BEFORE_FIRST_WRITE")
        self.assertTrue(plan["manifest_written_last"])
        self.assertFalse(plan["drive_write_performed"])

    def test_stage_a_fixture_never_authorizes_stage_b(self):
        contract = load_contract()
        self.assertEqual(contract["stage"], "A")
        self.assertFalse(contract["stage_a_remote_effects"]["source_network"])
        self.assertFalse(contract["stage_a_remote_effects"]["drive_write"])
        self.assertFalse(contract["stage_b_authorization"]["prior_task172_authorization_reusable"])


if __name__ == "__main__":
    unittest.main()

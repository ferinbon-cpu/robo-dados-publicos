import io
import json
import unittest
import zipfile

from scripts.task201_workforce_live_probe import (
    derive_sanitized_result,
    exact_auth_comment,
    parse_contracted_aggregate,
    parse_sme_bonds,
)


def _tiny_xlsx_bytes():
    workbook = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
 <sheets><sheet name="Docentes por Município" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""
    sheet = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
 <sheetData>
  <row r="1"><c r="A1" t="inlineStr"><is><t>Número de Docentes da Educação Básica</t></is></c></row>
  <row r="2"><c r="A2" t="inlineStr"><is><t>Dependência Administrativa</t></is></c></row>
  <row r="3"><c r="A3" t="inlineStr"><is><t>Municipal</t></is></c></row>
  <row r="4"><c r="A4" t="inlineStr"><is><t>Limeira</t></is></c><c r="B4"><v>999</v></c></row>
 </sheetData>
</worksheet>"""
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED) as xlsx:
        xlsx.writestr("xl/workbook.xml", workbook)
        xlsx.writestr("xl/_rels/workbook.xml.rels", rels)
        xlsx.writestr("xl/worksheets/sheet1.xml", sheet)
    return bio.getvalue()


def _tiny_inep_package():
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED) as outer:
        outer.writestr("Sinopse_2025.xlsx", _tiny_xlsx_bytes())
    return bio.getvalue()


def _home_html():
    return """
    <html><body>
    <p>Atribuição para Professores efetivos da Rede Municipal.</p>
    <p>Indicação dos Professores ( CLT ) que realizaram o Processo Seletivo.</p>
    </body></html>
    """.encode("utf-8")


def _contracted_html():
    return """
    <html><body>
    <h1>PROFESSORES CONTRATADOS EM CLASSE</h1>
    <p>IMPRESSÃO EM: 07-09-2026</p>
    <table>
      <tr><th>MATRÍCULA</th><th>NOME</th><th>C.P.F.</th><th>CARGO</th><th>UNIDADE ESCOALR</th></tr>
      <tr><td>000.001-1</td><td>PESSOA TESTE A</td><td>111.111.111-11</td><td>ENSINO FUNDAMENTAL</td><td>ESCOLA A</td></tr>
      <tr><td>000.001-1</td><td>PESSOA TESTE A</td><td>111.111.111-11</td><td>ARTE</td><td>ESCOLA B</td></tr>
      <tr><td>000.002-2</td><td>PESSOA TESTE B</td><td>222.222.222-22</td><td>EDUCAÇÃO INFANTIL</td><td>ESCOLA A</td></tr>
    </table>
    </body></html>
    """.encode("utf-8")


class TestTask201WorkforceLiveProbe(unittest.TestCase):
    def test_exact_authorization_comment_is_pinned(self):
        sha = "a" * 40
        self.assertEqual(
            exact_auth_comment(sha),
            (
                "TASK201_WORKFORCE_LIVE_AUTHORIZED "
                f"main={sha} issue=639 inep_attempts=3 sme_attempts=2 "
                "raw_persist=0 pii_persist=0"
            ),
        )

    def test_sme_taxonomy_requires_effective_and_clt(self):
        got = parse_sme_bonds(_home_html())
        self.assertEqual(got["bond_categories"], ["EFETIVO", "CLT_PROCESSO_SELETIVO"])
        self.assertEqual(got["category_count"], 2)

    def test_contracted_page_deduplicates_ephemerally_and_returns_aggregates_only(self):
        got = parse_contracted_aggregate(
            _contracted_html(),
            "PROFESSORES CONTRATADOS EM CLASSE",
        )
        self.assertEqual(got["assignment_row_count"], 3)
        self.assertEqual(got["unique_contracted_teacher_count"], 2)
        self.assertEqual(got["people_with_multiple_assignment_rows"], 1)
        self.assertEqual(got["distinct_school_label_count"], 2)
        encoded = json.dumps(got, ensure_ascii=False)
        self.assertNotIn("PESSOA TESTE", encoded)
        self.assertNotIn("111.111.111-11", encoded)
        self.assertNotIn("000.001-1", encoded)

    def test_combined_result_keeps_person_data_out_and_finds_inep_candidate(self):
        result = derive_sanitized_result(
            inep_bytes=_tiny_inep_package(),
            sme_home_bytes=_home_html(),
            sme_contracted_bytes=_contracted_html(),
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["inep_docente_probe"]["candidate_count"], 1)
        self.assertEqual(
            result["sme_contracted_aggregate"]["unique_contracted_teacher_count"],
            2,
        )
        self.assertFalse(result["guards"]["person_level_output"])
        self.assertFalse(result["guards"]["staff_count_materialized"])
        self.assertFalse(result["guards"]["employment_bond_materialized"])
        encoded = json.dumps(result, ensure_ascii=False)
        self.assertNotIn("PESSOA TESTE", encoded)
        self.assertNotIn("111.111.111-11", encoded)
        self.assertNotIn("000.001-1", encoded)


if __name__ == "__main__":
    unittest.main()

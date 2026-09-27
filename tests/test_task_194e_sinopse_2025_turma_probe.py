import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.task194e_sinopse_2025_turma_probe import (
    exact_auth_comment,
    scan_workbook,
    derive_candidates,
)


def _inline_cell(ref: str, value: str) -> str:
    return f'<c r="{ref}" t="inlineStr"><is><t>{value}</t></is></c>'


def _num_cell(ref: str, value: int) -> str:
    return f'<c r="{ref}"><v>{value}</v></c>'


def _synthetic_xlsx() -> bytes:
    workbook = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
      xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
      <sheets><sheet name="3. Turmas" sheetId="1" r:id="rId1"/></sheets>
    </workbook>"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
      <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
        Target="worksheets/sheet1.xml"/>
    </Relationships>"""
    rows = [
        f'<row r="1">{_inline_cell("A1","Tabela - Número de Turmas da Educação Básica por Dependência Administrativa")}</row>',
        f'<row r="2">{_inline_cell("A2","Município")}{_inline_cell("B2","Total")}{_inline_cell("C2","Federal")}{_inline_cell("D2","Estadual")}{_inline_cell("E2","Municipal")}{_inline_cell("F2","Privada")}</row>',
        f'<row r="3">{_inline_cell("A3","Limeira")}{_num_cell("B3",700)}{_num_cell("C3",0)}{_num_cell("D3",0)}{_num_cell("E3",650)}{_num_cell("F3",50)}</row>',
        f'<row r="4">{_inline_cell("A4","Outra Cidade")}{_num_cell("B4",10)}{_num_cell("E4",8)}</row>',
    ]
    sheet = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>""" + "".join(rows) + "</sheetData></worksheet>"
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("xl/workbook.xml",workbook)
        z.writestr("xl/_rels/workbook.xml.rels",rels)
        z.writestr("xl/worksheets/sheet1.xml",sheet)
    return out.getvalue()


class TestTask194ESinopseProbe(unittest.TestCase):
    def test_exact_auth_comment(self):
        sha="a"*40
        self.assertEqual(
            exact_auth_comment(sha),
            f"TASK194E_SINOPSE_2025_TURMAS_AUTHORIZED main={sha} issue=607 max_http_attempts=3 raw_persist=0",
        )

    def test_scan_workbook_finds_only_target_candidate(self):
        candidates=scan_workbook(
            _synthetic_xlsx(),
            "sinopse.xlsx",
            {
                "municipality_name":"Limeira",
                "keywords":["turma","dependencia administrativa","municipal"],
            },
        )
        self.assertEqual(len(candidates),1)
        c=candidates[0]
        self.assertEqual(c["sheet"],"3. Turmas")
        self.assertEqual(len(c["limeira_rows"]),1)
        values={x["ref"]:x["value"] for x in c["limeira_rows"][0]["cells"]}
        self.assertEqual(values["E3"],"650")
        payload=json.dumps(c,ensure_ascii=False)
        self.assertNotIn("Outra Cidade",payload)

    def test_outer_package_is_sanitized_and_does_not_materialize(self):
        with tempfile.TemporaryDirectory() as td:
            package=Path(td)/"package.zip"
            with zipfile.ZipFile(package,"w",compression=zipfile.ZIP_DEFLATED) as z:
                z.writestr("Sinopse_2025.xlsx",_synthetic_xlsx())
            result=derive_candidates(package)
        self.assertEqual(result["status"],"PASS")
        self.assertEqual(result["candidate_count"],1)
        self.assertFalse(result["guards"]["class_count_materialized"])
        self.assertFalse(result["guards"]["raw_zip_persisted"])
        self.assertFalse(result["guards"]["unrelated_municipality_rows_persisted"])


if __name__ == "__main__":
    unittest.main()

import io
import unittest
from zipfile import ZipFile

from robo_dados_publicos.research.task283_archive_inspection import (
    SOURCES, Task283Stop, _inventory, inspect_recovered_export,
)


def fixture(hidden=False, formula=False):
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    buffer = io.BytesIO()
    with ZipFile(buffer, "w") as z:
        z.writestr("xl/workbook.xml", f'<workbook xmlns="{ns}"><sheets><sheet name="Synthetic"/></sheets><definedNames/></workbook>')
        hidden_attribute = ' hidden="1"' if hidden else ''
        formula_element = '<f>1+1</f>' if formula else ''
        z.writestr("xl/worksheets/sheet1.xml", f'<worksheet xmlns="{ns}"><dimension ref="A1:C1"/><sheetData><row r="1"{hidden_attribute}><c r="A1" t="s"><v>0</v></c><c r="B1"><v>3286</v>{formula_element}</c><c r="C1" t="s"><v>1</v></c></row></sheetData></worksheet>')
        z.writestr("xl/sharedStrings.xml", f'<sst xmlns="{ns}"><si><t>03286-01</t></si><si><t>PRIVATE_SYNTHETIC_VALUE</t></si></sst>')
        z.writestr("docProps/core.xml", '<core/>')
    return buffer.getvalue()


class Task283ArchiveTests(unittest.TestCase):
    def test_fabricated_bytes_cannot_claim_an_official_export(self):
        for kind in SOURCES:
            with self.subTest(kind=kind), self.assertRaisesRegex(Task283Stop, "ARCHIVE_SHA256_MISMATCH"):
                inspect_recovered_export(kind, fixture())

    def test_inventory_does_not_promote_cooccurring_numbers_or_disclose_other_cells(self):
        result = _inventory(fixture(), ["A1"])
        self.assertEqual(result["selected_cells"], {"A1": "03286-01"})
        self.assertTrue(result["exact_cell_3286_present"])
        self.assertFalse(result["namespace_witness_proven"])
        self.assertNotIn("PRIVATE_SYNTHETIC_VALUE", str(result))
        self.assertFalse(result["core_creation_or_modification_timestamp_present"])

    def test_hidden_rows_and_formulas_are_reported(self):
        result = _inventory(fixture(hidden=True, formula=True), ["A1"])
        self.assertEqual(result["hidden_rows"], 1)
        self.assertEqual(result["formulas"], 1)
        self.assertFalse(result["namespace_witness_proven"])

    def test_size_limit_fails_closed(self):
        with self.assertRaisesRegex(Task283Stop, "ARCHIVE_SIZE_LIMIT"):
            _inventory(b"0" * 1_000_001, [])


if __name__ == "__main__":
    unittest.main()

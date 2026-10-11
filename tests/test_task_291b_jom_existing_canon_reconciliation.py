"""TASK291B zero-network tests of exact historical JOM identity reconciliation."""
from __future__ import annotations

import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from robo_dados_publicos.research import task291b_jom_existing_canon_reconciliation as target


class TestTask291B(unittest.TestCase):
    def test_source_anchored_113_99_14_79_65(self):
        rows, overview = target.reconcile()
        self.assertEqual(len(rows), 113)
        self.assertEqual(overview["custodied_identities"], 99)
        self.assertEqual(overview["historically_proven_identities_not_custodied"], 14)
        self.assertEqual(overview["numeric_gaps_still_without_identity_proof"], 65)
        self.assertEqual(overview["proven_unarchived_with_direct_pdf_url"], 5)
        self.assertEqual(overview["proven_unarchived_date_only"], 9)
        self.assertEqual(overview["january_identified_count"], 22)
        self.assertEqual(overview["source_pdf_get_count"], 0)
        self.assertEqual(overview["index_get_count"], 0)
        self.assertEqual(overview["drive_write_count"], 0)
        self.assertTrue(overview["post_2026_09_12_uninventoried"])

    def test_csv_committed_matches_deterministic_output_byte_for_byte(self):
        rows, _ = target.reconcile()
        expected = target.render_csv(rows)
        path = target.ROOT / "docs/evidence/task291/TASK291B_JOM_2026_113_IDENTIDADES_RECONCILIADAS.csv"
        self.assertEqual(path.read_text("utf-8"), expected)
        self.assertEqual(list(csv.DictReader(io.StringIO(expected)))[0]["edicao"], "7151")

    def test_january_ten_no_synthetic_source_ids_or_urls(self):
        rows, overview = target.reconcile()
        x = {int(z["edicao"]): z for z in rows}
        self.assertEqual([int(z["edicao"]) for z in rows[:22]], list(range(7151, 7173)))
        for ed in range(7151, 7161):
            self.assertEqual(x[ed]["situacao_drive_sme"], "NAO_CUSTODIADO_SME")
            self.assertEqual(x[ed]["source_id"], "")
        self.assertEqual(x[7151]["paginas_primario_historico"], "125")
        self.assertEqual(x[7151]["sha256_primario_historico"],
                         "ec298a6cff290723c97d24c291e36ef2c2044713b0fc5082b4560329e1d1dab8")
        self.assertTrue(x[7151]["url_pdf_oficial"].endswith("u_137_05012026203147.pdf"))
        for ed in range(7152, 7161):
            self.assertEqual(x[ed]["url_pdf_oficial"], "")
            self.assertEqual(x[ed]["sha256_primario_historico"], "")
        for ed in range(7321, 7325):
            self.assertEqual(x[ed]["situacao_drive_sme"], "NAO_CUSTODIADO_SME")
            self.assertTrue(x[ed]["url_pdf_oficial"].startswith("https://ecrie.com.br/"))
        self.assertEqual(overview["official_url_known_unarchived_editions"],
                         [7151, 7321, 7322, 7323, 7324])

    def test_no_unverified_numeric_candidates_promoted_to_source_data(self):
        rows, summary = target.reconcile()
        known = {int(x["edicao"]) for x in rows}
        self.assertFalse({7173, 7174, 7218, 7325, 7326, 7327, 7328} & known)
        self.assertEqual(len(summary["remaining_numeric_candidates"]), 65)
        self.assertIn(7327, summary["remaining_numeric_candidates"])
        self.assertIn(7328, summary["remaining_numeric_candidates"])

    def test_official_url_allowlist(self):
        kwargs=("2026-01-06", "", "TASK238_COMPLETE_JANUARY_IDENTITY_PRIMARY_URL_AND_SHA",
                "primary", "NAO_CUSTODIADO_SME")
        with self.assertRaisesRegex(target.ReconciliationStop, "URL_NOT_OFFICIAL"):
            target.checked_entry(7151, kwargs[0], kwargs[1],
                                 "https://example.com/fake.pdf", *kwargs[2:])
        with self.assertRaisesRegex(target.ReconciliationStop, "SOURCE_ID_REQUIRED"):
            target.checked_entry(7162, "2026-01-20", "", "https://ecrie.com.br/abc.pdf",
                                 "UNVERIFIED", "unknown", "NAO_CUSTODIADO_SME")

    def test_pinned_fixture_drift_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            damaged = Path(tmp)/"pinned.csv"
            data = target.PINNED.read_text("utf-8").splitlines()
            damaged.write_text("\n".join(data[:-1]) + "\n")
            with patch.object(target, "PINNED", damaged):
                with self.assertRaisesRegex(target.ReconciliationStop, "PINNED_COUNT"):
                    target.reconcile()

    def test_month_total_pr_915_not_silently_promoted(self):
        _, summary = target.reconcile()
        self.assertEqual(summary["nature"], "OFFLINE_CANONICAL_RECONCILIATION_NOT_COMPLETE_2026_INVENTORY")
        self.assertNotIn("full_year_complete", summary)
        self.assertFalse(summary["source_pdf_get_count"])


if __name__ == "__main__":
    unittest.main()

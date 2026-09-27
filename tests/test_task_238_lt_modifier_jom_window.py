import json
import unittest
from pathlib import Path

from robo_dados_publicos.research.task238_lt_modifier_jom_window import (
    build_bounded_window_inventory,
    evaluate_reports,
)

ROOT = Path(__file__).resolve().parents[1]


def edition(edition_id, publication_date, host="ecrie.com.br"):
    return {
        "edition": edition_id,
        "publication_date": publication_date,
        "source_id": f"LIMEIRA_JO_{edition_id:05d}",
        "logical_key": f"limeira/jornal_oficial/edicao/{edition_id}",
        "document_url": f"https://{host}/Sistema/Conteudos/DiarioOficial/upload/fake_{edition_id}.pdf",
    }


def report(year, month, rows, *, status="PASS_DISCOVERY", reported_total=None):
    return {
        "status": status,
        "year": year,
        "month": month,
        "pages_fetched": 2,
        "reported_total_items": len(rows) if reported_total is None else reported_total,
        "count": len(rows),
        "editions": rows,
    }


class Task238WindowInventoryTests(unittest.TestCase):
    def test_complete_reports_build_only_bounded_window(self):
        december = report(
            2025,
            12,
            [
                edition(7138, "2025-12-15"),
                edition(7141, "2025-12-17"),
                edition(7150, "2025-12-31"),
            ],
        )
        january = report(
            2026,
            1,
            [edition(7151, "2026-01-06"), edition(7172, "2026-01-31")],
        )
        out = build_bounded_window_inventory([december, january])
        self.assertEqual("PASS_COMPLETE_BOUNDED_WINDOW_INVENTORY", out["status"])
        self.assertEqual([7141, 7150, 7151, 7172], [row["edition"] for row in out["documents"]])
        self.assertEqual(4, out["window_document_count"])
        self.assertFalse(out["content_inspection_performed"])
        self.assertFalse(out["modifier_candidate_established"])
        self.assertFalse(out["absence_inference_allowed"])

    def test_partial_month_never_becomes_complete_window(self):
        december = report(2025, 12, [edition(7141, "2025-12-17")], status="PARTIAL_DISCOVERY_PAGINATION_UNRESOLVED")
        january = report(2026, 1, [edition(7172, "2026-01-31")])
        out = evaluate_reports([december, january])
        self.assertEqual("TASK238_MONTH_DISCOVERY_NOT_COMPLETE", out["status"])
        self.assertFalse(out["complete_window_inventory"])
        self.assertFalse(out["absence_inference_allowed"])

    def test_reported_total_must_reconcile(self):
        december = report(2025, 12, [edition(7141, "2025-12-17")], reported_total=2)
        january = report(2026, 1, [edition(7172, "2026-01-31")])
        out = evaluate_reports([december, january])
        self.assertEqual("TASK238_REPORTED_TOTAL_NOT_RECONCILED", out["status"])

    def test_document_route_must_be_official_https(self):
        december = report(2025, 12, [edition(7141, "2025-12-17", host="example.com")])
        january = report(2026, 1, [edition(7172, "2026-01-31")])
        out = evaluate_reports([december, january])
        self.assertEqual("TASK238_DOCUMENT_URL_HOST", out["status"])

    def test_duplicate_editions_fail_closed(self):
        december = report(
            2025,
            12,
            [edition(7141, "2025-12-17"), edition(7141, "2025-12-18")],
        )
        january = report(2026, 1, [edition(7172, "2026-01-31")])
        out = evaluate_reports([december, january])
        self.assertEqual("TASK238_DUPLICATE_EDITION", out["status"])

    def test_contract_preserves_task237_open_divergence(self):
        cfg = json.loads((ROOT / "config/lt_formation_timing_jom_window_inventory.v1.json").read_text(encoding="utf-8"))
        prior = json.loads((ROOT / "config/lt_formation_timing_modifier_audit.v1.json").read_text(encoding="utf-8"))
        self.assertEqual("TASK_238", cfg["task"])
        self.assertEqual("d678e521a6a3290ea1b51163a9433954e815fa07", cfg["base_main_sha"])
        self.assertEqual("OPEN_UNRESOLVED", cfg["content_state"]["divergence_status"])
        self.assertEqual("OPEN_UNRESOLVED", prior["result"]["divergence_status"])
        self.assertFalse(cfg["content_state"]["full_window_content_closed"])
        self.assertFalse(cfg["authorization_boundary"]["live_discovery_executed_by_this_commit"])
        self.assertEqual(0, cfg["task238_inventory_gate"]["content_downloads_in_inventory_gate"])

    def test_known_route_counts_are_consistent(self):
        cfg = json.loads((ROOT / "config/lt_formation_timing_jom_window_inventory.v1.json").read_text(encoding="utf-8"))
        routes = cfg["known_official_document_routes"]
        self.assertEqual(19, routes["count"])
        self.assertEqual(7, len(routes["december_task237_direct_primary"]))
        self.assertEqual(12, len(routes["january_task219_canonical_csv"]))
        self.assertEqual(13, routes["total_route_gaps_before_fresh_month_discovery"])
        self.assertEqual(10, cfg["official_month_listing_observations"]["2025-12"]["bounded_window_count"])
        self.assertEqual(22, cfg["official_month_listing_observations"]["2026-01"]["reported_total_items_full_month"])


if __name__ == "__main__":
    unittest.main()

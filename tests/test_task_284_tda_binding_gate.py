from copy import deepcopy
import unittest
from robo_dados_publicos.research.task283_tda_tce_namespace_dossier import Task283Stop
from robo_dados_publicos.research.task284_tda_binding_gate import load_contract, validate_binding


class Task284BindingTests(unittest.TestCase):
    def binding(self):
        return {"area_name": "Detalhe do Empenho", "area_origin": "2_92_guestuser_200_8_DSL0_VIS706", "area_id": "SYNTHETIC_DSA8", "area_count": 1, "filter_id": "AREAFILTER_SYNTHETIC_DSA8", "number_id": "FILTEREDIT_SYNTHETIC_DSA8_epn", "number_count": 1, "number_label": "Nro Empenho", "year_id": "FILTERCOMBO_SYNTHETIC_DSA8_exe", "year_count": 1, "year_label": "Exercício", "year_2026_option_count": 1, "controls_inside_filter": True, "submit_count": 1, "submit_visible": True, "submit_handler": "submmitApply('AREAFILTER_SYNTHETIC_DSA8');", "numeric_query_3286_explicitly_supported": True}

    def test_contract_has_no_automatic_executor_or_pncp(self):
        c = load_contract()
        self.assertFalse(c["automatic_execution_allowed"])
        self.assertEqual(c["limits"]["pncp_requests"], 0)
        self.assertFalse(c["task281_consumed"])

    def test_unique_binding_is_only_query_permission_not_identity(self):
        r = validate_binding(self.binding())
        self.assertFalse(r["namespace_identity_proven"])
        self.assertFalse(r["payment_attribution_authorized"])

    def test_duplicate_stale_unscoped_or_unsupported_controls_stop(self):
        for key, value in {"area_count": 2, "area_origin": "OTHER", "area_id": "OLD_SESSION", "number_count": 2, "number_label": "", "year_count": 0, "year_2026_option_count": 2, "controls_inside_filter": False, "submit_count": 0, "submit_visible": False, "numeric_query_3286_explicitly_supported": False}.items():
            with self.subTest(key=key):
                b = self.binding(); b[key] = value
                with self.assertRaises(Task283Stop): validate_binding(b)

    def test_area_id_only_or_ambiguous_handler_cannot_be_guessed(self):
        for handler in ["submmitApply('SYNTHETIC_DSA8')", "submmitApply('AREAFILTER_OTHER')", "submmitApply('AREAFILTER_SYNTHETIC_DSA8'); otherAction()"]:
            with self.subTest(handler=handler):
                b = self.binding(); b["submit_handler"] = handler
                with self.assertRaisesRegex(Task283Stop, "TASK284_SUBMIT_ARGUMENT"): validate_binding(b)


if __name__ == "__main__":
    unittest.main()

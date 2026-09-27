import unittest

from robo_dados_publicos.reconciliation.bounded_query_guard import (
    BoundedQueryGuard,
    BoundedQueryGuardError,
    validate_resolver_status,
)
from scripts.verify_task086_bounded_query_evidence import run as verify_task086


class TestTask086BoundedQueryEvidence(unittest.TestCase):
    def test_guard_allows_exact_budget_then_fourth_request_fails_closed(self):
        guard = BoundedQueryGuard("serv42.limeira.sp.gov.br", 3)
        for ordinal in range(1, 4):
            observed = guard.authorize(
                "https://serv42.limeira.sp.gov.br/ncweb/cns_contratos_web_mestre/",
                method="POST" if ordinal > 1 else "GET",
                params={"numero": "170"} if ordinal > 1 else None,
            )
            self.assertEqual(ordinal, observed["ordinal"])
        with self.assertRaisesRegex(BoundedQueryGuardError, "STOP_BOUNDED_QUERY_HTTP_BUDGET_EXCEEDED"):
            guard.authorize("https://serv42.limeira.sp.gov.br/ncweb/cns_contratos_web_mestre/")
        self.assertEqual(3, len(guard.request_log))

    def test_guard_rejects_non_allowlisted_host_without_consuming_budget(self):
        guard = BoundedQueryGuard("serv42.limeira.sp.gov.br", 3)
        with self.assertRaisesRegex(BoundedQueryGuardError, "STOP_BOUNDED_QUERY_ORIGIN_OUTSIDE_ALLOWLIST"):
            guard.authorize("https://example.invalid/ncweb/cns_contratos_web_mestre/")
        self.assertEqual([], guard.request_log)

    def test_unexpected_resolver_status_fails_closed(self):
        allowed = {"MATCH_CANDIDATE", "NO_MATCH"}
        self.assertEqual("NO_MATCH", validate_resolver_status("NO_MATCH", allowed))
        with self.assertRaisesRegex(BoundedQueryGuardError, "STOP_BOUNDED_QUERY_UNEXPECTED_RESOLVER_STATUS"):
            validate_resolver_status("UNEXPECTED", allowed)

    def test_pinned_live_payload_and_evidence_verify_offline(self):
        result = verify_task086()
        self.assertEqual("PASS_TASK086_BOUNDED_QUERY_EVIDENCE_OFFLINE", result["status"])
        self.assertEqual("80cd4dd6ffe018eb3cd019e6b453d750265dd0199bb288ba077ee58fa4955f61", result["canonical_sha256"])
        self.assertEqual(3, result["request_count"])
        self.assertEqual("serv42.limeira.sp.gov.br", result["allowed_host"])
        self.assertEqual("NO_MATCH", result["resolver_status"])
        self.assertEqual(0, result["candidate_count"])
        self.assertFalse(result["future_execution_authorized"])


if __name__ == "__main__":
    unittest.main()

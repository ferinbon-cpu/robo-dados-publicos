from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "github_public_readiness_audit.py"
spec = importlib.util.spec_from_file_location("public_readiness", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _codes(text: str) -> set[str]:
    return {code for code, _line in mod.scan_text(text)}


def test_known_secret_signatures_are_detected_without_literal_fixture_in_source() -> None:
    github_token = "gh" + "p_" + ("Ab9" * 12)
    google_secret = "GOC" + "SPX-" + ("aB9_" * 7)
    google_key = "AI" + "za" + ("A1_b" * 9)
    aws_key = "AK" + "IA" + ("A1B2" * 4)
    private_key_header = "-----BEGIN " + "PRIVATE KEY-----"
    codes = _codes("\n".join([github_token, google_secret, google_key, aws_key, private_key_header]))
    assert "GITHUB_TOKEN_PREFIX" in codes
    assert "GOOGLE_OAUTH_CLIENT_SECRET" in codes
    assert "GOOGLE_API_KEY" in codes
    assert "AWS_ACCESS_KEY_ID" in codes
    assert "PRIVATE_KEY_HEADER" in codes


def test_sensitive_assignment_detects_value_but_not_placeholder() -> None:
    realish = "refresh" + "_token=1//" + ("AbCd9_" * 8)
    placeholder = "client" + "_secret=${GOOGLE_DRIVE_CLIENT_SECRET}"
    assert "SENSITIVE_ASSIGNMENT_REFRESH_TOKEN" in _codes(realish)
    assert not _codes(placeholder)


def test_env_example_is_not_a_sensitive_filename() -> None:
    findings = mod._suspicious_path_findings([".env.example"])
    assert findings == []


def test_real_env_and_private_key_filename_require_review() -> None:
    findings = mod._suspicious_path_findings([".env", "config/service.key"])
    assert {item["path"] for item in findings} == {".env", "config/service.key"}


def test_audit_source_never_emits_matched_secret_value() -> None:
    token = "gh" + "o_" + ("Xy7" * 12)
    findings = mod.scan_text(token)
    assert findings
    serialized = repr(findings)
    assert token not in serialized

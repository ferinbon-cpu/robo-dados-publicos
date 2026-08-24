"""Sanitized, read-only observability products for operator-facing reports."""

from robo_dados_publicos.observability.cards import build_observability_report, render_markdown

__all__ = ["build_observability_report", "render_markdown"]

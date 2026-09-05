# TASK 126 — bounded TCESP HTML-index discovery

## Purpose

After TASK 124 and TASK 125 proved that raw ZIP transport is blocked in the current runtime, TASK 126 uses only web-accessible TCESP search/index surfaces to look for a Limeira 2026 expense-detail candidate containing an explicit EITI-related marker or the exact accounting clue 2607004.

## Scope integrity

Issue #449 was created before the searches and prospectively bounded the work. No code contract or CI preflight existed before the read-only web-index searches, so TASK 126 records that fact explicitly instead of retroactively claiming a preflight.

The execution used 15 exact search queries across 8 query families plus one direct-open control attempt that timed out without page content.

## Result

No indexed Limeira 2026 expense page containing the exact EITI policy markers or 2607004 was observed.

This is not a global NO_MATCH. Search indexes are incomplete and this result does not prove that:
- no EITI execution exists;
- no 2607004 record exists;
- no TCESP detail page exists outside the index.

## Structural controls

The accessible index does prove that Limeira 2026 TCESP expense pages can expose:
- empenho lifecycle events;
- program;
- action;
- funding source;
- fixed application code;
- subitem;
- history.

A generic Program 2001 detail page is retained only as schema control, not EITI evidence.

## Next

Escalate to discovery of a primary municipal Limeira transparency/accounting surface capable of exposing the same granular fields with a policy marker or stable accounting identifier.

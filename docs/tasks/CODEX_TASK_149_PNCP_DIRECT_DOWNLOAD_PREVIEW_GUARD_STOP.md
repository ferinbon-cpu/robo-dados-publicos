# TASK 149 — direct-download URL-preview guard stop

TASK 148 merged a fail-closed gate for exactly one direct temporary download of the corrected PNCP procurement-publication URL.

Exactly one direct-download invocation was attempted.

The download safety layer stopped before source retrieval with:

`download failed because url not viewed in conversation before. open the file or url using web.run first.`

A local post-check confirmed `NO_FILE_CREATED`.

Canonical result:

`STOP_DIRECT_DOWNLOAD_URL_NOT_PREVIEWED_PRE_SOURCE`

Semantics:

- direct-download invocations: 1;
- retry: 0;
- PNCP source reach: not established;
- PNCP HTTP status: not established;
- source data observed: false;
- temporary payload created: false;
- no candidate;
- no PNCP `NO_MATCH`;
- no exhaustive negative conclusion;
- no financial, transaction, or supplier identity change.

The single TASK 148 invocation authorization is consumed. The tool-required web preview was not authorized by TASK 148 and was not executed.

Any further live PNCP or alternative-source operation requires a new gate and fresh explicit owner authorization.

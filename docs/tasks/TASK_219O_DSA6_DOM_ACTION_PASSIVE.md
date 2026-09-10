# TASK 219O — exact DSA6 DOM action probe

Issue #719. First of two owner-authorized large leaps.

TASK 219N had already proved the public GeneXus area identity:
`Despesa -> AreaId ...DSA6 -> AreaOrigin ...VIS1343`.

TASK 219O performed one clean public browser load and inspected only the exact top-level DOM id `...DSA6`, with zero clicks, typing, form submissions, manual requests, PortalAction triggers or LayerInfo replay.

## Result

The exact `AreaId` was **not present as a stable top-level DOM node after load**.

Therefore no descendant action node could be inspected and no action contract was proved through this route.

This does **not** invalidate the TASK 219N area identity and does not prove content/action absence. TASK 219M already proved that the client processes server-returned LayerInfo objects dynamically.

The correct next route is to bind directly to the automatic `awsgetcontentareas.aspx` response object whose returned `id` equals the proven DSA6 identifier, then inspect that object's `info` in memory for public links/actions/forms.

## Provenance

Run `34421742752`; artifact `10131149993`.

ZIP SHA-256:
`c21ce8333e3e15fa6049a4fbb7cda885d964c9b860488d943700ecbd51fa3d3a`

Result SHA-256:
`15113b51ec77632313108616f47d8292f1bb6abb636848505c6f618e5c7f3a05`

Coverage remains 34/38.

Authorization slot 1/2 is consumed. Slot 2/2 remains authorized for TASK 219P.

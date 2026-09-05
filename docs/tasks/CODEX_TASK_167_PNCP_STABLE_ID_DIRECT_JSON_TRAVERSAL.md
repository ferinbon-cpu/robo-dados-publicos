# TASK 167 — PNCP stable-ID direct JSON traversal

## Purpose

Continue TASK 166 under the robot-wide `DIRECT_JSON_FIRST` policy. Two stable purchase identities were traversed without reverting to HTML/DOM/JavaScript reverse engineering.

Targets:

- school pass: `45132495000140-1-000368/2026`, process `I00055`;
- course: `45132495000140-1-000593/2026`, process `I00084`.

The standing PNCP read authorization was reused. No per-route authorization was requested.

## Integration API family

The documented `/api/pncp/v1` routes for purchase detail, items, history, budget sources and contracts were queried for both targets.

All 10 GETs reached PNCP and returned HTTP 503 with no payload.

Therefore the correct state is source/backend unavailability. It is not evidence that items, history, budget sources or contracts are absent.

## Public consultation purchase-detail family

The public consultation specific-purchase route succeeded for both targets:

`/api/consulta/v1/orgaos/45132495000140/compras/2026/368`

`/api/consulta/v1/orgaos/45132495000140/compras/2026/593`

Both returned HTTP 200 JSON and reconfirmed the stable IDs, process numbers and amounts.

### School pass

Observed:

- object: acquisition of school pass;
- estimated/homologated: R$ 3,816,720;
- legal basis: Lei 14.133/2021, art. 74, I;
- legal-basis description refers to exclusive producer/company/commercial representative;
- `fontesOrcamentarias=[]`.

This proves educational relevance and the legal-basis metadata. It does not by itself identify the supplier, budget source, EITI linkage, commitment or payment.

### I00084

Observed:

- object: training course;
- estimated/homologated: R$ 12,400;
- legal basis: Lei 14.133/2021, art. 74, III, f;
- legal-basis description explicitly refers to training and professional development of personnel;
- `fontesOrcamentarias=[]`.

This proves that the procurement is personnel training. It still does not identify an Education/EITI target.

## Public contracts consultation

The documented public `/api/consulta/v1/contratos` surface was attempted in four date partitions and then on the two exact purchase-publication dates.

All six requests timed out before receiving bytes.

Consequently:

- no contract match was observed;
- contract absence is **not** proven;
- supplier identity is not proven;
- commitment/liquidation/payment are not proven.

## Routing conclusion

The direct-JSON policy remains successful: the public purchase-detail route provided evidence while the integration and contract routes exposed clear transport/backend states.

No reverse engineering is required at this point. The machine-readable next action is to retry documented PNCP detail/contract routes when available or continue the remaining modality publication sweeps through the working public JSON endpoint.

Raw PNCP bodies were not persisted to Git or Drive.

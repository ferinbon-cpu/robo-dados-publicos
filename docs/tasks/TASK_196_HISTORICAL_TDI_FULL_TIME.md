# TASK 196 — historical TDI and full-time materialization

## Goal

Close two answerability partials using already existing custody before requesting new downloads:

- `NETWORK_Q2`: historical full-time share;
- `LEARN_Q3`: historical TDI.

## Evidence split

The pinned canonical analytic asset is:

`CAMADA_ANALITICA_V06_40_ESCOLAS_V08.xlsx`

SHA-256:

`0516868e06685aebe8254b11ca6488ef26b03dea61f927ff637840cf2a21e865`

The exact textual values used in this task were recovered through File Library from `ESTUDO_V5_6`. That source is not present as a separately hashed Drive asset in current custody. Its SHA is therefore deliberately `null`, not guessed.

## Full-time series

Exact municipal network series, years initial:

| Year | Active units in edition | Enrollment AI | Full-time AI |
|---|---:|---:|---:|
| 2018 | 77 | 13,140 | 11.1% |
| 2019 | 69 | 13,071 | 13.2% |
| 2020 | 69 | 13,092 | 11.5% |
| 2021 | 69 | 13,130 | 9.2% |
| 2022 | 69 | 12,815 | 14.9% |
| 2023 | 69 | 12,813 | 26.7% |
| 2024 | 69 | 12,928 | 30.0% |
| 2025 | 69 | 13,105 | 30.7% |

The source explicitly says that enrollment and full-time refer to years initial and to the municipal units that offered years initial in each edition. Therefore 2018 has 77 units and must not be retrofitted to the current fixed panel of 69.

2018→2025 change: +19.6 percentage points.

## TDI

The source declares an official municipal series covering 2006–2025, dependency municipal, total location, years initial.

The text explicitly publishes these points:

- 2006: 3.4%;
- 2011: 0.9%;
- 2012: 0.9%;
- 2017: 4.0%;
- 2023: 1.0%;
- 2024: 1.0%;
- 2025: 1.0%.

Only these exact anchors are materialized here. The task does **not** reconstruct or interpolate the unprinted intermediate annual values.

## Answerability

The existing answerability rule requires at least two periods for each of these metrics. These new rows provide:

- FULL_TIME_SHARE: 8 network periods;
- TDI: 7 exact network anchor periods.

The expected canonical movement is:

- before: 28 answerable / 8 partial / 2 explicit gaps;
- after: 30 answerable / 6 partial / 2 explicit gaps.

Only `NETWORK_Q2` and `LEARN_Q3` may change status.

## Guards

- years-initial full-time share != whole basic education full-time share;
- edition-specific provider universe != fixed current-69 panel;
- TDI anchors != complete annual table;
- no interpolation;
- no missing=zero;
- no invented hash for V5.6;
- no serving/publication/schedule/recurrence.

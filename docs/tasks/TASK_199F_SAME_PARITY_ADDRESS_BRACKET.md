# TASK 199F — same-parity address-bracket expansion

TASK 199F extends the proven school-to-sector crosswalk from 57/69 to 59/69 without using fuzzy or nearest-address inference.

## Method

A new tier D is allowed only when all of the following are true:

1. the school identity is already bridged by current SME CIE to INEP inside the verified 69-unit roster;
2. the current SME street is matched exactly after conservative normalization;
3. the current SME house number is numeric;
4. CNEFE has an immediate lower and immediate upper address on the same street and with the same parity as the SME number;
5. both bracketing addresses map to exactly the same census sector.

Opposite-side parity, one-sided extrapolation, simple nearest address, name-only and fuzzy-only matching remain forbidden.

## Two promotions

- EMEIEF Ary Gomes de Castro, Tenente Aviador: SME 220; same-parity CNEFE brackets 164 and 248; both sector 352690205000812P.
- CI Vilma Terezinha Marrafon Coppi: SME 1175; same-parity CNEFE brackets 1165 and 1189; both sector 352690205000135P.

## Result

Strong school-sector links:
57/69 -> 59/69 (85.5%).

TERRITORY_PROFILE:
239 -> 247 rows.

Ten schools remain held. EQUITY_Q1 remains partial because full-network coverage is still absent.

This task does not treat school-location territory as the socioeconomic profile of enrolled students.

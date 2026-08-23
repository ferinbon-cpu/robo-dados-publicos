# M4E.1 — TDA Limeira passive discovery runbook

## Goal
Map the public technical surface of Limeira's transparency portal before implementing a production collector.

Target supplied by the project owner:
`https://transparencia.limeira.sp.gov.br/tdaportalclient.aspx?418`

## Safety / non-invasive rules

The probe MUST NOT:
- solve or bypass CAPTCHA / human-verification;
- authenticate or reuse user cookies;
- submit forms;
- brute-force directories, IDs, parameters or endpoints;
- execute JavaScript;
- crawl the whole site;
- make high-frequency requests.

The probe MAY:
- request `robots.txt`;
- request the exact public target URL once;
- follow normal HTTP redirects;
- inventory scripts, links and forms already referenced by returned HTML;
- flag static hints containing `api`, `rest`, `json`, `csv`, `xls/xlsx`, `download`, `export` or `dadosabertos`.

If `robots.txt` explicitly disallows the target for the robot user-agent, result is `STOP_ROBOTS_DISALLOW`.
If a CAPTCHA/human-verification marker is detected, result is `STOP_HUMAN_CHALLENGE` and no bypass is attempted.

## Command

```bash
python main.py portal-probe \
  'https://transparencia.limeira.sp.gov.br/tdaportalclient.aspx?418' \
  --out runtime/tda_limeira_probe.json
```

## How to read the result

- `PASS_DISCOVERY`: passive inspection completed; it does NOT mean a data endpoint was found.
- `surface_class = SPA_ENTRY_OR_AUTH_GATE`: final URL looks like a login/bootstrap page and includes scripts. This is not, by itself, proof that authentication is required.
- `endpoint_hints`: only URLs already visible in static HTML. They are candidates, never assumed contracts.
- `STOP_HUMAN_CHALLENGE`: manual/human route or official alternative source required.
- `STOP_ROBOTS_DISALLOW`: do not fetch target with this robot user-agent.

## Next evidence gate

A TDA production connector may be enabled only after at least one of these is proven:
1. documented official API/download endpoint; or
2. public endpoint invoked by the portal itself, with stable request/response contract; or
3. stable official export route that does not require CAPTCHA or credentials.

For every proven route, capture:
- request method;
- URL/base path;
- required public parameters;
- pagination behavior;
- response content type;
- date/exercise semantics;
- update cadence;
- stable identifiers (supplier, empenho, program/action, source/destination etc.);
- rate-limit/robots/terms constraints;
- one small fixture for regression testing.

## Architecture decision

TDA-Limeira is treated as a municipal core source, not as the whole robot. The robot remains source-agnostic and should reconcile municipal evidence with TCE-SP, Siconfi, SIOPE, INEP and other official sources where relevant.

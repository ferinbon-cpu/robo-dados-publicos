# SOFTWARE V01 0.5.1 CANDIDATE — M4E.1 TDA/Limeira discovery

## Status
CANDIDATE. Does not replace active 0.4.0 until live validation.

## Added
- passive public-portal reconnaissance module (`discovery.portal_probe`);
- `portal-probe` CLI command;
- robots.txt policy check;
- normal redirect capture;
- static HTML inventory of scripts, stylesheets, forms and links;
- endpoint-hint detection without guessing endpoints;
- CAPTCHA/human-challenge STOP guard (no bypass);
- sensitive query-value redaction in probe logs;
- Limeira municipal source-map documentation;
- TDA-specific discovery runbook;
- discovery-only registry for the Limeira TDA portal.

## Deliberately not added
- no CAPTCHA solver;
- no credentialed portal automation;
- no endpoint brute force;
- no JavaScript/browser crawler;
- no production TDA collection before a public stable endpoint/export contract is proven.

## Acceptance gate
A live passive probe from Cloud Shell/GitHub must be captured before any TDA collection adapter is enabled.

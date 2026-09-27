# TASK 009E-L — autorização one-shot para descoberta documental oficial SIOPE 2025

## Estado

Autorização explícita do proprietário recebida após o merge da TASK 009E em `main` `21ae120bbabe93bb80bd473d2c76f7d99f18513c`.

Esta autorização é exclusivamente para uma descoberta documental pública e bounded, destinada a responder:

1. `S1_NUM_POPU`: definição oficial, fonte da população, regra temporal/vintage e aplicabilidade ao regime corrente/2025;
2. `S2_FINANCIAL_ALIAS_BRIDGE`: ponte oficial, campo a campo, entre os dez aliases financeiros atuais e os conceitos oficiais já documentados.

## Limites

- somente autoridade FNDE;
- hosts permitidos: `gov.br`, `www.gov.br`, `fnde.gov.br`, `www.fnde.gov.br`;
- GET/read-only;
- máximo de 12 URLs oficiais distintas e 12 aberturas de documentos oficiais;
- uma tentativa por URL;
- sem retry;
- sem autenticação, cookies, OAuth, credenciais ou sessão;
- sem repetir a rota SharePoint que retornou HTTP 401;
- sem login gov.br/Antonieta;
- sem consulta de registros financeiros de Limeira ou parâmetros município/ano/período em endpoint de dados;
- sem download de pacote binário;
- sem Drive, publicação, Bronze/Silver/Gold;
- sem promoção de alias, `NUM_POPU`, comparabilidade, fechamento anual ou série fechada durante a descoberta.

## Uso da autorização

A autorização é one-shot. A sessão remota deve produzir apenas uma evidência documental sanitizada e depois ser submetida a revisão T0 separada antes de qualquer promoção semântica.

O arquivo machine-readable correspondente é `config/siope_2025_official_alias_documentary_discovery_authorization.v1.json`.

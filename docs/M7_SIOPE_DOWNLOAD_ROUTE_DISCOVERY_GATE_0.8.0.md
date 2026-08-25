# M7 — SIOPE download-route discovery gate — 0.8.0 CANDIDATE

## Estado anterior validado

O gate `M7_SIOPE_LIMEIRA_ROUTE_DISCOVERY_GATE_0_8_0` passou ao vivo no GitHub Actions run `32791989543` (#2), commit `0e3ef17f9613dd0f249a4caeff0a17de9f7c80f8`.

A evidência confirmou:

- consulta clássica SIOPE observada com CAPTCHA;
- nenhuma submissão de formulário;
- produto Antonieta `Dados Gerais - SIOPE` observado;
- artefato declarado `exports/SIOPE/SIOPE_DADOS_GERAIS_SIOPE.txt.gz`;
- nenhuma URL absoluta de download exposta pela página (`explicit_download_url_count=0`);
- nenhum download de artefato;
- nenhuma escrita remota;
- nenhuma autorização de coleta, processamento, recorrência ou schedule.

Portanto o estado é `CANDIDATE_IDENTIFIED_ARTIFACT_NOT_VERIFIED`.

## Problema do subgate

O caminho de armazenamento declarado não deve ser transformado por inferência em uma URL de aquisição. Antes de verificar o `.txt.gz`, o robô precisa observar uma rota de download explicitamente declarada pela própria aplicação oficial.

## Escopo permitido

O workflow manual `M7 SIOPE DOWNLOAD ROUTE DISCOVERY GATE` pode ler somente:

1. a página oficial Antonieta do produto 20;
2. até 8 arquivos JavaScript explicitamente declarados por `<script src>` na própria página e servidos por `www.fnde.gov.br`.

Limites:

- página: 2 MiB;
- cada script: 1 MiB;
- total de scripts: 6 MiB;
- método de rede: GET apenas;
- redirects são revalidados contra a allowlist de host.

## Proibições

O gate não pode:

- inventar URL a partir de `exports/SIOPE/...`;
- fazer `HEAD` na rota candidata;
- chamar a rota candidata descoberta;
- baixar o `.txt.gz`;
- fazer POST ou submeter formulário;
- contornar CAPTCHA;
- usar OAuth ou Google Drive;
- coletar ou processar SIOPE;
- habilitar recorrência ou schedule.

Query strings de candidatas não são expostas no artifact: apenas a URL sem query e flags indicando presença de query/fragmento.

## Decisão

Se uma rota explícita for encontrada, o gate pode retornar `PASS_M7_SIOPE_DOWNLOAD_ROUTE_DISCOVERY_GATE` com `EXPLICIT_ROUTE_CANDIDATE_NOT_FETCHED`.

Isso ainda não autoriza aquisição. O próximo gate será `M7_SIOPE_ANTONIETA_ARTIFACT_VERIFICATION_GATE_0_8_0`, que somente poderá ser construído usando a rota explicitamente observada.

Se nenhuma rota explícita for observada, o resultado correto é STOP fail-closed, sem adivinhação.

## Validação offline inicial

CI `32793058402` (#106):

- preflight: PASS 56/56;
- gate M7 de desenho: PASS;
- compileall: PASS;
- testes unitários: 213/213 PASS;
- testes do novo parser/gate: 8/8 PASS;
- testes do novo workflow: 6/6 PASS;
- regressões históricas: 109/109 PASS.

O estado operacional permanece `NONE`.

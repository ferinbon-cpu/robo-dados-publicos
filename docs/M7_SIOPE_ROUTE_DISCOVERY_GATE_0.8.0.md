# M7 — Gate de descoberta passiva da rota SIOPE — 0.8.0

## Objetivo

Identificar uma rota de aquisição tecnicamente verificável para o piloto SIOPE–Limeira sem converter a descoberta em coleta. O gate é manual, somente-leitura e limitado a duas superfícies oficiais previamente declaradas.

## Pesquisa pública que motivou o gate

A pesquisa de 24/08/2026 encontrou três famílias de acesso ao SIOPE:

### 1. Consulta clássica SIOPE

Superfície: `https://webservice.fnde.gov.br/siope/dadosInformadosMunicipio.do`.

A interface apresenta seleção de ano, período, UF, município, administração e planilha. Rotas indexadas publicamente revelam parâmetros como `anos`, `periodos`, `cod_uf`, `municipios`, `admin` e `planilhas`, porém também há evidência de validação por CAPTCHA em consultas parametrizadas.

Decisão: a interface clássica não será usada para aquisição automatizada se houver CAPTCHA ou bloqueio. O robô não submete formulário, não envia token de CAPTCHA e não tenta contornar desafio humano.

### 2. Dados Abertos / Olinda

O catálogo público do SIOPE oferece recursos estruturados e referências a exportação JSON/CSV. Porém, o catálogo e relatos públicos disponíveis indicam necessidade de verificar atualização/cobertura antes de tratá-lo como fonte corrente.

Decisão: permanece como rota alternativa de pesquisa; não é promovida neste gate.

### 3. Plataforma Antonieta de Barros

Produto oficial publicado: `Dados Gerais - SIOPE`.

Página declarada: `https://www.fnde.gov.br/plataforma-antonieta-de-barros/dados/produtos-de-dados/visualizar/20`.

A página oficial declara o artefato:

`exports/SIOPE/SIOPE_DADOS_GERAIS_SIOPE.txt.gz`

A existência desse caminho torna a Antonieta a candidata preferencial para automação, mas **não prova por si só uma URL de download**. O código deste gate não concatena host, prefixo ou diretório para tentar adivinhar o endereço final.

## Escopo técnico do gate

O workflow `M7 SIOPE ROUTE DISCOVERY GATE`:

1. exige `workflow_dispatch` e confirmação booleana explícita;
2. roda preflight offline, dry-run, compilação, suíte unitária e regressões históricas;
3. faz no máximo dois GETs HTTPS nas superfícies oficiais declaradas;
4. limita a resposta a 2 MiB por página;
5. aceita somente `www.fnde.gov.br` e `webservice.fnde.gov.br`;
6. não usa OAuth do Drive;
7. não submete formulário;
8. não resolve/bypassa CAPTCHA;
9. não baixa o `.txt.gz`;
10. não escreve em Bronze, Silver, Gold, bancos, logs ou outputs;
11. publica somente um JSON sanitizado de decisão.

## Tratamento da interface clássica

A interface clássica é informativa, não obrigatória. Se a página responder e expuser CAPTCHA, o resultado registra `BLOCK_AUTOMATED_ACQUISITION_HUMAN_CHALLENGE`. Se houver rejeição/WAF ou indisponibilidade, registra `BLOCK_AUTOMATED_ACQUISITION_SURFACE_UNAVAILABLE`.

Nenhum desses casos derruba o gate se a página Antonieta puder ser validada, porque a Antonieta é a candidata de aquisição preferencial.

## Condição para PASS

O gate passa quando a página oficial da Antonieta:

- corresponde ao produto `Dados Gerais - SIOPE`;
- declara exatamente `exports/SIOPE/SIOPE_DADOS_GERAIS_SIOPE.txt.gz`;
- é observada sem download do artefato.

Mesmo em PASS, o estado da rota continua:

`CANDIDATE_IDENTIFIED_ARTIFACT_NOT_VERIFIED`.

A fonte não avança para `ONE_TIME_AUTHORIZED`.

## Próximo gate

`M7_SIOPE_ANTONIETA_ARTIFACT_VERIFICATION_GATE_0_8_0`.

Esse gate futuro poderá verificar o artefato somente se uma URL de download for explicitamente observada/provada. A verificação deverá ser uma aquisição temporária e não persistente, limitada a inspecionar:

- HTTP status e redirects;
- content-type / content-encoding;
- tamanho e hash;
- assinatura gzip;
- nome e estrutura do arquivo interno;
- cabeçalhos/schema;
- presença do recorte Limeira/SP e do exercício 2024;
- semântica necessária para distinguir receitas, despesas, MDE e Fundeb.

Ainda nesse estágio, não haverá persistência no Drive, publicação de relatório substantivo, recorrência ou schedule.

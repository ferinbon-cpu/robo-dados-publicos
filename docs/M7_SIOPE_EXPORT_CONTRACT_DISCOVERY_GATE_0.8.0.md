# M7 — SIOPE export contract discovery gate 0.8.0

## Objetivo

Caracterizar, de forma passiva e sanitizada, o contrato público do controle **Exportar artefato** da Plataforma Antonieta de Barros para o produto **Dados Gerais - SIOPE**, depois que a descoberta de rota estática confirmou que não existe URL explícita em `href`, `action` ou literal estático aceito pelo gate anterior.

## Evidência que motivou o subgate

O run `32794666678` do gate anterior observou:

- página oficial verificada;
- artefato `exports/SIOPE/SIOPE_DADOS_GERAIS_SIOPE.txt.gz` declarado;
- 1 script externo declarado e lido sem falha;
- 1 marcador de exportação em atributo `data-*`;
- 1 marcador de exportação em script inline;
- 0 `href/action` de exportação;
- 0 evento inline de exportação;
- 0 rota estática candidata.

A interpretação canônica é **controle dinâmico observado, rota de aquisição ainda não comprovada**.

## O que o gate pode ler

Somente:

1. a página oficial do produto SIOPE na Antonieta;
2. scripts JavaScript explicitamente declarados por essa página;
3. apenas no host `www.fnde.gov.br`;
4. via GET read-only;
5. respeitando limites de tamanho e quantidade já usados no gate anterior.

## O que o gate extrai

Somente metadados sanitizados:

- nomes de `data-*` associados a exportação;
- classe semântica do valor do atributo;
- valor público conservador somente quando curto, sem query e sem marcadores de segredo;
- chaves `dataset.*` e nomes lidos por `getAttribute('data-*')`;
- identificadores de função/variável relacionados a export/download/artefato;
- contagens de mecanismos JavaScript como `fetch`, XHR, axios, jQuery AJAX, `window.open`, navegação por `location`, submit, listeners, Blob e ObjectURL;
- templates de rota em strings normais e template literals com crase;
- `${...}` é normalizado para `{VAR}`;
- query strings não são persistidas.

O gate não persiste HTML ou JavaScript bruto.

## Proibições

O gate **não**:

- clica no botão;
- executa JavaScript no navegador;
- usa Playwright/Selenium/Puppeteer;
- chama uma rota candidata;
- faz HEAD no artefato;
- baixa `.txt.gz`;
- envia formulário;
- contorna CAPTCHA;
- usa OAuth ou Drive;
- coleta/processa dados SIOPE;
- habilita recorrência ou schedule.

## Estados possíveis

### PASS — `ROUTE_TEMPLATE_OBSERVED_NOT_CALLED`

Existe template de rota explicitamente observável no contrato JavaScript, mas ele não foi executado. Isso ainda não autoriza download.

### PASS — `DYNAMIC_EXPORT_CONTROL_OBSERVED_ROUTE_UNPROVEN`

O contrato do controle foi observado, mas a rota continua dependente de runtime. O próximo passo é **desenhar**, não executar automaticamente, um probe mínimo do runtime.

### STOP — `STOP_SIOPE_EXPORT_CONTRACT_NOT_OBSERVED`

O controle dinâmico não pôde ser caracterizado dentro da superfície explicitamente autorizada.

## Próximo gate

`M7_SIOPE_EXPORT_RUNTIME_ROUTE_PROBE_DESIGN_0_8_0`

Esse nome representa somente a etapa de desenho. Qualquer clique, execução de navegador, interceptação de request ou download exigirá gate separado e autorização explícita.

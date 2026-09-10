# TASK 219U — current-session live Despesa DOM

## Resultado canônico

A sessão pública única resolveu `Despesa` por `AreaName=Despesa` + `AreaOrigin=2_92_guestuser_207_6_DSL0_VIS1343` e obteve o `AreaId` da própria sessão:

`d10761cb41dc4ce5942ead9b39f54c66DSA6`

Após o carregamento automático normal do portal, o nó vivo com esse id existe e é:

- `div.chart.selected`;
- contém o resumo público renderizado de Despesa (`Fixado Total`, `Empenhado`, `Processado`);
- contém 30 `div`, 4 `img`, 4 `script`, 5 `style`, 1 `table`, 1 `tbody`, 4 `td` e 4 `tr` considerando o root;
- não contém `a`, `button`, `form`, `input`, `select`, `textarea`, `href` ou `onclick` explícitos aceitos pelo gate;
- o root não possui listener direto exposto pelo CDP.

Logo, o problema antigo de procurar um `AreaId` obsoleto foi encerrado: o **root vivo de Despesa da sessão atual está provado**.

## Correção fail-closed

O carrier registrou provisoriamente ausência de ação explícita porque encontrou zero ações aceitas no subtree. Essa flag não é canônica.

Existem quatro scripts inline de 787 caracteres no conteúdo e listeners delegados no `document`/`window`, incluindo listeners de `click`. A TASK 219U, por desenho, não persistiu corpos de scripts, não inspecionou a semântica dos handlers e não executou eventos.

Portanto o resultado científico correto é:

**CURRENT-SESSION LIVE DESPESA DOM = PROVADO COMO CONTAINER DE GRÁFICO; AÇÃO HTML EXPLÍCITA = NÃO ENCONTRADA; SEMÂNTICA DE AÇÃO DELEGADA VIA SCRIPT = AINDA NÃO PROVADA.**

Isso substitui qualquer leitura de “zero controles = não existe navegação”.

## Próximo gargalo único

A próxima etapa segura deve ler, em uma nova sessão autorizada, apenas o código já carregado em memória necessário para responder:

> Os quatro scripts inline do gráfico ou os handlers delegados de clique ligam explicitamente o `div.chart` de Despesa a alguma ação pública GeneXus/portal, rota ou parâmetro?

Persistência permitida nessa futura etapa: nomes de funções, seletores, identificadores de ação/rota, parâmetros públicos curtos, hashes e pequenos trechos estritamente necessários para provar o vínculo. Não persistir corpos completos de script.

Nenhum clique deve ocorrer antes de existir uma ação oficial única e documentalmente identificada.

## Limites preservados

A TASK 219U executou exatamente uma sessão e uma navegação inicial, sem clique, digitação, submissão, XHR/fetch manual, endpoint direto, PortalAction, replay/síntese de LayerInfo, retry ou consulta ao Empenho `3286-2026`.

Consequentemente continuam não provados:

- Contrato `45/2026` ↔ Empenho `3286-2026`;
- atribuição dos R$ 17.500,00 ao Contrato `45/2026`;
- `CTRL_Q2` e `PROC_Q1–Q3`.

Cobertura permanece `34/38`.

## Proveniência

- run: `34488422242`
- job: `102908568030`
- execution head: `1fe2c764cf03aa3b1e295a7e3c2b1f9b3ba3ea38`
- artifact: `10156669499`
- artifact ZIP SHA-256: `d6026162ad106c2d28767e497af17c386a8c22cade834214ec1908de972e46ba`
- artifact member SHA-256: `5112e2744cb23926373ac5d8c9bec0320ac6f92e1585645d9badee50accdf4c4`
- executed workflow blob = historical workflow blob: `d6e5b32e795a4941577ef7dc19b1d33598b93aba`
- live workflow removido após o run: `e604be7864d89c893ea6b1799593d74cc725e99f`

# TASK 195C — fechar a ponte semântica de `VL_DESP_DOTA_ATUA_EDU`

## Objetivo

Resolver o último alias financeiro SIOPE 2025 que permanecia parcial sem transformar uma diferença de R$ 1.000,00 em fórmula inventada do backend.

O alvo é `VL_DESP_DOTA_ATUA_EDU`, em `Dados_Gerais_Siope`, Limeira/SP, exercício 2025, período 6/Anual.

## Problema herdado

A TASK 010N-R-E-M3 havia provado 9/10 aliases financeiros por reconciliação operacional exata. O único parcial era:

- `VL_DESP_DOTA_ATUA_EDU = 520399255,47`;
- RREO Anexo 8, linha 33, DA = `520398255,47`;
- diferença = `1.000,00`;
- uma conta oficial `3.2.00.00.00` de Juros e Encargos da Dívida tinha DA de `1.000,00` e execução zero.

O gate anterior exigiu uma regra oficial de inclusão para explicar esse R$ 1.000,00. Isso foi correto enquanto a linha 33 do RREO era tratada como candidata a superfície de identidade do alias. A investigação atual provou que essa identidade não é requisito semântico do campo.

## Nova cadeia primária

### 1. Dicionário de Dados SIOPE 2019

Fonte FNDE:

`https://www.fnde.gov.br/phocadownload/sistemas/siope/Manuais/DICIONARIO%20DE%20DADOS%20SIOPE%202019.pdf`

Na seção `Dados Consolidados`, o documento define uma família única e ordenada de campos de receita, despesa total e despesa com educação. Entre eles aparecem:

- `VL_DESPESA_DOTACAO_ATUALIZADA` — valor de despesa dotada atualizada;
- `VL_DESPESA_EMPENHADA` — valor de despesa empenhada;
- `VL_DESPESA_LIQUIDADA` — valor de despesa liquidada;
- `VL_DESPESA_PAGA` — valor de despesa paga;
- `VL_DOTACAO_ATUALIZADA_EDUCACAO` — valor de despesa dotada atualizada com educação;
- `VL_DESPESA_EMPENHADA_EDUCACAO` — valor de despesa empenhada com educação;
- `VL_DESPESA_LIQUIDADA_EDUCACAO` — valor de despesa liquidada com educação;
- `VL_DESPESA_PAGA_EDUCACAO` — valor de despesa paga com educação.

A prova é conceitual e de família de campos; não é uma fórmula de soma por conta contábil.

### 2. Tutorial Básico SIOPE 2024 v2

Fonte FNDE:

`https://www.gov.br/fnde/pt-br/assuntos/sistemas/siope/media/Tutorial_Bsico_Siope_2024_v2.pdf`

A página impressa 21 mostra a própria aplicação SIOPE na guia `Dados Gerais`. Dentro dela aparecem três abas distintas:

1. `Receita total do Município`;
2. `Despesa total do Município`;
3. `Despesa com Educação (Função 12)`.

A página impressa 23 apresenta MDE em guia própria. A página impressa 25 apresenta `Demonstrativo da Função Educação` como outra tela. Logo, o sistema oficial separa explicitamente:

`Dados Gerais / Despesa com Educação (Função 12)`

≠

`MDE`

≠

`Demonstrativo da Função Educação / RREO usado como superfície de conferência`.

### 3. Metadata municipal 2025

O pacote oficial entregue anteriormente, `Metadados_Mun_2025.zip`, SHA-256 `41511c141e1af025ae2b565085583d6a3ab7b4577862f8ebdc308605101c1e5b`, identifica:

- versão de metadados 333;
- software 25.0.5.6;
- raiz `Despesas com Educação`, `COD_PAST=27`;
- 715 pastas na hierarquia;
- 561 pastas operacionais com `DA/DE/DL/DP`;
- `DA = Dotação Atualizada`;
- MDE em estruturas separadas.

### 4. Contrato OData atual

`Dados_Gerais_Siope` expõe o bloco atual:

- `VL_DESP_DOTA_ATUA_EDU`;
- `VL_DESP_EMPE_EDU`;
- `VL_DESP_LIQU_EDU`;
- `VL_DESP_ORCA_EDU`;
- `VL_DESP_PAGA_EDU`.

Os três irmãos de execução `EMPE/LIQU/PAGA` já foram reconciliados exatamente com agregados oficiais da função Educação. Somados aos seis aliases de receita/despesa total, 9/10 aliases já tinham prova operacional independente.

A nova cadeia documental fecha o décimo no nível correto: **identidade alias → conceito**, sem exigir reconstrução da fórmula interna do backend.

## Correção metodológica

A diferença de R$ 1.000,00 contra a linha 33 do RREO não é mais um bloqueio de semântica do alias. A linha 33 pode continuar como superfície de corroboração, mas não é a definição canônica de `Dados Gerais / Despesa com Educação (Função 12)`.

Portanto:

- o R$ 1.000,00 de `3.2.00.00.00` continua apenas explicação candidata;
- não se afirma que essa conta é a regra de inclusão do backend;
- não se afirma uma fórmula completa de agregação;
- não se força igualdade `VL_DESP_DOTA_ATUA_EDU = RREO linha 33`;
- não se força `EDU = MDE`.

## Probe remoto bounded desta rodada

Foi tentada uma rota adicional para obter `Despesas_Siope` com `IDN_CLAS=DA` diretamente do FNDE. A `$metadata` respondeu, mas a consulta de dados expirou em três execuções bounded, incluindo a réplica exata do filtro oficial que havia funcionado no handoff da TASK 195.

Runs:

- `34669276182` — timeout de transporte;
- `34669352736` — timeout de transporte;
- `34669441335` — timeout usando o filtro exato anteriormente bem-sucedido.

Nenhum timeout foi convertido em zero rows ou ausência de `DA`.

A superfície pública `relatorioQuadroResumoDespesasMuni.do` respondeu 200 em probe read-only. Seu fluxo final é POST e possui reCAPTCHA. Nenhum formulário foi submetido e nenhum CAPTCHA foi contornado. TinyFish não foi usado.

## Resultado

A TASK195C promove apenas:

`B2_FINANCIAL_ALIAS_BRIDGE = PROVEN_10_OF_10_ALIAS_TO_CONCEPT`

com:

`VL_DESP_DOTA_ATUA_EDU = PROVEN_ALIAS_TO_EDUCATION_EXPENSE_UPDATED_BUDGET_CONCEPT`

O conceito canônico é:

`DESPESA_COM_EDUCACAO_FUNCAO_12_DOTACAO_ATUALIZADA`.

A fórmula de agregação do backend permanece `NOT_PROVEN` e não é necessária para a identidade semântica do campo.

## O que não muda

- B1 já está resolvido pela disposição oficial FNDE que manda desconsiderar `NUM_POPU` para análise populacional e usar IBGE diretamente;
- B3 continua `NOT_PROVEN_EFFECTIVE_SELECTION_RULE_MISSING`;
- `annual_closure_status` continua `UNKNOWN`;
- Gold 2025 não é calculado nesta task;
- 0.8.0 continua `CANDIDATE`;
- série anual fechada continua 2016–2024;
- nenhuma evidência histórica M3/M4 é reescrita retrospectivamente.

## Guardas

- `DADOS_GERAIS_FUNCAO12_NE_RREO_LINE33_IDENTITY`;
- `EDU_NE_MDE`;
- `ALIAS_CONCEPT_PROOF_NE_BACKEND_AGGREGATION_FORMULA`;
- `THOUSAND_REAL_VARIANCE_NE_INCLUSION_RULE_PROOF`;
- `TRANSPORT_TIMEOUT_NE_ZERO_ROWS`;
- `CAPTCHA_NOT_BYPASSED`;
- `B3_UNCHANGED`;
- `NO_GOLD_2025_CALCULATION`;
- `NO_RELEASE_PROMOTION`.

# TASK 010L — análise estática offline da bridge OData SIOPE 2025

## Resultado

`KEEP_S2_NOT_PROVEN_LOCAL_STATIC_PAYLOAD_NO_LITERAL_ODATA_BRIDGE`

A análise estática foi concluída usando o instalador SIOPE 2025 disponível localmente, sem executar EXE, DLL, CML, CZIP ou qualquer conteúdo interno. O SHA-256 do instalador foi recalculado e coincide exatamente com o artefato já pinado.

A TASK 010L é exclusivamente B2. `NUM_POPU`, finalidade anual, Gold, série 2016–2025 e 2026 ficaram fora de escopo.

## Artefato e payload estático

Instalador recebido:

- `Siope_2025_Anual-25.0.5.6.exe.exe`
- tamanho: `29.772.070` bytes
- SHA-256: `3c85dd4195a31e67131b8e550509dc2d014ead3279bda26656192feeaac86bc2`
- executado: **não**

O payload Inno previamente decompresso por parsing estático possui `83.202.202` bytes e SHA-256 `3d23992cce9138558232fd38711c1752def4ab8d6fc0a5d8921975fc709f5e78`. Foram observadas dez imagens PE.

O PE principal possui `50.456.322` bytes e SHA-256 `a89aa356bf20a73c0c9f5033b1cef562afc3af1bf8e4c1dc7b80eff5dd024dc8`.

## Busca dos aliases e do recurso OData

A busca exata, case-insensitive, foi feita em ASCII e UTF-16LE sobre:

1. instalador original;
2. payload Inno estaticamente decompresso;
3. dez imagens PE observadas.

Resultado:

- `Dados_Gerais_Siope`: **0 hits**;
- `DADOS_ABERTOS_SIOPE`: **0 hits**;
- `olinda-ide`: **0 hits**;
- cada um dos dez aliases financeiros OData: **0 hits**.

Isso permite afirmar apenas que a bridge literal não está presente nas superfícies estáticas locais analisadas. Não permite inferir que a bridge inexista no backend remoto.

## Vocabulário interno observado no desktop

O PE principal contém símbolos Delphi atuais para o vocabulário conceitual interno, entre eles:

- `@Constantes@_PREV_ATUA`;
- `@Constantes@_RECE_REAL`;
- `@Constantes@_DOTA_ATUA`;
- `@Constantes@_DESP_EMPE`;
- `@Constantes@_DESP_LIQU`;
- `@Constantes@_DESP_PAGA`;
- `@Constantes@_COD_EDUCACAO`.

Isso é coerente com os conceitos já pinados pela TASK 010K, mas não cria uma identidade entre esses símbolos e os nomes publicados pelo recurso OData.

## SQL, FireDAC e SQLite

O cliente contém FireDAC/SQLite e SQL textual para diversas estruturas internas. Porém nenhum dos dez aliases-alvo aparece no payload. Consequentemente não foi possível pinar nenhuma construção inequívoca do tipo `campo_interno AS ALIAS_ODATA`, view ou serializer que produza os nomes publicados.

`mapping_mechanism = NOT_OBSERVED` para os dez aliases.

## Barramento e serviço

O PE principal contém as URLs:

- `https://hmg.fnde.gov.br/siopebarramento/auth-siope`;
- `https://www.fnde.gov.br/siopebarramento/auth-siope`.

Uma das imagens PE é identificada como `libWfOAuth2.dll`, com strings `siopebarramento.cliente` e `br.gov.fnde.siopebarramento.cliente`. Os exports observados são exclusivamente da família `WebFormAuth_*`, incluindo `WebFormAuth_jwt` e variantes de evento/log.

A evidência estática sustenta a presença de uma camada de autenticação para o barramento no cliente desktop. Não sustenta que a implementação do recurso público `Dados_Gerais_Siope` ou sua bridge financeira esteja embarcada nesse componente.

Também existem no PE principal URLs de importação remota do Tesouro para receita/despesa. Elas demonstram consumo de serviços externos pelo desktop, mas não são evidência da bridge OData pública em questão.

## Matriz B2

| Alias | Conceito atual conhecido | Bridge estática | Status |
|---|---|---|---|
| `VAL_RECE_PREV_ATUA` | PA / Previsão Atualizada | não observada | PARTIAL |
| `VAL_RECE_REAL` | RR / Receitas Realizadas | não observada | PARTIAL |
| `VAL_DESP_DOTA_ATUA` | DA / Dotação Atualizada | não observada | PARTIAL |
| `VAL_DESP_EMPE` | DE / Despesas Empenhadas | não observada | PARTIAL |
| `VAL_DESP_LIQU` | DL / Despesas Liquidadas | não observada | PARTIAL |
| `VAL_DESP_PAGA` | DP / Despesas Pagas | não observada | PARTIAL |
| `VL_DESP_DOTA_ATUA_EDU` | DA em escopo educacional; agregado exato não provado | não observada | PARTIAL |
| `VL_DESP_EMPE_EDU` | DE em escopo educacional; agregado exato não provado | não observada | PARTIAL |
| `VL_DESP_LIQU_EDU` | DL em escopo educacional; agregado exato não provado | não observada | PARTIAL |
| `VL_DESP_PAGA_EDU` | DP em escopo educacional; agregado exato não provado | não observada | PARTIAL |

Resumo: `PROVEN=0`, `PARTIAL=10`, `AMBIGUOUS=0`, `NOT_FOUND=0`.

## Aliases EDU

A TASK 010K já demonstrou que `Despesas com Educação` e MDE aparecem como estruturas distintas no metadata atual. A análise do instalador não encontrou serializer, view ou rotina de exportação ligando uma dessas estruturas aos quatro aliases `_EDU`.

Portanto `EDU = MDE` continua explicitamente proibido.

## Decisão B2

`S2_FINANCIAL_ALIAS_BRIDGE = NOT_PROVEN`.

O resultado negativo é informativo: a próxima investigação não deve repetir buscas por strings no mesmo cliente desktop. A bridge aparentemente depende de uma classe de evidência que não está contida de forma literal no payload local analisado.

Classes de evidência úteis daqui em diante:

- EDMX/metadata oficial do serviço com mapeamento semântico de origem;
- SQL/view ou código oficial do backend que monta `Dados_Gerais_Siope`;
- dicionário atual oficial que mapeie explicitamente os dez aliases;
- módulo estático adicional do backend/barramento que contenha a camada pública de exportação.

## Estados preservados

- `0.7.0 = ACTIVE`;
- `0.8.0 = CANDIDATE`;
- `2025 = PROVEN_STRUCTURAL_RECENT`;
- `S1_NUM_POPU = NOT_PROVEN`;
- `S2_FINANCIAL_ALIAS_BRIDGE = NOT_PROVEN`;
- `annual_closure_status = UNKNOWN`;
- `semantic_comparability_status = UNKNOWN`;
- `gold_metrics_status = UNKNOWN/BLOCKED`;
- série fechada = `2016-2024`;
- `2026 = UNPROVEN_CURRENT_YEAR`.

Nenhuma promoção foi realizada.

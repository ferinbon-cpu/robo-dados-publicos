# TASK 185 — Stage A: persistência real TCE 2026 e materialização futura do ACCOUNTING_LEDGER

## Objetivo

Preparar, sem rede e sem mutação remota, o contrato exato para recuperar e persistir as linhas reais de despesas 2026 de Limeira publicadas pelo TCE-SP e, em uma etapa posterior e separadamente autorizada, materializar o produto `ACCOUNTING_LEDGER`.

Esta Stage A é estritamente T0/OFFLINE. Ela não executa GET, não escreve no Drive, não altera serving e não publica nada.

## Fonte exata já provada

A TASK 172 provou a rota atual:

- source_id: `TCESP_LIMEIRA_2026_DESPESAS`
- URL: `https://transparencia.tce.sp.gov.br/sites/default/files/csv/despesas-limeira-2026.zip`
- membro esperado: `despesas-limeira-2026.csv`
- observação histórica da TASK 172: 39.780 linhas

A contagem 39.780 é somente evidência histórica. A futura execução não falhará apenas porque o arquivo oficial passou a conter outra quantidade legítima de linhas.

## Schema contábil

A Stage A reutiliza, sem redefinir semântica, o adapter da TASK 173.

As 17 colunas já provadas devem continuar presentes:

- tp_despesa
- nr_empenho
- identificador_despesa
- ds_despesa
- dt_emissao_despesa
- vl_despesa
- ds_funcao_governo
- ds_subfuncao_governo
- cd_programa
- ds_programa
- cd_acao
- ds_acao
- ds_fonte_recurso
- ds_cd_aplicacao_fixo
- ds_modalidade_lic
- ds_elemento
- historico_despesa

Coluna obrigatória ausente, cabeçalho duplicado, arquivo vazio ou membro ZIP incorreto implicam STOP. Colunas extras podem ser observadas e registradas, mas não são promovidas automaticamente a campos provados.

## Custódia futura

A estrutura do Drive já existente foi verificada.

Destino pinado para uma futura Stage B autorizada:

- camada: `01_BRONZE`
- pasta: `CONTABILIDADE_LIMEIRA_2025_2026`
- folder id: `1cgG2YiVm14DYEqAJGFpB7GOKaRloIqUC`

A Stage A não escreve nessa pasta.

Quando houver autorização específica, a persistência prevista é create-only e hash-addressed:

- ZIP: `TCESP_LIMEIRA_2026_DESPESAS__ZIP__{zip_sha256}.zip`
- CSV: `TCESP_LIMEIRA_2026_DESPESAS__CSV__{csv_sha256}.csv`
- manifesto: `TCESP_LIMEIRA_2026_DESPESAS__MANIFEST__{zip_sha256}.json`

O manifesto é escrito por último. Qualquer colisão deve interromper a operação antes da primeira escrita. Overwrite, delete e move não estão autorizados.

## Validador offline

`robo_dados_publicos/accounting/task185_persistence.py` fornece:

- validação do contrato Stage A contra TASK 172, TASK 173 e TASK 176;
- inspeção offline de bytes ZIP já fornecidos ao processo;
- verificação do membro exato;
- proteção contra caminho ZIP inseguro e archive size excessivo;
- SHA-256 do ZIP e do CSV;
- detecção conservadora de delimitador entre `;` e `,` somente quando o conjunto completo de headers provados resolve sem ambiguidade;
- contagem das linhas observadas;
- registro de colunas extras;
- plano determinístico do manifesto de custódia.

O módulo não implementa HTTP e não chama Google Drive.

## Stage B — ainda bloqueada

Uma nova autorização explícita do owner é obrigatória antes de qualquer GET.

A autorização anterior da TASK 172 está consumida e não pode ser reutilizada.

A futura autorização deve estar vinculada, no mínimo, a:

- URL exata;
- implementation SHA exato;
- pasta de custódia exata;
- orçamento máximo de 1 request;
- ausência de serving/publicação/schedule/recurrence.

A issue #581, por si só, não constitui essa autorização.

## Stage C — somente após persistência real

Depois que a fonte real estiver persistida e reconciliada:

1. cada linha real será normalizada por `normalize_tcesp_expense_row`;
2. os estágios COMMITMENT, LIQUIDATION, PAYMENT, REVERSAL e OTHER_REVIEW continuarão separados;
3. `build_accounting_ledger` produzirá snapshot determinístico;
4. chaves transacionais e dimensões programáticas serão preservadas;
5. valor, data, texto e semelhança semântica continuarão incapazes de criar identidade;
6. programa/ação/fonte/aplicação continuarão contexto, não prova de identidade de uma política específica;
7. a matriz das 38 perguntas será recalculada e o ganho atribuível ao ledger será reportado separadamente.

## Hard guards

- 39.780 histórico != contagem futura obrigatória
- registro TCE != identidade primária municipal da política
- empenho != liquidação != pagamento
- valor/data/texto != identidade
- programa/ação/fonte != identidade específica de política
- fixture sintética != ledger real
- leitura da fonte != autorização de escrita no Drive
- ACCOUNTING_LEDGER != serving/publicação

## Efeitos remotos desta Stage A

- source network: 0
- Drive read operacional: 0
- Drive write: 0
- serving: 0
- publication: 0
- schedule: 0
- recurrence: 0

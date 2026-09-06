# TASK 191 — gasto anual educacional por matrícula, 2025

## Objetivo

Fechar `FIN_Q2 — Quanto por aluno?` sem dividir gasto parcial de 2026 por matrícula anual de 2025.

A tarefa usa somente evidência já sob custódia lógica do projeto:

- RREO Anexo 8, linha 33, Limeira, 6º bimestre de 2025: R$ 463.766.660,32 empenhados, R$ 455.867.723,30 liquidados e R$ 420.264.584,22 pagos;
- painel Censo Escolar V08, 69 unidades atuais, 2025: 22.788 matrículas (`mat_bas`), soma previamente validada.

## Regra temporal

O fechamento do último bimestre não reutiliza a semântica corrente da TASK 190. Para 2025 anual, o numerador canônico é a despesa **empenhada** do 6º bimestre. Para o período corrente de 2026, FIN_Q1 permanece usando a despesa **liquidada até o bimestre**.

Portanto:

```text
2025 gasto anual empenhado / 2025 matrículas
= 463.766.660,32 / 22.788
= R$ 20.351,35 por matrícula
```

## Semântica do indicador

O resultado é **despesa anual total com Educação empenhada por matrícula do Censo Escolar**, não “custo individual do aluno”. O denominador é contagem censitária de matrículas e a linha 33 do RREO é um agregado municipal de Educação; ela não atribui gasto a cada escola ou estudante.

## Materialização

A tarefa acrescenta:

1. um registro `BASIC_EDUCATION_ENROLLMENT` de rede em 2025 ao `SCHOOL_INDICATOR_SERIES`;
2. um registro anual `EDUCATION_EXPENDITURE` de 2025 ao `FISCAL_SERIES`, com `stage_semantic=COMMITTED_FINAL_BIMESTER`;
3. uma derivação auditável `EDUCATION_SPENDING_PER_ENROLLMENT` com compatibilidade de exercício exigida.

A TASK 190 continua fornecendo os três estágios parciais de 2026 e FIN_Q1 não muda.

## Limites

- `PER_ENROLLMENT != INDIVIDUAL_STUDENT_COST`;
- `NOMINAL != REAL`;
- o agregado RREO não é gasto por escola;
- o digest do fixture sanitizado não é apresentado como hash do PDF-fonte;
- FIN_Q4 continua parcial enquanto não houver série real deflacionada por índice oficial.

## Efeito esperado na matriz

O primeiro CI fail-closed revelou um ganho colateral correto: a mesma matrícula também é um dos três sinais de `NETWORK_Q1 — Quantos alunos, turmas e escolas existem?`. Como `CLASS_COUNT` e `SCHOOL_COUNT` continuam ausentes, essa pergunta sobe apenas de gap para parcial.

Mudanças semânticas após a TASK 190:

- `FIN_Q2: MATERIALIZED_PARTIAL -> MATERIALIZED_ANSWERABLE`;
- `NETWORK_Q1: EXPLICIT_GAP -> MATERIALIZED_PARTIAL`.

Contagens esperadas:

- 26 `MATERIALIZED_ANSWERABLE`;
- 10 `MATERIALIZED_PARTIAL`;
- 2 `EXPLICIT_GAP`.

Essa correção foi descoberta pelo CI repository-wide; o gate não foi afrouxado.

# Runbook de observabilidade 0.6.3

## Objetivo

Dar ao operador uma resposta curta para quatro perguntas: a execução passou, qual fonte participou, quais checks passaram e o log append-only foi criado?

## Saídas

O bundle contém:

- `report.md`: leitura humana;
- `report.json`: contrato completo;
- `cards/run.json`: cartão da execução;
- `cards/source.json`: cartão das fontes;
- `cards/metrics.json`: métricas operacionais.

## Onde visualizar no GitHub

1. Abra o repositório.
2. Entre em **Actions**.
3. Abra **ROBO DADOS PUBLICOS** e a execução mais recente.
4. Na página **Summary**, leia o relatório apresentado abaixo dos jobs.
5. Ao final da página, em **Artifacts**, baixe `observability-report-<run_id>` se precisar dos JSONs.

## Interpretação

- `HEALTHY`: gate concluído e contrato de privacidade aprovado;
- `ATTENTION`: status conhecido, mas não conclusivo;
- `NOT_CONFIGURED`: componente deliberadamente não habilitado nesta execução;
- `STOPPED`: falha/STOP operacional ou contrato de privacidade inseguro.

`NOT_CONFIGURED` não significa falha. No workflow de infraestrutura da 0.6.3, a coleta de fontes permanece deliberadamente desabilitada.

## Limites

O relatório não é um dashboard histórico, não consulta o Drive, não substitui os logs de auditoria e não revela IDs remotos. Histórico, tendências e interface interativa pertencem à etapa 0.7.0.

# F02 — série mensal de caixa/saldos FUNDEB — 0.8.0

## Natureza

Os PDFs `FUNDEB_LIMEIRA_2026_01/02/03.pdf` são demonstrativos mensais de recursos do FUNDEB. Eles não têm o mesmo schema do relatório local `APLICACAO COM RECURSOS DO FUNDEB` usado em abril/maio.

Por isso este subtipo é tratado separadamente como `FUNDEB_MONTHLY_CASH_LOCAL`.

## O que pode ser extraído

- saldo inicial;
- transferências FUNDEB;
- rendimentos financeiros explicitamente rotulados;
- entrada FTI/Fomento Tempo Integral explicitamente rotulada;
- total de entradas;
- total de saídas;
- saldo final;
- contas explicitamente rotuladas ETI no saldo inicial/final.

## O que NÃO pode ser inferido

Saldo ETI, conta ETI ou entrada FTI **não é gasto EITI**. Este adapter não produz empenhado, liquidado ou pago de EITI e não autoriza conclusão de MDE/FUNDEB compliance.

## Invariantes

Por mês:
`saldo_inicial + entradas - saídas = saldo_final`.

Na série:
- fechamento de um mês = abertura do mês seguinte;
- quando ambos os lados possuem rótulo ETI explícito, fechamento ETI anterior = abertura ETI seguinte.

O resultado offline não persiste nada. A persistência Silver é um efeito create-only separado após merge/CI/DeepSeek.

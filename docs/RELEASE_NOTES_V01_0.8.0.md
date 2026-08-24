# Release Notes — 0.8.0 CANDIDATE

## M7 — expansão controlada de fontes

A 0.8.0 candidata introduz um contrato explícito para expansão de fontes sem transformar descoberta em autorização operacional.

### Fonte-piloto

- instituição: FNDE;
- sistema: SIOPE;
- superfície pública: `Dados Informados pelos Municípios`;
- município: Limeira/SP;
- código municipal de referência: `352690`;
- exercício piloto proposto: 2024, fechado;
- temas iniciais: receitas, despesas, MDE e Fundeb.

A superfície pública e a descrição institucional do SIOPE foram verificadas em 24/08/2026. O FNDE descreve acesso cidadão aos dados de receitas e despesas em educação sem necessidade de senha. Esta evidência não é tratada como prova de um endpoint/export estável.

### Ciclo de vida

`DISCOVERED → CONTRACT_VALIDATED → ONE_TIME_AUTHORIZED → LIVE_VALIDATED → RECURRENCE_ELIGIBLE`

O piloto está em `CONTRACT_VALIDATED`. Nesta candidata:

- rota de aquisição: `UNPROVEN`;
- content-type: `UNPROVEN`;
- schema: `UNPROVEN`;
- coleta: `PROHIBITED`;
- processamento: `PROHIBITED`;
- recorrência: `PROHIBITED`;
- schedule: `DISABLED`.

`RECURRENCE_ELIGIBLE` é somente uma qualificação técnica futura e nunca liga agenda automaticamente.

### Gate offline

O script `scripts/github_source_expansion_design_gate.py` valida o contrato sem rede e sem escrita remota. O arquivo canônico é `config/source_expansion.siope_limeira_0_8_0.json`.

O gate exige que a candidata pare em `CONTRACT_VALIDATED`. Uma tentativa de marcar a fonte como `ONE_TIME_AUTHORIZED` sem rota, schema e content-type comprovados falha fechada.

### Próximo gate

`M7_SIOPE_LIMEIRA_ROUTE_DISCOVERY_GATE_0_8_0`.

Esse próximo gate deverá provar, sem adivinhar URLs:

1. a rota oficial de aquisição/exportação;
2. o content-type esperado;
3. o schema e as unidades;
4. a semântica de nulos e zeros;
5. o crosswalk financeiro para receitas/despesas/MDE/Fundeb;
6. um contrato imutável para exatamente um exercício fechado;
7. manutenção de recorrência e schedule desabilitados.

A existência deste desenho não autoriza coleta real.

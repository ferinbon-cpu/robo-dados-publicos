# TASK 174 — broaden JOM event taxonomy across normative, fiscal and school-operation layers

## Objective

Expand the Jornal Oficial from an 11-type administrative event parser into a broader municipal event radar while preserving conservative, fixture-driven recognition.

The task serves the GENERAL_MUNICIPAL_PUBLIC_DATA_OBSERVATORY. It is not education-only and not EITI-specific.

## Event taxonomy

Legacy event types remain supported:

- CONTRATO;
- TERMO_ADITIVO_CONTRATO;
- APOSTILAMENTO;
- ATA_REGISTRO_PRECOS;
- CONVENIO;
- DECRETO;
- PORTARIA;
- LEI;
- RESOLUCAO;
- EDITAL;
- AVISO_LICITACAO.

New fixture-proven types:

- COMUNICADO;
- PARECER;
- INSTRUCAO_NORMATIVA;
- DELIBERACAO;
- RETIFICACAO;
- TERMO_COLABORACAO;
- TERMO_FOMENTO;
- ACORDO_COOPERACAO;
- ATO_CREDITO_ORCAMENTARIO;
- AVISO_OPERACAO_ESCOLAR.

## Conservative recognition rules

Ordinary prose is not promoted.

COMUNICADO, PARECER, INSTRUCAO_NORMATIVA and DELIBERACAO require explicit numbered headings.

RETIFICACAO requires an explicit target act type and number in the heading. The parser emits `target_act_type` and `target_act_number`; nearby acts are never inherited as the target.

ATO_CREDITO_ORCAMENTARIO requires an explicit credit heading. It does not reinterpret every Decreto that mentions budget language as a different document type; ordinary Decreto remains Decreto and is semantically classified separately.

AVISO_OPERACAO_ESCOLAR requires an explicit AVISO DE/SOBRE heading for matrícula, calendário escolar, atribuição, transporte, alimentação or funcionamento escolar.

## Semantic integration

The existing TASK 171 semantic classifier remains the second dimension. Event type, policy domain, evidence layer, financial stage and education topic remain independent.

New event-type hints include:

- INSTRUCAO_NORMATIVA -> NORMATIVE;
- DELIBERACAO -> NORMATIVE + GOVERNANCE;
- PARECER / COMUNICADO / RETIFICACAO / collaboration instruments -> GOVERNANCE;
- ATO_CREDITO_ORCAMENTARIO -> BUDGET_AUTHORIZATION;
- AVISO_OPERACAO_ESCOLAR -> SCHOOL_OR_SERVICE_OPERATION.

School-operation topics now separately include enrollment, calendar, class assignment, unit operation, hours/shift and infrastructure maintenance.

## Accounting integration

TASK 173 already causes every normal JOM event to emit an `accounting_query_tasks.jsonl` query candidate. New TASK 174 events automatically enter the same router.

This does not make semantic or textual matches into accounting identity.

## Guards

- event type != policy domain != evidence layer != financial stage;
- RETIFICACAO != target identity unless target is explicit;
- budget credit act proves authorization/change only, never commitment/liquidation/payment;
- school-operation notice proves publication only, not implementation or result;
- collaboration/fomento instruments are governance/partnership events, not procurement merely by type;
- unknown prose remains Silver/RAG text only;
- semantic similarity, amount and chronology never create accounting identity.

## Remote effects

T0/offline only:

- network 0;
- Drive read/write 0;
- serving/publication 0;
- schedule/recurrence 0.

## Next product step

After TASK 174, materialize a unified observatory query layer that can answer user questions across:

JOM events + semantic facets + accounting query tasks + TCE accounting ledger + SICONFI/SIOPE/FUNDEB + existing school indicators.

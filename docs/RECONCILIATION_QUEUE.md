# M4E.4 — Fila de reconciliação municipal

## Objetivo

Transformar eventos detectados no Jornal Oficial em **tarefas persistentes de busca e reconciliação**, sem promover automaticamente correspondência ou identidade financeira.

O fluxo desta candidate é:

```text
Jornal Oficial → evento Gold → planner determinístico → fila SQLite/JSONL
                                                ↓
                            contratos / TCE / TDA / licitações / SIAVE
```

A fila é o primeiro mecanismo explícito de **próxima ação** do agente. Ela não executa buscas externas nesta release; ela decide quais buscas são permitidas e quais chaves devem ser usadas.

## Alvos iniciais

### LIMEIRA_CONTRATOS

Cadastro municipal público de contratos, convênios, atas e locações. A interface pública apresenta pesquisa por ano, número do contrato/documento, tipo, objeto e fornecedor.

### TCE_SP_DESPESAS

Painel do TCESP usado como fonte de controle externo. O painel atual de Limeira oferece despesas detalhadas, consulta por fornecedor e histórico de eventos de despesa (empenhado, liquidado, pago, reforço e anulação).

**Cautela temporal:** a página pública de APIs do TCESP documenta explicitamente a API de receitas/despesas para 2014–2019. A 0.5.4 não presume que esse contrato de API cubra 2020+; para anos recentes, um adaptador deverá validar a superfície atual ou os arquivos em lote.

### TDA_LIMEIRA

Alvo financeiro municipal prioritário. Enquanto o endpoint/export público estável não for comprovado, tarefas são persistidas com status `BLOCKED_CONNECTOR_DISCOVERY`.

### LIMEIRA_LICITACOES

Alvo documental para edital, processo, atas, comunicados e anexos de contratação.

### SIAVE_LIMEIRA

Alvo para atos normativos/legislativos e tramitação quando o Jornal Oficial detecta lei, decreto, resolução ou portaria. Uma publicação executiva não é automaticamente equivalente a uma proposição legislativa.

## Regra de identidade

Nenhuma tarefa significa que dois registros são a mesma coisa.

- nome de fornecedor isolado = pista;
- objeto semelhante = pista;
- valor semelhante = pista;
- número de contrato + ano + CNPJ/processo = evidência mais forte;
- execução financeira exige estágio explícito e identidade contábil compatível;
- promoção de vínculo continua sujeita aos gates V16/V17.

## Status da fila

- `READY_SEARCH`: há chaves mínimas e a superfície-alvo já pode entrar em fase de adaptador;
- `BLOCKED_CONNECTOR_DISCOVERY`: a busca é conceitualmente válida, mas o contrato técnico do alvo ainda não foi provado;
- estados de resultado como `MATCH_CANDIDATE` só podem ser gravados por um resolver posterior, junto com a evidência coletada.

## Idempotência

`task_id` é derivado deterministicamente de evento, alvo, tipo de tarefa e chaves. Reprocessar a mesma edição não duplica a fila SQLite.

## Comandos

Planejar novamente a partir dos eventos Gold:

```bash
python3 main.py reconciliation-plan \
  --events-jsonl runtime/jornal_7309/events_gold.jsonl \
  --out runtime/jornal_7309/reconciliation_tasks.jsonl \
  --state-db runtime/robot_state.sqlite
```

Consultar a fila persistente:

```bash
python3 main.py reconciliation-status --state-db runtime/robot_state.sqlite
```

Somente tarefas bloqueadas por descoberta de conector:

```bash
python3 main.py reconciliation-status \
  --state-db runtime/robot_state.sqlite \
  --filter-status BLOCKED_CONNECTOR_DISCOVERY
```


## M4E.5 — resolvers implementados

`TCE_SP_DESPESAS` passa a ter resolução temporalmente bifurcada: 2014–2019 pela API oficial documentada; 2020+ por descoberta do link `Despesa Detalhada` na página do município/ano e validação estrita do ZIP/CSV. `LIMEIRA_CONTRATOS` passa a ter resolver adaptativo de formulário, que não submete quando o contrato de campos não puder ser inferido de forma inequívoca.

A fila persiste o resultado, mas `MATCH_CANDIDATE` não equivale a identidade. O vínculo contrato → empenho/liquidação/pagamento permanece submetido aos gates V16/V17.

## M4E.6 — primeira execução controlada candidata 0.6.2

O primeiro gate ao vivo foi tentado e parou com segurança diante de uma tarefa sem número de contrato nem fornecedor, sem gravar estado ou log. O contrato corrigido permite somente:

- uma tarefa `READY_SEARCH` de `LIMEIRA_CONTRATOS` com número de contrato ou fornecedor;
- preservação e salto das tarefas incompletas, sem chamada de rede;
- seleção determinística por prioridade decrescente e `task_id` crescente entre elegíveis;
- execução exatamente do `task_id` selecionado;
- resultado `MATCH_CANDIDATE` ou `NO_MATCH`;
- evidência documental `CANDIDATE_ONLY` quando houver correspondência;
- substituição do estado e log append-only após PASS integral.

TCE-SP, TDA, licitações e SIAVE ficam protegidos contra alteração. Qualquer falha operacional ou violação de escopo retorna STOP sem substituir o estado remoto e sem criar log. Não há recorrência, agendamento ou promoção automática de identidade financeira.

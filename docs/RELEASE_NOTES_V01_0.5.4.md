# SOFTWARE V01 0.5.4 — CANDIDATE

**Marco:** M4E.4 — fila persistente de reconciliação municipal  
**Release ativa de produção preservada:** 0.4.0

## Avanço substantivo

A 0.5.4 transforma eventos estruturados do Jornal Oficial em uma fila determinística de próximas ações. É o primeiro componente em que o software não apenas coleta/estrutura uma fonte, mas também decide **qual fonte pública deve ser consultada em seguida** e com quais chaves.

## Novos alvos de reconciliação

- `LIMEIRA_CONTRATOS` — cadastro municipal de contratos/convênios/atas/locações;
- `TCE_SP_DESPESAS` — controle externo de despesas e fornecedor;
- `TDA_LIMEIRA` — execução financeira municipal, mantido bloqueado até descoberta do contrato técnico;
- `LIMEIRA_LICITACOES` — documentação de contratação;
- `SIAVE_LIMEIRA` — atos normativos/legislativos e tramitação.

## Segurança epistemológica

A fila **não cria vínculos automaticamente**. Cada tarefa carrega:

- chaves de busca;
- pistas auxiliares;
- prioridade;
- regra de identidade;
- confiança mínima exigida para eventual promoção de vínculo;
- status do conector.

Nome, objeto ou valor isolado nunca são tratados como identidade financeira.

## Persistência

A tabela SQLite `reconciliation_tasks` é criada de forma retrocompatível pelo `StateRegistry`. `task_id` é determinístico, portanto reprocessar a mesma edição não duplica a fila.

## Comandos novos

```bash
python3 main.py reconciliation-plan --events-jsonl <events_gold.jsonl> --out <tasks.jsonl> --state-db <state.sqlite>
python3 main.py reconciliation-status --state-db <state.sqlite>
```

O comando `journal-process` passa a gerar `reconciliation_tasks.jsonl` por padrão. Use `--no-plan-reconciliation` somente para testes isolados.

## Gate temporal do TCE-SP

A documentação pública da API de despesas/receitas do TCESP especifica cobertura 2014–2019. A 0.5.4 não extrapola esse contrato para anos recentes. O resolver 2020+ exigirá validação própria da superfície atual ou dos arquivos em lote.

## Próximo passo

M4E.5: implementar o primeiro **resolver real** da fila, priorizando `LIMEIRA_CONTRATOS` e um adaptador de reconciliação `TCE_SP_DESPESAS`, mantendo TDA bloqueado até o probe live.

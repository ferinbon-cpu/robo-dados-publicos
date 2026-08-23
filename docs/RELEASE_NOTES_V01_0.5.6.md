# SOFTWARE V01 0.5.6 CANDIDATE — M4E.6 evidence ledger

## Avanço
A execução dos resolvers passa a produzir uma camada persistente de evidências de reconciliação, separada do status da tarefa.

- nova tabela SQLite `reconciliation_evidence`;
- IDs determinísticos e idempotentes por evidência;
- candidatos do cadastro municipal viram `documentary_correspondence_candidate`;
- registros TCE-SP viram `supplier_expense_candidate`;
- nenhuma aresta gerada automaticamente pode ser `financial_identity`;
- matches por CNPJ/fornecedor continuam candidatos até aplicação explícita dos gates V16/V17;
- executor grava as evidências juntamente com o resultado do resolver.

## Regra central
Aresta documental A não equivale a execução financeira A. A promoção para identidade financeira continua proibida nesta camada.

## Gate
Candidate; 0.4.0 continua release ativa até live validation.

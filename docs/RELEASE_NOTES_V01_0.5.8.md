# SOFTWARE V01 0.5.8 CANDIDATE — M4E live validation hardening

## Resultado do gate ao vivo

- Jornal Oficial: índice oficial de agosto de 2026 retornou 12 edições declaradas; a edição 7310 respondeu como `application/pdf` e foi processada com 76 páginas, 53 eventos Gold e 68 tarefas de reconciliação.
- Cadastro municipal de contratos: o resolver passou a provar os pares ScriptCase campo/autocomplete, preservar cookies, seguir somente o relay automático explícito e interpretar a grade externa mesmo com tabelas aninhadas. A chave pública `51/2025` retornou dois registros `MATCH_CANDIDATE`.
- TCE-SP: o dataset de 2026 foi descoberto a partir do painel municipal, validado como ZIP/CSV e interpretado com os aliases correntes `tp_despesa` e `identificador_despesa`.
- Ledger: uma correspondência positiva controlada gerou uma única aresta `supplier_expense_candidate`, com status `CANDIDATE_ONLY` e promoção para `financial_identity` explicitamente proibida.
- TDA Limeira: a rota pública preservada literalmente redirecionou para logout/início e não expôs endpoint ou export público comprovável. O conector permanece bloqueado.

## Correções

- reconhecimento fail-closed de pares ScriptCase somente quando o JavaScript comprova a cópia para o campo canônico;
- persistência isolada de cookies entre landing, busca e relay;
- seguimento de relay apenas quando há formulário POST oculto, explícito e de mesma origem;
- proibição de fallback para busca ampla por objeto quando faltam contrato e fornecedor;
- parser de tabela com pilha para preservar linhas externas de grades HTML aninhadas;
- aliases do schema corrente do TCE-SP;
- sanitização de URL sem reescrever queries públicas sem valor, como `?418`.

## Estado

A 0.5.8 permanece `CANDIDATE`. A release ativa validada continua sendo 0.4.0. A promoção exige revisão humana; o gate GitHub ao vivo permanece pendente.

Evidência detalhada: `docs/M4E_LIVE_VALIDATION_EVIDENCE_2026-08-22.md`.

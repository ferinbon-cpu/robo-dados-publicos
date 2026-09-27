# SOFTWARE V01 0.5.7 CANDIDATE — M4E.6 release identity hardening

## Correção

A auditoria da 0.5.6 identificou que o pacote e os manifestos correntes declaravam 0.5.6, enquanto o executor remoto, o estado SQLite, os logs, agentes HTTP, o README e parte da configuração ainda declaravam 0.5.5.

A 0.5.7:

- centraliza versão ativa, candidate, método, próxima ação e agentes HTTP em `robo_dados_publicos/release.py`;
- faz o executor remoto e a CLI persistirem a candidate corrente sem literais duplicados;
- sincroniza README, índice de releases, manifestos, QA e configuração de reconciliação;
- amplia o teste de consistência para cobrir metadados correntes e agentes HTTP;
- exige pacote de distribuição sem `__pycache__` e arquivos `.pyc`.

## Estado funcional preservado

- registro persistente `reconciliation_evidence`;
- evidências determinísticas e idempotentes;
- correspondências documentais e de fornecedor permanecem candidatas;
- promoção automática para `financial_identity` continua proibida;
- release ativa validada continua sendo 0.4.0.

## Gate

`M4E_LIVE_VALIDATION`: validar ao vivo Jornal Oficial, cadastro municipal de contratos e TCE-SP, capturando rota, status HTTP, content-type, schema e evidências sem promover identidade financeira automaticamente.

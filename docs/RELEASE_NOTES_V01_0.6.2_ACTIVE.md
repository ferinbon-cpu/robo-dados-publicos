# SOFTWARE V01 0.6.2 ACTIVE — M4E primeira reconciliação promovida

## Promoção

A candidata 0.6.2 foi promovida após a execução manual nº 8 concluir com `PASS_GITHUB_RECONCILIATION_EXECUTION_GATE`. A evidência candidata permanece em `release_manifest_v01_0.6.2.json`; a identidade ativa está em `release_manifest_v01_0.6.2_active.json`.

## Evidência validada

- commit de origem: `bca696c4792fe8e6a87be716b26855f450c22459`;
- duração: 33 segundos;
- exatamente uma tarefa elegível de `LIMEIRA_CONTRATOS` executada;
- resultado `MATCH_CANDIDATE`;
- uma aresta de evidência `CANDIDATE_ONLY`;
- zero relações `financial_identity`;
- alvos protegidos inalterados;
- estado remoto substituído e log append-only criado;
- nenhum secret, ID remoto, identificador de tarefa ou payload candidato exposto.

## Fechamento operacional

O input `confirm_reconciliation` e a chamada de `scripts/github_reconciliation_gate.py` foram removidos do workflow ativo. Também permanecem ausentes os caminhos de repetição da coleta e do processamento da edição 7310.

## Limites preservados

- `MATCH_CANDIDATE` não é identidade jurídica/financeira;
- promoção automática de `financial_identity` permanece proibida;
- TDA continua bloqueado sem endpoint/export público comprovado;
- TCE-SP, licitações e SIAVE não foram autorizados neste gate;
- reconciliação ampla, recorrência e agendamento permanecem desabilitados.

## Próxima decisão

Revisar a evidência candidata privada e definir, em contrato separado, se haverá novo gate. A promoção da 0.6.2 não autoriza nenhuma execução adicional.

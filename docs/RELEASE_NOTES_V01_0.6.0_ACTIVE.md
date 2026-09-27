# SOFTWARE V01 0.6.0 ACTIVE — M4E primeira coleta controlada

## Promoção

A candidata 0.6.0 foi promovida após autorização do usuário e conclusão do workflow manual `M4E source gate 0.6.0 by @ferinbon-cpu #3`. O gate retornou `PASS_GITHUB_SOURCE_COLLECTION_GATE`, com 16/16 verificações aprovadas.

## Evidência principal

- uma única fonte habilitada: Jornal Oficial de Limeira, edição 7310;
- `DOWNLOADED_NEW` em Bronze;
- HTTP 200 e `application/pdf`;
- 16.952.899 bytes;
- SHA-256 `78a23262023f6233cb59fdc78f1fadc196d0a7bbd52c418bbdd9244229f46680`;
- estado remoto substituído;
- log append-only criado;
- nenhum segredo exposto.

Evidência detalhada: `docs/M4E_FIRST_SOURCE_COLLECTION_EVIDENCE_2026-08-24.md`.

## Segurança preservada

- a candidata original permanece em `release_manifest_v01_0.6.0.json`;
- a opção de repetir a coleta da edição 7310 foi retirada do workflow;
- agenda e coleta recorrente permanecem desabilitadas;
- TDA continua bloqueado;
- `MATCH_CANDIDATE` continua sem promoção automática para identidade financeira.

## Próxima etapa

`M4E_FIRST_SOURCE_PROCESSING_GATE`: processar o PDF já armazenado em Bronze e validar os derivados Silver/Gold/RAG, sem baixar novamente o documento.

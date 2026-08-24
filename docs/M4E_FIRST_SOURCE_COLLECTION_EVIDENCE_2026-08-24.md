# M4E — evidência da primeira coleta controlada — 2026-08-24

## Resultado

O workflow manual `M4E source gate 0.6.0 by @ferinbon-cpu #3`, na branch `main` e no commit `9b7da0c07f5aaa981d751246508871dd182e6546`, concluiu com sucesso. O gate retornou `PASS_GITHUB_SOURCE_COLLECTION_GATE` e todas as 16 verificações foram verdadeiras.

## Artefato coletado

- fonte: `LIMEIRA_JORNAL_OFICIAL_EDICAO_7310`;
- situação: `DOWNLOADED_NEW`;
- HTTP: `200`;
- tipo: `application/pdf`;
- tamanho: `16.952.899` bytes;
- SHA-256: `78a23262023f6233cb59fdc78f1fadc196d0a7bbd52c418bbdd9244229f46680`;
- criação em Bronze: `PASS`;
- identificadores internos do Drive: preservados somente no log privado de auditoria.

## Persistência e auditoria

- estado remoto: `REPLACED`;
- origem do estado: `REMOTE_EXISTING`;
- log append-only: `CREATED`;
- identificadores e metadados internos do log: preservados somente no Drive privado;
- segredos expostos: `false`.

## Decisão de promoção

A 0.6.0 pode ser promovida a `ACTIVE` porque o artefato observado correspondeu exatamente ao contrato imutável, foi criado em Bronze, atualizou o estado remoto e gerou log append-only sem revelar credenciais. A candidata 0.6.0 permanece preservada separadamente.

A promoção não habilita agenda, coleta recorrente, TDA nem promoção automática de identidade financeira. A opção de repetir a coleta da edição 7310 é removida do workflow ativo.

## Próximo gate

`M4E_FIRST_SOURCE_PROCESSING_GATE`: processar de modo controlado o PDF já preservado em Bronze e validar os derivados Silver/Gold/RAG sem nova aquisição de rede.

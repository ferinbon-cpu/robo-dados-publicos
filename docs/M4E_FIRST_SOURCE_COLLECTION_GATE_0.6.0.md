# M4E — primeiro gate de coleta — 0.6.0

## Escopo fechado

Este gate baixa apenas a edição 7310 do Jornal Oficial, confirma seu contrato imutável e grava o original em `01_BRONZE`. Ele não processa automaticamente Silver/Gold/RAG, não executa reconciliação e não ativa agenda.

## Execução no GitHub

1. Abrir o repositório `ferinbon-cpu/robo-dados-publicos`.
2. Selecionar **Actions**.
3. Na coluna esquerda, selecionar **ROBO DADOS PUBLICOS**.
4. Clicar **Run workflow**.
5. Manter a branch `main`.
6. Marcar `confirm_persistence`.
7. Marcar `confirm_source_collection`.
8. Clicar o botão verde **Run workflow**.

## Critérios de PASS

- versão `0.6.0`, status `CANDIDATE`;
- preflight sem falhas;
- 92/92 testes e 109/109 regressões;
- `mode: SOURCE_COLLECTION_ENABLED`;
- `source_collection.status: PASS`;
- resultado `DOWNLOADED_NEW` para a fonte esperada;
- tipo `application/pdf`, 16.952.899 bytes e SHA-256 esperado;
- `remote_id` do novo Bronze presente;
- estado remoto substituído e novo log append-only criado;
- resultado final `PASS_GITHUB_SOURCE_COLLECTION_GATE`.

## STOP esperado

Qualquer divergência de tipo, hash ou tamanho envia o payload observado à quarentena e impede promoção. Ausência de uma das confirmações impede a coleta.

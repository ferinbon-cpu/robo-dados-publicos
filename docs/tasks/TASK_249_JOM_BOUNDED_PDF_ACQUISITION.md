# TASK 249 — aquisição bounded dos PDFs JOM 7321–7324

## Objetivo

Executar a primeira prova documental live sobre as quatro identidades descobertas pela TASK247 e canonizadas/fila pela TASK248. A TASK249 baixa exatamente os PDFs das edições 7321–7324, valida integridade estrutural e produz somente metadados sanitizados.

## Base canônica

- `main` de partida: `dc672da310bb60973f7894ed91566f908d8bfa25`;
- issue: `#830`;
- fila de entrada: `config/task248_jom_bounded_ingestion_queue.v1.json`;
- edições exatas: `7321`, `7322`, `7323`, `7324`;
- host documental permitido: `ecrie.com.br`.

## Fronteira operacional

A implementação live aceita no máximo quatro GETs, um por URL pinada na fila. São proibidos:

- redirect;
- retry;
- descoberta de URL alternativa;
- download de qualquer quinta identidade;
- persistência de PDF bruto;
- escrita no Drive;
- Bronze/Silver/Gold;
- OCR ou parser semântico;
- serving/publicação/promoção;
- schedule/recorrência.

Cada resposta precisa comprovar HTTP 200, URL final idêntica à solicitada, tipo de conteúdo PDF ou octet-stream, assinatura `%PDF-`, tamanho positivo dentro do budget, SHA-256 consistente e contagem de páginas parseável e positiva.

## Persistência

Os quatro PDFs existem apenas dentro de `TemporaryDirectory` no runner. O único artefato persistido é `task249_sanitized_pdf_acquisition_result.json`, com retenção de 1 dia. O workflow verifica que `runtime_out` contém exatamente esse JSON e nenhum `.pdf`.

## Autorização

A implementação não contém autorização live permanente. O runtime exige `runtime/task249_owner_authorization.json` vinculado ao SHA exato da implementação mesclada em `main`, com escopo `[7321, 7322, 7323, 7324]`, uma tentativa e todos os efeitos downstream `false`.

O runtime branch só pode divergir do SHA de implementação por:

- `runtime/task249_owner_authorization.json`;
- `runtime_triggers/task249_jom_bounded_pdf_acquisition.run`.

## Resultado esperado

Sucesso: `PASS_TASK249_BOUNDED_PDF_ACQUISITION`.

O resultado sanitizado contém, para cada edição: data, source_id, logical_key, URL, content-type, bytes, SHA-256 e páginas. Falha em qualquer documento encerra a tentativa sem retry e sem efeitos downstream.

## Próximo gate

Mesmo em caso de sucesso live, custódia no Drive, extração de texto, classificação, Bronze/Silver/Gold e recorrência permanecem tarefas separadas. O primeiro passo após o live é canonizar o resultado TASK249.

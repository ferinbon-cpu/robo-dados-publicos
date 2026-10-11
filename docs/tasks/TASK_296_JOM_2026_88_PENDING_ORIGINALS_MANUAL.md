# TASK296 — Aquisição manual e auditável de 88 originais JOM (LOA Limeira 2027)

Estado em 2026-10-11: **DESIGN/IMPLEMENTATION IN PR; ZERO LIVE DOWNLOADS THIS TASK.**
Base de trabalho: `main` `f06df9e1266161a2d7d06fbb0025a9e0c1d40236`.

## Proveniência e contagens

- Drive SME, aba `INVENTARIO_113`: 113 identidades indexadas (104 já custodiadas e 9 janeiro sem original).
- Drive SME, aba `URLS_PENDENTES_FEV_OUT_V58`: outras 79 posições numéricas candidatas (links oficiais fornecidos manualmente pelo usuário).
- A lista materializada em `config/jom_2026_88_pending_urls_v1.json` contém **88 URLs HTTPS eCrie distintas**, uma por posição ausente, e exclui as 104 custodiadas.
- **192 posições numéricas distintas de 7151 a 7342 não significam 192 identidades já validadas.** Há anomalia no índice de setembro: 7237/7238 em posição onde a sequência numérica sugere 7327/7328. O registro e a capa são provas distintas.
- Janeiro P01 = 7152–7160, nove URLs, nove datas indexadas. Demais registros têm `expected_date: null`, pois o timestamp do arquivo não comprova a data oficial.

## Contrato de aquisição proposto

Gate `TASK296_JOM_2026_88_PENDING_PDFS_MANUAL`, T2 manual only, bloqueado por padrão.

- Workflow `.github/workflows/task296-jom-2026-88-pdfs-manual.yml`, sem push, schedule, pull_request, workflow_run ou execução automática.
- `workflow_dispatch` requer escolher **um** de P01 a P10 e assinalar `autorizar_lote=true`. `main` protegido, tentativa 1, SHA do checkout, permissões `contents: read`.
- P01–P09: nove URLs exatas; P10: sete URLs. Nenhuma busca, paginação, resolução de links, segundo domínio, redirect ou retry.
- Pré-validação offline do universo completo, cardinalidade 88, URLs estritamente HTTPS eCrie, nomes pinados de 14 dígitos, ausência de edições duplicadas, range de edições exatamente delimitado, sem credenciais.
- Orçamento por PDF 200 MiB, por lote 500 MiB incluindo bytes transferidos em falhas, timeout 35 segundos por solicitação, sem retry.
- Corpo PDF validado por assinatura `%PDF-`, mime, Content-Length, pypdf, contagem de páginas e localização do número da edição nas duas primeiras páginas (método estabelecido na TASK292A).
- Se a capa divergir da edição candidata, **STOP para aquele PDF**: jamais promover um número com base apenas no timestamp do nome de arquivo.
- `manifest.json` auditável registra sucessos e falhas por item, hash SHA-256, bytes, páginas, URL, edição candidata, `get_attempts`, zero escrituras Drive e flags de ausência de custódia. O lote parcial pode ser anexado para diagnóstico, mas **não recebe PASS completo**.
- Artefato GitHub expira em 7 dias. É uma ponte para custódia Bronze, não uma evidência de Bronze definitiva.
- Não autoriza a transferência ao Drive, que requer gate T2 create-only separado, collision preflight e re-download/hash.
- A comprovação da data precisa de inspeção independente da capa, mesmo quando a edição numericamente bate.

## Gate de implementação versus operação

Esta PR somente instala o contrato e o código testável. Não constitui aprovação de aquisição: a política `future_batch_execution_authorized=false` permanece. Antes do primeiro run é necessário merge após revisão da CI e clique consciente do proprietário no `workflow_dispatch` para o P01. Não rodar os 10 lotes automaticamente. Nenhuma publicação fiscal ou interpretação legal decorre de recolher o JOM.

Testes offline em `tests/test_jom_2026_pending_manual.py` incluem drift de edição/URL, duplicidade, contexto manual, fake transport, erro MIME, redirect, parcial sem retries e orçamento declarado. Testes/CI no GitHub devem ser observados antes de afirmar PASS.

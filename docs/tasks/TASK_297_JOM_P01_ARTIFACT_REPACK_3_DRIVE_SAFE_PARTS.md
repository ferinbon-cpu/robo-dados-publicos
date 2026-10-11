# TASK297 — reempacotar artefato P01 validado em partes compatíveis com Drive

## Fonte preservada
- TASK296 run 38184075627, artifact 11719320676 (`task296-jom-P01-originais-manifesto`).
- `main` de origem `5869fbdfb803e06737696e4f487b814cea663bc3`.
- 9 originais P01 (7152–7160); SHA, páginas e datas de capa conferidos no GitHub e independentemente no container ChatGPT.
- ZIP do GitHub 191711503 bytes, SHA-256 `9f6adcc4cda2d32a646af672487f08c1eb147b71ae0815afd87d248f74beadfb`.
- Limite do conector Google Drive `upload_file`: 104857600 bytes por arquivo, por isso o original de 191711503 bytes não pode ser transferido diretamente.
- O problema de transporte **não invalida** os nove originais nem o manifesto.

## Desenho do repack

Workflow estritamente manual `.github/workflows/task297-p01-existing-artifact-repack.yml`, confirmação por owner, `main`, tentativa 1, Actions read + contents read. Obtém uma vez somente o artifact anterior, via `gh run download`; nenhum GET externo eCrie, nem Drive, nem retry.

Antes de qualquer saída, confere 9 registros, fonte run/SHA, cada hash SHA-256, tamanho, PDF/capa/número/páginas. Depois cria três ZIPs reconstituíveis, cada um abaixo de 95 MiB:
1. `TASK297_P01_EIGHT_ORIGINALS.zip`: oito PDFs exatos (7152–7158 e 7160) + manifesto TASK296.
2. `TASK297_P01_JOM7159_PART01.zip`: primeiros 70 MiB originais do JOM 7159 + manifesto do segmento.
3. `TASK297_P01_JOM7159_PART02.zip`: restante do JOM 7159 + manifesto do segmento.

Juntar binariamente os bytes dos segmentos 01 + 02 recupera o PDF 7159 bit a bit, devendo resultar no SHA-256 primário `935cd1b1ffe4a12f660cff9359a7eda276dbeed2f8bc97088efcabf87d1b091b`. A assinatura de cada segmento também é calculada. Quarto artefato é apenas o QA JSON minúsculo.

## Gate

Artefatos GitHub têm retenção 7 dias, não custódia permanente. Transferência para Drive SME necessita preflight collision/create-only e readback/hash e execução separada; somente então atualizar H na matriz INVENTARIO_113. Nenhum apagamento/overwrite nem marcação de CUSTODIADO antes da prova.

Validação de implementação por CI/PR e teste `tests/test_task297_jom_p01_repack.py`. Bloquear auto-merge/auto-run. O owner precisa aprovar qualquer workflow_dispatch.

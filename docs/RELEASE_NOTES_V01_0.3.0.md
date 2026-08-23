# ROBO_DADOS_PUBLICOS SOFTWARE V01 — 0.3.0

## Marco
Primeira release preparada para acesso nativo ao Google Drive a partir de um ambiente Cloud Shell já autenticado com `gcloud auth login --enable-gdrive-access`.

## Novidades
- `GcloudTokenProvider`: usa a conta ativa do `gcloud` sem gravar client secret/refresh token no projeto.
- `drive-ls`: lista uma pasta do Drive pelo próprio Python.
- `drive-roundtrip`: cria arquivo de teste, relê, confere bytes/SHA-256, exclui e confirma exclusão.
- método `delete()` e `metadata()` no cliente REST.
- mantém `oauth-env` para futura execução em servidor com secrets.

## Segurança
O round-trip usa arquivo efêmero `_ROBO_ROUNDTRIP_*.txt` e o remove no final. Não altera Bronze/Silver/Gold.

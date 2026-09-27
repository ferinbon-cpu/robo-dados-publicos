# TASK 257 — captura sanitizada do Location bruto

A TASK256 provou HTTP 301 no primeiro controle PNCP com curl exit 0 e transporte saudável, mas `%{redirect_url}` permaneceu vazio.

A TASK257 preserva esse resultado e prepara um único GET no mesmo URL. O curl grava os cabeçalhos somente em arquivo temporário, descarta o corpo em `/dev/null`, extrai `Location` de forma case-insensitive, apaga o arquivo bruto e persiste apenas o resultado sanitizado.

Guardas: 1 GET, retry 0, sem `--location`, sem descoberta alternativa, sem consulta aos outros sete controles, sem Drive/TCE/Gold/serving/publicação.

Próximo gate: `OWNER_AUTHORIZED_TOKEN_2_SINGLE_PNCP_NOFOLLOW_RAW_LOCATION_HEADER_CAPTURE_ON_MERGED_TASK257_SHA`.

# M7 SIOPE CLIENT LIMEIRA SILVER DRIVE READBACK VERIFICATION GATE — 0.8.0

## Objetivo

Verificar, por uma única releitura controlada, que o primeiro payload Silver de Limeira/SP persistido no Google Drive permanece byte a byte idêntico ao payload determinístico validado e pinado no repositório.

## Evidência de origem

O gate depende da revisão offline e fail-closed da persistência Silver do run manual `33021813756`, cujo artifact sanitizado é `9626815277` com digest `sha256:d60d51938bb7b4a2488c36f46614c9eccc5601e9a30485405998243493dc68e0`.

O payload esperado possui exatamente 2328 bytes, SHA-256 `072283e3d9e5f12e6a3a697d32e653b64e618f4665e28f53e553b35506ce68da`, um registro de 52 campos e contrato `SIOPE_DADOS_GERAIS_LIMEIRA_VALIDATED_RECORD_SILVER_V1`.

## Operação autorizada

O workflow é exclusivamente manual. Após preflight, revisão offline, dry-run, testes unitários e regressões históricas, ele pode:

1. localizar pelo nome exato o arquivo já existente no folder `02_SILVER`;
2. exigir exatamente um match;
3. conferir parent, nome, MIME, tamanho e MD5 derivado do payload esperado;
4. baixar exatamente uma cópia temporária;
5. conferir tamanho, MD5, SHA-256, identidade byte a byte e identidade JSON exata.

## Operações proibidas

- nenhum write no Drive;
- nenhum overwrite, delete ou replace;
- nenhum novo GET ao FNDE/SIOPE;
- nenhuma persistência do remote file ID;
- nenhum Gold;
- nenhum processamento derivado;
- nenhuma recorrência ou schedule.

Ausência, duplicata, alteração de metadata, alteração de bytes, drift de configuração ou qualquer desvio do contrato produz STOP fail-closed.

## Próximo gate

Um PASS apenas encaminha para `M7_SIOPE_CLIENT_LIMEIRA_SILVER_DRIVE_READBACK_REVIEW_0_8_0`, que deverá revisar offline a evidência antes de qualquer decisão sobre Gold ou processamento derivado.

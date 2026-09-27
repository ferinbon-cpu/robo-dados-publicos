# TASK 263 — controle de saúde pareado 645 × 648

Após três falhas consecutivas no 648 (500, 500/JDBC transient e 503), a próxima observação deixa de ser um retry cego. O gate consulta primeiro o 645, já provado anteriormente, como controle de saúde do mesmo endpoint e em seguida o 648.

Se 645 estiver saudável e 648 falhar, a evidência favorece falha específica da consulta/registro 648 no backend. Se ambos falharem, o estado do serviço no instante fica comprometido. Se 648 retornar 200 com identidade exata, a cadeia fecha 8/8.

Gate live: `OWNER_AUTHORIZED_TOKEN_8_PAIRED_PNCP_HEALTH_645_VS_TARGET_648_ON_MERGED_TASK263_SHA`.

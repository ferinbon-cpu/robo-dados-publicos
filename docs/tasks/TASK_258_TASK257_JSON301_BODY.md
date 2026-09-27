# TASK 258 — inspeção bounded do JSON da resposta 301

A TASK257 confirmou HTTP 301 com zero cabeçalhos Location. A TASK256 havia medido Content-Type JSON e corpo de 273 bytes.

A TASK258 prepara um único GET no mesmo URL, sem follow/retry. O corpo fica em arquivo temporário, limitado a 4096 bytes, é hashado e obrigatoriamente parseado como JSON. O arquivo é apagado e apenas uma projeção sanitizada de chaves/valores escalares é persistida.

Os sete controles restantes continuam intocados. Próximo gate: `OWNER_AUTHORIZED_TOKEN_3_SINGLE_PNCP_BOUNDED_JSON_301_BODY_INSPECTION_ON_MERGED_TASK258_SHA`.

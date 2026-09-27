# TASK 044 — Design do próximo gate read-only de evidência F01

## Objetivo

Definir offline a menor leitura adicional necessária para avançar a reconciliação PPA→LOA sem reabrir varredura ampla de documentos e sem confundir continuidade programática com identidade financeira.

A TASK 043 deixou dois pontos centrais: ação 2720 possui continuidade de chave programática comprovada, mas não identidade financeira; ação 2690 permanece bloqueada porque a linha PPA Ensino Médio/Superior não foi promovida. A identidade financeira EITI continua `EVIDENCIA_INSUFICIENTE`.

## Futuro gate proposto

Tier futuro: `T1_EXISTING_CUSTODY_READONLY`.

Ele ainda NÃO está autorizado. Depois desta task, uma autorização nova do owner deverá ser presa ao SHA exato da implementação revisada antes de qualquer leitura operacional do Drive.

### PPA JOM 7119

Arquivo sob custódia: `1ez1B_mJ428IxTIUht1AHM9-I5SCotKXj`, SHA-256 `cb65f29c772eb7133c902e827884a4ed19d8c09f64586b8de9d6483023d9133a`.

Páginas permitidas: 15–16 somente.

Objetivo único: resolver diretamente na fonte a linha ação 2690 / Ensino Médio-Superior, capturando apenas campos explicitamente visíveis, como função, subfunção, valores anuais e total. Se a linha continuar ambígua, permanecer `PARSER_REVIEW_REQUIRED`; nenhum melhor palpite é permitido.

### LOA JOM 7127

Arquivo sob custódia: `1bRpmMxacX16P1tJBvam-55OOPTYuQnIA`, SHA-256 `37ea54d85cc5428622b296881a279a17e1aeefd7574576e7a3414443bbee64c4`.

Páginas permitidas: 153–156 e 170–175 somente.

Justificativa: a TASK 036 já pinou variantes 2690 na pág. 154; as TASKS 035/039 validaram diretamente 2690 na pág. 171 e 2720 na pág. 174. Páginas adjacentes entram apenas porque cabeçalhos, unidades e campos orçamentários podem atravessar limites de página.

Campos-alvo permitidos, somente quando explícitos: unidade orçamentária, fonte/destinação, natureza da despesa, dotação, além das chaves programáticas já conhecidas. Ausência = `UNKNOWN_NOT_INFERRED`.

## Não fazer

Nenhum GET de fonte pública; nenhuma escrita no Drive; nenhuma paginação; retry; OCR pré-autorizado; Bronze/Silver/Gold; serving ou publicação. LOA não prova empenhado/liquidado/pago. Código, rótulo ou valor alinhado não provam identidade financeira. Programa 2001 e tabelas globais da LOA não podem ser atribuídos à EITI.

## Critério do futuro gate

A futura leitura deve responder três perguntas e parar:

1. A linha PPA 2690 Ensino Médio/Superior pode ser resolvida diretamente?
2. As páginas LOA selecionadas contêm explicitamente unidade/fonte/natureza/dotação para 2690 e/ou 2720?
3. Com esses campos, quais elos da cadeia financeira EITI continuam faltando?

Qualquer necessidade de OCR, página adicional ou nova fonte deve retornar STOP e exigir novo desenho/autorização.

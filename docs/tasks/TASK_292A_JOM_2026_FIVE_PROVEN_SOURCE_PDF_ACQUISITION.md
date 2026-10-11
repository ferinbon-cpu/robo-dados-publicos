# TASK292A — cinco JOM 2026 já conhecidos no robô, recuperação de originais auditáveis

Data de engenharia: 11/10/2026. **Apenas proposta de execução manual, não é autorização para a rodada em si.**

## Fontes oficiais fixadas

| Edição | Publicação | Origem da URL | Prova primária prévia |
|---|---|---|---|
| 7151 | 06/01/2026 | TASK238, inspeção primária | 44.002.985 bytes, 125 páginas, SHA256 `ec298a6cff290723c97d24c291e36ef2c2044713b0fc5082b4560329e1d1dab8` |
| 7321 | 09/09/2026 | TASK248, delta do índice oficial | Sem hash primário |
| 7322 | 10/09/2026 | TASK248, delta do índice oficial | Sem hash primário |
| 7323 | 11/09/2026 | TASK248, delta do índice oficial | Sem hash primário |
| 7324 | 12/09/2026 | TASK248, delta do índice oficial | Sem hash primário |

**Somente cinco URLs exatas** são lidas de:
`docs/evidence/TASK_238_JOM_PRIMARY_CONTENT_CLOSURE_0.8.0.json` e
`docs/evidence/TASK_248_JOM_LIVE_DELTA_CANONICAL_0.8.0.json`.
O source_id da 7151 **não é inventado**; fica nulo na origem primária. Nenhuma URL é deduzida a partir do número da edição, do dia anterior ou de sequência.

## Contrato de coleta

- `workflow_dispatch` em `main`, `confirmar_cinco_joms_292a=true`, uma execução humana explicitamente confirmada, `GITHUB_RUN_ATTEMPT=1`. Nada de retry de run antiga, recorrência ou agendamento.
- Teto de **5 GETs diretos a PDF**, 0 GETs ao índice, 0 robots, 0 Drive, 0 publicação; sem redirect, sem retry, sem credenciais. Host limitado a `https://ecrie.com.br/Sistema/Conteudos/DiarioOficial/upload/*.pdf`.
- Por PDF: máximo 200 MiB; máximo 500 MiB totais; validação MIME, Content-Length, cabeçalho, capa contendo edição, páginas via `PdfReader`, tamanho SHA256; 7151 exige também igualdade exata com SHA, tamanho e 125 páginas já apurados pela TASK238.
- Quando PDF for maior que 90 MiB, dividir em **partes binárias exatas e reversíveis**; SHA256 por parte, hash e páginas do PDF original no manifesto individual; cada artifact GitHub tem até 90 MiB de conteúdo primário. Cada edição ocupa no máximo três artifacts; gerar no máximo 16 artifacts (manifesto + 15 fragmentos) com retenção de 7 dias.
- O job registra resultados parciais mas **não dá PASS sem cinco originais íntegros**. Falha HTTP 403 e drift não são prova de inexistência do PDF. A saída GitHub não é custódia permanente.
- Sem download automático pelo Drive nem promoção Silver/Gold, sem alterar o acervo Bronze; **transferência posterior ao Drive SME é etapa humana separada**, create-only e com QA dos hashes após readback.

## O que não se confunde

A TASK291 teve HTTP403 exclusivamente em `/robots.txt`; isso não comprova indisponibilidade das URLs ecrie. As edições 7152–7160 também têm identidade/data, mas ainda não URL; são fora do escopo da TASK292A. As 65 lacunas numéricas restantes são não comprovadas por TASK018/219A/238/248. O PR #925 TASK291B está separado e precisa do próprio merge após revisão. O PR #915 TASK284 corrige completude mensal do indexador e permanece separado.

## Preflight / QA antes de merge

`python -m unittest tests.test_task_292a_jom_five_historical_acquisition -v`
`python scripts/github_preflight.py`
`python scripts/github_automation_policy_gate.py`
`python scripts/github_codex_engineer_policy_gate.py`

Depois de reviews/checks verdes, o owner deve avaliar merge na `main` e só depois despachar uma execução manual. **NÃO executar o workflow enquanto estiver somente nesta branch.**

## Evidência e futura custódia

Para cada artifact: preservar run_id, artifact_id, SHA ZIP do GitHub, source_url, edição e data, SHA256 do PDF e das partes, número de páginas. Para transferir ao SME, criar arquivos novos com nomes exatos e conferir por download de retorno integral + SHA256 das partes + recomposição do PDF, jamais considerar apenas tamanho como QA final.

# TASK 289 — B06: reempacotar nove originais a partir do artifact GitHub já aprovado

**Data:** 10/10/2026. **Objetivo:** resolver limite de 100 MiB da transferência por conector GitHub→Drive SME, sem pedir download ao usuário e **sem executar novos GETs ao JOM oficial**.

## Evidência do lote já obtido

- GitHub Actions run original: https://github.com/ferinbon-cpu/robo-dados-publicos/actions/runs/38067488083 .
- Artifact: `jom2026-originais-B06-manifesto`; artifact id 11675985617; `sha256:154e4216085439e94edaf067d6ec29595086e1fd9498ed36dfeb39c2923d7fab`.
- Manifest extraído e auditado no ambiente ChatGPT: 9/9 `VALIDATED_ORIGINAL`, 565 páginas, 127.199.878 bytes de PDFs originais; SHA-256 de cada original coincidiu com manifesto, contagem de páginas também.
- Documentos: 7244 (23 páginas), 7245 (50), 7246 (59), 7247 (35), 7248 (131), 7249 (85), 7250 (27), 7251 (49), 7252 (106).
- Nenhum original B06 preexistia na custódia SME em 10/10/2026.
- Tentativa de upload de ZIP via conector Google Drive foi bloqueada de forma clara por limite 100 MiB: 127.206.741 bytes > 104.857.600. Arquivos locais não geram `file_uri` compatível com o conector Drive; carregamento transitório na Library também não gera `file_uri` de conector, portanto sem substituir a integridade por cópia ou alegar upload não ocorrido.

## Solução delimitada

Um novo workflow **exclusivamente manual** é apresentado para ler somente o artefato B06 da run **38067488083** dentro do GitHub, verificar todos os PDFs e o manifesto novamente e criar **9 artifacts, um por edição, com ZIP próprio menor que 100 MiB**. Usa `gh run download` via `GITHUB_TOKEN` com permissão somente `actions:read`, exclusivamente na `main`, `workflow_dispatch` e primeira tentativa. No total: 1 artifact GET ao GitHub, 9 artefatos create-only, zero GET aos sites oficiais, zero Drive reads/writes e zero publicação.

Cada pacote terá o PDF original integral **em bytes idênticos** e `manifest_excerpt.json`, com SHA-256, run original e URL oficial. Artifact é transitório por 7 dias; custódia SME permanece operação separada. Nenhuma credencial Drive no GitHub.

## Execução após revisão, CI e merge pelo owner

Acessar GitHub → Actions → `JOM B06 — reempacotar artefato anterior para custódia SME` → `Run workflow`, selecionar `main`, marcar `confirmar_reempacotamento_b06=true` e executar **uma vez**.

Após PASS: o ChatGPT baixará cada um dos nove artifacts, conferirá nome, manifesto, SHA-256, bytes, páginas e número da edição, e fará upload create-only diretamente ao <https://drive.google.com/drive/folders/1XQ0Yp5c6Ms7eu3gCIwCMwE0fqIjimwEd> na conta SME, com verificação de leitura no Drive. Nenhum download/upload manual do usuário é necessário além do clique do workflow.

## Gates

`python -m unittest tests.test_task_289_jom_b06_repackage -v`

`python scripts/github_preflight.py`

`python scripts/github_automation_policy_gate.py`

`python scripts/github_codex_engineer_policy_gate.py`

`python -m unittest discover -s tests -v`

Nunca declarar PASS para CI ou Drive antes da observação real. Este PR não deve fazer self-merge; segue `AGENTS.md`.

# TASK300 — P07 reempacotamento manual do artifact existente, sem nova coleta

## 1. Diagnóstico e fonte congelada

- TASK296/P07: [run 38275577819](https://github.com/ferinbon-cpu/robo-dados-publicos/actions/runs/38275577819), HEAD `41993a2b1fb2ab41f13b455650ad898ea3678f2d`, `workflow_dispatch`, resultado `success`, `PASS_ALL_PDFS_IN_TEMP_ARTIFACT` com 9 solicitados, 9 validados, nove GETs oficiais originais e nenhuma falha.
- Artifact original da execução P07, **id 11758672719**, `task296-jom-P07-originais-manifesto`, **411.100.793 bytes** (ZIP GitHub) e digest `sha256:940729f83fe883787c0fd50206beed08bde04b1ce01745bd1108aa42712d8390`; validade informada até **2026-10-19T16:12:19Z**.
- As nove edições candidatas, em ordem canônica: **7278, 7279, 7280, 7281, 7282, 7285, 7286, 7295, 7296**. O artifact temporário **não é custódia Bronze**.
- Inventário SME [matriz](https://docs.google.com/spreadsheets/d/1yoFzRzGSRdaN525LQMH8fXjye8h_hOM8ELM25ffW0H8/edit): **158/192 custodiados, 34 pendentes**, dentre estes nove P07. O checkpoint [V75](https://docs.google.com/document/d/1rLVORvqVZJE8lAq0sdryCaSOS6NYiTdv-3sxFV6HFC4/edit) registra o incidente de transporte.

## 2. Implementação (T2, manual e uma vez por autorização)

Adaptar a receita já validada na TASK299/P05, mas somente para o P07:
1. Novo `workflow_dispatch`, com confirmação booleana explícita, apenas `main`, primeira tentativa `GITHUB_RUN_ATTEMPT=1`, repo fixo, token de GitHub com apenas `contents: read` e `actions: read`.
2. Único download permitido é o **artefato GitHub pré-existente** da run 38275577819 por `gh run download`. Não acessar `ecrie.com.br`, índices, TinyFish nem Google Drive.
3. Validar precisamente nove arquivos originais contra manifesto, URLs congeladas P07, hashes, bytes, número de edição nas primeiras páginas e contagem de páginas. Bloquear por qualquer divergência antes de emitir parte.
4. Construir `TASK300_P07_NINE_EXACT_ORIGINALS.zip`, com os PDFs inalterados e respectivos manifestos; dividir os bytes desse ZIP em **seis partes de no máximo 70 MiB**, cada uma envolta num ZIP menor que 95 MiB e com hash separado. O ZIP original agrupado deve ser reconstituível por concatenação binária das seis partes em ordem.
5. Publicar exatamente seis artifacts GitHub de partes e um manifesto QA (sete no total, retenção 7 dias), informando `source_site_gets=0`, `drive_writes=0`. Evidência de CI/testes **não prova** execução ao vivo; só declarar PASS quando houver run manual auditável.

O contrato `config/automation_policy.v1.json` registra nova gate `TASK300_P07_EXISTING_ARTIFACT_SIX_LOSSLESS_PARTS_MANUAL`, `T2_CREATE_ONLY`, `auto_allowed=false`, `human_confirmation_required=true`, `github_artifact_create_count_max=7`, `source_get_count_max=0`, `drive_writes=0`.

## 3. Fechamento ainda não autorizado por esta PR

- O PR requer revisão e merge manual do proprietário **após CI**; não permite self-merge.
- A criação da PR não dispara o workflow. O proprietário deverá executar `task300-p07-existing-artifact-6parts-manual.yml` em `main`, escolhendo `confirmar_reempacotamento=true`.
- Após esse run, recuperar os seis pacotes, checar SHA-256/ZIP CRC, fazer upload **create-only** na pasta Bronze SME e **readback**, concatenar e reconstruir os nove PDFs exatos e conferir capa/páginas/hashes.
- **Somente então** alterar o status na matriz (158 → 167 custodiados), anexar relatório final e atualizar checkpoint.
- Não continuar o P08 automaticamente nem inventar identidades nas edições de setembro.

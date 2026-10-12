# TASK299 — P05, nove JOMs validados no GitHub, transferência por partes exatas

## Evidência documental existente
- Execução TASK296 lote P05: https://github.com/ferinbon-cpu/robo-dados-publicos/actions/runs/38256908207
- Conclusão `success`, no main SHA `56e72683819c1eae98e860db3ee3ec660fbbf92c`.
- Artifact `task296-jom-P05-originais-manifesto` ID `11750672822`, 330245869 bytes, SHA-256 ZIP do GitHub `bf3f7175bfc0b50834f9cd569f6a6c35eb5f1ff62cf7d0870b9d4ce1082dfb53`, expiração 19/10/2026 às 13:37 UTC.
- Gate do runner: `PASS_TASK296_TEMPORARY_ARTIFACT_ONLY P05 9`, manifesto gerado declara 9/9 arquivos originais de fontes públicas, sem retries, sem Drive.
- Edições candidatas fixas: 7236–7241 e 7254–7256. Verificação manual de capa e conteúdo fora do GitHub ainda deve ser feita antes de atualizar a custódia SME.
- A matriz SME, antes da TASK299, registra 140 custodiados e 52 posições candidatas ainda pendentes. P05 permanece fora da custódia permanente.

## Bloqueio de transferência
- O artifact ZIP integral (330 MB) excede o limite de upload do conector Drive. O `files.manage_library` também retornou `file_too_large` em tentativa create-only; **nenhum arquivo foi criado** na pasta Bronze.
- A execução Python/container desta sessão apresentou falha de serviço, impossibilitando subdividir localmente os bytes neste momento. Não inferir que a validação do GitHub represente custódia Drive.

## Procedimento excepcional, sem duplicação de download eCrie
- Branch proposta TASK299, script `scripts/repackage_task299_p05_existing_artifact.py` e workflow manual `.github/workflows/task299-p05-existing-artifact-5parts-manual.yml`.
- `workflow_dispatch` restrito a `main`, confirmação explícita, primeira tentativa; permissões `actions:read` e `contents:read`, checkout sem credenciais.
- Baixa **somente** o artifact GitHub já existente da run 38256908207, sem novo GET eCrie, sem Drive e sem publicar.
- Confere manifesto, SHA de cada original, URL oficial congelada, bytes, número da capa e páginas dos nove PDFs antes de produzir qualquer pacote.
- Agrupa exatamente os nove originais em um ZIP armazenado sem compressão e o divide binariamente em 5 partes de 70 MiB no máximo; cada parte é embalada em ZIP próprio com manifesto, hash SHA-256 original, hash SHA-256 da parte, índice e regra explícita de recomposição.
- Um sexto artifact traz QA de conjunto. Todos são temporários (retention 7 days) e **não** significam custódia.
- Depois de concluir uma execução manual, baixar os cinco artifacts, conferir manifesto, fazer upload create-only de cada ZIP abaixo de 100 MiB ao Drive SME `02_JOM_UNICAMP_BRONZE` e baixar novamente do Drive; conferir SHA-256 dos cinco ZIPs e reconstrução concatenada exata. Reextrair e verificar SHA e páginas dos 9 PDFs. Só então alterar estados da aba `URLS_PENDENTES_FEV_OUT_V58`.
- Zero retries, zero recorrência, zero execução automática de outros lotes. Não usar TinyFish.

## Critério de STOP
Se a CI ou QA falhar, não executar workflow nem promover registros. Se o artifact original expirar, não presumir possibilidade de recuperá-lo. Exigir nova decisão do proprietário e fonte oficial, sem reabrir coleta automaticamente.

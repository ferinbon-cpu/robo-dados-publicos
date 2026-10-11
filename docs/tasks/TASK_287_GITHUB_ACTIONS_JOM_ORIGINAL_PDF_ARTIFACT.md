# TASK 287 — Baixar cinco JOMs originais pelo GitHub Actions

## Fluxo simples autorizado pelo usuário
Este PR substitui a complexidade de três PRs de descoberta por **um único workflow manual**, independente de TASK284–286.

Após PR revisado/mergeado na main protegida, abrir:
`Actions → JOM LOA 2027 — baixar 5 PDFs originais → Run workflow`;
selecionar branch `main`, marcar `autorizar_5_arquivos` e iniciar **uma vez**.

O workflow exige que a execução seja `workflow_dispatch` na `main`, `run_attempt=1` e checkbox true antes de qualquer GET.

## PDFs candidatos exatos
O corpus vem do arquivo já pinado por hash e validado pela TASK219A:
`docs/evidence/fixtures/task219/TASK_219A_CANONICAL_87_DOCUMENT_TARGETS.csv`
Nenhuma edição é deduzida a partir de número, data ou nome de arquivo.

| Edição | Data | Fonte exata |
|---|---|---|
| 7211 | 2026-03-28 | `u_137_27032026212718.pdf` |
| 7208 | 2026-03-25 | `u_137_24032026180152.pdf` |
| 7209 | 2026-03-26 | `u_137_25032026171101.pdf` |
| 7210 | 2026-03-27 | `u_137_26032026165705.pdf` |
| 7212 | 2026-03-31 | `u_137_30032026164910.pdf` |

Todas as URLs são HTTPS sob `ecrie.com.br/Sistema/Conteudos/DiarioOficial/upload/`. A edição 7211 contém o Decreto Municipal 62/2026, segundo índice oficial legislativo, mas conteúdo e Anexos I/II ainda não foram vistos.

## Limites e efeitos
- Exatamente **5 GETs máximos**, um por URL, 0 GETs ao índice, 0 retries.
- **200 MiB por arquivo**, **500 MiB agregados**, nenhum redirect permitido.
- Validação de URL final idêntica, Content-Type PDF/octet-stream, assinatura `%PDF-`, pypdf, contagem de páginas e **número da edição na capa**; SHA-256 bytes.
- Upload create-only em **1 GitHub Actions artifact de 7 dias**, não em Drive, contendo PDFs validados e `manifest.json`.
- **Não possui** credenciais Drive, secret, publicação Gold, sincronização, schedule, auto re-run, update/overwrite ou exclusão.
- Se algumas fontes falharem, o artifact poderá conter somente os PDFs efetivamente válidos, com estado `PARTIAL_STOP_REVIEW_FAILURES` e erro explicitado. O workflow falha para 4/5 ou menos. **Falha de acesso não é prova de ausência.**
- Registrar o hash e não duplicar os 17 PDFs já preservados no Drive SME; essa futura custódia depende de etapa separada.
- GitHub Artifact não é custódia permanente: expira em **7 dias**. O usuário/assistente deve transferir para SME com QA SHA-256 se houver documentos válidos.

## Política
A `config/automation_policy.v1.json` recebe um **novo gate T2_CREATE_ONLY manual**, `auto_allowed=false`; o PR não reclassifica T1/T2 como execução automática. A revisão/merge deve ser feita pelo proprietário, pois `AGENTS.md` proíbe self-merge do agente.

## CLI/T0
- `python -m unittest tests.test_task_287_jom_original_pdf_artifact -v`
- `python scripts/github_preflight.py`
- `python scripts/github_automation_policy_gate.py`
- `python scripts/github_codex_engineer_policy_gate.py`
- `python -m compileall -q .`
- `python -m unittest discover -s tests -v`
- `python main.py selftest`

Não afirmar PASS antes de observar os logs CI do PR.

## Relação com a LOA 2027
A coleta serve exclusivamente à prova documental de decretos de crédito de 2026, em especial os Anexos I/II por ação/fonte. Não atribuir valores orçamentários na ausência de quadro original completo. O instrumento não edita nenhum arquivo municipal nem protocola manifestação cidadã.

# TASK 288 — Custódia documental JOM Limeira 2026: 81 originais em nove lotes manuais

**Data:** 10/10/2026. **Escopo:** extensão do piloto TASK287 bem-sucedido (run 38054712029) sem ampliar automaticamente o serviço. **Estado deste PR:** engenharia offline; nenhum GET remoto efetuado por esta tarefa ainda.

## Inventário de base e lacunas

- TASK219A mantém **87 URLs oficiais** do JOM 2026 com fixture CSV **verificada por Git blob hash**.
- O inventário anterior totalizava **99 identidades de edições** de 01/01 a 08/09/2026 (87 TASK219A + 12 já indexadas TASK184); isso NÃO representa todas as edições efetivamente publicadas em 2026.
- Pasta custodiada no SME (leitura em 10/10/2026): **18 PDFs JOM de 2026**: 7208, 7209, 7210, 7211, 7212 e 7294, além de 7304–7315. Os demais originais custodiados nessa pasta são de 2025 e NÃO contam no universo de 2026.
- Para o subuniverso de 87 URLs TASK219A, **6 já estão custodiadas no SME**: `7208, 7209, 7210, 7211, 7212, 7294`; permanecem **81 URLs oficiais ainda sem original preservado nesse acervo**.
- Esses 81 são apenas uma **parte das lacunas do ano**: é necessário inventariar o restante dos meses, especialmente 01–16/jan, 01–10/fev, lacunas de mar–ago, set pós-08/09 e out até a data de corte, SEM inferir ausência a partir de intervalo numérico.

## Fluxo de operação

Após PR revisado e mesclado na `main` protegida, na aba GitHub Actions abrir
`JOM 2026 — recuperar 81 originais por lotes de 9`.

Selecionar exatamente **um** `lote` (B01–B09), marcar `autorizar_lote=true` e clicar `Run workflow` **uma vez por lote**. É necessário revisar resultado antes de iniciar outro lote. Nenhum `schedule`, `push`, `workflow_run`, `repository_dispatch` ou retry implícito.

Por lote: **no máximo 9 GET** a URLs HTTPS fixas da fixture, 0 chamadas ao índice, 0 retries, limite de 200 MiB/PDF e 500 MiB agregados, sem redirecionamento, validação da capa e parser PDF, SHA-256, identidade de edição, Content-Length e MIME. Artefato GitHub 7 dias contém originais e `manifest.json`; se parcial, job marca STOP e mantém PDFs comprovados para análise humana. **Sem credenciais Drive, sem escrita Drive, sem Silver/Gold, sem publicação orçamentária**.

**Custódia permanente é separada**: somente após run confirmado, baixar cada original, validar SHA-256 contra o manifesto e subir create-only ao Drive SME (pasta `02_JOM_UNICAMP_BRONZE`) com deduplicação por edição/hash e QA por re-download. O artefato ZIP pode ultrapassar 100 MB e falhar no conector Drive; preferir PDFs individuais. Jamais substituir os 18 originais anteriores.

## Lotes determinísticos

A composição é a ordem crescente dos números de edição dentre as **81** linhas da fixture, excluindo os seis originais existentes na SME.

| Lote | 9 edições | Período da fixture |
|---|---|---|
| **B01** | 7161, 7162, 7163, 7164, 7165, 7166, 7167, 7168, 7169 | 2026-01-17 a 2026-01-29 |
| **B02** | 7170, 7171, 7172, 7179, 7180, 7181, 7182, 7183, 7184 | 2026-01-30 a 2026-02-20 |
| **B03** | 7185, 7186, 7187, 7188, 7189, 7190, 7201, 7202, 7203 | 2026-02-21 a 2026-03-18 |
| **B04** | 7204, 7205, 7206, 7207, 7221, 7222, 7223, 7224, 7225 | 2026-03-19 a 2026-04-17 |
| **B05** | 7226, 7227, 7228, 7229, 7230, 7231, 7232, 7242, 7243 | 2026-04-18 a 2026-05-16 |
| **B06** | 7244, 7245, 7246, 7247, 7248, 7249, 7250, 7251, 7252 | 2026-05-19 a 2026-05-29 |
| **B07** | 7253, 7262, 7263, 7264, 7265, 7266, 7267, 7268, 7269 | 2026-05-30 a 2026-06-24 |
| **B08** | 7270, 7271, 7272, 7273, 7283, 7284, 7287, 7288, 7289 | 2026-06-25 a 2026-07-24 |
| **B09** | 7290, 7291, 7292, 7293, 7316, 7317, 7318, 7319, 7320 | 2026-07-25 a 2026-09-05 |

## Limite de escopo e análises orçamentárias

Este PR resolve somente a recuperação reproduzível de **81 JOMs com URL oficial já conhecida**. Não afirma ter feito a coleta nem que 99 edições cobrem todo o ano. Uma **etapa futura separada** deverá inventariar todos os PDFs publicados até 10/10/2026 no portal oficial, registrar URLs verificáveis para as lacunas fora da fixture e propor novas coletas bounded com revisão prévia.

O fluxo analítico posterior deverá pesquisar **todas as páginas** dos JOMs, identificar decretos de créditos suplementares/especiais, seus Anexos I e II, anulações, fontes e retificações, e alimentar ledger por chave `exercício / ato / publicação / órgão / função / subfunção / programa / ação / fonte / natureza / tipo / valor`. Créditos não representam pagamento; fonte de cobertura por anulação não representa aumento líquido da despesa autorizada. RREO, TCESP e QDD são reconciliação separada.

## Gate de QA

`python -m unittest tests.test_task_288_jom_2026_archive_batched -v`

`python scripts/github_preflight.py`

`python scripts/github_automation_policy_gate.py`

`python scripts/github_codex_engineer_policy_gate.py`

`python -m unittest discover -s tests -v`

`python main.py selftest`

Resultados não devem ser declarados PASS antes de conferência do GitHub CI. Política: `JOM_2026_81_ORIGINALS_MANUAL_BATCH_ARCHIVE`, T2 manual, `auto_allowed=false`.

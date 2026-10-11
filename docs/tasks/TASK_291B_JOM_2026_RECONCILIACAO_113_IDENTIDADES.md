# TASK291B — Reconciliar JOM 2026 com dados já conhecidos pelo robô

**Em 11/10/2026:** reconciliação determinística offline, sem GETs, sem novas consultas ao Jornal, sem PDF e sem Drive mutável. Escopo: manifestos históricos **TASK018, TASK219A, TASK238 e TASK248** no próprio repositório e os 99 IDs já preservados no SME.

## Estado apurado

| Evidência | Edições 2026 | Já na SME | Não custodiadas |
|---|---:|---:|---:|
| TASK219A — fixture URLs oficiais fixadas | 87 | 87 | 0 |
| TASK018 — 12 identidades agosto | 12 | 12 | 0 |
| TASK238 — janeiro 7151–7160 | 10 | 0 | 10 |
| TASK248 — setembro 7321–7324 | 4 | 0 | 4 |
| **Total identidades distintas** | **113** | **99** | **14** |

**Janeiro está fechado quanto a identidade**: 22 edições 7151–7172 (TASK238), 12 sob custódia, 10 a preservar. A edição 7151 foi inspecionada previamente pela TASK238 com prova exata (URL, SHA256 `ec298a6cff290723c97d24c291e36ef2c2044713b0fc5082b4560329e1d1dab8`, 44.002.985 bytes, 125 páginas). Para 7152–7160, conhecem-se edição e data, mas **nem URL nem SHA primário foram localizados nos quatro manifestos reconciliados**. Por isso os campos estão vazios no CSV; **source_id não deve ser inferido**.

As quatro edições 7321–7324 foram descobertas e canonizadas pelo próprio índice municipal nas TASK247/248. O manifesto registra URLs oficiais diretas, sem afirmar que PDFs foram adquiridos ou inspecionados.

O período conhecido com datas e URLs não equivale ao ano completo: até o recorte numérico 7151–7328, havia 79 lacunas contra a custódia 99; agora **14 já têm identidade oficial histórica confirmada**, restando **65 números candidatos ainda sem prova individual**. A lista é numérica e pode não corresponder 1:1 a edições publicadas; novas edições após 12/09 ainda precisam de verificação. Não equiparar 113 a total anual. Não confundir `PASS_COMPLETE_DISCOVERY_CANONIZED` da TASK217C com fechamento mês a mês; janeiro teve contagem incompleta (12 vs 22), e o PR #915 TASK284 mantém correção de completude ainda aberta.

## Arquivos de saída

- `docs/evidence/task291/TASK291B_JOM_2026_113_IDENTIDADES_RECONCILIADAS.csv` — 113 linhas, com data, source id **somente quando fonte contém**, URL declarada, fonte de evidência, status de custódia, prova SHA/pages 7151.
- `robo_dados_publicos/research/task291b_jom_existing_canon_reconciliation.py` — reconciliação offline T0 e checks fail-closed, exibe resumo JSON e reproduz CSV.
- `tests/test_task_291b_jom_existing_canon_reconciliation.py` — garante 113/99/14, URL primária para 5, 9 janeiro date-only, CSV byte-idêntico e proibição de inventar source IDs.

## Iniciativas separadas

**P0 — 5 URLs prontas para gate de recuperação:** 7151, 7321, 7322, 7323, 7324. Permitir aquisição apenas em gate manual de PDF, URLs exatas pinadas e autenticação/fonte oficial suficiente; validar PDF, capa, data, páginas, bytes e SHA256; custódia create-only no Drive SME + readback. A 7151 deve concordar com SHA e tamanho históricos. **Nenhum download é autorizado por esta TASK291B sozinha.**

**P1 — 9 edições de janeiro com data conhecida, URL ainda pendente:** 7152–7160. Recuperar pelo índice/consultas autorizadas, ou referências oficiais já existentes em outros arquivos, sem deduzir URL pelo nome de upload.

**P2 — 65 lacunas numéricas sem prova documental individual:** revisar os manifestos históricos adicionais antes de solicitar indexação. Resolver conflito aparente de 7237/7238 vs 7327/7328 pelas capas, não por correção presumida.

**P3 — fechar oficialmente a janela restante até a data corrente:** posterior a 12/09 até 11/10, e depois acompanhar o que vier até 31/12; não inventar total de futuras edições.

**TASK284 PR #915:** correção T0 de contagem de itens no HTML e falha de paginação, ainda não mesclada neste diagnóstico; não duplicar seu código neste PR. O erro TASK291 run #38108507113 foi 403 no `robots.txt` após uma única requisição; não prova bloqueio dos índices e não deve ser repetido identicamente.

## Proveniência auditável

- `docs/evidence/fixtures/task219/TASK_219A_CANONICAL_87_DOCUMENT_TARGETS.csv`
- `docs/evidence/TASK_018_JORNAL_COMPLETED_CANONICAL_CHECKPOINT_0.8.0.json`
- `config/lt_formation_timing_jom_direct_discovery.v3.json`
- `docs/evidence/TASK_238_JOM_PRIMARY_CONTENT_CLOSURE_0.8.0.json`
- `docs/evidence/TASK_248_JOM_LIVE_DELTA_CANONICAL_0.8.0.json`

Nenhum arquivo histórico é reescrito, nenhuma proveniência é promovida acima do que o documento primário suporta; este é um cruzamento T0 dos arquivos existentes.

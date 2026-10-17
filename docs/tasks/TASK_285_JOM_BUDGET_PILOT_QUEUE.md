# TASK 285 — Lote piloto JOM: fila imutável de cinco URLs oficiais (T0)

## Razão
A LOA 2026 de Limeira requer os **Anexos I e II** dos atos de crédito adicional para reconstruir dotações por ação/fonte e conciliar o RREO Educação atualizado de abril (R$ 556.540.143,01). Identificar decreto pelo título ou número não comprova os valores por dotação.

## Fonte primária / seleção exata
A TASK219A fixou oficialmente 87 URLs de PDFs no arquivo
`docs/evidence/fixtures/task219/TASK_219A_CANONICAL_87_DOCUMENT_TARGETS.csv`.
Esta tarefa T0 deriva **cinco URLs já declaradas pela fonte**, sem criar rotas:

- 7211 — 28/03/2026: Decreto Municipal nº 62/2026, página 5, citado na Legislação Digital (este é o **único decreto efetivamente identificado neste lote**);
- 7208 — 25/03/2026, triagem;
- 7209 — 26/03/2026, triagem;
- 7210 — 27/03/2026, triagem;
- 7212 — 31/03/2026, triagem.

Edições vizinhas não implicam que contenham créditos orçamentários. Não extrapolar para toda a série; as 99 identidades da TASK217C/219A são recorte e não inventário mensal completo. Para janeiro, **TASK238 V3 já prova as 22 identidades (7151–7172)**, mas não fornece URLs integrais para todas elas.

Fontes:
- `config/lt_formation_timing_jom_direct_discovery.v3.json`.
- `docs/evidence/TASK_238_JOM_PRIMARY_CONTENT_CLOSURE_0.8.0.json`.
- `docs/tasks/TASK_219B_JOM_STRONG_IDENTITY_CANONIZATION.md`.
- https://legislacao.limeira.sp.leg.br/Limeira-SP/DecretosMunicipais/62-2026

## Entrega técnica
`robo_dados_publicos/research/task285_jom_budget_pilot_queue.py`: `build_pilot_queue()`, leitura local da fixture CSV (87 linhas), verificação de schema, data, IDs, unicidade, host oficial HTTPS, extensão `.pdf`, caminho permitido, e seleção exata em ordem. Falhas resultam em `Task285Stop`, sem I/O remoto.

`tests/test_task_285_jom_budget_pilot_queue.py`: 7 testes offline com URL host falsificada, identidade alterada, duplicidade, linha ausente, edição piloto ausente e assertions de não autorização.

O output sinaliza expressamente:
- `status: READY_FOR_SEPARATE_T1_GATE`;
- `network_request_count = pdf_download_count = drive_write_count = 0`;
- `live_execution_authorized = false`;
- `download_gate_required = custody_gate_required = true`.

## Não autorizado pelo patch
Não há workflow novo nem alteração de política; este patch não chama a rede, não baixa PDF, não faz OCR, não produz linhas orçamentárias e não escreve no Drive. NÃO transforma o termo “prossiga” em autorização genérica de T1/T2. Também não altera `main`, histórico canônico ou execução financeira.

## Próximos gates
1. Rever e mesclar PR **TASK284** quando CI e revisão do responsável concluírem. (Reparo de completude por total do portal; PR independente.)
2. Rever e mesclar TASK285 com CI antes de propor download.
3. T1 com autorização específica **após** o SHA do código de aquisição aprovado, 5 GETs no máximo, URL final idêntica, sem redirecionamento, bytes e páginas limitados, SHA e PDF validado; sem gravação remota.
4. T2 separado para custódia imutável Bronze/create-only no Drive, com QA de retorno, sem publicação.
5. Extrator T0 por página (Anexos I/II) com revisão das tabelas, sem inventar rubricas por semelhança textual, e teste com RREO.

Risco especial: o JOM nº 7211 pode conter uma página de decreto e anexos em páginas subsequentes ou publicação separada. Ausência no PDF alvo requer estado `ANEXO_PENDENTE`, não valor zero.

**Estado no momento do PR:** T0 apenas; testes locais/CI precisam ser comprovados por execução, não declarados PASS previamente.

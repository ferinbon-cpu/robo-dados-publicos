# BI-001 — arquitetura do output analítico Drive-first

## Problema e boundary

BI-001 define, em `T0_OFFLINE`, uma projeção tabular entre as camadas derivadas e consumidores analíticos. BI não é fonte de verdade e não corrige Gold: `SOURCE → BRONZE → SILVER → GOLD/DOCUMENT/RAG/RECONCILIATION → BI → Looker/relatórios`. Esta task não acessa rede ou Drive, não cria Sheet, não publica, não chama Looker e não autoriza BI-002, TASK 024, recorrência ou schedule.

## Local e arquitetura proposta

Recomenda-se **`09_BI`**, irmã de `08_OUTPUTS`: outputs são produtos publicados para pessoas; BI é uma projeção serving com contratos próprios. A pasta remota não é criada aqui. Dentro dela, cada dataset terá snapshots imutáveis e, somente após nova decisão de governança, uma fonte serving estável.

A decisão é **OPÇÃO 3 — snapshots create-only + serving Sheet estável**:

* Modelo A (Sheet mutável apenas) favorece Looker, mas perde a trilha imutável e exige mutação controlada.
* Modelo B (snapshots apenas) maximiza auditabilidade/readback, mas quebra o identificador estável esperado pelo Looker.
* Modelo C preserva snapshots create-only como evidência, permite readback/hash por snapshot e isola a mutação da serving Sheet. É a melhor separação entre auditabilidade e consumo.

A atualização da serving Sheet é **`GOVERNANCE_DECISION_REQUIRED`**: BI-002 deve ter gate humano separado, inventário/preflight antes da primeira escrita, chave do snapshot pinada, rebuild determinístico, readback tabular e nenhuma publicação implícita. A implementação desta PR não flexibiliza create-only.

## Datasets, granularidade e chaves

| Dataset | Grão | Chave | Origem | Estratégia futura |
|---|---|---|---|---|
| `BI_SIOPE_SERIES` | ano × município × métrica | municipality_code, year, metric_id | Gold | full rebuild em snapshot |
| `BI_JORNAL_EVENTOS` | evento documental | event_id | Bronze/Silver/Gold | append lógico em snapshot |
| `BI_RECONCILIACAO` | relação/candidato | reconciliation_id | reconciliação | histórico append + view corrente rebuild |
| `BI_FONTES_STATUS` | source/module | source_id | estado/proveniência | rebuild |
| `BI_EXECUCOES_ROBO` | run/batch | run_id, batch_id | logs/estado/proveniência | append lógico |
| `BI_DICIONARIO` | campo de dataset | dataset, field | contrato BI | rebuild |

O contrato machine-readable é canônico para campos e tipos. Campos candidatos não comprovados pelo parser atual não foram promovidos; os presentes são observados no `JournalEvent`, identidade da edição ou explicitamente nullable. Campo desconhecido termina em `FIELD_NOT_PROVEN`. `null` preserva ausência/não extração; `NOT_APPLICABLE` é enum semântico e não substitui silenciosamente null.

SIOPE é LONG, usa `2016=P1`, `2017–2024=P6` e recusa 2025. A série continua descritiva e não produz compliance, auditoria ou causalidade. Reconciliação preserva `MATCH_CANDIDATE != financial_identity`; `PROVEN` só poderá ser usado se esse estado existir e a identidade estiver provada.

## Proveniência, privacidade e Looker-ready

Toda linha carrega `provenance_id` (ou `provenance_reference` em fontes). A chave resolve deterministicamente source/edição ou ano, Bronze, Silver/Gold, run, batch, SHA e transformação; hashes úteis à exploração permanecem desnormalizados. A serving layer não substitui o registro de proveniência.

Os schemas têm uma linha de cabeçalho, nomes estáveis, tipos escalares, datas ISO, IDs textuais, booleanos reais, números/moeda numéricos, enums previsíveis e nenhuma semântica em cor, merge, título ou subtotal. CPF, RG, contato pessoal, secrets, tokens, credenciais e IDs remotos sensíveis são recusados; CNPJ só é nullable e nunca inferido.

## Páginas-alvo e opcionais

Os seis datasets suportam visão geral (fontes/runs), SIOPE (LONG), Jornal (eventos/filtros), reconciliação (status/confiança sem promoção) e saúde (runs/freshness/STOP). Nenhum gráfico é criado.

Recomendações futuras: `BI_ALERTAS` traz valor ao separar STOP/drift/freshness; `BI_CALENDARIO` pode simplificar períodos no Looker; `BI_METRICAS` será útil quando houver mais famílias de métricas. `BI_DOCUMENTOS`, `BI_FORNECEDORES` e `BI_CONTRATOS` devem aguardar prova de campos e casos de uso, evitando agregação que esconda evidência ou invente identidade.

## Limitações, riscos e próximos passos

Fixtures provam estrutura, não materializam todo o acervo. Freshness e estados operacionais dependem de snapshots autoritativos futuros. Uma serving Sheet estável introduz mutação e risco de corrupção; por isso deve ser derivável de snapshot pinado, atualizada somente sob autorização e aceita apenas após readback semântico. Looker não pode editar BI/Gold.

BI-002 deverá: (1) decidir e autorizar T2 para snapshots create-only; (2) decidir separadamente o tier da serving Sheet mutável; (3) criar `09_BI`; (4) materializar somente os seis contratos; (5) gravar manifest por último e verificar valores/tipos/hashes; (6) manter rollback como repoint para snapshot válido, nunca apagar/reparar evidência. BI-003 conecta Looker; BI-004 endurece readback; BI-005 só então avalia automação. TASK 024 permanece independente e não autorizada.

Release inalterada: 0.7.0 ACTIVE; 0.8.0 CANDIDATE; B1/B2/B3 PENDING; série fechada 2016–2024; 2025 `PROVEN_STRUCTURAL_RECENT`, S1/S2 `NOT_PROVEN`, closure/comparabilidade `UNKNOWN`, Gold `UNKNOWN/BLOCKED`; 2026 `UNPROVEN_CURRENT_YEAR`.

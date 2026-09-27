# Checklist final de QA do portal

Marcar somente após observação direta; uma caixa vazia não é autorização para corrigir fontes por overwrite.

## Fontes e schema

- [ ] Exatamente seis serving sources, com os seis nomes exatos do contrato.
- [ ] Somente `DATA` é fonte analítica; `META` está reservado para auditoria/proveniência.
- [ ] Todas as fontes estão schema-bound a BI-001.
- [ ] Nenhum campo inventado e nenhum dataset extra.
- [ ] Snapshots, manifests e servings permanecem preservados e não modificados pelo portal.

## Semântica

- [ ] SIOPE contém somente 2016–2024; 2016=P1; 2017–2024=P6; 2025 ausente.
- [ ] Unidades SIOPE são exibidas e unidades incompatíveis não compartilham eixo.
- [ ] Null do Jornal permanece null; campos ausentes não foram preenchidos.
- [ ] `MATCH_CANDIDATE != FINANCIAL_IDENTITY` aparece textual e visualmente.
- [ ] Não existe indicador de fraude, risco arbitrário, compliance, MDE/Fundeb, conclusão fiscal ou causalidade.
- [ ] Data Studio e Google Sites declaram que não são source of truth.

## Produto, UX e operação

- [ ] Um relatório contém exatamente cinco páginas analíticas e cada visual responde à pergunta contratada.
- [ ] Filtros respeitam `REPORT_LEVEL`, `PAGE_LEVEL` ou `SOURCE_SPECIFIC` e fontes compatíveis.
- [ ] Datas, datetimes, booleanos, números e currency mantêm tipos; números não são textos decorativos.
- [ ] Contraste, navegação, responsividade/mobile, ordem de leitura e avisos foram revisados.
- [ ] Metodologia, proveniência, dicionário, Sobre, aviso de atualização e limitações estão presentes.
- [ ] Zero efeitos remotos nesta task; zero publicação; zero T3 ativa.
- [ ] Zero Workspace Studio/automação/schedule/recurrence.
- [ ] Zero Google Cloud, BigQuery e AppSheet.

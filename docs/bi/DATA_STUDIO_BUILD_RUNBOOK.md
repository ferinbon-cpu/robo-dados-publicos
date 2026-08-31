# Runbook — construir o relatório no Data Studio

## Pré-condições

Executar somente sob autorização operacional posterior. Usar exatamente as seis stable servings do contrato, aba `DATA`; `META` é auditoria. Manter uma única métrica/unidade no eixo SIOPE. Não publicar antes do QA.

## Sequência exata

1. Abrir Data Studio (antigo Looker Studio).
2. Criar um único relatório multipágina com o título configurado no contrato.
3. Adicionar `BI_SIOPE_SERIES__SERVING` como fonte.
4. Selecionar exclusivamente a aba `DATA` (`META` não é fonte analítica principal).
5. Conferir todos os tipos contra `config/bi/analytics_output.v1.json`; não aceitar conversão automática divergente.
6. Repetir conexão, seleção de `DATA` e conferência para `BI_JORNAL_EVENTOS__SERVING`, `BI_RECONCILIACAO__SERVING`, `BI_FONTES_STATUS__SERVING`, `BI_EXECUCOES_ROBO__SERVING` e `BI_DICIONARIO__SERVING`.
7. Configurar somente agregações especificadas em `charts`; IDs usam `COUNT_DISTINCT`, contagens usam `SUM` quando indicado e valores SIOPE não são agregados entre métricas/unidades.
8. Configurar somente campos calculados aprovados em `calculated_fields` (lista vazia nesta versão); não improvisar fórmulas.
9. Construir **Visão Geral** com os componentes do contrato, sem números hardcoded.
10. Construir **SIOPE** com controle de métrica, série anual, contexto e tabela; exibir unidade e cautela.
11. Construir **Jornal Oficial** com totais, distribuições, filtros e tabela; preservar null.
12. Construir **Reconciliação** usando somente `reconciliation_id`, IDs/lados, `logical_key`, `match_rule`, `candidate_score`, `decision`, `status`, `reason_code`, proveniência, valores e nomes de entidade definidos no schema; inserir o texto obrigatório de alto destaque.
13. Construir **Saúde e Proveniência** com fontes, execuções e dicionário.
14. Configurar controles exatamente conforme `filters`; não aplicar controles a fontes incompatíveis.
15. Revisar todas as cautelas por componente e página.
16. Testar cada filtro isolado e combinado somente dentro do escopo coerente.
17. Testar que null do Jornal permanece vazio/null e nunca vira zero.
18. Testar datas, datetimes, booleanos, números e currency contra as Sheets e o contrato.
19. Validar que SIOPE contém apenas 2016–2024, com 2016=P1, demais anos=P6 e 2025 ausente.
20. Validar Reconciliação contra `decision`, `status`, `match_rule` e `reason_code`, mantendo visível que `MATCH_CANDIDATE` não representa identidade financeira comprovada.
21. Validar compartilhamento mínimo necessário, sem tornar snapshots/manifests editáveis ou fontes do relatório.
22. Obter o embed de cada página somente após QA completo; não publicar o relatório nesta task.

## Layout e acessibilidade

Usar hierarquia clara, contraste, texto alternativo quando suportado, paleta com significado documentado, navegação consistente e layouts desktop/mobile. Evitar 3D, gauge decorativo, redundância e métricas sem contexto. Cada visual deve responder à pergunta registrada no contrato.

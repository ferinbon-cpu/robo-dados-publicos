# Portal Analítico de Dados Públicos — arquitetura final

## Decisão, papel e público

O título provisório configurável é **Observatório de Dados Públicos de Limeira**. O produto atende pessoas não técnicas que precisam entender achados do robô, explorar SIOPE e Jornal Oficial, consultar candidatos de reconciliação, verificar fontes e execuções e compreender campos, método, proveniência e limitações.

`PORTAL_ROLE = DERIVED_ANALYTICAL_PRODUCT_NOT_SOURCE_OF_TRUTH`. O padrão é preservação → camada derivada → exploração. Portal, relatório e Site nunca substituem fontes originais, Bronze, Silver, Gold, snapshots, manifests, proveniência, documentação, GitHub ou hashes; nunca os modificam para adequar uma visualização.

Decisão tecnológica desta versão:

* as seis stable serving Sheets são a camada estável BI; `DATA` é fonte analítica e `META` é auditoria/proveniência;
* Data Studio (antigo Looker Studio) é o motor analítico e de visualização, em um relatório com cinco páginas;
* Google Sites é a interface principal e incorpora a página correspondente do relatório onde há exploração interativa;
* Workspace Studio é somente automação operacional futura e não é necessário ao dashboard;
* GitHub, hashes, manifests e snapshots sustentam auditabilidade e reprodutibilidade;
* BigQuery só será reavaliado por escala; AppSheet, somente por necessidade transacional;
* Google Cloud, Looker Core e Data Studio Pro não são necessários nesta versão.

## Arquitetura e proveniência

`FONTES PÚBLICAS → ROBÔ/GitHub Actions → Bronze → Silver → Gold/RAG/Reconciliation → snapshots imutáveis + manifests → seis stable servings → Data Studio → Google Sites`.

O caminho conceitual reverso de auditoria é `dado exibido → serving DATA → snapshot → Gold/Silver/Bronze → fonte original → run/batch/hash`. Snapshot é uma projeção imutável identificada pelo conteúdo; manifest registra identidade, schema, contagens, hashes, software e proveniência; hash permite detectar divergência; proveniência permite rastrear origem e transformação. “Produto analítico derivado” significa uma interface reconstruível que não se torna registro canônico.

## Relatório Data Studio

Há um relatório principal multipágina:

1. **Visão geral** — cards calculados a partir das fontes (eventos, anos/métricas SIOPE, candidatos, fontes), status de execução, warnings, STOP e readback. Números não são hardcoded.
2. **SIOPE** — seletor de `metric_id`, série `year → metric_value`, contexto de `metric_unit`, `annual_period`, `series_status`, cautela e tabela detalhada. Uma seleção não mistura unidades incompatíveis.
3. **Jornal Oficial** — totais e distribuições por data, edição e tipos documentais, filtros contratuais, tabela detalhada e `document_url` quando apropriado. Null permanece null.
4. **Reconciliação** — candidatos, status e tabela, sempre com banner: **MATCH_CANDIDATE NÃO REPRESENTA IDENTIDADE FINANCEIRA COMPROVADA.** Não há risco arbitrário nem indicadores `MATCH`, `FINANCIAL_MATCH` ou `PROVEN_MATCH` para candidatos.
5. **Saúde e proveniência** — fontes, execuções e dicionário com os campos definidos no contrato.

Cada componente machine-readable registra pergunta, fonte, dimensão, métrica, agregação, filtro e cautela. Filtros são `REPORT_LEVEL`, `PAGE_LEVEL` ou `SOURCE_SPECIFIC`; não há filtro global artificial entre fontes incompatíveis. Não há campo calculado nesta versão: agregações seguras pertencem aos componentes e nenhuma fórmula produz compliance ou interpretação fiscal/jurídica.

## Google Sites

O Sites contém Home/Visão Geral, SIOPE/Financiamento, Jornal Oficial, Reconciliação, Saúde do Robô, Metodologia e Proveniência, Dicionário e Sobre. As cinco primeiras incorporam a página analítica correspondente; as demais priorizam texto e a tabela contratada do dicionário. Embed recomendado: largura 100%, altura 900 px, com revisão mobile. Navegação, cabeçalho, rodapé, aviso de atualização baseado apenas em campo temporal autoritativo e aviso de limitações são obrigatórios.

Metodologia explica em linguagem acessível as camadas, snapshot, manifest, hash, proveniência, produto derivado e separação da fonte de verdade. Sobre descreve finalidade e limitações sem afirmações institucionais não documentadas.

## Limites semânticos e UX

SIOPE permanece fechado em 2016–2024: 2016=P1, 2017–2024=P6, 2025 ausente. Não há inferência de compliance, cumprimento constitucional/MDE/Fundeb, auditoria fiscal ou causalidade. Métricas respeitam unidades e unidades incompatíveis nunca compartilham o mesmo eixo quantitativo.

Jornal não inventa campos, não preenche ausência nem promove documento a decisão jurídica. Reconciliação preserva `MATCH_CANDIDATE != FINANCIAL_IDENTITY`. O portal não conclui fraude, ilegalidade, irregularidade, responsabilidade individual ou identidade financeira.

A experiência deve ser sóbria, institucional, responsiva, acessível e orientada a perguntas. São vedados 3D, velocímetros decorativos, cores sem significado, cards gigantes sem contexto, excesso e redundância.

## FUTURE_OPERATIONAL_AUTOMATION e escala

Workspace Studio permanece `NOT_IMPLEMENTED`, `NO_ACTIVE_AUTOMATION`, `NO_SCHEDULE`, `NO_RECURRENCE`. Ideias futuras: avisar nova serving/snapshot, fonte BLOCKED, execução STOP ou criar tarefa de revisão.

BigQuery só será considerado com centenas de milhares/milhões de linhas, múltiplos municípios, consultas pesadas, atualização frequente ou inadequação comprovada de Sheets. AppSheet só com formulário, botão, aprovação, revisão humana, operação transacional ou aplicativo móvel. Nenhum é usado aqui.

## Encerramento formal

**PORTAL_ANALITICO_FINAL encerra a fase de engenharia necessária para o produto analítico atual baseado nos seis datasets contratados. Após o merge, a próxima etapa é a construção real do relatório no Data Studio e do portal no Google Sites. Não são previstas novas tasks BI individuais para páginas, gráficos ou datasets atuais, salvo correção de defeito, mudança de schema, novo dataset ou decisão arquitetural futura.**

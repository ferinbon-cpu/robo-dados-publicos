# M7 — SIOPE/Olinda exact-contract corroboration — 0.8.0

Status: `CORROBORATION_ONLY_NOT_AUTHORIZATION`

Este dossiê registra prior art e fontes institucionais que corroboram o contrato candidato do serviço SIOPE/Olinda. Ele **não autoriza coleta, não substitui evidência oficial observada pelo runtime e não permite pular os gates fail-closed**.

## Contrato candidato

Base oficial candidata:

`https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata`

Recurso candidato:

`Dados_Gerais_Siope(Ano_Consulta=@Ano_Consulta,Num_Peri=@Num_Peri,Sig_UF=@Sig_UF)`

Aliases documentados/corroborados:

- `@Ano_Consulta`
- `@Num_Peri`
- `@Sig_UF`
- `$format=json`

Forma completa corroborada por implementações independentes:

`https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata/Dados_Gerais_Siope(Ano_Consulta=@Ano_Consulta,Num_Peri=@Num_Peri,Sig_UF=@Sig_UF)?@Ano_Consulta={ano}&@Num_Peri={periodo}&@Sig_UF='{uf}'&$format=json`

`$select`, `$filter`, `$orderby` e paginação OData aparecem em clientes independentes, mas não são necessários para o primeiro GET mínimo.

## Corroborações principais

### StrategicProjects/tesouror

- Repositório: `https://github.com/StrategicProjects/tesouror`
- Arquivo: `R/siope.R`
- commit observado: `6781890d7174f4ab9cbf9ce7bfbd38dc723c949f`
- Observação: base `/versao/v1/odata`, recurso `Dados_Gerais_Siope`, parâmetros `Ano_Consulta`, `Num_Peri`, `Sig_UF`; suporte a filtro, ordenação, seleção e paginação.
- Classe: `SDK_CLIENTE` / `IMPLEMENTACAO_INDEPENDENTE`.

### StrategicProjects/tesouropy

- Repositório: `https://github.com/StrategicProjects/tesouropy`
- Arquivos: `src/tesouropy/siope.py`, `src/tesouropy/_core.py`
- commit observado para `siope.py`: `b49f5e46f03e199f336675bf370da231cc0fd57a`
- Observação: implementação Python do padrão `Resource(P1=@P1,...)?@P1=value&$format=json`, com a mesma família de recursos e aliases SIOPE.
- Classe: `SDK_CLIENTE`.

### BrenoNsm/painelEduca

- Repositório: `https://github.com/BrenoNsm/painelEduca`
- Arquivo: `coleta_siope.py`
- commit observado em pesquisa: `1123d97e...`
- Observação: `Dados_Gerais_Siope`, mesmos aliases, base `/odata`, leitura de `@odata.nextLink`.
- Classe: `IMPLEMENTACAO_INDEPENDENTE`.

### tuffyli/RA_work — Insper/Cátedra Ruth Cardoso

- Repositório: `https://github.com/tuffyli/RA_work`
- Arquivos observados: `Giovanni.R`, `00_siope_extract.R`
- commit observado em pesquisa: `3e75030...`
- Observação: forma literal do recurso com aliases, `$format=json` e `$select`; também usa outros recursos SIOPE com a mesma convenção.
- Classe: `IMPLEMENTACAO_INDEPENDENTE`.

### InstitutoSESI/dashboard-pne-react

- Repositório: `https://github.com/InstitutoSESI/dashboard-pne-react`
- Arquivo: `data_pipeline/src/siope_publication.py`
- Observação: `Indicadores_Siope` com a mesma família de parâmetros; validações de cobertura e crosswalk municipal.
- Classe: `IMPLEMENTACAO_INDEPENDENTE`.

### michaelferreir12345678/plataforma_fiscal_backend

- Repositório: `https://github.com/michaelferreir12345678/plataforma_fiscal_backend`
- Observação: cliente OData com paginação, `@odata.nextLink`, retries, timeout, codificação `%20` e conector SIOPE específico.
- Classe: `IMPLEMENTACAO_INDEPENDENTE` / `PRIOR_ART_ARQUITETURAL`.

## Fontes institucionais complementares

- FNDE Olinda SIOPE: aplicação oficial sob `www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/`.
- Portal brasileiro de Dados Abertos: catálogo SIOPE e tutorial de uso do formulário Olinda.
- Plataforma Antonieta de Barros/FNDE: produto `Dados Gerais - SIOPE`, com alternativa institucional de exportação em lote `exports/SIOPE/SIOPE_DADOS_GERAIS_SIOPE.txt.gz` observada na superfície pública.

## Relação com a evidência interna pinada

O run oficial `33005164515`, head `5653bb6920db6a534f18d1d40d899c8d44f4843a`, confirmou de forma passiva e sanitizada:

- 40 scripts lidos, 0 falhas de leitura;
- 4 ocorrências de callable, particionadas em 2 `location.hash` e 2 `ngRoute`, 0 ambíguas;
- ambas as ocorrências `location.hash` contêm os três nomes de parâmetros dentro de 1024 caracteres;
- `location.hash` e `$format` ficam do mesmo lado nas duas ocorrências;
- `/odata/` aparece do lado oposto nas duas ocorrências;
- nenhum GET de recurso foi realizado.

Isso continua provando apenas associação/localidade/ordem relativa; **não prova mesma expressão, dataflow ou contrato executável**.

## Decisão de engenharia

A combinação de evidência oficial passiva + corroboração independente forte justifica um próximo gate mais direto, mas ainda estritamente controlado:

1. review offline pinado deste dossiê e da evidência live;
2. design de um único GET exato, somente leitura, com valores públicos fixos e não-Limeira;
3. nenhuma paginação, nenhuma coleta recorrente, nenhuma promoção automática;
4. persistência apenas de metadados sanitizados: status, content-type, tamanho, hash, contagem de registros, nomes de campos e presença booleana de `@odata.nextLink`;
5. corpo, valores de registros, URL de nextLink e valores de query não podem ser persistidos.

O primeiro GET continua dependendo de workflow manual explícito.

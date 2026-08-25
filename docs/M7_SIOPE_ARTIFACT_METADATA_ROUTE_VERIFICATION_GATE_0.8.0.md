# M7 — SIOPE artifact metadata route verification gate — 0.8.0

## Evidência de origem

O runtime probe V2 (`32837068191`) observou, sem enviar, uma única requisição não-estática associada ao clique `Exportar artefato` do produto `Dados Gerais - SIOPE` (produto 20):

`GET https://www.fnde.gov.br/plataforma-antonieta-de-barros-api/products/data-products/20/artifact-metadata`

Essa observação prova uma rota candidata de **metadata**, não a rota final do artefato `.txt.gz`.

## Objetivo

Executar um único GET somente-leitura para a rota exata observada e validar:

- HTTP 200;
- JSON válido e limitado a 128 KiB;
- conteúdo apenas resumido por estrutura;
- presença eventual do caminho declarado `exports/SIOPE/SIOPE_DADOS_GERAIS_SIOPE.txt.gz`;
- URLs ou caminhos eventualmente presentes, sempre sanitizados e nunca chamados.

## O que pode ser persistido

Somente:

- status e content-type;
- tamanho da resposta;
- tipo da raiz JSON;
- nomes de chaves e caminhos de chaves de interesse;
- booleanos sobre produto/artefato;
- URLs sem query ou caminhos relativos;
- nomes das chaves de query, nunca seus valores.

O JSON bruto e o corpo bruto não são persistidos.

## Segurança

O gate não autoriza:

- download do artefato;
- GET de qualquer URL encontrada dentro da metadata;
- HEAD;
- cookies, headers ou bodies em evidência;
- Drive ou escrita remota;
- coleta ou processamento SIOPE;
- recorrência ou schedule.

Redirects são aceitos somente para HTTPS no mesmo host oficial `www.fnde.gov.br`.

## Estados

### PASS

`PASS_M7_SIOPE_ARTIFACT_METADATA_ROUTE_VERIFICATION_GATE`

Significa apenas que a rota de metadata respondeu 200 com JSON válido sob o contrato. Se o JSON expuser uma URL/caminho candidato de download, o próximo estágio será um **novo desenho de verificação dessa rota**, sem chamada automática.

### STOP

O gate fecha em STOP para host/URL divergente, redirect não permitido, timeout, erro HTTP, content-type inesperado, JSON inválido, resposta acima do limite ou resumo truncado.

## Workflow

`M7 SIOPE ARTIFACT METADATA ROUTE VERIFICATION GATE`

É manual e exige `confirm_artifact_metadata_route_verification=true`.

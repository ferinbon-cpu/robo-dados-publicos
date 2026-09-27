# M7 — SIOPE export call-site route discovery gate — 0.8.0

## Contexto

O gate `M7 SIOPE EXPORT CONTRACT DISCOVERY GATE` foi executado ao vivo no run `32795676213` e terminou com `PASS_M7_SIOPE_EXPORT_CONTRACT_DISCOVERY_GATE` e `DYNAMIC_EXPORT_CONTROL_OBSERVED_ROUTE_UNPROVEN`.

A página oficial da Plataforma Antonieta de Barros confirmou o produto `Dados Gerais - SIOPE` e o artefato declarado `exports/SIOPE/SIOPE_DADOS_GERAIS_SIOPE.txt.gz`. O bundle JavaScript oficial expôs identificadores específicos ligados à exportação — incluindo `getArtifactByDataProductId`, `getArtifactMetadataByDataProductId`, `downloadFile` e `exportKey` — mas nenhum template estático de rota foi comprovado.

## Objetivo deste subgate

Antes de introduzir browser automation ou interceptação de runtime, este gate faz uma análise estática mais focalizada: procura literais de rota apenas em janelas lexicais delimitadas ao redor dos identificadores de exportação já observados.

Esse desenho reduz o risco de promover rotas genéricas do bundle a rotas do artefato SIOPE.

## Escopo de rede

O gate pode fazer somente:

1. um GET da página oficial do produto na Antonieta;
2. GETs dos arquivos JavaScript explicitamente declarados nessa página, limitados pela configuração.

Não há chamada de rota candidata.

## Regras fail-closed

- somente HTTPS;
- host permitido: `www.fnde.gov.br`;
- máximo de 8 scripts declarados;
- máximo de 1 MiB por script e 6 MiB no total;
- no máximo 24 call-sites analisados;
- janela lexical de 2400 caracteres ao redor de cada identificador;
- rotas cross-origin são descartadas;
- query strings e fragments não são persistidos na evidência;
- assets estáticos não são promovidos a candidatos;
- uma rota fora da janela do call-site não é considerada evidência.

## Proibições

O gate não executa browser, JavaScript, clique, formulário ou CAPTCHA; não faz HEAD; não requisita a rota candidata; não baixa o `.txt.gz`; não usa OAuth/Drive; não coleta nem processa a fonte; não autoriza recorrência e não habilita schedule.

## Estados possíveis

`CALLSITE_ROUTE_CANDIDATE_OBSERVED_NOT_CALLED`: ao menos uma rota same-origin foi observada dentro da vizinhança lexical de um identificador de exportação. Isso ainda não prova que a rota entrega o artefato.

`EXPORT_CALLSITE_OBSERVED_ROUTE_UNPROVEN`: os call-sites foram encontrados, mas nenhuma rota candidata pôde ser comprovada estaticamente. Nesse caso, o próximo passo é desenhar um runtime route probe controlado.

Se nenhum dos identificadores-alvo for observado, o gate para em STOP.

## Próxima decisão

Uma rota candidata encontrada deverá passar por um gate separado de verificação antes de qualquer download. Se nenhuma rota for encontrada, somente então será avaliado um probe de runtime estritamente interceptado.

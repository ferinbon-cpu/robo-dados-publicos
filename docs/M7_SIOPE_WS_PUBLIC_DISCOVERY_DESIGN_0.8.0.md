# M7 SIOPE — desenho de descoberta pública do WS-SIOPE (0.8.0)

## Motivação

A trilha da Plataforma Antonieta de Barros mostrou que a página do produto e a metadata são públicas, mas o clique anônimo em `Exportar artefato` abre uma fronteira de autenticação gov.br. Por isso, a rota de artifact não deve ser perseguida por automação autenticada neste estágio.

Em paralelo, página oficial de downloads do SIOPE registra explicitamente em notas de versão a `Inclusão indicadores no WS-SIOPE`, o que justifica uma trilha separada de descoberta pública e read-only do webservice oficial.

## Escopo

O gate de descoberta deverá:

- usar somente GET;
- começar por páginas oficiais já conhecidas;
- seguir somente links explicitamente declarados nas páginas obtidas;
- limitar hosts a `www.fnde.gov.br` e `webservice.fnde.gov.br`;
- registrar apenas endpoints/documentação públicos explicitamente observados;
- não sintetizar paths, parâmetros ou operações;
- não submeter formulários;
- não contornar CAPTCHA;
- não autenticar;
- não capturar credenciais, cookies ou sessão;
- não baixar artefatos.

## Critério de sucesso

PASS somente se for observado um endpoint público do WS-SIOPE ou documentação oficial que declare seu contrato.

A mera presença da expressão `WS-SIOPE` não prova endpoint, método, parâmetros ou schema.

## Consequências

Mesmo com PASS, coleta e processamento continuam desautorizados. O passo seguinte seria uma verificação de contrato separada e limitada ao endpoint explicitamente observado.

Se nenhuma documentação ou endpoint público explícito for encontrado, o M7 deve parar para decisão humana sobre eventual desenho de fluxo autenticado — nunca automatizar gov.br por inferência.

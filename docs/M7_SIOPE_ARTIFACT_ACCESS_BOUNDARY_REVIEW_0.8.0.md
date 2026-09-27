# M7 SIOPE — revisão da fronteira de acesso ao artefato (0.8.0)

## Conclusão

O produto `Dados Gerais - SIOPE` e sua metadata de artefato são acessíveis anonimamente na superfície pública da Plataforma Antonieta de Barros. Entretanto, o diagnóstico DOM live do run `32855472741` mostrou que o clique anônimo em `Exportar artefato` introduz um controle novo `Entrar com gov.br`, apontando para `/plataforma-antonieta-de-barros/login` com a chave de query `returnUrl`.

Isso estabelece uma fronteira de autenticação antes de qualquer rota final de download observada.

## O que está provado

- página pública do produto: verificada;
- artefato declarado: verificado;
- metadata pública: verificada por GET controlado;
- metadata entregue ao frontend: verificada;
- clique único em `Exportar artefato`: executado;
- mudança DOM pós-clique: observada;
- controle `Entrar com gov.br`: observado;
- download nativo do Chrome: não iniciado;
- rota HTTP final do artefato: não provada;
- download do artefato: não realizado.

## Interpretação operacional

A existência de página pública e metadata pública não autoriza concluir que o arquivo seja exportável anonimamente. O estado correto do piloto é:

`PUBLIC_METADATA_VERIFIED + AUTHENTICATION_BOUNDARY_OBSERVED + ARTIFACT_ROUTE_UNPROVEN`

Não é permitido sintetizar uma URL de download a partir de `exports/SIOPE/` ou de outros fragmentos de storage observados.

## Política de segurança

Até nova decisão explícita:

- não automatizar login gov.br;
- não clicar em `Entrar com gov.br` em workflow;
- não capturar credenciais;
- não capturar cookies ou sessão autenticada;
- não reaproveitar sessão pessoal;
- não contornar CAPTCHA, MFA ou qualquer desafio humano;
- não habilitar coleta, processamento, recorrência ou schedule.

## Próximos caminhos permitidos

1. procurar documentação oficial de API/export público que não exija autenticação; ou
2. desenhar, em gate separado, um fluxo autenticado com autorização humana explícita, sem captura de credenciais e sem transformar autenticação pessoal em automação persistente.

Nenhum desses caminhos está autorizado automaticamente por esta revisão.

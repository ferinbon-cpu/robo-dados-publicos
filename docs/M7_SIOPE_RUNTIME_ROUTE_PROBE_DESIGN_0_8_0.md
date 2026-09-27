# M7 SIOPE runtime route probe design — 0.8.0

## Motivação

A análise estática do export da Plataforma Antonieta de Barros observou contexto de requisição e identificadores de exportação, mas não conseguiu provar uma rota direta ou composta. O run `32797644562` terminou com `EXPORT_REQUEST_CONTEXT_OBSERVED_ROUTE_UNPROVEN` e nenhum candidato foi chamado.

## Objetivo do próximo probe

Observar a requisição que a interface tenta produzir quando o controle **Exportar artefato** é acionado, sem permitir que essa requisição chegue à rede e sem receber corpo de resposta ou arquivo.

## Estratégia escolhida

- usar apenas Chrome/Chromium já disponível no runner;
- controlar o navegador por Chrome DevTools Protocol (CDP);
- perfil efêmero em diretório temporário;
- nenhuma instalação ou download de navegador;
- navegação inicial somente para a página oficial do produto 20;
- host inicial permitido: `www.fnde.gov.br`;
- requisições iniciais cross-origin devem ser abortadas;
- no máximo um clique no controle cujo texto é `Exportar artefato`;
- antes do clique, habilitar interceptação CDP `Fetch` no estágio `Request`;
- depois do clique, qualquer nova requisição deve ser interceptada e abortada antes da rede;
- downloads do navegador devem ser negados;
- somente metadados sanitizados podem ser registrados: método, rota sem query, nomes de query e tipo de recurso;
- cabeçalhos, cookies, valores de query, corpo de requisição e corpo de resposta são proibidos;
- PASS somente se houver exatamente um candidato deduplicado;
- zero ou múltiplos candidatos resultam em STOP;
- qualquer falha de interceptação ou ausência de navegador resulta em STOP;
- nenhum resultado deste probe autoriza coleta, processamento, recorrência ou schedule.

## Próximo estado possível

Se houver uma única rota interceptada e não enviada, o próximo estágio será `M7_SIOPE_ANTONIETA_ARTIFACT_ROUTE_VERIFICATION_DESIGN_0_8_0`. Se a rota continuar não comprovada, o processo para para revisão da evidência de runtime.

# M7 SIOPE — Artifact Download DOM Intent Diagnostics Gate 0.8.0

## Objetivo

Diagnosticar, de forma sanitizada e fail-closed, se o clique único já comprovado em **Exportar artefato** altera a interface e revela uma segunda intenção explícita de exportação (por exemplo, novo botão, link ou diálogo), depois de a metadata verificada ser entregue ao frontend.

## Evidência antecedente

O run `32851952092` do gate de eventos de download passou com `NO_BROWSER_DOWNLOAD_EVENT_OBSERVED`: uma requisição de metadata verificada foi enviada, nenhum `Browser.downloadWillBegin` ocorreu e nenhum artefato foi baixado.

## Contrato operacional

- exatamente um clique: o controle já comprovado `Exportar artefato`;
- nenhum segundo clique ou confirmação automática;
- download do navegador permanece `DENY`;
- somente assets estáticos oficiais e a rota exata de metadata já verificada podem seguir após o clique;
- toda outra requisição pós-clique é abortada antes da rede;
- compara somente formas DOM sanitizadas antes/depois;
- controles: tag, role, texto público curto, estado disabled e forma de href sem valores de query;
- diálogos: tag, role e texto público curto;
- máximo de 64 controles, 8 diálogos e saída limitada a 16 controles novos / 8 diálogos novos.

## Proibições

Não captura HTML bruto, valores de inputs, headers, cookies, request/response bodies ou valores de query. Não executa HEAD, download, Drive, coleta, processamento, recorrência ou schedule.

## Interpretação

`DOM_INTENT_CHANGE_OBSERVED` apenas prova mudança de interface após o clique. Não autoriza executar um novo controle. Qualquer segundo passo deve ser desenhado e autorizado em gate separado.

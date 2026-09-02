# TASK 028 — LOA OFFICIAL EQUIVALENCE PROBE DESIGN

## Objetivo

Preparar, em T0/offline, uma futura sondagem pública, pequena e read-only para verificar se existe uma representação oficial estruturada da LOA 2026 que possa evitar OCR integral.

A tarefa não executa a sondagem. Ela fixa o orçamento máximo, as superfícies permitidas, as regras de classificação e os STOPs antes de qualquer chamada de rede.

## Alvo

- LOA 2026 de Limeira;
- Lei Municipal 7.223/2025;
- fonte canônica já fixada: PDF integral de 466 páginas;
- SHA-256 canônico: `bc4c8bf4b2b1e8f59e880318c37ec7f7fbd4357a85a8b46c97750444dbf01d4b`.

## Superfícies iniciais permitidas

A futura prova deverá começar somente nas três superfícies oficiais já identificadas:

1. página de Orçamentos da Prefeitura;
2. Legislação Digital da Câmara;
3. Portal da Transparência da Prefeitura.

O plano admite no máximo 6 requisições, sendo 3 superfícies iniciais e reserva máxima de 3 follow-ups de candidatos. Paginação, retry automático, download de documento e qualquer efeito no Drive permanecem bloqueados.

## O que é apenas candidato

Um link CSV/XLS/XLSX/ODS/JSON/XML localizado em uma página oficial, mesmo com sinais de `LOA`, `2026` e `7.223`, é apenas:

`OFFICIAL_MACHINE_READABLE_CANDIDATE_NOT_EQUIVALENCE_PROVEN`

Ele não substitui o PDF e não autoriza ingestão.

ZIP recebe revisão específica. PDF continua documento, não machine-readable. HTML/TXT pode ser candidato textual, mas sua completude precisa ser demonstrada.

## Portal da Transparência

Dados de execução orçamentária são extremamente úteis para a etapa financeira posterior, mas não devem ser promovidos automaticamente a representação da LOA promulgada. Uma consulta genérica de despesas/receitas recebe:

`EXECUTION_DATA_NOT_ENACTED_LOA_EQUIVALENCE`

Isso não diminui seu valor analítico; apenas preserva a identidade documental correta.

## Regra de não ausência

Se a sondagem limitada não encontrar CSV/XLSX/JSON/XML, a conclusão permitida é:

`NO_MACHINE_READABLE_EQUIVALENT_CANDIDATE_OBSERVED_BOUNDED_PROBE`

Não é permitido concluir “não existe”. O resultado descreve apenas o que foi observado dentro do orçamento autorizado.

## Prova de equivalência

Mesmo um candidato estruturado precisa provar cumulativamente:

- origem oficial;
- exercício 2026;
- identidade com a Lei 7.223/2025;
- completude dos anexos;
- equivalência estrutural com a fonte canônica;
- hash e tamanho da representação usada.

Caso as seis provas sejam satisfeitas, o resultado ainda é apenas:

`CANDIDATE_PROOF_COMPLETE_REQUIRES_SEPARATE_AUTHORIZATION`

Assim, a prova não abre Silver automaticamente.

## Segurança

A implementação usa observações injetadas em testes. Nenhum HTTP client é chamado. Não há download, OCR, Drive, Bronze/Silver/Gold, serving ou publicação.

Hosts fora da allowlist são rejeitados. Estouro de orçamento de requisições ou candidatos também produz STOP.

## Próxima etapa

Depois do merge, uma eventual TASK seguinte poderá autorizar **uma única sondagem live read-only**, presa ao SHA auditado desta implementação. O resultado dessa sondagem deverá ser classificado sem follow-up automático. Se nenhum candidato equivalente for provado, a rota seguinte será a prova de OCR determinístico em amostra pequena definida pela TASK 027.

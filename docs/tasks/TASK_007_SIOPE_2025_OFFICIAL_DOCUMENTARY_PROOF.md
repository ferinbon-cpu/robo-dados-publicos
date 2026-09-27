# TASK 007 — prova documental oficial para SIOPE 2025

## Classificação

`T0_DOCUMENTARY_RESEARCH`. Esta tarefa não executa coleta de dados SIOPE, não lê ou escreve no Google Drive operacional, não calcula Gold e não publica objetos.

## Ponto de partida

A TASK 006 deixou 2025 como `PROVEN_STRUCTURAL_RECENT`: P1–P6 foram observados, o P6 possui schema exato de 52 campos e os 11 inputs usados pelo contrato Gold histórico estão presentes. Entretanto, fechamento anual e comparabilidade semântica continuavam `UNKNOWN`.

## Gate A — papel anual de P6 versus fechamento final

A documentação primária do FNDE resolve uma parte importante da dúvida. O Dicionário de Dados SIOPE 2019 declara que, a partir de 2017, os dados são bimestrais e o período 6 corresponde à consolidação anual. O Guia do FNDE para Novos Prefeitos 2025 usa a categoria de recibo `Anual`, estabelece a lógica de envio após o encerramento de cada bimestre e, para o exercício de 2024, trata a transmissão e validação do sexto bimestre como entrega de encerramento do exercício.

Isso prova o **papel documental de P6 como consolidação anual** no regime moderno. Não prova, porém, que o registro observado em 2025 esteja em um estado final que não possa mais mudar. O Tutorial SIOPE 2024 v2 documenta explicitamente a possibilidade de declaração retificadora do sexto bimestre mediante autorização da equipe técnica. Por isso, a conclusão correta é:

`P6_ANNUAL_CONSOLIDATION_PROVEN_FINALITY_UNKNOWN`.

O `annual_closure_status` permanece `UNKNOWN`; 2025 não entra na série anual fechada.

## Gate B — semântica dos 11 inputs Gold

O mesmo dicionário oficial fornece definições históricas para dez conceitos financeiros usados pelas oito fórmulas: previsão atualizada e realização da receita; dotação atualizada, empenho, liquidação e pagamento da despesa total; e os quatro conceitos equivalentes de despesa com educação.

Entretanto, o recurso OData 2025 usa aliases abreviados (`VAL_RECE_PREV_ATUA`, `VAL_DESP_DOTA_ATUA`, etc.). Não foi localizada, em fonte primária acessível nesta tarefa, uma tabela oficial aplicável a 2025 que prove alias por alias a identidade entre esses nomes e os campos do dicionário histórico. A página oficial atual confirma que existem pacotes de metadados 2025, mas seus conteúdos não ficaram acessíveis pelo conector documental utilizado. Além disso, não foi localizada uma definição primária oficial de `NUM_POPU`, necessária às duas métricas per capita.

Assim, o resultado do Gate B é `PARTIAL_NOT_PROVEN`, mantendo `semantic_comparability_status=UNKNOWN` e todas as oito métricas Gold de 2025 em `UNKNOWN`.

## Fontes oficiais pinadas por referência

- FNDE — Dicionário de Dados SIOPE 2019: <https://www.fnde.gov.br/phocadownload/sistemas/siope/Manuais/DICIONARIO%20DE%20DADOS%20SIOPE%202019.pdf>
- FNDE — Guia para Novos Prefeitos 2025: <https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/guia_prefeitos_2025.pdf>
- FNDE — Tutorial Básico SIOPE 2024 v2: <https://www.gov.br/fnde/pt-br/assuntos/sistemas/siope/media/Tutorial_Bsico_Siope_2024_v2.pdf>
- FNDE — Downloads / metadados SIOPE: <https://www.gov.br/fnde/pt-br/assuntos/sistemas/siope/downloads>

Os PDFs não são reproduzidos no repositório. A evidência pinada contém somente claims normalizados, URLs oficiais e limitações explícitas, preservando o escopo documental e evitando cópia desnecessária de documentos integrais.

## Estado resultante

- 2016–2024: série anual fechada permanece provada;
- 2025: `PROVEN_STRUCTURAL_RECENT`;
- P6 2025: disponibilidade provada; função documental de consolidação anual provada; finalidade/imutabilidade não provada;
- fechamento anual 2025: `UNKNOWN`;
- comparabilidade semântica: `UNKNOWN`;
- Gold 2025: `UNKNOWN`;
- 2026: `UNPROVEN_CURRENT_YEAR`;
- `future_batch_execution_authorized=false`.

## Próxima fronteira

A próxima etapa só deve promover 2025 se conseguir pinar evidência primária que (1) determine o estado de finalidade/retificação da declaração 2025 observada e (2) prove o mapeamento oficial dos 11 aliases OData, incluindo a definição e a regra temporal de `NUM_POPU`. Nenhuma semelhança de nome é suficiente para essa promoção.

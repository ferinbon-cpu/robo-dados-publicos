# TASK 010A — inspector offline de metadados SIOPE 2025

## Escopo e fronteira operacional

Esta fase T0 prepara, sem aquisição, a inspeção futura de um arquivo local do pacote oficial **`Metadados de 2025 — Municipal`**. Nenhum byte oficial foi baixado, nenhuma URL SharePoint foi acessada e nenhum GET, Drive, instalador, consulta financeira, persistência ou publicação foi executado na 010A. A issue #227 é requisito de trabalho, não evidência positiva.

Todos os archives usados pelos testes são artefatos **inteiramente sintéticos**, gerados deterministicamente em diretório temporário durante cada teste e nunca versionados. Resultados `PROVEN` obtidos sobre essas fixtures efêmeras provam somente que o analisador reconheceu o caso de teste: nunca constituem evidência sobre SIOPE, FNDE, Limeira, 2025 ou identidade financeira.

## Inspector

O comando offline futuro é:

```bash
python scripts/inspect_siope_2025_metadata_offline.py /caminho/local/artefato
```

Ele lê bytes locais, calcula SHA-256, identifica ZIP por assinatura, inventaria entradas e analisa somente texto UTF-8 nos formatos allowlisted `.csv`, `.json`, `.txt` e `.xml`. Não extrai para disco e nunca executa conteúdo. A extensão externa não determina o tipo real.

Antes de carregar os bytes, o inspector consulta o tamanho do archive local e aplica o limite conservador padrão de 128 MiB. Antes de ler uma entrada, rejeita caminho absoluto ou com `..`, profundidade excessiva, symlink, extensão ativa/executável, formato não allowlisted, excesso de entradas, tamanho individual ou total excedido e razão de compressão anormal. Arquivos corrompidos, conteúdo ativo por magic bytes e texto inválido encerram com `STOP_TASK_010A_*`.

## Alvos e matriz futura

O reconhecimento sintético cobre `NUM_POPU` e os dez aliases financeiros listados no contrato da TASK 010. A matriz está preparada com as colunas `field`, `presence`, `definition`, `source`, `temporal_rule`, `conceptual_bridge` e `decision`; somente os estados `PROVEN`, `PARTIAL`, `NOT_FOUND`, `AMBIGUOUS` e `NOT_APPLICABLE` são admitidos. O marcador `synthetic_only` impede que a saída de teste seja confundida com evidência canônica.

## Estado preservado

- `0.7.0 = ACTIVE` e `0.8.0 = CANDIDATE`;
- `2025 = PROVEN_STRUCTURAL_RECENT`;
- `S1_NUM_POPU = NOT_PROVEN`;
- `S2_FINANCIAL_ALIAS_BRIDGE = NOT_PROVEN`;
- `annual_closure_status = UNKNOWN`;
- `semantic_comparability_status = UNKNOWN`;
- `gold_metrics_status = UNKNOWN/BLOCKED`;
- série anual fechada = `2016–2024`;
- `2026 = UNPROVEN_CURRENT_YEAR`.

O gate `scripts/github_task_010a_siope_metadata_inspector_gate.py` fixa essa fronteira e falha diante de aquisição oficial declarada, rede, autorização 010B, promoção semântica, fechamento, Gold 2025, inclusão de 2025 na série fechada, autorização de 2026 ou recorrência.

## Próximo gate permitido

A única continuação admissível é **preparar e revisar a 010B bounded remote acquisition** em mudança separada. A existência deste inspector não concede essa autorização, não autoriza aquisição e não substitui confirmação humana específica.

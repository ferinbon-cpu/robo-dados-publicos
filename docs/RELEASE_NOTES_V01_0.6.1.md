# SOFTWARE V01 0.6.1 CANDIDATE — M4E processamento controlado do Bronze

## Objetivo

Processar a edição 7310 já preservada no Bronze, sem acessar novamente a fonte pública e sem recriar ou alterar o PDF original.

## Contrato

- localizar o artefato somente pela referência privada registrada no estado remoto;
- exigir SHA-256 `78a23262023f6233cb59fdc78f1fadc196d0a7bbd52c418bbdd9244229f46680` e 16.952.899 bytes;
- esperar 76 páginas, 195.540 caracteres extraídos, 53 eventos Gold, 148 chunks RAG e 68 tarefas;
- parar antes de qualquer derivado se fonte, hash, tamanho ou métricas divergirem;
- não imprimir IDs do Drive;
- manter agenda e recorrência desligadas.

## Derivados planejados

- `02_SILVER`: páginas com texto minimizado;
- `03_GOLD`: eventos e fila de reconciliação;
- `04_DOCUMENTOS`: manifesto da edição;
- `05_RAG`: chunks minimizados.

Os nomes remotos incorporam o hash de cada derivado. Uma repetição só reutiliza um arquivo existente após baixar e comprovar conteúdo idêntico; divergência interrompe o gate.

## Segurança

O processamento não chama a URL de origem, não copia novamente o Bronze, não executa resolvers externos, não promove `MATCH_CANDIDATE` para identidade financeira e não habilita TDA.

## Promoção pendente

`M4E_FIRST_SOURCE_PROCESSING_LIVE_GATE_0_6_1`: executar uma única vez com confirmação manual específica e exigir `PASS_GITHUB_JOURNAL_PROCESSING_GATE`.

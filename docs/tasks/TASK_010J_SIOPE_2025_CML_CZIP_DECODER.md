# TASK 010J — decoder offline CML/CZIP SIOPE 2025

## Resultado

`LITERAL_OFFLINE_DECODER_IMPLEMENTED_SYNTHETICALLY_VALIDATED`

Esta task transforma o contrato canônico pinado em um parser Python offline. Ela não redescobre o algoritmo, não executa containers ou conteúdo interno, não acessa rede e não promove conclusões semânticas.

## Contrato reproduzido

A implementação valida a derivação SHA-1 peculiar de `UnicodeString`, a chave Blowfish de 32 bytes, o IV implícito DCP1COMPAT, o header cifrado de 32 bytes e o payload no offset 32. A decodificação lê chunks lógicos de 1025 bytes: blocos completos usam CBC com continuidade pelo último bloco cifrado completo; cada resto de 1 a 7 bytes usa XOR com o prefixo de `EncryptECB(CV)` e não avança o CV. Não há padding PKCS#5/PKCS#7.

O arquivo `config/siope_2025_cml_czip_codec_contract.v1.json` continua sendo a fonte normativa. Derivações intermediárias e constantes calculadas são comparadas ao contrato e qualquer drift termina em `STOP_TASK_010J_*`.

## Inspeção segura

O ZIP interno é processado somente em memória e nunca extraído. Antes de qualquer `read()` ou descompressão, a inspeção faz preflight completo do `infolist()`:

- exige assinatura ZIP;
- verifica CRC;
- bloqueia path traversal, caminhos absolutos e symlinks;
- aplica limites de quantidade, profundidade, tamanho por entrada, tamanho total e taxa de compressão;
- limita o arquivo a 128 MiB, cada membro a 8 MiB e o total declarado a 32 MiB;
- rejeita symlinks e qualquer special file que não seja arquivo regular ou diretório;
- em CML, aceita somente XML e rejeita declarações DTD e entity antes de qualquer análise;
- em CZIP, aceita somente HTML, CSS, GIF e ICO como bytes estáticos, sem renderização, interpretação ou decodificação;
- retorna somente nomes, tamanhos e hashes, sem imprimir conteúdo XML.

O tipo do container é passado explicitamente à API: permissões CZIP nunca são inferidas somente pela extensão de um membro interno. O outer ZIP recebe o mesmo preflight completo antes da leitura de qualquer CML/CZIP, e seu SHA-256 é calculado por streaming após o `stat` e a validação do limite de 128 MiB.

Os domínios de limites são deliberadamente separados. O outer ZIP mantém `max_compression_ratio = 100`. Os ZIPs internos decodificados usam `max_compression_ratio = 150`: o maior valor observado externamente no pacote oficial de referência foi `140.79133980582524` para `Metadados.xml`, e 150 é o limite conservador pinado acima desse caso legítimo. Essa observação externa não altera o status da validação local registrado abaixo.

A CLI recebe um caminho local explícito. Ela não procura nem baixa artefatos e não persiste bytes decodificados.

## Testes sintéticos

Os testes constroem ZIPs e containers determinísticos em runtime, incluindo CML XML-only e o shape CZIP estático com `images/`, três GIFs, favicon, HTML e CSS. Também cobrem limites exatos de chunk, múltiplos chunks, todos os tipos de remainder, tipos ativos ou inesperados, special files e casos fail-closed de framing, corrupção, CRC, paths e limites. Regressões distintas provam que o outer rejeita ratio acima de 100, enquanto o inner aceita o caso sintético próximo de 140,7913 e rejeita valores acima de 150. Spies provam que `read()`/`testzip()` não são chamados antes de um preflight rejeitar metadados inválidos. Nenhum CML, CZIP, XML ou ZIP oficial foi versionado.

## Validação do pacote real

`REAL_PACKAGE_VALIDATION = NOT_RUN_LOCAL_ARTIFACT_UNAVAILABLE`

O arquivo local `Metadados_Mun_2025.zip` com SHA-256 esperado `41511c141e1af025ae2b565085583d6a3ab7b4577862f8ebdc308605101c1e5b` não estava disponível nesta implementação. Portanto, os resultados históricos pinados de 146 containers, 146 headers, 146 ZIPs e 146 CRCs **não** são reivindicados como reproduzidos por este código.

## Estados preservados

- `0.7.0 = ACTIVE`;
- `0.8.0 = CANDIDATE`;
- `2025 = PROVEN_STRUCTURAL_RECENT`;
- `S1_NUM_POPU = NOT_PROVEN`;
- `S2_FINANCIAL_ALIAS_BRIDGE = NOT_PROVEN`;
- `annual_closure_status = UNKNOWN`;
- `semantic_comparability_status = UNKNOWN`;
- `gold_metrics_status = UNKNOWN/BLOCKED`;
- série anual fechada = `2016-2024`;
- `2026 = UNPROVEN_CURRENT_YEAR`.

## Limites e próximo gate

Esta task não decide `NUM_POPU`, os dez aliases financeiros, o fechamento anual ou Gold 2025. Não expande a série e não habilita recorrência. O próximo gate permitido é somente review semântico offline separado de `NUM_POPU` e dos dez aliases, depois da aceitação do parser. Gold 2025 permanece bloqueado.

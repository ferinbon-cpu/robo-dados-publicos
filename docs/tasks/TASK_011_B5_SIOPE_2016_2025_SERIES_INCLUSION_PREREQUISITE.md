# TASK 011 — pré-requisito B5 de inclusão na série

O gate preserva e confere a série fechada, ordenada e sem duplicatas de
`2016–2024`: 2016 usa o regime histórico P1 e 2017–2024 usam P6. Uma futura
linha 2025 somente poderá ser avaliada após B4 autorizado/computado, evidência
Gold com proveniência e aritmética validadas, comparabilidade semântica, QA de
regressão e uma decisão explícita de inclusão.

O gate não anexa linhas automaticamente. Decisão atual:
`STOP_2025_SERIES_INCLUSION_GOLD_NOT_ELIGIBLE`.

`candidate_2025` permanece ausente. O contrato separado de candidato fixa
2025/P6 Annual/SP/Limeira/352690 e reutiliza o contrato Gold canônico
`SIOPE_DADOS_GERAIS_LIMEIRA_ARITHMETIC_SUMMARY_GOLD_V1`, o `source_id` e os oito
IDs de métricas de `robo_dados_publicos/product/siope_historical.py`. Um candidato
futuro também precisará dos hashes SHA-256 de record, Silver e Gold, sem conter
valores financeiros neste contrato. O mapa histórico continua sendo apenas mapa
de regimes e seu validador permanece limitado a 2016–2024. Somente um candidato
válido com todos os pré-requisitos provados produz
`READY_2025_SERIES_INCLUSION_REQUIRES_SEPARATE_EXECUTION`, ainda com zero escrita,
append ou promoção.

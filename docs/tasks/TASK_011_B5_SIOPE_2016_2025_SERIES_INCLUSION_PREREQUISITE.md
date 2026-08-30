# TASK 011 — pré-requisito B5 de inclusão na série

O gate preserva e confere a série fechada, ordenada e sem duplicatas de
`2016–2024`: 2016 usa o regime histórico P1 e 2017–2024 usam P6. Uma futura
linha 2025 somente poderá ser avaliada após B4 autorizado/computado, evidência
Gold com proveniência e aritmética validadas, comparabilidade semântica, QA de
regressão e uma decisão explícita de inclusão.

O gate não anexa linhas automaticamente. Decisão atual:
`STOP_2025_SERIES_INCLUSION_GOLD_NOT_ELIGIBLE`.

`candidate_2025` permanece ausente. O contrato separado de candidato fixa
2025/P6 Annual/SP/Limeira/352690 e reutiliza o schema
`SIOPE_HISTORICAL_REGIME_MAP_V1` de `config/siope_historical_regimes.v1.json`
para validar proveniência e aritmética, sem conter valores. Somente um candidato
válido com todos os pré-requisitos provados produz
`READY_2025_SERIES_INCLUSION_REQUIRES_SEPARATE_EXECUTION`, ainda com zero escrita,
append ou promoção.

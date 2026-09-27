# Limeira Source Map V01 — discovery backlog

This map broadens ROBO_DADOS_PUBLICOS from an education-first pipeline into a general municipal public-data observatory for Limeira/SP.

## Tier A — municipal core

1. TDA Portal da Transparência — revenue, expenditure and related administrative transparency surfaces.
2. Jornal Oficial — núcleo de eventos/atos. Discovery determinístico implementado em 0.5.2; PDF → Bronze/Silver/Gold/RAG em 0.5.3; fila de reconciliação cross-source em 0.5.4; primeiros resolvers de TCE-SP/Contratos em 0.5.5; produção aguarda validação ao vivo das rotas e schemas reais.
3. Municipal contracts/procurement systems — contracts, amendments, suppliers, notices and awards.
4. Câmara / legislative information system — bills, opinions, proceedings, laws and requests for information.

## Tier B — external reconciliation

1. TCE-SP — detailed municipal revenues/expenditures, suppliers, restos a pagar and audit context.
2. Siconfi/STN — fiscal/accounting statements and cross-municipality comparability.
3. SIOPE/FNDE — education finance.
4. INEP / state education sources — education outcomes and school indicators.
5. IBGE and labor/economic official datasets — demographic and socioeconomic context.

## Tier C — thematic municipal/public datasets

Health, works, personnel, social assistance, mobility, environment, public safety and other policy domains.

## Acquisition priority rule

API > official bulk download > official table/query > structured HTML > textual PDF > complex PDF > image/OCR > browser automation.

A browser agent is a fallback acquisition tool. It is never authorized to bypass CAPTCHA or access controls. Human verification becomes an explicit STOP state and should trigger a search for an official alternative route.

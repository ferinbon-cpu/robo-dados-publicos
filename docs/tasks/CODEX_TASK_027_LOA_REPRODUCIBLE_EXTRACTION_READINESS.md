# TASK 027 — LOA REPRODUCIBLE EXTRACTION READINESS

## Objetivo

Fechar, em T0/offline, o desenho técnico que permitirá transformar a LOA 2026 canônica de Limeira em texto/dados reproduzíveis sem substituir a fonte oficial, sem adivinhar números e sem promover o F01 para Silver antes da hora.

A fonte canônica continua sendo o PDF oficial integral da Lei Municipal 7.223/2025, exercício 2026, com 466 páginas e SHA-256 fixado na TASK 025. A TASK 026 reconciliou o staging e manteve a LOA integral bloqueada porque esse PDF não possui camada textual extraível pelo parser atual.

## Ordem de preferência

A rota de extração deve obedecer a esta prioridade:

1. **equivalente oficial machine-readable**, se for localizado e sua equivalência integral for comprovada;
2. **equivalente oficial textual completo**, se preservar a identidade legal e todos os anexos;
3. **OCR determinístico auditado do PDF canônico**, somente como derivado da fonte.

A existência de um portal com dados orçamentários não basta para dizer que ele é equivalente à LOA promulgada. É preciso provar identidade legal, exercício, completude dos anexos e equivalência estrutural.

## Discovery público read-only realizado para o desenho

A consulta pública usada para orientar esta tarefa encontrou três superfícies oficiais relevantes:

- a página de Orçamentos da Prefeitura lista a Lei Municipal 7.223/25 e os anexos da LOA 2026;
- a Legislação Digital da Câmara confirma a Lei Ordinária 7.223/2025, de 28/11/2025, como LOA do exercício de 2026;
- o Portal da Transparência municipal oferece informações de execução orçamentária e financeira.

Esse discovery **não provou** uma representação machine-readable completa e estruturalmente equivalente aos 466 anexos da fonte canônica. Isso não autoriza concluir que ela não exista. A rota oficial continua sendo a primeira opção e qualquer futura sondagem operacional deverá ser separada e limitada.

## Contrato de equivalência oficial

Uma fonte alternativa oficial só pode substituir OCR como rota de extração se provar cumulativamente:

- origem oficial;
- exercício 2026;
- identidade com a Lei 7.223/2025;
- completude dos anexos;
- equivalência estrutural com a fonte canônica;
- hash e tamanho imutáveis da representação usada.

Se qualquer prova faltar, retornar STOP e não misturar essa representação com Silver.

## Contrato de OCR determinístico

Se a rota oficial estruturada não for provada, um futuro OCR deverá receber **exatamente** o PDF canônico de SHA-256 `bc4c8bf4b2b1e8f59e880318c37ec7f7fbd4357a85a8b46c97750444dbf01d4b` e 466 páginas.

Cada página deverá gerar uma linha de manifest contendo pelo menos:

- número da página;
- SHA-256 da imagem renderizada;
- SHA-256 do texto OCR;
- número de caracteres OCR;
- indicador de página em branco;
- nome e versão do engine;
- SHA-256 da configuração do engine;
- DPI de renderização;
- nome e versão do renderizador.

O conjunto aceito deve conter exatamente as páginas `1..466`, sem duplicidade e sem lacunas. Versões diferentes de engine/configuração ou renderização dentro do mesmo lote são proibidas.

## Regra para números críticos

OCR não autoriza reconstrução numérica automática. Dotação, fonte, natureza, valor, empenhado, liquidado ou pago que forem utilizados analiticamente precisam conservar localizador da página-fonte e passar por validação visual ou independente.

Enquanto isso não ocorrer, o campo deve permanecer `REVIEW_REQUIRED`.

Mesmo um candidato numérico revisado não é automaticamente Silver: a revisão só valida o candidato; a promoção continua dependente de reconciliação estrutural do lote inteiro.

## LLM/IA

LLM pode ajudar a classificar, localizar e explicar campos derivados depois que o texto auditável existir. Não pode preencher algarismos ausentes, corrigir silenciosamente OCR ou inventar uma linha orçamentária a partir do contexto.

## Efeitos e autorização

Esta tarefa não executa OCR, não baixa nova fonte, não acessa Drive pelo runtime, não escreve Bronze/Silver/Gold, não altera serving/site e não publica nada.

O discovery web usado para elaborar o desenho foi leitura externa ao runtime do repositório e fica registrado apenas como evidência de pesquisa; ele não é autorização para futura coleta automática.

## Próxima decisão operacional

Depois do merge desta tarefa, há duas rotas possíveis, ambas exigindo tarefa/autorizações separadas:

- uma prova bounded/read-only de equivalência oficial, para tentar evitar OCR; ou
- uma prova de OCR determinístico em amostra pequena e auditável antes de qualquer processamento integral das 466 páginas.

A preferência permanece: **fonte oficial estruturada antes de OCR**.

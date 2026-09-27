# TASK 267 — canonização do snapshot PNCP ITEMS 8/8

A TASK264 provou oito identidades JOM→PNCP exatas. As TASK265 e TASK266 resolveram a rota documentada de ITEMS para os oito controles.

Estado canonizado:

- 8/8 controles com HTTP 200 e lista JSON;
- 40 linhas de item sanitizadas;
- 28 linhas de material;
- 12 linhas de serviço;
- zero controle unresolved;
- todos os 40 itens observados estavam com `situacaoCompraItemNome = Em andamento` no instante bounded.

A fixture não replica corpos brutos nem descrições integrais. Para cada controle, preserva hash do corpo, hash da projeção ITEM_ALLOW, contagens, faixa de `numeroItem`, composição material/serviço e a soma descritiva dos campos `valorTotal`.

A soma de `valorTotal` dos itens é apenas agregação descritiva do retorno PNCP. Ela não é tratada como pagamento, execução orçamentária, homologação, reconciliação contábil ou ponte PNCP→TCE.

Nenhuma rede é executada nesta task. HISTORY, fonte orçamentária, contratos vinculados e TCE continuam separados.

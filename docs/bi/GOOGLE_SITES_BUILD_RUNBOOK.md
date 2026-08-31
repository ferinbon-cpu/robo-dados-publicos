# Runbook — construir o portal no Google Sites

## Sequência exata

1. Criar um Google Site em branco somente sob autorização operacional posterior.
2. Definir o título configurável do contrato; não tratá-lo como nome institucional irreversível.
3. Criar Home/Visão Geral, SIOPE/Financiamento, Jornal Oficial, Reconciliação, Saúde do Robô, Metodologia e Proveniência, Dicionário de Dados e Sobre o Projeto.
4. Criar Home com explicação curta, limitações, aviso de atualização e embed da página `VISAO_GERAL`.
5. Incorporar o relatório Data Studio com largura 100%, altura recomendada 900 px e navegação acessível.
6. Criar SIOPE e incorporar somente a página `SIOPE`, mantendo aviso 2016–2024 e unidades.
7. Criar Jornal e incorporar `JORNAL_OFICIAL`, explicando que null significa ausência/não extração documentada.
8. Criar Reconciliação, incorporar `RECONCILIACAO` e exibir em destaque “MATCH_CANDIDATE NÃO REPRESENTA IDENTIDADE FINANCEIRA COMPROVADA.”
9. Criar Saúde e incorporar `SAUDE_E_PROVENIENCIA`.
10. Criar Metodologia explicando Fontes → Bronze → Silver → Gold → BI → Serving → Data Studio, snapshots, manifests, hashes e produto derivado.
11. Criar Proveniência com o caminho dado exibido → serving → snapshot → camadas → fonte → run/batch/hash.
12. Criar Dicionário com explicação acessível e tabela/filtro alimentado por `BI_DICIONARIO__SERVING.DATA`.
13. Criar Sobre sem afirmações institucionais não documentadas; explicar finalidade e limites.
14. Revisar navegação, cabeçalho configurável, rodapé com versão/metodologia/proveniência e links internos.
15. Revisar versão mobile: embeds, tabelas, contraste, zoom, ordem de leitura e ausência de corte horizontal evitável.
16. Revisar permissões do Site, relatório e fontes; público do portal não recebe edição das servings.
17. Não publicar até o QA final estar integralmente concluído e uma autorização separada permitir publicação.

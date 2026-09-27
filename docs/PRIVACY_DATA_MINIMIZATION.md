# Minimização de dados pessoais em derivados

O observatório trabalha com documentos públicos, mas publicidade da fonte não significa que todo identificador pessoal deva ser replicado indefinidamente em bases derivadas ou RAG.

## Contrato atual
- Bronze: preserva o PDF oficial integral, por hash, como evidência.
- Silver/RAG/Gold: minimizam CPF, RG, e-mail e telefone quando reconhecidos.
- CNPJ: preservado por ser identificador de pessoa jurídica e relevante à análise de contratos/fornecedores.
- nomes próprios: não são removidos automaticamente na 0.5.3; podem ser essenciais em atos de pessoal e o sistema ainda não possui classificador de pessoa natural suficientemente validado para uma remoção automática segura.
- endereço pessoal: ainda não possui redator determinístico de alta precisão; deve entrar em fase posterior com fixtures reais antes de ser habilitado.

## Regra de segurança
Quando um novo padrão de identificador pessoal for encontrado, ele deve entrar como fixture/teste antes de ser usado em produção. Não usar LLM para alterar silenciosamente a evidência original.

# Release Notes — Software V01 / 0.2.0

## Entregue
- bootstrap Python;
- M4A: conector HTTP real e cliente Google Drive REST/OAuth;
- bootstrap OAuth PKCE preparado;
- CLI única;
- núcleo determinístico;
- SQLite de estado;
- regressão histórica V04–V17;
- documentação de arquitetura e segurança.

## Critério de aceite desta release
- `python main.py init-state` deve concluir sem erro;
- `python main.py selftest` deve retornar status PASS;
- `python -m unittest discover -s tests -v` deve retornar OK (8 casos nesta release);
- `python main.py status` deve reconstruir o estado sem depender de chat.

## Não entregue ainda
- execução automática externa;
- round-trip Google Drive via OAuth real (cliente implementado; autorização ainda pendente);
- conectores públicos em produção;
- camada LLM/RAG completa.

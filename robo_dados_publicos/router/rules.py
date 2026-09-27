import re

DOC_TERMS = ("documento", "ato", "lei", "norma", "onde", "carga horária", "carga horaria", "comitê", "comite", "fórum", "forum", "instituiu", "vigente")

def route_query(query: str) -> str:
    q = query.lower()
    has_doc = any(t in q for t in DOC_TERMS)
    # Uma referência a uma meta dentro de uma descrição documental (ex.: "Meta 6")
    # não transforma a pergunta em numérica. O sinal numérico exige pedido de valor.
    asks_value = (
        "qual a meta" in q or "qual é a meta" in q or "qual o percentual" in q
        or "qual é o percentual" in q or "percentual planejado" in q
        or "índice recente" in q or "indice recente" in q
        or bool(re.search(r"meta\s+(?:do índice|do indice)?\s*para\s+20\d{2}", q))
    )
    if has_doc and asks_value:
        return "HYBRID"
    if has_doc:
        return "RAG"
    if asks_value or any(t in q for t in ("meta", "percentual", "índice", "indice", "planejado")):
        return "SQL"
    return "RAG"

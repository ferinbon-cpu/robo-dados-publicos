from pathlib import Path

FAMILIES = {
    "A_2012_2014": {
        "required": ["Código da Escola", "Nome da Escola", "Anos Iniciais"],
        "mapping": {"codigo_inep": "H", "unidade": "I", "localizacao": "F", "dependencia": "G", "tnr_ai": "K"},
    },
    "B_2015": {
        "required": ["CO_ENTIDADE", "NO_ENTIDADE", "TNR_F14"],
        "mapping": {"codigo_inep": "F", "unidade": "G", "localizacao": "H", "dependencia": "I", "tnr_ai": "K"},
    },
    "C_2016": {
        "required": ["CODIGO", "NO_CODIGO", "FUN_AI_CAT4"],
        "mapping": {"codigo_inep": "F", "unidade": "G", "localizacao": "H", "dependencia": "I", "tnr_ai": "K"},
    },
}

def classify_extension(path):
    ext = Path(path).suffix.lower()
    if ext == ".xls": return {"status": "BLOQUEIO_PARSER_BIFF", "action": "STOP"}
    if ext != ".xlsx": return {"status": "FORMATO_NAO_RECONHECIDO", "action": "STOP"}
    return {"status": "INSPECIONAR_CABECALHO", "action": "CONTINUE"}

def classify_headers(headers):
    joined = " | ".join(str(x) for x in headers)
    for family, spec in FAMILIES.items():
        if all(term in joined for term in spec["required"]):
            return {"status": "MAPEADO", "family": family, "mapping": spec["mapping"]}
    return {"status": "DRIFT_DESCONHECIDO", "action": "STOP"}

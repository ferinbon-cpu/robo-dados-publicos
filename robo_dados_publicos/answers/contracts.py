from robo_dados_publicos.core.models import AnswerContract

FIELDS = ("status", "DADO", "CÁLCULO", "CORRESPONDÊNCIA", "INTERPRETAÇÃO", "CAUTELA", "FONTES")

def evidence_insufficient(caution, sources=()):
    return AnswerContract(status="EVIDENCIA_INSUFICIENTE", cautela=caution, fontes=tuple(sources))

def answered(dado="", calculo="", correspondencia="", interpretacao="", cautela="", fontes=()):
    return AnswerContract("ANSWERED", dado, calculo, correspondencia, interpretacao, cautela, tuple(fontes))

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Iterable

from robo_dados_publicos.core.models import AnswerContract


GOLD_CONTRACT = "SIOPE_DADOS_GERAIS_LIMEIRA_ARITHMETIC_SUMMARY_GOLD_V1"
SOURCE_ID = "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA"
EXPECTED_YEARS = tuple(range(2016, 2025))
EXPECTED_PERIOD_BY_YEAR = {year: (1 if year == 2016 else 6) for year in EXPECTED_YEARS}
EXPECTED_METRIC_IDS = (
    "receita_realizada_sobre_previsao_atualizada_pct",
    "despesa_paga_sobre_dotacao_atualizada_pct",
    "despesa_educacao_paga_sobre_dotacao_atualizada_educacao_pct",
    "participacao_educacao_na_despesa_empenhada_pct",
    "participacao_educacao_na_despesa_liquidada_pct",
    "participacao_educacao_na_despesa_paga_pct",
    "despesa_total_paga_por_habitante",
    "despesa_educacao_paga_por_habitante",
)

_METRIC_META = {
    "receita_realizada_sobre_previsao_atualizada_pct": {
        "label": "Receita realizada sobre previsão atualizada (%)",
        "calculation": "VAL_RECE_REAL / VAL_RECE_PREV_ATUA × 100",
        "interpretation": (
            "Compara a receita realizada com a previsão atualizada. Valores acima ou abaixo de 100% "
            "indicam realização acima ou abaixo da previsão, sem constituir juízo de qualidade fiscal."
        ),
    },
    "despesa_paga_sobre_dotacao_atualizada_pct": {
        "label": "Despesa paga sobre dotação atualizada (%)",
        "calculation": "VAL_DESP_PAGA / VAL_DESP_DOTA_ATUA × 100",
        "interpretation": (
            "Mostra a proporção da dotação atualizada que chegou ao estágio de pagamento no exercício."
        ),
    },
    "despesa_educacao_paga_sobre_dotacao_atualizada_educacao_pct": {
        "label": "Despesa de educação paga sobre dotação atualizada da educação (%)",
        "calculation": "VL_DESP_PAGA_EDU / VL_DESP_DOTA_ATUA_EDU × 100",
        "interpretation": (
            "Mostra a proporção da dotação atualizada da educação que chegou ao estágio de pagamento."
        ),
    },
    "participacao_educacao_na_despesa_empenhada_pct": {
        "label": "Participação da educação na despesa empenhada (%)",
        "calculation": "VL_DESP_EMPE_EDU / VAL_DESP_EMPE × 100",
        "interpretation": "Expressa a participação relativa da educação na despesa total empenhada.",
    },
    "participacao_educacao_na_despesa_liquidada_pct": {
        "label": "Participação da educação na despesa liquidada (%)",
        "calculation": "VL_DESP_LIQU_EDU / VAL_DESP_LIQU × 100",
        "interpretation": "Expressa a participação relativa da educação na despesa total liquidada.",
    },
    "participacao_educacao_na_despesa_paga_pct": {
        "label": "Participação da educação na despesa paga (%)",
        "calculation": "VL_DESP_PAGA_EDU / VAL_DESP_PAGA × 100",
        "interpretation": "Expressa a participação relativa da educação na despesa total paga.",
    },
    "despesa_total_paga_por_habitante": {
        "label": "Despesa total paga por habitante",
        "calculation": "VAL_DESP_PAGA / NUM_POPU",
        "interpretation": "Divide a despesa total paga pela população informada no registro SIOPE.",
    },
    "despesa_educacao_paga_por_habitante": {
        "label": "Despesa de educação paga por habitante",
        "calculation": "VL_DESP_PAGA_EDU / NUM_POPU",
        "interpretation": "Divide a despesa de educação paga pela população informada no registro SIOPE.",
    },
}


class SiopeHistoricalProductError(ValueError):
    pass


def _stop(code: str) -> None:
    raise SiopeHistoricalProductError(f"STOP_M8_SIOPE_HISTORICAL_PRODUCT_{code}")


def _as_int(value, code: str) -> int:  # noqa: ANN001
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        _stop(code)


def _metric_text(value, metric_id: str) -> str:  # noqa: ANN001
    if value is None or isinstance(value, bool):
        _stop(f"METRIC_VALUE_{metric_id}")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        _stop(f"METRIC_VALUE_{metric_id}")
    if not number.is_finite():
        _stop(f"METRIC_VALUE_{metric_id}")
    return str(value)


def _validate_payload(payload: dict) -> dict:
    if not isinstance(payload, dict):
        _stop("PAYLOAD_OBJECT_REQUIRED")
    if payload.get("gold_contract") != GOLD_CONTRACT:
        _stop("GOLD_CONTRACT")

    identity = payload.get("identity")
    if not isinstance(identity, dict):
        _stop("IDENTITY")
    if _as_int(identity.get("municipality_code"), "MUNICIPALITY_CODE") != 352690:
        _stop("MUNICIPALITY_CODE")
    if str(identity.get("municipality_name", "")).strip() != "Limeira":
        _stop("MUNICIPALITY_NAME")
    if str(identity.get("state", "")).strip().upper() != "SP":
        _stop("STATE")
    if str(identity.get("resource", "")).strip() != "Dados_Gerais_Siope":
        _stop("RESOURCE")

    year = _as_int(identity.get("year"), "YEAR")
    period = _as_int(identity.get("period"), f"PERIOD_{year}")
    if year not in EXPECTED_PERIOD_BY_YEAR:
        _stop(f"YEAR_{year}")
    if period != EXPECTED_PERIOD_BY_YEAR[year]:
        _stop(f"PERIOD_{year}")

    metrics = payload.get("metrics")
    if not isinstance(metrics, dict) or tuple(metrics) != EXPECTED_METRIC_IDS:
        _stop("METRIC_IDS")
    normalized_metrics = {metric_id: _metric_text(metrics[metric_id], metric_id) for metric_id in EXPECTED_METRIC_IDS}

    semantic_scope = payload.get("semantic_scope")
    if not isinstance(semantic_scope, dict):
        _stop("SEMANTIC_SCOPE")
    for field in (
        "fiscal_audit_conclusion",
        "fundeb_compliance_conclusion",
        "imputation_performed",
        "mde_compliance_conclusion",
    ):
        if semantic_scope.get(field) is not False:
            _stop(field.upper())

    provenance = payload.get("provenance")
    if not isinstance(provenance, dict) or provenance.get("source_id") != SOURCE_ID:
        _stop("PROVENANCE_SOURCE")
    record_sha256 = str(provenance.get("record_sha256", "")).strip()
    silver_sha256 = str(provenance.get("silver_payload_sha256", "")).strip()
    if len(record_sha256) != 64 or len(silver_sha256) != 64:
        _stop("PROVENANCE_HASH")

    return {
        "year": year,
        "period": period,
        "metrics": normalized_metrics,
        "record_sha256": record_sha256,
        "silver_payload_sha256": silver_sha256,
    }


def validate_gold_series(payloads: Iterable[dict]) -> tuple[dict, ...]:
    rows = [_validate_payload(payload) for payload in payloads]
    years = [row["year"] for row in rows]
    if len(years) != len(set(years)):
        _stop("DUPLICATE_YEAR")
    rows.sort(key=lambda item: item["year"])
    if tuple(row["year"] for row in rows) != EXPECTED_YEARS:
        _stop("COVERAGE_YEARS")
    return tuple(rows)


def build_siope_historical_answers(payloads: Iterable[dict]) -> tuple[AnswerContract, ...]:
    series = validate_gold_series(payloads)
    correspondence = (
        "FNDE/SIOPE Dados_Gerais_Siope; Limeira/SP; série anual 2016–2024; "
        "2016 usa P1 e 2017–2024 usam P6; somente Gold aritmético validado."
    )
    caution = (
        "Série descritiva: não constitui auditoria fiscal, conclusão de cumprimento de MDE/Fundeb, "
        "identidade financeira ou explicação causal. Valores por habitante não são deflacionados neste adaptador."
    )
    answers = []
    for metric_id in EXPECTED_METRIC_IDS:
        meta = _METRIC_META[metric_id]
        values = "; ".join(f"{row['year']}: {row['metrics'][metric_id]}" for row in series)
        sources = tuple(
            (
                f"{SOURCE_ID}|Dados_Gerais_Siope|Limeira_SP|{row['year']}/P{row['period']}|"
                f"record_sha256={row['record_sha256']}|silver_sha256={row['silver_payload_sha256']}"
            )
            for row in series
        )
        answers.append(
            AnswerContract(
                status="ANSWERED",
                dado=f"{meta['label']}. Série: {values}",
                calculo=meta["calculation"],
                correspondencia=correspondence,
                interpretacao=meta["interpretation"],
                cautela=caution,
                fontes=sources,
            )
        )
    return tuple(answers)

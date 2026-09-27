def canonical_identity(entity, period, source_code, application_code, accounting_nature, regime_id):
    return "|".join(map(str, [entity, period, source_code, application_code, accounting_nature, regime_id]))

def may_promote_to_execution(record: dict, expected_application="2607004") -> bool:
    required = {"application_code", "stage", "value"}
    if not required.issubset(record):
        return False
    return str(record["application_code"]) == str(expected_application) and str(record["stage"]).lower() in {"empenhado", "liquidado", "pago"}

def same_accounting_identity(a: dict, b: dict) -> bool:
    keys = ("entity", "period", "source_code", "application_code", "accounting_nature", "regime_id")
    return all(str(a.get(k, "")) == str(b.get(k, "")) for k in keys)

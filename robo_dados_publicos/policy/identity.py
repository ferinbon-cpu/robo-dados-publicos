def classify_identity(same_entity, same_period, same_value, compatible_label, explicit_act=False, official_transition=False):
    if explicit_act or (same_entity and same_period and same_value and compatible_label):
        return "A"
    if official_transition:
        return "B"
    if compatible_label:
        return "C"
    return "D"

def is_executed_expense(record_type: str) -> bool:
    return record_type.lower() in {"empenhado", "liquidado", "pago"}

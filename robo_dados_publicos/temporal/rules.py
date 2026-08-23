from decimal import Decimal

def temporal_decision(incoming_period, incoming_hash, current_period=None, current_hash=None):
    if current_period is None:
        return "APPEND_NEWER_SNAPSHOT"
    if incoming_period == current_period:
        return "DUPLICATE_SKIP" if incoming_hash == current_hash else "REVISED_SAME_PERIOD"
    if incoming_period > current_period:
        return "APPEND_NEWER_SNAPSHOT"
    return "HISTORICAL_APPEND_NO_SUPERSEDE"

def reconcile(balance_begin, inflow, outflow, balance_end, tolerance=Decimal("0.01")):
    vals = [Decimal(str(x)) for x in (balance_begin, inflow, outflow, balance_end)]
    diff = vals[0] + vals[1] - vals[2] - vals[3]
    return abs(diff) <= tolerance

def aggregate_series(records, value_field, kind: str):
    """Fluxo soma; estoque usa apenas o snapshot mais recente."""
    if not records:
        return None
    ordered = sorted(records, key=lambda r: r["periodo"])
    if kind == "flow":
        return sum(Decimal(str(r[value_field])) for r in ordered)
    if kind == "stock":
        return Decimal(str(ordered[-1][value_field]))
    raise ValueError("kind deve ser 'flow' ou 'stock'")

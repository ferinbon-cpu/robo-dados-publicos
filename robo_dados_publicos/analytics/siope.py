from decimal import Decimal
import csv

def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def official_totals(rows, year):
    selected = [r for r in rows if str(r.get("ano")) == str(year) and str(r.get("eh_total_oficial")).lower() == "true"]
    return selected

def canonical_total(rows, year, code="3"):
    hits = [r for r in official_totals(rows, year) if str(r.get("codigo")) == str(code)]
    if len(hits) != 1:
        raise ValueError(f"esperado 1 total oficial código {code} para {year}; encontrado {len(hits)}")
    return hits[0]

def pct(numerator_centavos, denominator_centavos):
    den = Decimal(str(denominator_centavos))
    if den == 0: return None
    return (Decimal(str(numerator_centavos)) / den * Decimal("100")).quantize(Decimal("0.0001"))

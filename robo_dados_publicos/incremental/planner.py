def dependency_closure(changed_year: int):
    return {
        "silver": {changed_year},
        "gold_absolute": {changed_year},
        "gold_growth": {changed_year, changed_year + 1},
    }

def patch_decision(diff_count: int):
    return "APPLY_PATCH" if diff_count else "NO_CHANGE_IDEMPOTENT"

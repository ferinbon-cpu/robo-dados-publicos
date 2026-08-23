import csv

class EvidenceGraph:
    def __init__(self, edges):
        self.edges = list(edges)

    @classmethod
    def from_csv(cls, path):
        with open(path, encoding="utf-8-sig", newline="") as f:
            return cls(csv.DictReader(f))

    @staticmethod
    def _get(edge, canonical, legacy):
        return edge.get(canonical, edge.get(legacy))

    def exists(self, source, target, relation):
        return any(
            self._get(e, "source", "source_id") == source
            and self._get(e, "target", "target_id") == target
            and self._get(e, "relation", "relation_type") == relation
            for e in self.edges
        )

    def allowed_financial_identity(self, source, target):
        return any(
            self._get(e, "source", "source_id") == source
            and self._get(e, "target", "target_id") == target
            and self._get(e, "relation", "relation_type") == "financial_identity"
            and str(e.get("confidence", e.get("confidence_class", ""))).upper() == "A"
            for e in self.edges
        )

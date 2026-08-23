from pathlib import Path
from robo_dados_publicos.ingest.gates import decide_ingest
from robo_dados_publicos.state.registry import StateRegistry

class Engine:
    def __init__(self, state_db):
        self.state_db = state_db

    def ingest_local(self, path, logical_key=None, schema_known=True):
        p = Path(path)
        with StateRegistry(self.state_db) as state:
            known = {r[0] for r in state.con.execute("SELECT sha256 FROM files")}
            decision = decide_ingest(p, known, schema_known=schema_known)
            state.event("INGEST_DECISION", {"file": p.name, "decision": decision.decision, "sha256": decision.sha256})
            if decision.decision == "NEW_INGEST":
                state.register_file(decision.sha256, logical_key or p.stem, p.name, "BRONZE_REGISTERED")
            return decision

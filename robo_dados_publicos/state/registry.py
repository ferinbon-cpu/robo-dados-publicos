from pathlib import Path
import sqlite3, json
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS files (sha256 TEXT PRIMARY KEY, logical_key TEXT, file_name TEXT, status TEXT, first_seen TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS runs (run_id INTEGER PRIMARY KEY AUTOINCREMENT, started_at TEXT NOT NULL, finished_at TEXT, status TEXT NOT NULL, summary_json TEXT);
CREATE TABLE IF NOT EXISTS blockers (blocker_id TEXT PRIMARY KEY, status TEXT NOT NULL, description TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS events (event_id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, event_type TEXT NOT NULL, payload_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS source_state (source_id TEXT PRIMARY KEY, url TEXT NOT NULL, etag TEXT, last_modified TEXT, last_sha256 TEXT, last_status TEXT NOT NULL, remote_file_id TEXT, last_checked_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS reconciliation_tasks (task_id TEXT PRIMARY KEY, origin_event_id TEXT NOT NULL, origin_source_id TEXT NOT NULL, target_source TEXT NOT NULL, task_type TEXT NOT NULL, status TEXT NOT NULL, priority INTEGER NOT NULL, rationale TEXT NOT NULL, match_keys_json TEXT NOT NULL, search_hints_json TEXT NOT NULL, minimum_link_confidence TEXT NOT NULL, identity_rule TEXT NOT NULL, result_json TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS reconciliation_evidence (edge_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, source_node TEXT NOT NULL, target_node TEXT NOT NULL, relation TEXT NOT NULL, confidence TEXT NOT NULL, status TEXT NOT NULL, evidence_json TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
"""

class StateRegistry:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(self.path)
        self.con.executescript(SCHEMA)
        self.con.commit()

    def close(self): self.con.close()
    def __enter__(self): return self
    def __exit__(self, *args): self.close()

    @staticmethod
    def now(): return datetime.now(timezone.utc).isoformat()

    def set_meta(self, key, value):
        self.con.execute("INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))
        self.con.commit()

    def get_meta(self, key, default=None):
        row = self.con.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

    def has_hash(self, digest):
        return self.con.execute("SELECT 1 FROM files WHERE sha256=?", (digest,)).fetchone() is not None

    def register_file(self, digest, logical_key, file_name, status):
        self.con.execute("INSERT OR IGNORE INTO files VALUES(?,?,?,?,?)", (digest, logical_key, file_name, status, self.now()))
        self.con.commit()

    def set_blocker(self, blocker_id, status, description):
        self.con.execute("INSERT INTO blockers VALUES(?,?,?,?) ON CONFLICT(blocker_id) DO UPDATE SET status=excluded.status, description=excluded.description, updated_at=excluded.updated_at", (blocker_id,status,description,self.now()))
        self.con.commit()

    def blockers(self):
        return [dict(zip(("blocker_id","status","description","updated_at"), r)) for r in self.con.execute("SELECT blocker_id,status,description,updated_at FROM blockers ORDER BY blocker_id")]

    def start_run(self, status="RUNNING", summary=None):
        cur = self.con.execute(
            "INSERT INTO runs(started_at,status,summary_json) VALUES(?,?,?)",
            (self.now(), status, json.dumps(summary or {}, ensure_ascii=False, sort_keys=True)),
        )
        self.con.commit()
        return int(cur.lastrowid)

    def finish_run(self, run_id, status, summary=None):
        self.con.execute(
            "UPDATE runs SET finished_at=?, status=?, summary_json=? WHERE run_id=?",
            (self.now(), status, json.dumps(summary or {}, ensure_ascii=False, sort_keys=True), int(run_id)),
        )
        self.con.commit()


    def get_source_state(self, source_id):
        row = self.con.execute(
            "SELECT source_id,url,etag,last_modified,last_sha256,last_status,remote_file_id,last_checked_at FROM source_state WHERE source_id=?",
            (source_id,),
        ).fetchone()
        if not row:
            return None
        return dict(zip(("source_id","url","etag","last_modified","last_sha256","last_status","remote_file_id","last_checked_at"), row))

    def upsert_source_state(self, source_id, url, *, etag=None, last_modified=None, last_sha256=None, last_status="UNKNOWN", remote_file_id=None):
        self.con.execute(
            """INSERT INTO source_state(source_id,url,etag,last_modified,last_sha256,last_status,remote_file_id,last_checked_at)
               VALUES(?,?,?,?,?,?,?,?)
               ON CONFLICT(source_id) DO UPDATE SET
                 url=excluded.url, etag=excluded.etag, last_modified=excluded.last_modified,
                 last_sha256=excluded.last_sha256, last_status=excluded.last_status,
                 remote_file_id=excluded.remote_file_id, last_checked_at=excluded.last_checked_at""",
            (source_id, url, etag, last_modified, last_sha256, last_status, remote_file_id, self.now()),
        )
        self.con.commit()

    def list_source_states(self):
        rows = self.con.execute(
            "SELECT source_id,url,etag,last_modified,last_sha256,last_status,remote_file_id,last_checked_at FROM source_state ORDER BY source_id"
        )
        keys=("source_id","url","etag","last_modified","last_sha256","last_status","remote_file_id","last_checked_at")
        return [dict(zip(keys, r)) for r in rows]


    def upsert_reconciliation_task(self, task):
        payload = task.to_dict() if hasattr(task, "to_dict") else dict(task)
        now = self.now()
        self.con.execute(
            """INSERT INTO reconciliation_tasks(
                 task_id,origin_event_id,origin_source_id,target_source,task_type,status,priority,rationale,
                 match_keys_json,search_hints_json,minimum_link_confidence,identity_rule,result_json,created_at,updated_at
               ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(task_id) DO UPDATE SET
                 status=excluded.status, priority=excluded.priority, rationale=excluded.rationale,
                 match_keys_json=excluded.match_keys_json, search_hints_json=excluded.search_hints_json,
                 minimum_link_confidence=excluded.minimum_link_confidence, identity_rule=excluded.identity_rule,
                 updated_at=excluded.updated_at""",
            (
                payload["task_id"], payload["origin_event_id"], payload["origin_source_id"],
                payload["target_source"], payload["task_type"], payload["status"], int(payload["priority"]),
                payload["rationale"], json.dumps(payload.get("match_keys", {}), ensure_ascii=False, sort_keys=True),
                json.dumps(payload.get("search_hints", {}), ensure_ascii=False, sort_keys=True),
                payload["minimum_link_confidence"], payload["identity_rule"], None, now, now,
            ),
        )
        self.con.commit()

    def list_reconciliation_tasks(self, status=None):
        sql = "SELECT task_id,origin_event_id,origin_source_id,target_source,task_type,status,priority,rationale,match_keys_json,search_hints_json,minimum_link_confidence,identity_rule,result_json,created_at,updated_at FROM reconciliation_tasks"
        params = ()
        if status is not None:
            sql += " WHERE status=?"
            params = (status,)
        sql += " ORDER BY priority DESC, task_id"
        keys=("task_id","origin_event_id","origin_source_id","target_source","task_type","status","priority","rationale","match_keys_json","search_hints_json","minimum_link_confidence","identity_rule","result_json","created_at","updated_at")
        out=[]
        for row in self.con.execute(sql, params):
            item=dict(zip(keys,row))
            item["match_keys"]=json.loads(item.pop("match_keys_json"))
            item["search_hints"]=json.loads(item.pop("search_hints_json"))
            raw_result=item.pop("result_json")
            item["result"]=json.loads(raw_result) if raw_result else None
            out.append(item)
        return out

    def update_reconciliation_task(self, task_id, status, result=None):
        self.con.execute(
            "UPDATE reconciliation_tasks SET status=?, result_json=?, updated_at=? WHERE task_id=?",
            (status, json.dumps(result, ensure_ascii=False, sort_keys=True) if result is not None else None, self.now(), task_id),
        )
        self.con.commit()


    def upsert_reconciliation_evidence(self, edge):
        payload=edge.to_dict() if hasattr(edge, "to_dict") else dict(edge)
        now=self.now()
        self.con.execute(
            """INSERT INTO reconciliation_evidence(edge_id,task_id,source_node,target_node,relation,confidence,status,evidence_json,created_at,updated_at)
               VALUES(?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(edge_id) DO UPDATE SET confidence=excluded.confidence,status=excluded.status,evidence_json=excluded.evidence_json,updated_at=excluded.updated_at""",
            (payload["edge_id"],payload["task_id"],payload["source_node"],payload["target_node"],payload["relation"],payload["confidence"],payload["status"],json.dumps(payload.get("evidence",{}),ensure_ascii=False,sort_keys=True),payload.get("created_at") or now,now),
        )
        self.con.commit()

    def list_reconciliation_evidence(self, task_id=None):
        sql="SELECT edge_id,task_id,source_node,target_node,relation,confidence,status,evidence_json,created_at,updated_at FROM reconciliation_evidence"
        params=()
        if task_id is not None:
            sql += " WHERE task_id=?"; params=(task_id,)
        sql += " ORDER BY edge_id"
        keys=("edge_id","task_id","source_node","target_node","relation","confidence","status","evidence_json","created_at","updated_at")
        out=[]
        for row in self.con.execute(sql,params):
            item=dict(zip(keys,row)); item["evidence"]=json.loads(item.pop("evidence_json")); out.append(item)
        return out

    def event(self, event_type, payload):
        self.con.execute("INSERT INTO events(ts,event_type,payload_json) VALUES(?,?,?)", (self.now(),event_type,json.dumps(payload,ensure_ascii=False,sort_keys=True)))
        self.con.commit()

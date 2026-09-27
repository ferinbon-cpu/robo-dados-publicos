from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from datetime import datetime, timezone
import json


def _now():
    return datetime.now(timezone.utc).isoformat()


def _stable_id(parts) -> str:
    raw=json.dumps(parts,ensure_ascii=False,sort_keys=True,separators=(',',':'))
    return 'RECEDGE_' + sha256(raw.encode('utf-8')).hexdigest()[:24]


@dataclass(frozen=True)
class ReconciliationEvidence:
    edge_id: str
    task_id: str
    source_node: str
    target_node: str
    relation: str
    confidence: str
    status: str
    evidence: dict
    created_at: str

    def to_dict(self):
        return asdict(self)


class ReconciliationEvidenceAssembler:
    """Convert resolver candidates into non-promoted evidence edges.

    This layer is intentionally conservative: it never emits `financial_identity`.
    Resolver matches become documentary/supplier candidates only. Promotion to a
    stronger relation remains a separate V16/V17 gate.
    """

    def assemble(self, task: dict, result: dict) -> list[ReconciliationEvidence]:
        if result.get('status') != 'MATCH_CANDIDATE':
            return []
        target=result.get('target_source') or task.get('target_source') or ''
        origin=str(task.get('origin_event_id') or '')
        out=[]
        for idx,cand in enumerate(result.get('candidates') or []):
            if target == 'LIMEIRA_CONTRATOS':
                relation='documentary_correspondence_candidate'
                signals=set(cand.get('match_signals') or [])
                if 'CONTRACT_FULL' in signals and 'CNPJ' in signals:
                    confidence='A_DOCUMENTARY'
                elif 'CONTRACT_FULL' in signals or 'CNPJ' in signals:
                    confidence='B_DOCUMENTARY'
                else:
                    confidence='C_DOCUMENTARY'
                target_node='LIMEIRA_CONTRATO:' + str(cand.get('contract_number') or cand.get('row_hash') or idx)
            elif target == 'TCE_SP_DESPESAS':
                relation='supplier_expense_candidate'
                confidence='B_SUPPLIER' if str(cand.get('match_basis','')).startswith('CNPJ') else 'C_SUPPLIER'
                target_node='TCE_DESPESA:' + '|'.join(str(cand.get(k) or '') for k in ('year','commitment','stage','date','value'))
            else:
                continue
            payload={
                'resolver_status':result.get('status'),
                'target_source':target,
                'candidate':cand,
                'identity_rule':task.get('identity_rule'),
                'minimum_link_confidence':task.get('minimum_link_confidence'),
                'prohibited_promotion':'financial_identity',
            }
            edge_id=_stable_id([task.get('task_id'),target_node,relation,payload])
            out.append(ReconciliationEvidence(edge_id,str(task.get('task_id')),origin,target_node,relation,confidence,'CANDIDATE_ONLY',payload,_now()))
        return out

    @staticmethod
    def summary(edges: list[ReconciliationEvidence]) -> dict:
        counts={}
        for e in edges:
            counts[e.relation]=counts.get(e.relation,0)+1
        return {'status':'PASS_EVIDENCE_ASSEMBLY','edges':len(edges),'relations':counts,
                'financial_identity_edges':sum(1 for e in edges if e.relation=='financial_identity')}

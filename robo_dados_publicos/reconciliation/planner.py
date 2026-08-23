from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
import json
import re
from typing import Iterable, Mapping


CONTRACT_EVENT_TYPES = {
    "CONTRATO",
    "TERMO_ADITIVO_CONTRATO",
    "APOSTILAMENTO",
    "ATA_REGISTRO_PRECOS",
    "CONVENIO",
}
PROCUREMENT_EVENT_TYPES = {
    "CONTRATO",
    "TERMO_ADITIVO_CONTRATO",
    "ATA_REGISTRO_PRECOS",
    "EDITAL",
    "AVISO_LICITACAO",
}
LEGISLATIVE_EVENT_TYPES = {"LEI", "DECRETO", "RESOLUCAO", "PORTARIA"}


@dataclass(frozen=True)
class ReconciliationTask:
    task_id: str
    origin_event_id: str
    origin_source_id: str
    target_source: str
    task_type: str
    status: str
    priority: int
    rationale: str
    match_keys: dict
    search_hints: dict
    minimum_link_confidence: str
    identity_rule: str

    def to_dict(self) -> dict:
        return asdict(self)


class ReconciliationPlanner:
    """Turn extracted Journal Oficial events into a deterministic work queue.

    Planning never asserts that two records are identical. It only emits search/
    reconciliation tasks. A later connector/resolver must collect evidence and apply
    V16/V17 identity gates before a relationship can be promoted.
    """

    TARGETS = {
        "LIMEIRA_CONTRATOS": {
            "url": "https://serv42.limeira.sp.gov.br/ncweb/cns_contratos_web_mestre/",
            "capability": "SEARCH_BY_YEAR_CONTRACT_OBJECT_SUPPLIER",
            "connector_state": "DISCOVERY_READY",
        },
        "TCE_SP_DESPESAS": {
            "url": "https://transparencia.tce.sp.gov.br/municipio/limeira",
            "capability": "EXPENSE_EVENTS_AND_SUPPLIER_CROSSCHECK",
            "connector_state": "DISCOVERY_READY",
        },
        "TDA_LIMEIRA": {
            "url": "https://transparencia.limeira.sp.gov.br/tdaportalclient.aspx?418",
            "capability": "MUNICIPAL_FINANCIAL_EXECUTION",
            "connector_state": "BLOCKED_CONNECTOR_DISCOVERY",
        },
        "LIMEIRA_LICITACOES": {
            "url": "https://www.limeira.sp.gov.br/licitacoes",
            "capability": "PROCUREMENT_DOCUMENTS",
            "connector_state": "DISCOVERY_READY",
        },
        "SIAVE_LIMEIRA": {
            "url": "https://siave.limeira.sp.leg.br/",
            "capability": "LEGISLATIVE_DOCUMENTS_AND_TRAMITATION",
            "connector_state": "DISCOVERY_READY",
        },
    }

    @staticmethod
    def _publication_year(event: Mapping) -> int | None:
        publication_date = str(event.get("publication_date") or "")
        m = re.match(r"^(\d{4})-", publication_date)
        return int(m.group(1)) if m else None

    @staticmethod
    def _identifier_year(value) -> int | None:
        years = re.findall(r"(?:19|20)\d{2}", str(value or ""))
        return int(years[-1]) if years else None

    @classmethod
    def _candidate_years(cls, event: Mapping) -> list[int]:
        years = []
        pub = cls._publication_year(event)
        if pub:
            years.append(pub)
        for key in ("contract_number", "process_number", "edital_number", "bidding_number", "act_number"):
            y = cls._identifier_year(event.get(key))
            if y:
                years.append(y)
        return sorted(set(years))

    @staticmethod
    def _clean(value):
        if value is None:
            return None
        value = " ".join(str(value).split()).strip()
        return value or None

    @staticmethod
    def _task_id(origin_event_id: str, target_source: str, task_type: str, match_keys: dict) -> str:
        material = json.dumps(
            [origin_event_id, target_source, task_type, match_keys],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return "RECTASK_" + sha256(material.encode("utf-8")).hexdigest()[:24]

    def _build(
        self,
        event: Mapping,
        *,
        target_source: str,
        task_type: str,
        priority: int,
        rationale: str,
        match_keys: dict,
        search_hints: dict,
        minimum_link_confidence: str = "A",
        identity_rule: str,
    ) -> ReconciliationTask:
        target = self.TARGETS[target_source]
        status = "READY_SEARCH" if target["connector_state"] != "BLOCKED_CONNECTOR_DISCOVERY" else "BLOCKED_CONNECTOR_DISCOVERY"
        event_id = str(event["event_id"])
        return ReconciliationTask(
            task_id=self._task_id(event_id, target_source, task_type, match_keys),
            origin_event_id=event_id,
            origin_source_id=str(event.get("source_id") or ""),
            target_source=target_source,
            task_type=task_type,
            status=status,
            priority=int(priority),
            rationale=rationale,
            match_keys=match_keys,
            search_hints={**search_hints, "target_url": target["url"], "target_capability": target["capability"]},
            minimum_link_confidence=minimum_link_confidence,
            identity_rule=identity_rule,
        )

    def plan_event(self, event: Mapping) -> list[ReconciliationTask]:
        event_type = str(event.get("event_type") or "").upper()
        publication_year = self._publication_year(event)
        candidate_years = self._candidate_years(event)
        contract_number = self._clean(event.get("contract_number"))
        process_number = self._clean(event.get("process_number"))
        bidding_number = self._clean(event.get("bidding_number"))
        edital_number = self._clean(event.get("edital_number"))
        act_number = self._clean(event.get("act_number"))
        contractor = self._clean(event.get("contractor"))
        cnpj = re.sub(r"\D", "", str(event.get("cnpj") or "")) or None
        object_text = self._clean(event.get("object_text"))
        value_brl = self._clean(event.get("value_brl"))
        contract_year = self._identifier_year(contract_number) or self._identifier_year(process_number) or publication_year
        procurement_year = self._identifier_year(bidding_number) or self._identifier_year(edital_number) or self._identifier_year(process_number) or publication_year
        act_year = self._identifier_year(act_number) or publication_year

        tasks: list[ReconciliationTask] = []

        if event_type in CONTRACT_EVENT_TYPES and any([contract_number, contractor, cnpj, object_text]):
            keys = {k: v for k, v in {
                "year": contract_year,
                "contract_number": contract_number,
                "cnpj": cnpj,
                "contractor": contractor,
            }.items() if v is not None}
            tasks.append(self._build(
                event,
                target_source="LIMEIRA_CONTRATOS",
                task_type="FIND_CONTRACT_RECORD",
                priority=100,
                rationale="Confirmar o ato publicado no cadastro municipal de contratos/convênios/atas/locações.",
                match_keys=keys,
                search_hints={k: v for k, v in {
                    "object_text": object_text,
                    "process_number": process_number,
                    "edital_number": edital_number,
                }.items() if v is not None},
                identity_rule="Não promover identidade por nome/objeto isolado. Preferir número do contrato + ano e, quando disponível, CNPJ/processo.",
            ))

        if event_type in CONTRACT_EVENT_TYPES and any([cnpj, contractor]) and candidate_years:
            keys = {k: v for k, v in {
                "candidate_years": candidate_years,
                "cnpj": cnpj,
                "contractor": contractor,
                "value_brl": value_brl,
            }.items() if v is not None}
            tasks.append(self._build(
                event,
                target_source="TCE_SP_DESPESAS",
                task_type="FIND_EXPENSE_EVENTS_FOR_SUPPLIER",
                priority=90,
                rationale="Procurar empenhos/liquidações/pagamentos do fornecedor no controle externo para reconciliação financeira.",
                match_keys=keys,
                search_hints={k: v for k, v in {
                    "contract_number": contract_number,
                    "process_number": process_number,
                }.items() if v is not None},
                identity_rule="Fornecedor igual não prova vínculo com o contrato. Exigir compatibilidade temporal e evidência adicional; valores próximos são apenas pista.",
            ))

        if event_type in CONTRACT_EVENT_TYPES and any([contract_number, process_number, cnpj, contractor]):
            keys = {k: v for k, v in {
                "year": contract_year,
                "contract_number": contract_number,
                "process_number": process_number,
                "cnpj": cnpj,
                "contractor": contractor,
            }.items() if v is not None}
            tasks.append(self._build(
                event,
                target_source="TDA_LIMEIRA",
                task_type="FIND_MUNICIPAL_FINANCIAL_EXECUTION",
                priority=95,
                rationale="Cruzar o ato com a execução financeira municipal assim que o contrato técnico do TDA estiver comprovado.",
                match_keys=keys,
                search_hints={"value_brl": value_brl} if value_brl else {},
                identity_rule="Somente promover execução quando houver chave financeira compatível e estágio explícito (empenhado/liquidado/pago); contrato publicado não equivale a gasto.",
            ))

        if event_type in PROCUREMENT_EVENT_TYPES and any([bidding_number, edital_number, process_number]):
            keys = {k: v for k, v in {
                "year": procurement_year,
                "bidding_number": bidding_number,
                "edital_number": edital_number,
                "process_number": process_number,
            }.items() if v is not None}
            tasks.append(self._build(
                event,
                target_source="LIMEIRA_LICITACOES",
                task_type="FIND_PROCUREMENT_DOCUMENTS",
                priority=85,
                rationale="Localizar edital, atas, comunicados, esclarecimentos e anexos do procedimento de contratação.",
                match_keys=keys,
                search_hints={"contractor": contractor} if contractor else {},
                minimum_link_confidence="B",
                identity_rule="Número de edital/processo compatível sustenta correspondência documental; identidade financeira continua sujeita a gate próprio.",
            ))

        if event_type in LEGISLATIVE_EVENT_TYPES and act_number:
            keys = {k: v for k, v in {"year": act_year, "act_number": act_number, "event_type": event_type}.items() if v is not None}
            tasks.append(self._build(
                event,
                target_source="SIAVE_LIMEIRA",
                task_type="FIND_LEGISLATIVE_OR_NORMATIVE_RECORD",
                priority=70,
                rationale="Buscar versão normativa/legislativa e eventual tramitação relacionada ao ato publicado.",
                match_keys=keys,
                search_hints={},
                minimum_link_confidence="B",
                identity_rule="Número/tipo/ano compatíveis permitem correspondência documental; preservar a distinção entre publicação executiva e proposição/tramitação legislativa.",
            ))

        # Stable order is part of the contract and makes retries/idempotency predictable.
        return sorted(tasks, key=lambda t: (-t.priority, t.target_source, t.task_id))

    def plan_events(self, events: Iterable[Mapping]) -> list[ReconciliationTask]:
        by_id: dict[str, ReconciliationTask] = {}
        for event in events:
            for task in self.plan_event(event):
                by_id[task.task_id] = task
        return sorted(by_id.values(), key=lambda t: (-t.priority, t.origin_event_id, t.target_source, t.task_id))

    @staticmethod
    def read_jsonl(path: str | Path) -> list[dict]:
        rows = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))
        return rows

    @staticmethod
    def write_jsonl(path: str | Path, tasks: Iterable[ReconciliationTask]) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for task in tasks:
                f.write(json.dumps(task.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")

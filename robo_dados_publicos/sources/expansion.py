from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
import json


LIFECYCLE_STATES = (
    "DISCOVERED",
    "CONTRACT_VALIDATED",
    "ONE_TIME_AUTHORIZED",
    "LIVE_VALIDATED",
    "RECURRENCE_ELIGIBLE",
)


class SourceExpansionError(ValueError):
    pass


def _https_url(value: object, field: str) -> str:
    text = str(value or "").strip()
    parsed = urlparse(text)
    if parsed.scheme != "https" or not parsed.netloc:
        raise SourceExpansionError(f"SOURCE_EXPANSION_HTTPS_REQUIRED:{field}")
    return text


@dataclass(frozen=True)
class PilotScope:
    municipality: str
    state: str
    municipality_code: str
    year: int
    period: str

    @classmethod
    def from_mapping(cls, raw: dict) -> "PilotScope":
        if not isinstance(raw, dict):
            raise SourceExpansionError("SOURCE_EXPANSION_PILOT_MAPPING_REQUIRED")
        municipality = str(raw.get("municipality", "")).strip()
        state = str(raw.get("state", "")).strip().upper()
        municipality_code = str(raw.get("municipality_code", "")).strip()
        period = str(raw.get("period", "")).strip()
        try:
            year = int(raw.get("year"))
        except (TypeError, ValueError) as exc:
            raise SourceExpansionError("SOURCE_EXPANSION_PILOT_YEAR_INVALID") from exc
        if not municipality or len(state) != 2 or not municipality_code.isdigit() or not period:
            raise SourceExpansionError("SOURCE_EXPANSION_PILOT_INVALID")
        if year < 2000 or year > 2100:
            raise SourceExpansionError("SOURCE_EXPANSION_PILOT_YEAR_INVALID")
        return cls(municipality, state, municipality_code, year, period)


@dataclass(frozen=True)
class SourceExpansionContract:
    source_id: str
    institution: str
    system: str
    public_surface_url: str
    official_description_url: str
    public_access: str
    domain: str
    themes: tuple[str, ...]
    lifecycle_state: str
    acquisition_route_status: str
    schema_status: str
    content_type_status: str
    collection_authorization: str
    recurrence_authorization: str
    schedule: str
    null_semantics: str
    financial_semantics: str
    pilot: PilotScope

    @classmethod
    def from_mapping(cls, raw: dict) -> "SourceExpansionContract":
        if not isinstance(raw, dict):
            raise SourceExpansionError("SOURCE_EXPANSION_SOURCE_MAPPING_REQUIRED")
        source_id = str(raw.get("source_id", "")).strip()
        institution = str(raw.get("institution", "")).strip()
        system = str(raw.get("system", "")).strip()
        public_access = str(raw.get("public_access", "")).strip()
        domain = str(raw.get("domain", "")).strip()
        lifecycle_state = str(raw.get("lifecycle_state", "")).strip()
        acquisition_route_status = str(raw.get("acquisition_route_status", "")).strip()
        schema_status = str(raw.get("schema_status", "")).strip()
        content_type_status = str(raw.get("content_type_status", "")).strip()
        collection_authorization = str(raw.get("collection_authorization", "")).strip()
        recurrence_authorization = str(raw.get("recurrence_authorization", "")).strip()
        schedule = str(raw.get("schedule", "")).strip()
        null_semantics = str(raw.get("null_semantics", "")).strip()
        financial_semantics = str(raw.get("financial_semantics", "")).strip()
        themes_raw = raw.get("themes", [])
        if not source_id or not source_id.replace("_", "").replace("-", "").isalnum():
            raise SourceExpansionError("SOURCE_EXPANSION_SOURCE_ID_INVALID")
        if not institution or not system or not public_access or not domain:
            raise SourceExpansionError("SOURCE_EXPANSION_IDENTITY_FIELDS_REQUIRED")
        if not isinstance(themes_raw, list) or not themes_raw:
            raise SourceExpansionError("SOURCE_EXPANSION_THEMES_REQUIRED")
        themes = tuple(str(value).strip() for value in themes_raw if str(value).strip())
        if not themes:
            raise SourceExpansionError("SOURCE_EXPANSION_THEMES_REQUIRED")
        if lifecycle_state not in LIFECYCLE_STATES:
            raise SourceExpansionError("SOURCE_EXPANSION_LIFECYCLE_INVALID")
        if acquisition_route_status not in {"UNPROVEN", "PROVEN"}:
            raise SourceExpansionError("SOURCE_EXPANSION_ROUTE_STATUS_INVALID")
        if schema_status not in {"UNPROVEN", "PROVEN"}:
            raise SourceExpansionError("SOURCE_EXPANSION_SCHEMA_STATUS_INVALID")
        if content_type_status not in {"UNPROVEN", "PROVEN"}:
            raise SourceExpansionError("SOURCE_EXPANSION_CONTENT_TYPE_STATUS_INVALID")
        if collection_authorization not in {"PROHIBITED", "ONE_TIME_AUTHORIZED"}:
            raise SourceExpansionError("SOURCE_EXPANSION_COLLECTION_AUTH_INVALID")
        if recurrence_authorization not in {"PROHIBITED", "ELIGIBLE_NOT_AUTHORIZED", "AUTHORIZED"}:
            raise SourceExpansionError("SOURCE_EXPANSION_RECURRENCE_AUTH_INVALID")
        if schedule not in {"DISABLED", "ENABLED"}:
            raise SourceExpansionError("SOURCE_EXPANSION_SCHEDULE_INVALID")
        if not null_semantics or not financial_semantics:
            raise SourceExpansionError("SOURCE_EXPANSION_SEMANTICS_REQUIRED")

        contract = cls(
            source_id=source_id,
            institution=institution,
            system=system,
            public_surface_url=_https_url(raw.get("public_surface_url"), "public_surface_url"),
            official_description_url=_https_url(raw.get("official_description_url"), "official_description_url"),
            public_access=public_access,
            domain=domain,
            themes=themes,
            lifecycle_state=lifecycle_state,
            acquisition_route_status=acquisition_route_status,
            schema_status=schema_status,
            content_type_status=content_type_status,
            collection_authorization=collection_authorization,
            recurrence_authorization=recurrence_authorization,
            schedule=schedule,
            null_semantics=null_semantics,
            financial_semantics=financial_semantics,
            pilot=PilotScope.from_mapping(raw.get("pilot", {})),
        )
        contract._validate_fail_closed()
        return contract

    def _validate_fail_closed(self) -> None:
        rank = LIFECYCLE_STATES.index(self.lifecycle_state)
        if rank < LIFECYCLE_STATES.index("ONE_TIME_AUTHORIZED") and self.collection_authorization != "PROHIBITED":
            raise SourceExpansionError("SOURCE_EXPANSION_COLLECTION_REQUIRES_AUTHORIZED_STATE")
        if self.collection_authorization == "ONE_TIME_AUTHORIZED":
            if self.acquisition_route_status != "PROVEN" or self.schema_status != "PROVEN" or self.content_type_status != "PROVEN":
                raise SourceExpansionError("SOURCE_EXPANSION_COLLECTION_REQUIRES_PROVEN_ROUTE_SCHEMA_CONTENT_TYPE")
        if self.recurrence_authorization != "PROHIBITED" and rank < LIFECYCLE_STATES.index("RECURRENCE_ELIGIBLE"):
            raise SourceExpansionError("SOURCE_EXPANSION_RECURRENCE_REQUIRES_ELIGIBLE_STATE")
        if self.schedule == "ENABLED" and self.recurrence_authorization != "AUTHORIZED":
            raise SourceExpansionError("SOURCE_EXPANSION_SCHEDULE_REQUIRES_RECURRENCE_AUTHORIZATION")

    @property
    def can_collect(self) -> bool:
        return (
            self.lifecycle_state in {"ONE_TIME_AUTHORIZED", "LIVE_VALIDATED", "RECURRENCE_ELIGIBLE"}
            and self.collection_authorization == "ONE_TIME_AUTHORIZED"
            and self.acquisition_route_status == "PROVEN"
            and self.schema_status == "PROVEN"
            and self.content_type_status == "PROVEN"
        )

    @property
    def can_schedule(self) -> bool:
        return (
            self.lifecycle_state == "RECURRENCE_ELIGIBLE"
            and self.recurrence_authorization == "AUTHORIZED"
            and self.schedule == "ENABLED"
        )


@dataclass(frozen=True)
class SourceExpansionGate:
    schema_version: int
    gate_id: str
    software_version: str
    release_status: str
    active_validated_version: str
    mode: str
    network: str
    remote_writes: str
    source_collection: str
    source_processing: str
    recurrence: str
    schedule: str
    source: SourceExpansionContract
    next_gate_requirements: tuple[str, ...]

    @classmethod
    def from_mapping(cls, raw: dict) -> "SourceExpansionGate":
        if not isinstance(raw, dict):
            raise SourceExpansionError("SOURCE_EXPANSION_GATE_MAPPING_REQUIRED")
        requirements = raw.get("next_gate_requirements", [])
        if not isinstance(requirements, list) or not requirements:
            raise SourceExpansionError("SOURCE_EXPANSION_NEXT_GATE_REQUIREMENTS_REQUIRED")
        gate = cls(
            schema_version=int(raw.get("schema_version", 0)),
            gate_id=str(raw.get("gate_id", "")).strip(),
            software_version=str(raw.get("software_version", "")).strip(),
            release_status=str(raw.get("release_status", "")).strip(),
            active_validated_version=str(raw.get("active_validated_version", "")).strip(),
            mode=str(raw.get("mode", "")).strip(),
            network=str(raw.get("network", "")).strip(),
            remote_writes=str(raw.get("remote_writes", "")).strip(),
            source_collection=str(raw.get("source_collection", "")).strip(),
            source_processing=str(raw.get("source_processing", "")).strip(),
            recurrence=str(raw.get("recurrence", "")).strip(),
            schedule=str(raw.get("schedule", "")).strip(),
            source=SourceExpansionContract.from_mapping(raw.get("source", {})),
            next_gate_requirements=tuple(str(x).strip() for x in requirements if str(x).strip()),
        )
        gate._validate_design_gate()
        return gate

    def _validate_design_gate(self) -> None:
        expected = {
            "schema_version": 1,
            "software_version": "0.8.0",
            "release_status": "CANDIDATE",
            "active_validated_version": "0.7.0",
            "mode": "DESIGN_ONLY",
            "network": "PROHIBITED",
            "remote_writes": "PROHIBITED",
            "source_collection": "PROHIBITED",
            "source_processing": "PROHIBITED",
            "recurrence": "PROHIBITED",
            "schedule": "DISABLED",
        }
        for field, value in expected.items():
            if getattr(self, field) != value:
                raise SourceExpansionError(f"SOURCE_EXPANSION_GATE_CONTRACT:{field}")
        if not self.gate_id:
            raise SourceExpansionError("SOURCE_EXPANSION_GATE_ID_REQUIRED")
        if self.source.lifecycle_state != "CONTRACT_VALIDATED":
            raise SourceExpansionError("SOURCE_EXPANSION_DESIGN_MUST_STOP_AT_CONTRACT_VALIDATED")
        if self.source.can_collect or self.source.can_schedule:
            raise SourceExpansionError("SOURCE_EXPANSION_DESIGN_CANNOT_AUTHORIZE_EXECUTION")

    def summary(self) -> dict:
        return {
            "status": "PASS_M7_SOURCE_EXPANSION_DESIGN_GATE",
            "gate_id": self.gate_id,
            "software_version": self.software_version,
            "active_validated_version": self.active_validated_version,
            "source_id": self.source.source_id,
            "system": self.source.system,
            "pilot": {
                "municipality": self.source.pilot.municipality,
                "state": self.source.pilot.state,
                "municipality_code": self.source.pilot.municipality_code,
                "year": self.source.pilot.year,
                "period": self.source.pilot.period,
            },
            "lifecycle_state": self.source.lifecycle_state,
            "acquisition_route_status": self.source.acquisition_route_status,
            "collection_authorized": self.source.can_collect,
            "recurrence_authorized": False,
            "schedule_enabled": self.source.can_schedule,
            "network_called": False,
            "remote_writes": "NONE",
        }


def load_source_expansion_gate(path: str | Path) -> SourceExpansionGate:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return SourceExpansionGate.from_mapping(raw)

from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REQUIRED_EXECUTION_EFFECTS={"CONTENT_READ","SHA256_HASH","BRONZE_CREATE_ONLY"}


def load_authorization(path): return json.loads(Path(path).read_text(encoding='utf-8'))


def is_authorized(manifest, *, folder_id, family, effect, maturity_ready, is_descendant=False):
    if not manifest.get('enabled') or manifest.get('control',{}).get('revoked'): return False
    scope=manifest.get('scope',{})
    folder_ok=folder_id in scope.get('folder_ids',[]) or (is_descendant and scope.get('include_descendants') is True)
    return bool(folder_ok and family in scope.get('families',[]) and effect in manifest.get('allowed_effects',[]) and maturity_ready)


def validate_manifest(manifest):
    if any(x in manifest.get('allowed_effects',[]) for x in manifest.get('forbidden_effects',[])): raise ValueError('STOP_AUTH_EFFECT_CONFLICT')
    if manifest.get('enabled') and not manifest.get('control',{}).get('owner_authorization_ref'): raise ValueError('STOP_ENABLED_AUTH_WITHOUT_OWNER_REF')
    return True


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    reasons: tuple[str,...]


def authorize_record(record: dict[str,Any], family: str|None, manifest: dict[str,Any]) -> AuthorizationDecision:
    validate_manifest(manifest)
    reasons=[]
    if manifest.get('enabled') is not True: reasons.append('AUTH_DISABLED')
    control=manifest.get('control') or {}
    if control.get('revoked') is True: reasons.append('AUTH_REVOKED')
    scope=manifest.get('scope') or {}
    if family not in set(scope.get('families') or []): reasons.append('FAMILY_NOT_AUTHORIZED')
    roots=set(scope.get('folder_ids') or []); parents=set(record.get('parent_ids') or []); ancestors=set(record.get('ancestor_folder_ids') or [])
    folder_ok=bool(roots & (parents|ancestors)) if scope.get('include_descendants') is True else bool(roots & parents)
    if not folder_ok: reasons.append('FOLDER_NOT_AUTHORIZED')
    if not REQUIRED_EXECUTION_EFFECTS.issubset(set(manifest.get('allowed_effects') or [])): reasons.append('REQUIRED_EFFECT_NOT_AUTHORIZED')
    if record.get('content_hydrated') is True: reasons.append('METADATA_PHASE_CONTENT_HYDRATION_BREACH')
    if not record.get('id'): reasons.append('MISSING_STABLE_FILE_ID')
    if record.get('unresolved_duplicate_signal') is True: reasons.append('UNRESOLVED_DUPLICATE_SIGNAL')
    return AuthorizationDecision(not reasons,tuple(reasons) if reasons else ('AUTHORIZED_FOLDER_FAMILY_EFFECTS',))

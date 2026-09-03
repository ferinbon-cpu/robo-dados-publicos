from __future__ import annotations
import json
from pathlib import Path


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

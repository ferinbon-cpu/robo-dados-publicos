from pathlib import Path
from robo_dados_publicos.storage.hashing import sha256_file
from robo_dados_publicos.core.models import IngestDecision

SUPPORTED = {".csv", ".xlsx", ".json", ".pdf", ".zip"}


def decide_ingest(path, known_hashes=None, schema_known=True) -> IngestDecision:
    p = Path(path)
    digest = sha256_file(p)
    known_hashes = set(known_hashes or [])
    if digest in known_hashes:
        return IngestDecision("DUPLICATE_SKIP", digest, "hash já registrado")
    ext = p.suffix.lower()
    if ext == ".xls":
        return IngestDecision("BLOQUEIO_PARSER_BIFF", digest, "formato XLS/BIFF legado requer parser explícito")
    if ext not in SUPPORTED:
        return IngestDecision("FORMATO_NAO_SUPORTADO", digest, f"extensão {ext or '<sem extensão>'}")
    if not schema_known:
        return IngestDecision("DRIFT_DESCONHECIDO", digest, "schema não reconhecido; enviar à quarentena")
    return IngestDecision("NEW_INGEST", digest, "novo arquivo aceito pelo gate")


def decide_version(known_hash: str | None, incoming_hash: str, logical_key_known=True) -> str:
    if not logical_key_known:
        return "NEW_INGEST"
    if known_hash and known_hash == incoming_hash:
        return "DUPLICATE_SKIP"
    return "NEW_VERSION_REVIEW"

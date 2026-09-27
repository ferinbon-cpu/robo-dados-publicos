"""Production adapters for TASK 018; construction occurs only after authorization."""
from __future__ import annotations

import hashlib
import json
import mimetypes
import tempfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from robo_dados_publicos.journal.official import JornalOficialLimeira
from robo_dados_publicos.journal.processing import JournalPdfProcessor
from robo_dados_publicos.orchestration.cloud_runner import CloudLayout
from robo_dados_publicos.reconciliation.resolvers import LimeiraContractsResolver, ReconciliationExecutor
from robo_dados_publicos.storage.drive_rest import DriveRESTClient, OAuthCredentials, TokenProvider


class DiscoveryContractError(RuntimeError):
    def __init__(self, report: dict):
        super().__init__("STOP_DISCOVERY_CONTRACT_BROKEN")
        self.status = "STOP_DISCOVERY_CONTRACT_BROKEN"
        self.report = {
            "status": report.get("status"),
            "year": report.get("year"),
            "month": report.get("month"),
            "requested_url": report.get("requested_url"),
            "pages_fetched": report.get("pages_fetched"),
            "reported_total_items": report.get("reported_total_items"),
            "count": report.get("count"),
        }


class JornalSourceAdapter:
    """Reuse official discovery and expose exact request telemetry."""

    def __init__(self, journal=None, opener=urlopen):
        self.journal = journal or JornalOficialLimeira()
        self.opener = opener

    def discover(self, family: dict, maximum_pages: int):
        if not isinstance(maximum_pages, int) or not 1 <= maximum_pages <= 50:
            raise ValueError("BAD_MAX_PAGES")
        report = self.journal.discover_month(
            int(family["year"]),
            int(family["month"]),
            max_pages=maximum_pages,
        )
        if report.get("status") != "PASS_DISCOVERY":
            raise DiscoveryContractError(report)
        pages = int(report.get("pages_fetched") or 0)
        rows = []
        for edition in report.get("editions") or []:
            rows.append(
                {
                    "source_id": edition["source_id"],
                    "logical_key": edition["logical_key"],
                    "file_name": edition.get("file_name"),
                    "url": edition["document_url"],
                    "publication_date": edition["publication_date"],
                    "allowed_hosts": list(family["allowed_hosts"]),
                    "edition": edition["edition"],
                    "source_page_url": edition["source_page_url"],
                    "archive_class": edition["archive_class"],
                }
            )
        telemetry = {
            "discovery_status": report["status"],
            "robots_get_count": pages,
            "index_get_count": pages,
            "pages_fetched": pages,
            "reported_total_items": report.get("reported_total_items"),
        }
        return rows, telemetry

    def get(self, url: str, maximum_bytes: int):
        req = Request(
            url,
            headers={"User-Agent": self.journal.user_agent, "Accept": "application/pdf"},
            method="GET",
        )
        with self.opener(req, timeout=self.journal.timeout) as response:
            content_type = (response.headers.get("Content-Type") or "").split(";", 1)[0].lower()
            data = response.read(maximum_bytes + 1)
            final_url = response.geturl()
        return data, {
            "https": urlparse(final_url).scheme == "https",
            "final_host": (urlparse(final_url).hostname or "").lower(),
            "content_type": content_type,
            "remote_get_count": 1,
        }


class JournalProcessorAdapter:
    """Run the mature JournalPdfProcessor and expose its canonical files/tasks."""

    # Keep reconciliation_tasks.jsonl as derived Gold evidence. 06_BANCOS is
    # reserved for the canonical StateRegistry SQLite state/snapshots.
    LAYERS = {
        "pages_silver.jsonl": "Silver",
        "events_gold.jsonl": "Gold",
        "reconciliation_tasks.jsonl": "Gold",
        "chunks_rag.jsonl": "RAG",
        "edition_manifest.json": "Documentos",
    }

    def __init__(self, processor=None):
        self.processor = processor or JournalPdfProcessor()

    def process(self, item: dict, data: bytes):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            pdf = root / "source.pdf"
            pdf.write_bytes(data)
            out = root / "derived"
            manifest = self.processor.process(
                pdf,
                edition=int(item["edition"]),
                publication_date=item.get("publication_date"),
                source_url=item["url"],
                out_dir=out,
                stage_bronze=False,
                plan_reconciliation=True,
            )
            if manifest.get("status") != "PASS_DOCUMENT_PROCESSING":
                error = RuntimeError(manifest.get("status") or "STOP_PROCESSING")
                error.status = manifest.get("status") or "STOP_PROCESSING"
                raise error
            layers, tasks = {}, []
            for filename, destination in self.LAYERS.items():
                path = out / filename
                if path.exists():
                    layers.setdefault(destination, []).append(
                        (f"{item['source_id']}_{filename}", path.read_bytes())
                    )
                if filename == "reconciliation_tasks.jsonl" and path.exists():
                    tasks = [
                        json.loads(line)
                        for line in path.read_text(encoding="utf-8").splitlines()
                        if line.strip()
                    ]
            return {"layers": layers, "tasks": tasks, "metrics": manifest}


class DriveCreateOnlyStore:
    """Create-only adapter over DriveRESTClient with mandatory hash readback."""

    def __init__(self, drive: DriveRESTClient, layout: CloudLayout, cache_dir: str | Path):
        self.drive = drive
        self.layout = layout
        self.cache = Path(cache_dir)
        self.cache.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_environment(cls, cache_dir):
        root = Path(__file__).resolve().parents[2]
        layout = CloudLayout.from_mapping(
            json.loads((root / "config/cloud.json").read_text(encoding="utf-8"))
        )
        return cls(
            DriveRESTClient(TokenProvider(OAuthCredentials.from_env())),
            layout,
            cache_dir,
        )

    def _parent(self, destination):
        return getattr(self.layout, destination.lower() + "_id")

    @staticmethod
    def _name(logical_key, suffix):
        return logical_key.replace("/", "_") + suffix

    def lookup(self, destination, logical_key, suffix=""):
        return self.lookup_name(destination, self._name(logical_key, suffix))

    def lookup_name(self, destination, name):
        found = self.drive.find_by_name(self._parent(destination), name)
        if len(found) > 1:
            raise RuntimeError("STOP_CREATE_ONLY_INVARIANT")
        if not found:
            return None
        local = self.cache / hashlib.sha256((destination + name).encode()).hexdigest()
        read = self.drive.get(found[0]["id"], local)
        return {**found[0], **read, "data": local.read_bytes(), "name": name}

    def get_by_id(self, file_id, *, cache_key="remote"):
        local = self.cache / hashlib.sha256((cache_key + str(file_id)).encode()).hexdigest()
        read = self.drive.get(file_id, local)
        return {**read, "data": local.read_bytes()}

    def load_named_file(self, destination, name, local_path):
        found = self.drive.find_by_name(self._parent(destination), name)
        if len(found) > 1:
            raise RuntimeError("STOP_CREATE_ONLY_INVARIANT")
        if not found:
            return None
        target = Path(local_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        read = self.drive.get(found[0]["id"], target)
        return {**found[0], **read, "path": str(target)}

    def create(self, destination, name, data, metadata):
        parent = self._parent(destination)
        found = self.drive.find_by_name(parent, name)
        digest = hashlib.sha256(data).hexdigest()
        if found:
            if len(found) != 1:
                raise RuntimeError("STOP_CREATE_ONLY_INVARIANT")
            read = self.readback(destination, name)
            if read["sha256"] != digest or read["bytes"] != len(data):
                raise RuntimeError("STOP_CREATE_ONLY_INVARIANT")
            return {"status": "REUSED_IDENTICAL", **read}
        local = self.cache / (hashlib.sha256(name.encode()).hexdigest() + ".upload")
        local.write_bytes(data)
        created = self.drive.put(
            local,
            name,
            parent,
            metadata.get("content_type")
            or mimetypes.guess_type(name)[0]
            or "application/octet-stream",
        )
        read = self.readback(destination, name)
        if read["sha256"] != digest or read["bytes"] != len(data):
            raise RuntimeError("STOP_MANIFEST_INTEGRITY")
        return {"status": "CREATED", **created, **read}

    def readback(self, destination, name):
        found = self.drive.find_by_name(self._parent(destination), name)
        if len(found) != 1:
            raise RuntimeError("STOP_MANIFEST_INTEGRITY")
        local = self.cache / hashlib.sha256(
            (destination + name + "readback").encode()
        ).hexdigest()
        return {**found[0], **self.drive.get(found[0]["id"], local)}


class LimeiraReconcilerAdapter:
    def __init__(self, executor=None):
        self.executor = executor

    def execute(self, task, work_dir, maximum_requests):
        if maximum_requests < 1:
            raise RuntimeError("PARTIAL_BATCH_SAFETY_BUDGET_REACHED")
        if self.executor is not None:
            result = self.executor.execute_task(task, work_dir=work_dir).to_dict()
            actual = int(result.pop("remote_request_count", 1))
            if actual > maximum_requests:
                raise RuntimeError("PARTIAL_BATCH_SAFETY_BUDGET_REACHED")
            return result, actual

        resolver = LimeiraContractsResolver()
        original = resolver._opener

        class CountingOpener:
            def __init__(inner):
                inner.count = 0

            def open(inner, request, **kwargs):
                if inner.count >= maximum_requests:
                    raise RuntimeError("PARTIAL_BATCH_SAFETY_BUDGET_REACHED")
                inner.count += 1
                return original.open(request, **kwargs)

        counted = CountingOpener()
        resolver._opener = counted
        result = ReconciliationExecutor(
            contracts_resolver=resolver
        ).execute_task(task, work_dir=work_dir).to_dict()
        return result, counted.count


def build_production_adapters(workspace):
    """Called only after authorization/preflight; credential construction is here."""
    workspace = Path(workspace)
    return (
        JornalSourceAdapter(),
        DriveCreateOnlyStore.from_environment(workspace / "drive-cache"),
        JournalProcessorAdapter(),
        LimeiraReconcilerAdapter(),
    )


def build_source_adapter():
    return JornalSourceAdapter()


def build_drive_store(workspace):
    return DriveCreateOnlyStore.from_environment(Path(workspace) / "drive-cache")

import argparse, json, tempfile, uuid, hashlib, os
from pathlib import Path
from robo_dados_publicos.qa.regression import RegressionSuite
from robo_dados_publicos.storage.hashing import sha256_file
from robo_dados_publicos.orchestration.engine import Engine
from robo_dados_publicos.state.registry import StateRegistry
from robo_dados_publicos.storage.drive_rest import OAuthCredentials, TokenProvider, GcloudTokenProvider, EnvironmentAccessTokenProvider, DriveRESTClient
from robo_dados_publicos.orchestration.cloud_runner import CloudLayout, CloudProductionRunner
from robo_dados_publicos.sources.inventory import load_source_inventory
from robo_dados_publicos.discovery.portal_probe import PortalProbe
from robo_dados_publicos.journal.official import JornalOficialLimeira
from robo_dados_publicos.journal.processing import JournalPdfProcessor
from robo_dados_publicos.reconciliation.planner import ReconciliationPlanner
from robo_dados_publicos.reconciliation.resolvers import ReconciliationExecutor
from robo_dados_publicos.release import (
    ACTIVE_VALIDATED_VERSION,
    CURRENT_CANDIDATE_VERSION,
    METHOD_VERSION,
    NEXT_ACTION,
    RELEASE_STATUS,
    SOFTWARE_VERSION,
)

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FIXTURES = PACKAGE_ROOT / 'tests' / 'fixtures'
DEFAULT_STATE = PACKAGE_ROOT / 'runtime' / 'robot_state.sqlite'
DEFAULT_CLOUD_CONFIG = PACKAGE_ROOT / 'config' / 'cloud.json'


def cmd_selftest(args):
    summary = RegressionSuite(args.fixtures).run()
    print(json.dumps({k:v for k,v in summary.items() if k!='results'}, ensure_ascii=False, indent=2))
    if args.verbose:
        for r in summary['results']:
            print(f"[{r['status']}] {r['test']} {r['detail']}")
    return 0 if summary['status']=='PASS' else 2

def cmd_hash(args):
    print(sha256_file(args.file)); return 0

def cmd_ingest(args):
    decision = Engine(args.state_db).ingest_local(args.file,args.logical_key,schema_known=not args.unknown_schema)
    print(json.dumps(decision.__dict__,ensure_ascii=False,indent=2)); return 0

def cmd_status(args):
    with StateRegistry(args.state_db) as st:
        data={
            'PROJECT_PHASE': st.get_meta('PROJECT_PHASE','SOFTWARE_V01_BOOTSTRAP'),
            'RELEASE_STATUS': RELEASE_STATUS,
            'LATEST_METHOD_VERSION': st.get_meta('LATEST_METHOD_VERSION', METHOD_VERSION),
            'LATEST_SOFTWARE_VERSION': st.get_meta('LATEST_SOFTWARE_VERSION', ACTIVE_VALIDATED_VERSION),
            'LATEST_SOFTWARE_CANDIDATE': st.get_meta('LATEST_SOFTWARE_CANDIDATE', CURRENT_CANDIDATE_VERSION),
            'blockers': st.blockers(),
        }
    print(json.dumps(data,ensure_ascii=False,indent=2)); return 0

def cmd_init_state(args):
    with StateRegistry(args.state_db) as st:
        st.set_meta('PROJECT_PHASE','SOFTWARE_V01_AUTONOMOUS_RUNTIME_READY')
        st.set_meta('LATEST_METHOD_VERSION', METHOD_VERSION)
        st.set_meta('LATEST_SOFTWARE_VERSION', ACTIVE_VALIDATED_VERSION)
        st.set_meta('LATEST_SOFTWARE_CANDIDATE', CURRENT_CANDIDATE_VERSION)
        st.set_meta('NEXT_ACTION', NEXT_ACTION)
        st.set_blocker('FOMENTO_ETI_EXECUTION','STOP_DATA_DEPENDENCY','V18 metodológica depende de evidência de execução específica do Fomento ETI/2607004.')
    print(args.state_db); return 0



def _drive_client(auth_mode):
    if auth_mode == 'gcloud':
        return DriveRESTClient(GcloudTokenProvider())
    if auth_mode == 'oauth-env':
        return DriveRESTClient(TokenProvider(OAuthCredentials.from_env()))
    if auth_mode == 'access-token-env':
        return DriveRESTClient(EnvironmentAccessTokenProvider())
    raise ValueError(auth_mode)

def cmd_drive_ls(args):
    client=_drive_client(args.auth)
    items=client.list_children(args.parent_id)
    print(json.dumps({"parent_id":args.parent_id,"count":len(items),"files":items},ensure_ascii=False,indent=2))
    return 0

def cmd_drive_roundtrip(args):
    client=_drive_client(args.auth)
    name=args.name or f"_ROBO_ROUNDTRIP_{uuid.uuid4().hex[:12]}.txt"
    payload=("ROBO_DADOS_PUBLICOS ROUNDTRIP\n"+name+"\n").encode('utf-8')
    expected=hashlib.sha256(payload).hexdigest()
    remote_id=None
    try:
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/name; src.write_bytes(payload)
            up=client.put(src,name,args.parent_id,'text/plain')
            remote_id=up['id']
            dest=Path(td)/('downloaded_'+name)
            got=client.get(remote_id,dest)
            after=client.find_by_name(args.parent_id,name)
            checks={
                'uploaded': bool(remote_id),
                'visible_after_upload': any(x.get('id')==remote_id for x in after),
                'sha256_match': got['sha256']==expected,
                'bytes_match': dest.read_bytes()==payload,
            }
        client.delete(remote_id)
        after_delete=client.find_by_name(args.parent_id,name)
        checks['deleted']=not any(x.get('id')==remote_id for x in after_delete)
        status='PASS' if all(checks.values()) else 'FAIL'
        out={
            'status':status,'auth':args.auth,'parent_id':args.parent_id,
            'remote_name':name,'remote_id':remote_id,'sha256':expected,'checks':checks
        }
        print(json.dumps(out,ensure_ascii=False,indent=2))
        return 0 if status=='PASS' else 3
    except Exception:
        if remote_id:
            try: client.delete(remote_id)
            except Exception: pass
        raise


def _load_cloud_layout(path):
    with open(path, 'r', encoding='utf-8') as f:
        return CloudLayout.from_mapping(json.load(f))

def cmd_cloud_preflight(args):
    client=_drive_client(args.auth)
    layout=_load_cloud_layout(args.cloud_config)
    runner=CloudProductionRunner(client,layout,args.fixtures)
    out=runner.preflight()
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 0 if out['status']=='PASS' else 4

def cmd_run(args):
    client=_drive_client(args.auth)
    layout=_load_cloud_layout(args.cloud_config)
    runner=CloudProductionRunner(client,layout,args.fixtures)
    out=runner.run(
        state_name=args.state_name,
        persist=not args.no_persist,
        write_log=not args.no_log,
        source_config=args.source_config,
        dry_run_sources=args.dry_run_sources,
    )
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 0 if out.get('status')=='PASS' else 5


def cmd_sources_validate(args):
    inventory=load_source_inventory(args.source_config)
    print(json.dumps({"status":"PASS", **inventory.summary()},ensure_ascii=False,indent=2))
    return 0


def cmd_portal_probe(args):
    probe = PortalProbe(timeout=args.timeout, max_bytes=args.max_bytes)
    out = probe.probe(args.url)
    payload = out.to_dict()
    if args.out:
        PortalProbe.write_json(out, args.out)
        payload["output_file"] = str(args.out)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if out.status == "PASS_DISCOVERY" else 6


def cmd_journal_discover(args):
    jo = JornalOficialLimeira(timeout=args.timeout)
    if args.year is not None or args.month is not None:
        if args.year is None or args.month is None:
            raise ValueError("YEAR_AND_MONTH_REQUIRED_TOGETHER")
        out = jo.discover_month(args.year, args.month, max_pages=args.max_pages)
    else:
        url = args.url or jo.MODERN_INDEX
        out = jo.discover_page(url, archive_class=args.archive_class)
    if args.emit_inventory:
        from robo_dados_publicos.journal.official import JournalEdition
        editions = [JournalEdition(
            edition=int(x["edition"]), publication_date=x.get("publication_date"),
            document_url=x["document_url"], source_page_url=x["source_page_url"],
            archive_class=x["archive_class"], label=x.get("label", ""),
        ) for x in out["editions"]]
        inv = jo.emit_disabled_inventory(editions)
        jo.write_json(inv, args.emit_inventory)
        out["inventory_file"] = str(args.emit_inventory)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out.get("status") == "PASS_DISCOVERY" else 7

def cmd_journal_process(args):
    processor = JournalPdfProcessor(
        min_total_chars=args.min_total_chars,
        min_page_chars=args.min_page_chars,
        sparse_page_ratio_stop=args.sparse_page_ratio_stop,
    )
    out = processor.process(
        args.pdf,
        edition=args.edition,
        publication_date=args.publication_date,
        source_url=args.source_url,
        out_dir=args.out_dir,
        stage_bronze=not args.no_stage_bronze,
        plan_reconciliation=not args.no_plan_reconciliation,
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out.get("status") == "PASS_DOCUMENT_PROCESSING" else 8


def cmd_reconciliation_plan(args):
    planner = ReconciliationPlanner()
    events = planner.read_jsonl(args.events_jsonl)
    tasks = planner.plan_events(events)
    if args.out:
        planner.write_jsonl(args.out, tasks)
    persisted = 0
    if args.state_db:
        with StateRegistry(args.state_db) as st:
            for task in tasks:
                st.upsert_reconciliation_task(task)
                persisted += 1
    summary = {
        "status": "PASS_RECONCILIATION_PLANNING",
        "events": len(events),
        "tasks": len(tasks),
        "ready_search": sum(1 for t in tasks if t.status == "READY_SEARCH"),
        "blocked_connector_discovery": sum(1 for t in tasks if t.status == "BLOCKED_CONNECTOR_DISCOVERY"),
        "persisted": persisted,
        "output_file": str(args.out) if args.out else None,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def cmd_reconciliation_status(args):
    with StateRegistry(args.state_db) as st:
        tasks = st.list_reconciliation_tasks(status=args.filter_status)
    print(json.dumps({"status":"PASS", "count":len(tasks), "tasks":tasks}, ensure_ascii=False, indent=2))
    return 0


def cmd_reconciliation_execute(args):
    executor = ReconciliationExecutor()
    out = executor.run_queue(
        args.state_db,
        work_dir=args.work_dir,
        limit=args.limit,
        targets=args.target,
        dry_run=args.dry_run,
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out.get("status", "").startswith("PASS_") else 9


def build_parser():
    p=argparse.ArgumentParser(prog='robo-dados-publicos')
    sub=p.add_subparsers(dest='cmd',required=True)
    s=sub.add_parser('selftest'); s.add_argument('--fixtures',default=str(DEFAULT_FIXTURES)); s.add_argument('-v','--verbose',action='store_true'); s.set_defaults(func=cmd_selftest)
    s=sub.add_parser('hash'); s.add_argument('file'); s.set_defaults(func=cmd_hash)
    s=sub.add_parser('ingest'); s.add_argument('file'); s.add_argument('--logical-key'); s.add_argument('--state-db',default=str(DEFAULT_STATE)); s.add_argument('--unknown-schema',action='store_true'); s.set_defaults(func=cmd_ingest)
    s=sub.add_parser('status'); s.add_argument('--state-db',default=str(DEFAULT_STATE)); s.set_defaults(func=cmd_status)
    s=sub.add_parser('init-state'); s.add_argument('--state-db',default=str(DEFAULT_STATE)); s.set_defaults(func=cmd_init_state)
    auth_choices=['gcloud','oauth-env','access-token-env']
    s=sub.add_parser('drive-ls'); s.add_argument('--parent-id',required=True); s.add_argument('--auth',choices=auth_choices,default=os.getenv('ROBO_DRIVE_AUTH','gcloud')); s.set_defaults(func=cmd_drive_ls)
    s=sub.add_parser('drive-roundtrip'); s.add_argument('--parent-id',required=True); s.add_argument('--name'); s.add_argument('--auth',choices=auth_choices,default=os.getenv('ROBO_DRIVE_AUTH','gcloud')); s.set_defaults(func=cmd_drive_roundtrip)
    s=sub.add_parser('cloud-preflight'); s.add_argument('--auth',choices=auth_choices,default=os.getenv('ROBO_DRIVE_AUTH','gcloud')); s.add_argument('--cloud-config',default=str(DEFAULT_CLOUD_CONFIG)); s.add_argument('--fixtures',default=str(DEFAULT_FIXTURES)); s.set_defaults(func=cmd_cloud_preflight)
    s=sub.add_parser('sources-validate'); s.add_argument('--source-config',required=True); s.set_defaults(func=cmd_sources_validate)
    s=sub.add_parser('portal-probe'); s.add_argument('url'); s.add_argument('--out'); s.add_argument('--timeout',type=float,default=15.0); s.add_argument('--max-bytes',type=int,default=2000000); s.set_defaults(func=cmd_portal_probe)
    s=sub.add_parser('journal-discover'); s.add_argument('--url'); s.add_argument('--year',type=int); s.add_argument('--month',type=int); s.add_argument('--archive-class',choices=['modern','legacy'],default='modern'); s.add_argument('--emit-inventory'); s.add_argument('--timeout',type=float,default=20.0); s.add_argument('--max-pages',type=int,default=8); s.set_defaults(func=cmd_journal_discover)
    s=sub.add_parser('journal-process'); s.add_argument('--pdf',required=True); s.add_argument('--edition',required=True,type=int); s.add_argument('--publication-date'); s.add_argument('--source-url'); s.add_argument('--out-dir',required=True); s.add_argument('--no-stage-bronze',action='store_true'); s.add_argument('--no-plan-reconciliation',action='store_true'); s.add_argument('--min-total-chars',type=int,default=120); s.add_argument('--min-page-chars',type=int,default=20); s.add_argument('--sparse-page-ratio-stop',type=float,default=0.8); s.set_defaults(func=cmd_journal_process)
    s=sub.add_parser('reconciliation-plan'); s.add_argument('--events-jsonl',required=True); s.add_argument('--out'); s.add_argument('--state-db'); s.set_defaults(func=cmd_reconciliation_plan)
    s=sub.add_parser('reconciliation-status'); s.add_argument('--state-db',default=str(DEFAULT_STATE)); s.add_argument('--filter-status'); s.set_defaults(func=cmd_reconciliation_status)
    s=sub.add_parser('reconciliation-execute'); s.add_argument('--state-db',default=str(DEFAULT_STATE)); s.add_argument('--work-dir',default=str(PACKAGE_ROOT / 'runtime' / 'reconciliation')); s.add_argument('--limit',type=int,default=10); s.add_argument('--target',action='append',choices=['LIMEIRA_CONTRATOS','TCE_SP_DESPESAS']); s.add_argument('--dry-run',action='store_true'); s.set_defaults(func=cmd_reconciliation_execute)
    s=sub.add_parser('run'); s.add_argument('--auth',choices=auth_choices,default=os.getenv('ROBO_DRIVE_AUTH','oauth-env')); s.add_argument('--cloud-config',default=str(DEFAULT_CLOUD_CONFIG)); s.add_argument('--fixtures',default=str(DEFAULT_FIXTURES)); s.add_argument('--state-name',default='ROBOT_STATE.sqlite'); s.add_argument('--source-config'); s.add_argument('--dry-run-sources',action='store_true'); s.add_argument('--no-persist',action='store_true'); s.add_argument('--no-log',action='store_true'); s.set_defaults(func=cmd_run)
    return p

def main(argv=None):
    args=build_parser().parse_args(argv)
    return args.func(args)

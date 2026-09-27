import os
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.storage.drive_rest import EnvironmentAccessTokenProvider
from robo_dados_publicos.orchestration.cloud_runner import CloudLayout, CloudProductionRunner, EXPECTED_ROOT_NAMES
from robo_dados_publicos.release import (
    ACTIVE_VALIDATED_VERSION,
    CURRENT_CANDIDATE_VERSION,
    SOFTWARE_VERSION,
)


class MemoryDrive:
    def __init__(self, layout):
        self.layout=layout
        self.files={}
        self.children={layout.root_id: []}
        ids={
            '00_DOCUMENTACAO':layout.documentation_id,'01_BRONZE':layout.bronze_id,'02_SILVER':layout.silver_id,
            '03_GOLD':layout.gold_id,'04_DOCUMENTOS':layout.documentos_id,'05_RAG':layout.rag_id,
            '06_BANCOS':layout.bancos_id,'07_LOGS':layout.logs_id,'08_OUTPUTS':layout.outputs_id,
            '09_SCRIPTS':layout.scripts_id,'10_INBOX':layout.inbox_id,'11_QUARENTENA':layout.quarantine_id,
            '12_SOFTWARE':layout.software_id,'START_HERE_ROBO_DADOS_PUBLICOS':'START',
        }
        for name,fid in ids.items():
            self.children[layout.root_id].append({'id':fid,'name':name,'mimeType':'application/vnd.google-apps.folder'})
        for fid in ids.values(): self.children.setdefault(fid,[])
        self.seq=0

    def list_children(self,parent_id): return list(self.children.get(parent_id,[]))
    def find_by_name(self,parent_id,name): return [x for x in self.list_children(parent_id) if x.get('name')==name]
    def put(self,local_path,remote_name,parent_id=None,mime_type='application/octet-stream'):
        self.seq += 1; fid=f'F{self.seq}'
        data=Path(local_path).read_bytes(); self.files[fid]=data
        item={'id':fid,'name':remote_name,'mimeType':mime_type,'parents':[parent_id] if parent_id else []}
        self.children.setdefault(parent_id,[]).append(item)
        return item
    def get(self,file_id,destination):
        data=self.files[file_id]; p=Path(destination); p.write_bytes(data)
        import hashlib
        return {'file_id':file_id,'path':str(p),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    def replace_content(self,file_id,local_path,mime_type='application/octet-stream'):
        self.files[file_id]=Path(local_path).read_bytes()
        for items in self.children.values():
            for x in items:
                if x.get('id')==file_id: return x
        raise KeyError(file_id)


def layout():
    return CloudLayout(
        root_id='ROOT',documentation_id='D0',bronze_id='D1',silver_id='D2',gold_id='D3',documentos_id='D4',
        rag_id='D5',bancos_id='D6',logs_id='D7',outputs_id='D8',scripts_id='D9',inbox_id='D10',
        quarantine_id='D11',software_id='D12')


class TestM4CCloudRunner(unittest.TestCase):
    def test_access_token_env_provider(self):
        old=os.environ.get('GOOGLE_DRIVE_ACCESS_TOKEN')
        try:
            os.environ['GOOGLE_DRIVE_ACCESS_TOKEN']='EPHEMERAL'
            self.assertEqual('EPHEMERAL',EnvironmentAccessTokenProvider().access_token())
        finally:
            if old is None: os.environ.pop('GOOGLE_DRIVE_ACCESS_TOKEN',None)
            else: os.environ['GOOGLE_DRIVE_ACCESS_TOKEN']=old

    def test_preflight_pass(self):
        l=layout(); d=MemoryDrive(l)
        runner=CloudProductionRunner(d,l,Path(__file__).parent/'fixtures')
        out=runner.preflight()
        self.assertEqual('PASS',out['status'])
        self.assertEqual(14,out['count'])
        self.assertEqual(EXPECTED_ROOT_NAMES,{x['name'] for x in d.list_children(l.root_id)})

    def test_preflight_missing_stops(self):
        l=layout(); d=MemoryDrive(l)
        d.children[l.root_id]=[x for x in d.children[l.root_id] if x['name']!='01_BRONZE']
        out=CloudProductionRunner(d,l,Path(__file__).parent/'fixtures').preflight()
        self.assertEqual('STOP_REPOSITORY_LAYOUT',out['status'])
        self.assertIn('01_BRONZE',out['missing'])


    def test_active_runtime_persists_promoted_release_metadata(self):
        l=layout(); d=MemoryDrive(l)
        runner=CloudProductionRunner(d,l,Path(__file__).parent/'fixtures')
        out=runner.run()
        self.assertEqual(SOFTWARE_VERSION, out['software_version'])
        remote=d.find_by_name(l.bancos_id,'ROBOT_STATE.sqlite')[0]
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/'state.sqlite'
            db.write_bytes(d.files[remote['id']])
            from robo_dados_publicos.state.registry import StateRegistry
            with StateRegistry(db) as st:
                self.assertEqual(ACTIVE_VALIDATED_VERSION, st.get_meta('LATEST_SOFTWARE_VERSION'))
                self.assertEqual(CURRENT_CANDIDATE_VERSION, st.get_meta('LATEST_SOFTWARE_CANDIDATE'))

    def test_run_persists_state_and_log(self):
        l=layout(); d=MemoryDrive(l)
        runner=CloudProductionRunner(d,l,Path(__file__).parent/'fixtures')
        first=runner.run()
        self.assertEqual('PASS',first['status'])
        self.assertEqual(109,first['qa']['tests'])
        self.assertEqual(1,len(d.find_by_name(l.bancos_id,'ROBOT_STATE.sqlite')))
        self.assertEqual(1,len([x for x in d.list_children(l.logs_id) if x['name'].startswith('ROBO_RUN_')]))
        second=runner.run()
        self.assertEqual('PASS',second['status'])
        self.assertEqual('REMOTE_EXISTING',second['state_source'])
        self.assertEqual(1,len(d.find_by_name(l.bancos_id,'ROBOT_STATE.sqlite')))

if __name__=='__main__': unittest.main()

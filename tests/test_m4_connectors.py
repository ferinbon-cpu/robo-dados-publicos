import unittest, tempfile, threading, hashlib, json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from robo_dados_publicos.connectors.http_source import HttpSourceConnector
from robo_dados_publicos.storage.drive_rest import OAuthCredentials, TokenProvider, GcloudTokenProvider, DriveRESTClient

PAYLOAD=b"dados-publicos-m4-test\n"
ETAG='"m4-etag-v1"'
SHEETS_MIME='application/vnd.google-apps.spreadsheet'

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.headers.get('If-None-Match') == ETAG:
            self.send_response(304); self.end_headers(); return
        self.send_response(200)
        self.send_header('Content-Type','text/csv')
        self.send_header('ETag',ETAG)
        self.send_header('Content-Length',str(len(PAYLOAD)))
        self.end_headers(); self.wfile.write(PAYLOAD)
    def log_message(self,*args): pass

class FakeResponse:
    def __init__(self,data): self.data=data
    def __enter__(self): return self
    def __exit__(self,*a): return False
    def read(self,*a):
        if self.data is None: return b''
        d=self.data; self.data=None; return d

class FakeOpener:
    def __init__(self): self.requests=[]
    def __call__(self,req,timeout=0):
        self.requests.append(req)
        url=req.full_url
        if 'oauth2.googleapis.com/token' in url:
            return FakeResponse(json.dumps({'access_token':'TOKEN','expires_in':3600}).encode())
        if '/drive/v3/about?' in url:
            return FakeResponse(json.dumps({'importFormats':{'text/csv':[SHEETS_MIME]}}).encode())
        if '/drive/v3/files/F1/export?' in url:
            return FakeResponse(b'a,b\n1,2\n')
        if '/drive/v3/files?' in url and 'upload' not in url:
            return FakeResponse(json.dumps({'files':[{'id':'F1','name':'a.csv'}]}).encode())
        if '/upload/drive/v3/files?' in url:
            return FakeResponse(json.dumps({'id':'UP1','name':'x.csv'}).encode())
        raise AssertionError(url)

class TestM4Connectors(unittest.TestCase):
    def test_http_download_and_304(self):
        server=HTTPServer(('127.0.0.1',0),Handler)
        t=threading.Thread(target=server.serve_forever,daemon=True); t.start()
        try:
            url=f'http://127.0.0.1:{server.server_port}/x.csv'
            with tempfile.TemporaryDirectory() as td:
                dest=Path(td)/'x.csv'
                c=HttpSourceConnector()
                r1=c.download(url,dest)
                self.assertEqual('DOWNLOADED',r1.status)
                self.assertEqual(hashlib.sha256(PAYLOAD).hexdigest(),r1.sha256)
                r2=c.download(url,dest,etag=r1.etag)
                self.assertEqual('NOT_MODIFIED',r2.status)
        finally: server.shutdown(); server.server_close()

    def test_drive_oauth_and_list_contract_with_fake_transport(self):
        fake=FakeOpener(); creds=OAuthCredentials('CID','SECRET','REFRESH')
        tp=TokenProvider(creds,opener=fake)
        client=DriveRESTClient(tp,opener=fake)
        files=client.list_children('PARENT')
        self.assertEqual('F1',files[0]['id'])
        self.assertEqual('TOKEN',tp.access_token())
        self.assertTrue(any('oauth2.googleapis.com/token' in r.full_url for r in fake.requests))

    def test_drive_upload_contract_with_fake_transport(self):
        fake=FakeOpener(); tp=TokenProvider(OAuthCredentials('CID','SECRET','REFRESH'),opener=fake)
        client=DriveRESTClient(tp,opener=fake)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'x.csv'; p.write_text('a,b\n1,2\n')
            out=client.put(p,'x.csv','PARENT','text/csv')
        self.assertEqual('UP1',out['id'])
        req=[r for r in fake.requests if '/upload/drive/v3/files?' in r.full_url][0]
        self.assertIn('multipart/related',req.headers.get('Content-type',''))
        self.assertIn(b'"parents": ["PARENT"]',req.data)

    def test_drive_csv_to_google_sheets_conversion_contract(self):
        fake=FakeOpener(); tp=TokenProvider(OAuthCredentials('CID','SECRET','REFRESH'),opener=fake)
        client=DriveRESTClient(tp,opener=fake)
        formats=client.import_formats()
        self.assertIn(SHEETS_MIME,formats['text/csv'])
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'x.csv'; p.write_text('a,b\n1,2\n')
            out=client.put_converted(p,'Planilha teste','PARENT','text/csv',SHEETS_MIME)
        self.assertEqual('UP1',out['id'])
        req=[r for r in fake.requests if '/upload/drive/v3/files?' in r.full_url][0]
        self.assertIn(b'"mimeType": "application/vnd.google-apps.spreadsheet"',req.data)
        self.assertIn(b'Content-Type: text/csv',req.data)
        self.assertIn(b'"parents": ["PARENT"]',req.data)

    def test_drive_workspace_export_contract(self):
        fake=FakeOpener(); tp=TokenProvider(OAuthCredentials('CID','SECRET','REFRESH'),opener=fake)
        client=DriveRESTClient(tp,opener=fake)
        with tempfile.TemporaryDirectory() as td:
            destination=Path(td)/'readback.csv'
            out=client.export('F1',destination,'text/csv')
            self.assertEqual(b'a,b\n1,2\n',destination.read_bytes())
        self.assertEqual(hashlib.sha256(b'a,b\n1,2\n').hexdigest(),out['sha256'])
        req=[r for r in fake.requests if '/drive/v3/files/F1/export?' in r.full_url][0]
        self.assertEqual('GET',req.get_method())
        self.assertIn('mimeType=text%2Fcsv',req.full_url)

    def test_gcloud_token_provider_contract(self):
        class CP:
            stdout='GCLOUD_TOKEN\n'
        calls=[]
        def runner(cmd,**kwargs):
            calls.append((cmd,kwargs)); return CP()
        tp=GcloudTokenProvider(runner=runner,cache_seconds=300)
        self.assertEqual('GCLOUD_TOKEN',tp.access_token())
        self.assertEqual('GCLOUD_TOKEN',tp.access_token())
        self.assertEqual(1,len(calls))
        self.assertEqual(['gcloud','auth','print-access-token'],calls[0][0])

    def test_drive_delete_contract_with_fake_transport(self):
        class DeleteOpener(FakeOpener):
            def __call__(self,req,timeout=0):
                if req.get_method()=='DELETE' and '/drive/v3/files/' in req.full_url:
                    self.requests.append(req); return FakeResponse(b'')
                return super().__call__(req,timeout)
        fake=DeleteOpener(); tp=TokenProvider(OAuthCredentials('CID','SECRET','REFRESH'),opener=fake)
        client=DriveRESTClient(tp,opener=fake)
        out=client.delete('F1')
        self.assertTrue(out['deleted'])

if __name__=='__main__': unittest.main()

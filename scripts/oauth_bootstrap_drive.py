#!/usr/bin/env python3
"""One-time OAuth bootstrap for the external robot.

Does not send passwords to the script. Authentication happens in the browser.
The resulting refresh token must be stored as a secret, never committed to Git.
"""
import argparse, base64, hashlib, json, os, secrets, threading, webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlencode, urlparse, parse_qs
from urllib.request import Request, urlopen

AUTH_URL="https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL="https://oauth2.googleapis.com/token"
SCOPES={
    "drive":"https://www.googleapis.com/auth/drive",
    "drive.file":"https://www.googleapis.com/auth/drive.file",
    "drive.readonly":"https://www.googleapis.com/auth/drive.readonly",
}

def pkce_pair():
    verifier=base64.urlsafe_b64encode(secrets.token_bytes(48)).decode().rstrip('=')
    challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
    return verifier,challenge

def build_auth_url(client_id,redirect_uri,scope,state,challenge):
    return AUTH_URL+"?"+urlencode({
        "client_id":client_id,
        "redirect_uri":redirect_uri,
        "response_type":"code",
        "scope":scope,
        "access_type":"offline",
        "prompt":"consent",
        "state":state,
        "code_challenge":challenge,
        "code_challenge_method":"S256",
    })

def exchange_code(client_id,client_secret,code,redirect_uri,verifier):
    body={
        "client_id":client_id,
        "code":code,
        "code_verifier":verifier,
        "redirect_uri":redirect_uri,
        "grant_type":"authorization_code",
    }
    if client_secret: body["client_secret"]=client_secret
    req=Request(TOKEN_URL,data=urlencode(body).encode(),headers={"Content-Type":"application/x-www-form-urlencoded"},method="POST")
    with urlopen(req,timeout=30) as resp:
        return json.loads(resp.read().decode())

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--client-id',default=os.getenv('GOOGLE_DRIVE_CLIENT_ID',''))
    ap.add_argument('--client-secret',default=os.getenv('GOOGLE_DRIVE_CLIENT_SECRET',''))
    ap.add_argument('--scope',choices=SCOPES,default='drive')
    ap.add_argument('--no-browser',action='store_true')
    ap.add_argument('--output',help='arquivo JSON local para salvar tokens; mantenha fora do Git')
    args=ap.parse_args()
    if not args.client_id:
        raise SystemExit('Informe --client-id ou GOOGLE_DRIVE_CLIENT_ID')

    state=secrets.token_urlsafe(24); verifier,challenge=pkce_pair(); result={}
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            q=parse_qs(urlparse(self.path).query)
            result.update({k:v[0] for k,v in q.items() if v})
            self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.end_headers()
            self.wfile.write('<h2>Autorização recebida. Você pode fechar esta janela.</h2>'.encode())
        def log_message(self,*a): pass
    server=HTTPServer(('127.0.0.1',0),Handler)
    redirect=f'http://127.0.0.1:{server.server_port}'
    url=build_auth_url(args.client_id,redirect,SCOPES[args.scope],state,challenge)
    print('Abra este endereço no navegador:\n',url,'\n',sep='')
    if not args.no_browser: webbrowser.open(url)
    server.handle_request(); server.server_close()
    if result.get('state') != state: raise SystemExit('STATE inválido; interrompido')
    if 'error' in result: raise SystemExit('OAuth recusado: '+result['error'])
    tokens=exchange_code(args.client_id,args.client_secret,result['code'],redirect,verifier)
    safe={k:v for k,v in tokens.items() if k not in {'access_token','refresh_token'}}
    print('OAuth concluído. Metadados:',json.dumps(safe,indent=2))
    if args.output:
        path=os.path.abspath(args.output)
        with open(path,'w',encoding='utf-8') as f: json.dump(tokens,f,indent=2)
        try: os.chmod(path,0o600)
        except OSError: pass
        print('Tokens gravados em:',path)
    else:
        print('Refresh token obtido, mas não exibido por segurança. Use --output em local seguro para persistir.')

if __name__=='__main__': main()

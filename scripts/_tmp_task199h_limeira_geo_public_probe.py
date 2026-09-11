from __future__ import annotations

import hashlib
import json
import math
import os
import sqlite3
import ssl
import struct
import urllib.request
from pathlib import Path

OUT = Path('probe-output/task199h_limeira_geo_public_probe.json')
GPKG_URL = 'https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/malha_com_atributos/setores/gpkg/UF/SP/SP_setores_CD2022.gpkg'
TMP = Path('/tmp/SP_setores_CD2022.gpkg')
UA = 'robo-dados-publicos/TASK199H bounded-official-ibge-point-in-polygon'
MAX_BYTES = 300 * 1024 * 1024
MUNI_PREFIX = '3526902'

# Official municipal GeoPortal points recovered from public layer 1234.
# Theresa uses the named non-Extensao feature whose returned address is Rua Manoel Rato, 25,
# matching the current municipal-school address; the separate Extensao feature is preserved below.
SCHOOLS = [
    {'codigo_inep':'35208437','school':'EMEIEF Ismael Pereira Lago, Pastor','lon':-47.44221918395775,'lat':-22.56221889274754,'geoportal_gid':49,'geoportal_address':'Av Luis Vaz De Camoes 330 Jd Caieira','identity_rule':'EXACT_SINGLE_NAMED_FEATURE'},
    {'codigo_inep':'35286229','school':'EMEIEF Maurício Sebastião Ferreira, Padre','lon':-47.42359146537795,'lat':-22.607998943052685,'geoportal_gid':67,'geoportal_address':'R: João Pompeu Filho, 571 Jardim Do Lago','identity_rule':'EXACT_SINGLE_NAMED_FEATURE'},
    {'codigo_inep':'35004773','school':'EMEIEF Raquel Aparecida Gonçalves Franceschi, Profa.','lon':-47.42800455870972,'lat':-22.61613584039013,'geoportal_gid':76,'geoportal_address':'Rua Sebastião Teixeira, 200, Residencial Rubi','identity_rule':'UNIQUE_RAQUEL_QUERY_PLUS_RETURNED_NAMED_FEATURE_AND_CURRENT_ADDRESS'},
    {'codigo_inep':'35099569','school':'CI Neusa Francisco Correa da Silva','lon':-47.375594422497144,'lat':-22.56150560013331,'geoportal_gid':26,'geoportal_address':'Rua Olivia Sacco Iaquinta, S/N - Vila Labak','identity_rule':'EXACT_SINGLE_NAMED_FEATURE_CURRENT_GEOPORTAL_SITE;ADDRESS_CONFLICT_PRESERVED'},
    {'codigo_inep':'35241885','school':'EMEI Theresa Veronesi D Andrea','lon':-47.39943489231738,'lat':-22.598737108288702,'geoportal_gid':80,'geoportal_address':'Rua Manoel Rato, 25, Jardim Parque Novo Mundo','identity_rule':'NAMED_NON_EXTENSION_FEATURE_MATCHES_CURRENT_MANOEL_RATO_25'},
]
THERESA_EXTENSION = {'geoportal_gid':38,'name':"EMEI - Theresa Veronesi D'Andrea (Extensão)",'address':'Rua Senador Vergueiro, 1309, Centro','lon':-47.407418339584524,'lat':-22.56881213228995,'excluded_reason':'EXPLICIT_EXTENSION_NOT_MAIN_UNIT'}


def download() -> dict:
    h = hashlib.sha256(); total = 0
    req = urllib.request.Request(GPKG_URL, headers={'User-Agent': UA, 'Accept': 'application/geopackage+sqlite3,application/octet-stream,*/*;q=0.3'}, method='GET')
    with urllib.request.urlopen(req, timeout=90, context=ssl.create_default_context()) as r, TMP.open('wb') as f:
        status = int(r.status); final_url = r.geturl(); ctype = r.headers.get('Content-Type'); clen = r.headers.get('Content-Length')
        while True:
            chunk = r.read(1024 * 1024)
            if not chunk: break
            total += len(chunk)
            if total > MAX_BYTES:
                raise RuntimeError(f'GPKG exceeds bounded maximum {MAX_BYTES}')
            f.write(chunk); h.update(chunk)
    return {'status':status,'final_url':final_url,'content_type':ctype,'content_length_header':clen,'bytes':total,'sha256':h.hexdigest()}


def table_cols(conn, table):
    return [r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')]


def find_layer(conn):
    rows = conn.execute('SELECT c.table_name,c.data_type,c.identifier,c.srs_id,g.column_name,g.geometry_type_name FROM gpkg_contents c JOIN gpkg_geometry_columns g ON c.table_name=g.table_name WHERE c.data_type="features"').fetchall()
    candidates=[]
    for r in rows:
        cols=table_cols(conn,r[0])
        code_cols=[c for c in cols if c.upper() in ('CD_SETOR','COD_SETOR','CDSETOR') or ('SETOR' in c.upper() and c.upper().startswith(('CD','COD')))]
        candidates.append({'table_name':r[0],'data_type':r[1],'identifier':r[2],'srs_id':r[3],'geometry_column':r[4],'geometry_type':r[5],'columns':cols,'sector_code_candidates':code_cols})
    good=[c for c in candidates if c['sector_code_candidates']]
    if len(good)!=1:
        raise RuntimeError(f'Expected exactly one sector feature layer; got {len(good)} from {len(candidates)}')
    return good[0], candidates


def gpkg_wkb(blob: bytes):
    if not blob or len(blob)<8 or blob[:2] != b'GP':
        raise ValueError('not a GeoPackage geometry')
    flags=blob[3]
    little=bool(flags & 1)
    endian='<' if little else '>'
    srs_id=struct.unpack_from(endian+'i',blob,4)[0]
    env=(flags >> 1) & 0x07
    env_len={0:0,1:32,2:48,3:48,4:64}.get(env)
    if env_len is None: raise ValueError(f'unsupported envelope indicator {env}')
    off=8+env_len
    return srs_id, blob[off:]


def norm_type(t):
    # ISO WKB Z/M/ZM offsets plus EWKB flags.
    base=t & 0xFF
    if base in (1,2,3,4,5,6,7): return base
    if 1000 <= t < 4000: return t % 1000
    return base


def parse_wkb(buf: bytes, off=0):
    if off+5>len(buf): raise ValueError('short WKB')
    endian='<' if buf[off]==1 else '>' if buf[off]==0 else None
    if not endian: raise ValueError('bad byte order')
    off += 1
    raw=struct.unpack_from(endian+'I',buf,off)[0]; off+=4
    has_z=bool(raw & 0x80000000); has_m=bool(raw & 0x40000000); has_srid=bool(raw & 0x20000000)
    base=norm_type(raw)
    if has_srid: off += 4
    dims=2+int(has_z)+int(has_m)
    if raw < 4000 and not (raw & 0xE0000000):
        if raw >= 3000: dims=4
        elif raw >= 2000: dims=3
        elif raw >= 1000: dims=3
    if base==1:
        vals=struct.unpack_from(endian+'d'*dims,buf,off); off+=8*dims
        return ('POINT',(vals[0],vals[1])),off
    if base==3:
        nr=struct.unpack_from(endian+'I',buf,off)[0]; off+=4; rings=[]
        for _ in range(nr):
            n=struct.unpack_from(endian+'I',buf,off)[0]; off+=4; ring=[]
            for __ in range(n):
                vals=struct.unpack_from(endian+'d'*dims,buf,off); off+=8*dims; ring.append((vals[0],vals[1]))
            rings.append(ring)
        return ('POLYGON',rings),off
    if base==6:
        n=struct.unpack_from(endian+'I',buf,off)[0]; off+=4; polys=[]
        for _ in range(n):
            g,off=parse_wkb(buf,off)
            if g[0]!='POLYGON': raise ValueError('multipolygon child is not polygon')
            polys.append(g[1])
        return ('MULTIPOLYGON',polys),off
    raise ValueError(f'unsupported geometry type {raw}/{base}')


def on_segment(px,py,a,b,eps=1e-11):
    (x1,y1),(x2,y2)=a,b
    cross=(px-x1)*(y2-y1)-(py-y1)*(x2-x1)
    if abs(cross)>eps: return False
    return min(x1,x2)-eps<=px<=max(x1,x2)+eps and min(y1,y2)-eps<=py<=max(y1,y2)+eps


def in_ring(px,py,ring):
    inside=False
    n=len(ring)
    for i in range(n):
        a=ring[i]; b=ring[(i+1)%n]
        if on_segment(px,py,a,b): return True, True
        x1,y1=a; x2,y2=b
        if ((y1>py)!=(y2>py)):
            xint=(x2-x1)*(py-y1)/(y2-y1)+x1
            if px < xint: inside=not inside
    return inside, False


def in_polygon(px,py,rings):
    if not rings: return False,False
    outer,bound=in_ring(px,py,rings[0])
    if bound:return True,True
    if not outer:return False,False
    for hole in rings[1:]:
        ih,bh=in_ring(px,py,hole)
        if bh:return True,True
        if ih:return False,False
    return True,False


def contains(g,px,py):
    typ,data=g
    if typ=='POLYGON': return in_polygon(px,py,data)
    if typ=='MULTIPOLYGON':
        any_boundary=False
        for p in data:
            inside,bound=in_polygon(px,py,p)
            if inside:return True,bound
            any_boundary |= bound
        return False,any_boundary
    return False,False


def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={'schema':'TASK199H_IBGE_GPKG_POINT_IN_POLYGON_V13','mode':'EPHEMERAL_OFFICIAL_BINARY_READ_ONLY','source_url':GPKG_URL,'raw_persisted':False,'drive_write':False,'repo_binary_write':False,'tinyfish_used':False,'schools':SCHOOLS,'theresa_extension_excluded':THERESA_EXTENSION,'status':'STOP_NOT_RUN'}
    try:
        result['download']=download()
        if result['download']['status']!=200 or result['download']['bytes']<1_000_000: raise RuntimeError('invalid GPKG download')
        conn=sqlite3.connect(f'file:{TMP}?mode=ro',uri=True)
        layer,inventory=find_layer(conn); result['feature_layer']=layer; result['layer_inventory']=inventory
        code=layer['sector_code_candidates'][0]; geom=layer['geometry_column']; table=layer['table_name']; srs=layer['srs_id']
        result['coordinate_compatibility']={'school_points_crs':'EPSG:4326_WGS84_CONVERTED_FROM_OFFICIAL_EPSG3857','sector_layer_srs_id':srs,'direct_lonlat_test_allowed':srs in (4326,4674)}
        if srs not in (4326,4674): raise RuntimeError(f'unsupported sector SRS {srs}; no silent reprojection')
        q=f'SELECT "{code}", "{geom}" FROM "{table}" WHERE CAST("{code}" AS TEXT) LIKE ?'
        rows=conn.execute(q,(MUNI_PREFIX+'%',)).fetchall()
        result['limeira_sector_rows']=len(rows)
        parsed=[]; geom_srs=set(); parse_errors=[]
        for cd,b in rows:
            try:
                gs,w=gpkg_wkb(b); geom_srs.add(gs); g,_=parse_wkb(w); parsed.append((str(cd),g))
            except Exception as e:
                parse_errors.append({'sector':str(cd),'error':f'{type(e).__name__}:{e}'})
        result['geometry_srs_ids']=sorted(geom_srs); result['geometry_parse_errors']=parse_errors[:20]; result['parsed_sector_rows']=len(parsed)
        matches=[]
        for s in SCHOOLS:
            hit=[]
            for cd,g in parsed:
                inside,bound=contains(g,s['lon'],s['lat'])
                if inside: hit.append({'sector_id':cd,'on_boundary':bound})
            matches.append({'codigo_inep':s['codigo_inep'],'school':s['school'],'lon':s['lon'],'lat':s['lat'],'sector_matches':hit,'match_count':len(hit)})
        result['point_in_polygon']=matches
        unique=sum(1 for x in matches if x['match_count']==1 and not x['sector_matches'][0]['on_boundary'])
        result['unique_interior_matches']=unique
        result['status']='PASS_FIVE_UNIQUE_INTERIOR_SECTOR_MATCHES' if unique==5 else 'STOP_NOT_ALL_POINTS_UNIQUE_INTERIOR'
        result['next_step']='canonize only exact municipal point to unique 2022 IBGE sector links; preserve source-address conflicts' if unique==5 else 'retain unresolved cases; inspect boundary/multiplicity without forced promotion'
        conn.close()
    except Exception as e:
        result['status']='STOP_GPKG_POINT_IN_POLYGON_ERROR'; result['error']=f'{type(e).__name__}:{e}'; result['next_step']='no geography promotion from failed transport/parser'
    finally:
        try: TMP.unlink(missing_ok=True)
        except Exception: pass
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':result['status'],'download_bytes':(result.get('download') or {}).get('bytes'),'sha256':(result.get('download') or {}).get('sha256'),'limeira_sector_rows':result.get('limeira_sector_rows'),'unique_matches':result.get('unique_interior_matches'),'matches':[(x['codigo_inep'],x['sector_matches']) for x in result.get('point_in_polygon',[])],'out':str(OUT)},ensure_ascii=False))
    return 0

if __name__=='__main__': raise SystemExit(main())

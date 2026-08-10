#!/usr/bin/env python3
"""Vía API de CRITERIUM COMPÁS: campos de Negocio por /metadata e import de leads por /graphql.

Uso:  python3 scripts/importar-leads.py leads.tsv [--solo-campos]

El TSV sale de la base de compas-nexia (SOLO lectura):
  psql "$(~/.secrets/kc get compas-nexia/env/DATABASE_URL)" -A -F $'\t' -t -c \
    "SELECT l.slug, l.nombre, l.municipio, coalesce(l.barrio,''), l.fase, l.prioridad,
            coalesce(l.nota::text,''), coalesce(l.resenas::text,''), l.\"queTieneHoy\",
            coalesce(l.gancho,''), coalesce(u.nombre,''), coalesce(z.nombre,''),
            coalesce(d.url,''), l.sector
     FROM \"Lead\" l
     LEFT JOIN \"Usuario\" u ON u.id=l.\"ownerId\"
     LEFT JOIN \"Zona\" z ON z.id=l.\"zonaId\"
     LEFT JOIN \"Demo\" d ON d.\"leadId\"=l.id ORDER BY l.slug" > leads.tsv

La API key sale del Llavero y no se imprime nunca."""
import json
import subprocess
import sys
import urllib.request

BASE = 'http://localhost:3000'
ORIGIN = BASE
EMAIL = 'hola@estudionexia.com'
HOME = subprocess.run(['sh', '-c', 'echo $HOME'], capture_output=True, text=True).stdout.strip()


def gql(path, query, variables=None, token=None):
    body = json.dumps({'query': query, 'variables': variables or {}}).encode()
    req = urllib.request.Request(BASE + path, data=body, headers={'content-type': 'application/json'})
    if token:
        req.add_header('Authorization', 'Bearer ' + token)
    with urllib.request.urlopen(req) as r:
        out = json.load(r)
    if out.get('errors'):
        raise RuntimeError(json.dumps(out['errors'])[:500])
    return out['data']


def login():
    """API key de COMPÁS, generada en Ajustes → MCP y API y guardada en el Llavero."""
    tok = subprocess.run([HOME + '/.secrets/kc', 'get', 'pruebas/twenty/API_KEY'],
                         capture_output=True, text=True).stdout.strip()
    if not tok:
        sys.exit('falta la API key: ~/.secrets/kc set pruebas/twenty/API_KEY')
    return tok


def main():
    tok = login()
    print('login ok')

    d = gql('/metadata', '''query{objects(paging:{first:1000}){edges{node{id nameSingular}}}}''', token=tok)
    oid = None
    for e in d['objects']['edges']:
        if e['node']['nameSingular'] == 'negocio':
            oid = e['node']['id']
    if not oid:
        sys.exit('objeto negocio no encontrado')
    print('objectMetadataId:', oid)

    # campos existentes (fase ya creada por UI)
    d = gql('/metadata', '''query($id:UUID!){object(id:$id){
      fields(paging:{first:200}){edges{node{id name type options}}}}}''',
            {'id': oid}, token=tok)
    existing = {}
    for e in d['object']['fields']['edges']:
        existing[e['node']['name']] = e['node']
    print('campos existentes:', sorted(existing.keys()))

    def crea(field):
        field['objectMetadataId'] = oid
        gql('/metadata', '''mutation($input:CreateOneFieldMetadataInput!){
          createOneField(input:$input){id name}}''', {'input': {'field': field}}, token=tok)
        print('campo creado:', field['name'])

    nuevos = [
        {'name': 'slug', 'label': 'Slug', 'type': 'TEXT', 'icon': 'IconLink',
         'description': 'El mismo slug que la demo en nexia-demos; la clave del sistema.'},
        {'name': 'notaGoogle', 'label': 'Nota Google', 'type': 'NUMBER', 'icon': 'IconStar',
         'settings': {'decimals': 1, 'type': 'number'}},
        {'name': 'resenas', 'label': 'Reseñas', 'type': 'NUMBER', 'icon': 'IconMessageCircle'},
        {'name': 'queTieneHoy', 'label': 'Qué tiene hoy', 'type': 'SELECT', 'icon': 'IconWorldWww',
         'options': [
             {'value': 'NADA', 'label': 'Nada', 'color': 'red', 'position': 0},
             {'value': 'SOLO_INSTAGRAM', 'label': 'Solo Instagram', 'color': 'pink', 'position': 1},
             {'value': 'PLANTILLA_AJENA', 'label': 'Plantilla ajena', 'color': 'orange', 'position': 2},
             {'value': 'WEB_PROPIA', 'label': 'Web propia', 'color': 'green', 'position': 3}]},
        {'name': 'gancho', 'label': 'Gancho', 'type': 'TEXT', 'icon': 'IconFishHook',
         'description': 'La línea verificada de por qué le escribimos a ÉL.'},
        {'name': 'demo', 'label': 'Demo', 'type': 'LINKS', 'icon': 'IconExternalLink'},
        {'name': 'comercial', 'label': 'Comercial', 'type': 'TEXT', 'icon': 'IconUser'},
        {'name': 'zona', 'label': 'Zona', 'type': 'TEXT', 'icon': 'IconMap'},
        {'name': 'municipio', 'label': 'Municipio', 'type': 'TEXT', 'icon': 'IconMapPin'},
        {'name': 'prioridad', 'label': 'Prioridad', 'type': 'NUMBER', 'icon': 'IconFlag',
         'description': '1 = sin web y nota alta; 4 = la cola.'},
    ]
    for f in nuevos:
        if f['name'] in existing:
            print('ya existe:', f['name'])
            continue
        try:
            crea(dict(f))
        except RuntimeError as err:
            print('ERROR', f['name'], err)

    # mapa de valores de fase (creada por UI, valores generados por Twenty)
    d = gql('/metadata', '''query($id:UUID!){object(id:$id){
      fields(paging:{first:200}){edges{node{name options}}}}}''', {'id': oid}, token=tok)
    fase_map = {}
    for e in d['object']['fields']['edges']:
        if e['node']['name'] == 'fase':
            for o in e['node']['options'] or []:
                fase_map[o['label'].lower()] = o['value']
    print('fase_map:', fase_map)

    if '--solo-campos' in sys.argv:
        return

    label_fase = {
        'cualificado': 'cualificado', 'demo_hecha': 'demo hecha', 'contactado': 'contactado',
        'respondido': 'respondido', 'visitado': 'visitado', 'ganado': 'ganado',
        'perdido': 'perdido', 'descartado': 'descartado'}

    tsv = sys.argv[1]
    rows = []
    for line in open(tsv, encoding='utf-8'):
        c = line.rstrip('\n').split('\t')
        if len(c) < 14:
            continue
        slug, nombre, municipio, barrio, fase, prioridad, nota, resenas, qth, gancho, owner, zona, demo, sector = c[:14]
        r = {
            'name': nombre,
            'slug': slug,
            'fase': fase_map.get(label_fase.get(fase, fase), None),
            'prioridad': int(prioridad),
            'queTieneHoy': qth.upper(),
            'gancho': gancho or None,
            'comercial': owner or None,
            'zona': zona or None,
            'municipio': municipio or None,
        }
        if nota:
            r['notaGoogle'] = float(nota)
        if resenas:
            r['resenas'] = int(resenas)
        if demo:
            r['demo'] = {'primaryLinkUrl': demo, 'primaryLinkLabel': 'demo'}
        rows.append({k: v for k, v in r.items() if v is not None})

    print('a importar:', len(rows))
    d = gql('/graphql', '''mutation($data:[NegocioCreateInput!]!){
      createNegocios(data:$data){id slug}}''', {'data': rows}, token=tok)
    print('creados:', len(d['createNegocios']))


main()

import os, json, urllib.request, urllib.parse, time

TOKEN = os.environ['META_ACCESS_TOKEN']
ACT = 'act_615338413578534'
API = 'https://graph.facebook.com/v19.0'

def get(path, params):
    params['access_token'] = TOKEN
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    for attempt in range(6):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if 'limit' in body.lower() and attempt < 5:
                time.sleep(45); continue
            print('ERR', path, body[:400]); return {}
        except Exception as ex:
            time.sleep(20)
    return {}

# 1. achar campanhas BRASIL
camps = get(f'{ACT}/campaigns', {'fields':'id,name,status','limit':200}).get('data',[])
br = [c for c in camps if 'BRASIL' in c['name'].upper()]
print('=== CAMPANHAS BR ===')
for c in br: print(c['id'], '|', c['name'], '|', c['status'])

ids = [c['id'] for c in br]

def acts(row):
    d = {}
    for a in row.get('actions', []):
        d[a['action_type']] = float(a['value'])
    return d

def pull(level_ids, breakdowns, label):
    out = []
    for cid in level_ids:
        p = {'level':'campaign','time_range':json.dumps({'since':'2026-07-29','until':'2026-08-04'}),
             'fields':'spend,impressions,clicks,inline_link_clicks,actions,reach',
             'limit':500}
        if breakdowns: p['breakdowns'] = breakdowns
        r = get(f'{cid}/insights', p)
        for row in r.get('data', []):
            row['_camp'] = next(c['name'] for c in br if c['id']==cid)
            out.append(row)
    print(f'\n=== {label} ===')
    for row in out:
        a = acts(row)
        key = ' / '.join(str(row.get(b,'')) for b in breakdowns.split(',')) if breakdowns else 'TOTAL'
        print(json.dumps({
            'camp': row['_camp'], 'key': key,
            'spend': row.get('spend'), 'impr': row.get('impressions'),
            'clicks': row.get('clicks'), 'link_clicks': row.get('inline_link_clicks'),
            'lpv': a.get('landing_page_view'), 
            'lead': a.get('lead') or a.get('offsite_conversion.fb_pixel_lead') or a.get('onsite_conversion.lead_grouped'),
            'all_actions': {k:v for k,v in a.items() if 'lead' in k.lower() or 'landing' in k.lower() or 'view_content' in k.lower()}
        }, ensure_ascii=False))
    return out

pull(ids, 'publisher_platform', 'POR PLATAFORMA')
pull(ids, 'publisher_platform,platform_position', 'POR PLATAFORMA+POSICAO')
pull(ids, 'age', 'POR IDADE (TODAS PLATAFORMAS)')
pull(ids, '', 'TOTAL GERAL')

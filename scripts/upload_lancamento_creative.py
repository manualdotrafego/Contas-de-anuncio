import os, json, urllib.request, urllib.parse, time
TOKEN = os.environ['META_ACCESS_TOKEN']; API='https://graph.facebook.com/v19.0'
def get(path, params):
    params['access_token']=TOKEN
    url=f"{API}/{path}?{urllib.parse.urlencode(params)}"
    for a in range(5):
        try:
            with urllib.request.urlopen(url,timeout=120) as r: return json.load(r)
        except urllib.error.HTTPError as e:
            b=e.read().decode()
            if 'limit' in b.lower() and a<4: time.sleep(45); continue
            return {'__err': b[:300]}
        except Exception: time.sleep(15)
    return {}
CID='120256165865940002'  # LANDPAGE AJUSTADA
TR=json.dumps({'since':'2026-07-29','until':'2026-08-04'})
def acts(r):
    return {x['action_type']:float(x['value']) for x in r.get('actions',[])}
for bd in ['age,publisher_platform','publisher_platform,age','impression_device,publisher_platform']:
    r=get(f'{CID}/insights',{'level':'campaign','time_range':TR,'breakdowns':bd,
        'fields':'spend,impressions,inline_link_clicks,actions','limit':500})
    print(f'\n### {bd}')
    if '__err' in r: print('  FALHOU:', r['__err'][:200]); continue
    for row in r.get('data',[]):
        a=acts(row)
        print(json.dumps({'k':[row.get(x) for x in bd.split(',')],'spend':row.get('spend'),
          'lc':row.get('inline_link_clicks'),'lpv':a.get('landing_page_view'),'lead':a.get('lead')},ensure_ascii=False))
# fallback: adset x plataforma
r=get(f'{CID}/insights',{'level':'adset','time_range':TR,'breakdowns':'publisher_platform',
    'fields':'adset_name,spend,inline_link_clicks,actions','limit':500})
print('\n### ADSET x PLATAFORMA')
for row in r.get('data',[]):
    a=acts(row)
    print(json.dumps({'adset':row.get('adset_name'),'plat':row.get('publisher_platform'),
      'spend':row.get('spend'),'lc':row.get('inline_link_clicks'),'lpv':a.get('landing_page_view'),'lead':a.get('lead')},ensure_ascii=False))

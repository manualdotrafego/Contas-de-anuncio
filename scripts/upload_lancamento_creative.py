import os, json, urllib.request, urllib.parse, time
TOKEN=os.environ['META_ACCESS_TOKEN']; ACT='act_615338413578534'; API='https://graph.facebook.com/v19.0'
def get(path,params):
    params['access_token']=TOKEN
    url=f"{API}/{path}?{urllib.parse.urlencode(params)}"
    for a in range(5):
        try:
            with urllib.request.urlopen(url,timeout=180) as r: return json.load(r)
        except urllib.error.HTTPError as e:
            b=e.read().decode()
            if 'limit' in b.lower() and a<4: time.sleep(50); continue
            return {'__err':b[:300]}
        except Exception: time.sleep(15)
    return {}
camps=get(f'{ACT}/campaigns',{'fields':'id,name,status,effective_status','limit':300}).get('data',[])
pt=[c for c in camps if 'BRASIL' not in c['name'].upper()]
print('=== CAMPANHAS NAO-BR ===')
for c in pt: print(c['id'],'|',c['name'],'|',c['effective_status'])
TR=json.dumps({'since':'2026-07-29','until':'2026-08-04'})
def A(r): return {x['action_type']:float(x['value']) for x in r.get('actions',[])}
def show(rows,bd,label):
    print(f'\n=== {label} ===')
    for row in rows:
        a=A(row); lead=a.get('lead') or a.get('offsite_conversion.fb_pixel_lead') or a.get('onsite_conversion.lead_grouped')
        print(json.dumps({'camp':row.get('_c'),'k':[row.get(x) for x in bd] if bd else 'TOTAL',
          'spend':row.get('spend'),'impr':row.get('impressions'),'lc':row.get('inline_link_clicks'),
          'lpv':a.get('landing_page_view'),'lead':lead},ensure_ascii=False))
def pull(bd,label):
    out=[]
    for c in pt:
        p={'level':'campaign','time_range':TR,'fields':'spend,impressions,clicks,inline_link_clicks,actions','limit':500}
        if bd: p['breakdowns']=','.join(bd)
        r=get(f"{c['id']}/insights",p)
        if '__err' in r: print('ERRO',c['name'],r['__err'][:150]); continue
        for row in r.get('data',[]):
            if float(row.get('spend',0))==0: continue
            row['_c']=c['name']; out.append(row)
    show(out,bd,label)
pull([],'TOTAL POR CAMPANHA')
pull(['publisher_platform'],'POR PLATAFORMA')
pull(['publisher_platform','platform_position'],'POR POSICAO')
pull(['age'],'POR IDADE')
pull(['impression_device'],'POR DISPOSITIVO')

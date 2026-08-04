import os,json,urllib.request,urllib.parse,time
TOKEN=os.environ['META_ACCESS_TOKEN']; API='https://graph.facebook.com/v19.0'
CID='120255355949960002'
def get(p,q):
    q['access_token']=TOKEN
    for a in range(5):
        try:
            with urllib.request.urlopen(f"{API}/{p}?{urllib.parse.urlencode(q)}",timeout=180) as r: return json.load(r)
        except urllib.error.HTTPError as e:
            b=e.read().decode()
            if 'limit' in b.lower() and a<4: time.sleep(50); continue
            return {'__err':b[:250]}
        except Exception: time.sleep(15)
    return {}
print('=== CONJUNTOS E SEGMENTACAO ===')
ads=get(f'{CID}/adsets',{'fields':'id,name,effective_status,daily_budget,targeting{age_min,age_max,genders,geo_locations,publisher_platforms}','limit':100}).get('data',[])
for s in ads:
    t=s.get('targeting',{})
    print(json.dumps({'id':s['id'],'nome':s['name'],'st':s['effective_status'],
      'budget':(int(s['daily_budget'])/100 if s.get('daily_budget') else None),
      'age':f"{t.get('age_min')}-{t.get('age_max')}",'gen':t.get('genders'),
      'plat':t.get('publisher_platforms'),
      'geo':(t.get('geo_locations',{}).get('countries') or t.get('geo_locations',{}).get('cities'))},ensure_ascii=False))
TR=json.dumps({'since':'2026-07-29','until':'2026-08-04'})
def A(r): return {x['action_type']:float(x['value']) for x in r.get('actions',[])}
for bd,lb in [('age','ADSET x IDADE'),('age,gender','ADSET x IDADE x GENERO')]:
    r=get(f'{CID}/insights',{'level':'adset','time_range':TR,'breakdowns':bd,
      'fields':'adset_name,spend,impressions,inline_link_clicks,actions','limit':500})
    print(f'\n=== {lb} ===')
    if '__err' in r: print(' FALHOU',r['__err'][:180]); continue
    for row in r.get('data',[]):
        if float(row.get('spend',0))==0: continue
        a=A(row)
        print(json.dumps({'adset':row['adset_name'][:46],'k':[row.get(x) for x in bd.split(',')],
          'spend':row['spend'],'impr':row.get('impressions'),'lc':row.get('inline_link_clicks'),
          'lpv':a.get('landing_page_view'),'lead':a.get('lead')},ensure_ascii=False))

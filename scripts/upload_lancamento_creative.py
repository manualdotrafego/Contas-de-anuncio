import os,json,urllib.request,urllib.parse,time
TOKEN=os.environ['META_ACCESS_TOKEN']; API='https://graph.facebook.com/v19.0'
LAL='120256321507330002'
def req(path,params,post=False):
    params['access_token']=TOKEN
    data=urllib.parse.urlencode(params).encode() if post else None
    url=f"{API}/{path}"+('' if post else '?'+urllib.parse.urlencode(params))
    for a in range(5):
        try:
            r=urllib.request.Request(url,data=data,method='POST' if post else 'GET')
            with urllib.request.urlopen(r,timeout=120) as resp: return json.load(resp)
        except urllib.error.HTTPError as e:
            b=e.read().decode()
            if 'limit' in b.lower() and a<4: time.sleep(50); continue
            return {'__err':b[:500]}
        except Exception: 
            if a<4: time.sleep(15); continue
            return {'__err':'net'}
    return {}
t=req(LAL,{'fields':'targeting'}).get('targeting',{})
t.pop('custom_audiences',None)                      # remove o LAL de PT (o que trava a entrega)
# mantem excluded_custom_audiences (PP - LEAD30D) e excluded_geo_locations (PT)
IG=t.get('instagram_positions') or []
if 'explore_home' in IG and 'explore' not in IG:
    IG.insert(IG.index('explore_home'),'explore'); t['instagram_positions']=IG
print('TENTATIVA 1 targeting:',json.dumps(t,ensure_ascii=False))
r=req(LAL,{'targeting':json.dumps(t)},post=True); print('POST1:',json.dumps(r,ensure_ascii=False))
if '__err' in r:
    t2=dict(t); t2['instagram_positions']=['stream','story','reels','profile_feed']
    print('\nTENTATIVA 2 (sem explore):',json.dumps(t2.get('instagram_positions')))
    r=req(LAL,{'targeting':json.dumps(t2)},post=True); print('POST2:',json.dumps(r,ensure_ascii=False))
    if '__err' in r:
        t3={'age_min':t.get('age_min'),'age_max':t.get('age_max'),
            'geo_locations':t.get('geo_locations'),'excluded_geo_locations':t.get('excluded_geo_locations'),
            'excluded_custom_audiences':t.get('excluded_custom_audiences'),
            'publisher_platforms':['facebook','instagram'],'device_platforms':['mobile','desktop']}
        print('\nTENTATIVA 3 (posicoes automaticas):',json.dumps(t3,ensure_ascii=False))
        r=req(LAL,{'targeting':json.dumps(t3)},post=True); print('POST3:',json.dumps(r,ensure_ascii=False))
time.sleep(4)
d=req(LAL,{'fields':'name,effective_status,daily_budget,targeting,learning_stage_info'})
tt=d.get('targeting',{})
print('\n===== ESTADO FINAL [LAL 1%] =====')
print(json.dumps({'nome':d.get('name'),'st':d.get('effective_status'),
  'orc':int(d['daily_budget'])/100,'age':f"{tt.get('age_min')}-{tt.get('age_max')}",
  'geo':(tt.get('geo_locations') or {}).get('countries'),
  'geo_excl':(tt.get('excluded_geo_locations') or {}).get('countries'),
  'custom_audiences':[c.get('name') for c in (tt.get('custom_audiences') or [])],
  'exclusoes':[c.get('name') for c in (tt.get('excluded_custom_audiences') or [])],
  'plat':tt.get('publisher_platforms'),'ig_pos':tt.get('instagram_positions'),
  'fb_pos':tt.get('facebook_positions')},ensure_ascii=False))
de=req(f'{LAL}/delivery_estimate',{'fields':'estimate_mau_lower_bound,estimate_mau_upper_bound'})
print('TAMANHO PUBLICO:',json.dumps(de.get('data',[{}])[0],ensure_ascii=False))
print('\n===== TODOS OS CONJUNTOS =====')
for s in req('120256297322760002/adsets',{'fields':'name,effective_status,daily_budget,'
    'targeting{age_min,age_max,custom_audiences,geo_locations},learning_stage_info','limit':50}).get('data',[]):
    tt=s.get('targeting',{})
    print(json.dumps({'nome':s['name'][:46],'st':s['effective_status'],
      'orc':int(s['daily_budget'])/100,'age':f"{tt.get('age_min')}-{tt.get('age_max')}",
      'geo':(tt.get('geo_locations') or {}).get('countries'),
      'ca':[c.get('name') for c in (tt.get('custom_audiences') or [])],
      'conv':(s.get('learning_stage_info') or {}).get('conversions')},ensure_ascii=False))

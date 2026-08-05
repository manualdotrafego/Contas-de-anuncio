import os,json,urllib.request,urllib.parse,time
TOKEN=os.environ['META_ACCESS_TOKEN']; API='https://graph.facebook.com/v19.0'
INT='120256297322770002'   # INTERESSE RESTRITO
LAL='120256321507330002'   # LAL 1%
def req(path,params,post=False):
    params['access_token']=TOKEN
    data=urllib.parse.urlencode(params).encode() if post else None
    url=f"{API}/{path}" + ('' if post else '?'+urllib.parse.urlencode(params))
    for a in range(5):
        try:
            r=urllib.request.Request(url,data=data,method='POST' if post else 'GET')
            with urllib.request.urlopen(r,timeout=120) as resp: return json.load(resp)
        except urllib.error.HTTPError as e:
            b=e.read().decode()
            if 'limit' in b.lower() and a<4: time.sleep(50); continue
            return {'__err':b[:600]}
        except Exception as ex:
            if a<4: time.sleep(15); continue
            return {'__err':str(ex)[:300]}
    return {}

print('===== 1) ORCAMENTO [INTERESSE RESTRITO] =====')
b=req(INT,{'fields':'name,daily_budget,learning_stage_info'})
print('ANTES:',json.dumps(b,ensure_ascii=False))
r=req(INT,{'daily_budget':'1200'},post=True)
print('POST:',json.dumps(r,ensure_ascii=False))
time.sleep(3)
print('DEPOIS:',json.dumps(req(INT,{'fields':'name,daily_budget,effective_status,learning_stage_info'}),ensure_ascii=False))

print('\n===== 2) [LAL 1%] REMOVER PUBLICO PERSONALIZADO =====')
a=req(LAL,{'fields':'name,effective_status,daily_budget,targeting'})
print('ANTES nome:',a.get('name'))
t=a.get('targeting',{})
print('TARGETING ANTES:',json.dumps(t,ensure_ascii=False))
for k in ('custom_audiences','excluded_custom_audiences'):
    if k in t: print(f'  removendo {k}:',json.dumps(t[k],ensure_ascii=False)); t.pop(k)
# limpar chaves derivadas que a API costuma rejeitar no POST
for k in ('brand_safety_content_filter_levels','targeting_relaxation_types',
          'targeting_automation','is_whatsapp_destination_ad'):
    t.pop(k,None)
print('TARGETING NOVO:',json.dumps(t,ensure_ascii=False))
r=req(LAL,{'targeting':json.dumps(t)},post=True)
print('POST:',json.dumps(r,ensure_ascii=False))
if '__err' in r:
    print('-> tentando spec minima')
    t2={k:v for k,v in t.items() if k in ('geo_locations','age_min','age_max','genders',
        'publisher_platforms','facebook_positions','instagram_positions','messenger_positions',
        'device_platforms','locales')}
    print('SPEC MINIMA:',json.dumps(t2,ensure_ascii=False))
    r=req(LAL,{'targeting':json.dumps(t2)},post=True)
    print('POST 2:',json.dumps(r,ensure_ascii=False))
time.sleep(3)
d=req(LAL,{'fields':'name,effective_status,daily_budget,targeting,learning_stage_info'})
print('DEPOIS:',json.dumps(d,ensure_ascii=False))
de=req(f'{LAL}/delivery_estimate',{'fields':'estimate_mau_lower_bound,estimate_mau_upper_bound'})
print('TAMANHO PUBLICO DEPOIS:',json.dumps(de.get('data',[{}])[0],ensure_ascii=False))

print('\n===== RESUMO CONJUNTOS =====')
for s in req('120256297322760002/adsets',{'fields':'id,name,effective_status,daily_budget,'
    'targeting{age_min,age_max,custom_audiences,geo_locations,publisher_platforms},learning_stage_info','limit':50}).get('data',[]):
    t=s.get('targeting',{})
    print(json.dumps({'nome':s['name'][:45],'st':s['effective_status'],
      'orc':(int(s['daily_budget'])/100 if s.get('daily_budget') else None),
      'age':f"{t.get('age_min')}-{t.get('age_max')}",
      'geo':(t.get('geo_locations') or {}).get('countries'),
      'ca':[c.get('name') for c in (t.get('custom_audiences') or [])],
      'aprend':(s.get('learning_stage_info') or {}).get('status'),
      'conv':(s.get('learning_stage_info') or {}).get('conversions')},ensure_ascii=False))

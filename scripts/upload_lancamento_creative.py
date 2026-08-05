import os,json,urllib.request,urllib.parse,time
TOKEN=os.environ['META_ACCESS_TOKEN']; API='https://graph.facebook.com/v19.0'
LAL='120256321507330002'; NOVO='[PUBLICO ABERTO] - [ABERTO 24 - 45] - [POS IG E FB]'
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
            return {'__err':b[:400]}
        except Exception:
            if a<4: time.sleep(15); continue
            return {'__err':'net'}
    return {}
print('ANTES:',json.dumps(req(LAL,{'fields':'name,effective_status'}),ensure_ascii=False))
print('POST :',json.dumps(req(LAL,{'name':NOVO},post=True),ensure_ascii=False))
time.sleep(4)
print('DEPOIS:',json.dumps(req(LAL,{'fields':'name,effective_status,daily_budget,learning_stage_info'}),ensure_ascii=False))
print('\n===== CONJUNTOS DA CAMPANHA =====')
for s in req('120256297322760002/adsets',{'fields':'name,effective_status,daily_budget,'
    'targeting{age_min,age_max,custom_audiences},learning_stage_info','limit':50}).get('data',[]):
    t=s.get('targeting',{}); li=s.get('learning_stage_info') or {}
    print(json.dumps({'nome':s['name'],'st':s['effective_status'],
      'orc':int(s['daily_budget'])/100,'age':f"{t.get('age_min')}-{t.get('age_max')}",
      'ca':[c.get('name') for c in (t.get('custom_audiences') or [])],
      'conv':li.get('conversions'),'aprend':li.get('status')},ensure_ascii=False))
r=req('120256297322760002/insights',{'level':'campaign','date_preset':'today',
  'fields':'spend,impressions,inline_link_clicks,actions'})
for row in r.get('data',[]):
    a={x['action_type']:float(x['value']) for x in row.get('actions',[])}
    print('\nCAMPANHA HOJE:',json.dumps({'spend':row['spend'],'impr':row.get('impressions'),
      'lc':row.get('inline_link_clicks'),'lpv':a.get('landing_page_view'),'lead':a.get('lead')},ensure_ascii=False))

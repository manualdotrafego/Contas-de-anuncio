import os,json,urllib.request,urllib.parse,time
TOKEN=os.environ['META_ACCESS_TOKEN']; ACT='act_615338413578534'; API='https://graph.facebook.com/v19.0'
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
def A(r): return {x['action_type']:float(x['value']) for x in r.get('actions',[])}
def L(a): return a.get('lead') or a.get('offsite_conversion.fb_pixel_lead') or a.get('onsite_conversion.lead_grouped')
FLD='spend,impressions,clicks,inline_link_clicks,actions,reach,frequency'

print('=== CAMPANHAS COM GASTO HOJE (fuso da conta) ===')
r=get(f'{ACT}/insights',{'level':'campaign','date_preset':'today',
  'fields':'campaign_id,campaign_name,'+FLD,'limit':200})
BR=[]
for row in r.get('data',[]):
    a=A(row)
    print(json.dumps({'id':row['campaign_id'],'nome':row['campaign_name'],'spend':row['spend'],
      'impr':row.get('impressions'),'lc':row.get('inline_link_clicks'),'lpv':a.get('landing_page_view'),
      'lead':L(a),'reach':row.get('reach')},ensure_ascii=False))
    if 'BRASIL' in row['campaign_name'].upper(): BR.append(row['campaign_id'])

for cid in BR:
    c=get(cid,{'fields':'name,status,objective,created_time,start_time,daily_budget,lifetime_budget,bid_strategy'})
    print('\n=== CAMPANHA',c.get('name'),'===')
    print(json.dumps(c,ensure_ascii=False))
    st=get(f'{cid}/adsets',{'fields':'id,name,effective_status,daily_budget,optimization_goal,billing_event,'
      'targeting{age_min,age_max,genders,publisher_platforms,facebook_positions,instagram_positions,geo_locations,flexible_spec,interests},'
      'promoted_object','limit':50}).get('data',[])
    print('--- CONJUNTOS ---')
    for s in st:
        t=s.get('targeting',{})
        fs=t.get('flexible_spec') or []
        ints=[i.get('name') for g in fs for i in (g.get('interests') or [])]
        print(json.dumps({'nome':s['name'],'st':s['effective_status'],
          'orc':(int(s['daily_budget'])/100 if s.get('daily_budget') else None),
          'goal':s.get('optimization_goal'),'age':f"{t.get('age_min')}-{t.get('age_max')}",
          'gen':t.get('genders'),'plat':t.get('publisher_platforms'),
          'fbpos':t.get('facebook_positions'),'igpos':t.get('instagram_positions'),
          'interesses':ints[:12]},ensure_ascii=False))
    for lvl,bd,lab in [('adset',None,'ADSET'),('ad',None,'ANUNCIO'),
                       ('campaign','publisher_platform','PLATAFORMA'),
                       ('campaign','publisher_platform,platform_position','POSICAO'),
                       ('campaign','age','IDADE'),('campaign','age,gender','IDADE+GENERO'),
                       ('campaign','hourly_stats_aggregated_by_advertiser_time_zone','HORA')]:
        q={'level':lvl,'date_preset':'today','fields':('adset_name,ad_name,' if lvl!='campaign' else '')+FLD,'limit':500}
        if bd: q['breakdowns']=bd
        rr=get(f'{cid}/insights',q)
        print(f'--- {lab} ---')
        if '__err' in rr: print(' FALHOU',rr['__err'][:160]); continue
        for row in rr.get('data',[]):
            if float(row.get('spend',0))==0: continue
            a=A(row)
            k=[row.get(x) for x in bd.split(',')] if bd else (row.get('ad_name') or row.get('adset_name'))
            print(json.dumps({'k':k,'spend':row['spend'],'impr':row.get('impressions'),
              'lc':row.get('inline_link_clicks'),'lpv':a.get('landing_page_view'),'lead':L(a),
              'freq':row.get('frequency')},ensure_ascii=False))

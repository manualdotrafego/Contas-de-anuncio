import os,json,urllib.request,urllib.parse,time,datetime
TOKEN=os.environ['META_ACCESS_TOKEN']; API='https://graph.facebook.com/v19.0'; CID='120256297322760002'
def get(p,q):
    q['access_token']=TOKEN
    for a in range(5):
        try:
            with urllib.request.urlopen(f"{API}/{p}?{urllib.parse.urlencode(q)}",timeout=180) as r: return json.load(r)
        except urllib.error.HTTPError as e:
            b=e.read().decode()
            if 'limit' in b.lower() and a<4: time.sleep(50); continue
            return {'__err':b[:300]}
        except Exception: time.sleep(15)
    return {}
def A(r): return {x['action_type']:float(x['value']) for x in r.get('actions',[])}
def L(a): return a.get('lead') or a.get('offsite_conversion.fb_pixel_lead') or a.get('onsite_conversion.lead_grouped')
print('AGORA UTC:',datetime.datetime.utcnow().isoformat())
acc=get('act_615338413578534',{'fields':'timezone_name,currency,amount_spent,balance'})
print('CONTA:',json.dumps(acc,ensure_ascii=False))
ads=get(f'{CID}/adsets',{'fields':'id,name,effective_status,daily_budget,budget_remaining,'
  'learning_stage_info,optimization_goal,bid_strategy,created_time,'
  'targeting{age_min,age_max,publisher_platforms,custom_audiences,flexible_spec}','limit':50}).get('data',[])
print('\n--- CONJUNTOS ---')
info={}
for s in ads:
    t=s.get('targeting',{})
    fs=t.get('flexible_spec') or []
    ints=[i.get('name') for g in fs for i in (g.get('interests') or [])]
    info[s['id']]=s['name']
    print(json.dumps({'id':s['id'],'nome':s['name'],'st':s['effective_status'],
      'orc_dia':(int(s['daily_budget'])/100 if s.get('daily_budget') else None),
      'aprendizagem':s.get('learning_stage_info'),'goal':s.get('optimization_goal'),
      'bid':s.get('bid_strategy'),'criado':s.get('created_time'),
      'age':f"{t.get('age_min')}-{t.get('age_max')}",
      'ca':[c.get('name') for c in (t.get('custom_audiences') or [])],'int':ints[:10]},ensure_ascii=False))
    de=get(f"{s['id']}/delivery_estimate",{'fields':'estimate_dau,estimate_mau_lower_bound,estimate_mau_upper_bound'})
    if de.get('data'): print('   tamanho_publico:',json.dumps(de['data'][0],ensure_ascii=False))
F='spend,impressions,clicks,inline_link_clicks,actions,reach,frequency,cpm,ctr'
for prst,lab in [('today','HOJE'),('maximum','VIDA')]:
    r=get(f'{CID}/insights',{'level':'adset','date_preset':prst,'fields':'adset_id,adset_name,'+F,'limit':100})
    print(f'\n--- CONJUNTO {lab} ---')
    for row in r.get('data',[]):
        a=A(row)
        print(json.dumps({'nome':row['adset_name'][:44],'spend':row['spend'],'impr':row.get('impressions'),
          'reach':row.get('reach'),'freq':row.get('frequency'),'cpm':row.get('cpm'),'ctr':row.get('ctr'),
          'lc':row.get('inline_link_clicks'),'lpv':a.get('landing_page_view'),'lead':L(a)},ensure_ascii=False))
r=get(f'{CID}/insights',{'level':'campaign','date_preset':'today','fields':F,'limit':10})
for row in r.get('data',[]):
    a=A(row); print('\nCAMPANHA HOJE:',json.dumps({'spend':row['spend'],'impr':row.get('impressions'),
      'lc':row.get('inline_link_clicks'),'lpv':a.get('landing_page_view'),'lead':L(a),
      'freq':row.get('frequency'),'cpm':row.get('cpm')},ensure_ascii=False))
r=get(f'{CID}/insights',{'level':'adset','date_preset':'today','time_increment':'1',
  'breakdowns':'hourly_stats_aggregated_by_advertiser_time_zone','fields':'adset_name,spend,actions','limit':500})
print('\n--- GASTO POR HORA HOJE (conta, Lisboa) ---')
agg={}
for row in r.get('data',[]):
    h=row['hourly_stats_aggregated_by_advertiser_time_zone'][:5]
    agg.setdefault(h,[0,0]); agg[h][0]+=float(row['spend']); agg[h][1]+=(L(A(row)) or 0)
for h in sorted(agg): print(f'  {h}  EUR {agg[h][0]:6.2f}   leads {int(agg[h][1])}')

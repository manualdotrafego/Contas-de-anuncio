import os,json,urllib.request,urllib.parse,time,datetime
TOKEN=os.environ['META_ACCESS_TOKEN']; API='https://graph.facebook.com/v19.0'
CID='120256297322760002'
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
F='spend,impressions,clicks,inline_link_clicks,actions,reach,frequency,cpm,ctr'
print('AGORA (UTC):',datetime.datetime.utcnow().isoformat())
c=get(CID,{'fields':'name,status,effective_status,created_time,daily_budget,objective'})
print('CAMPANHA:',json.dumps(c,ensure_ascii=False))
print('\n--- CONJUNTOS (config atual) ---')
for s in get(f'{CID}/adsets',{'fields':'id,name,effective_status,daily_budget,optimization_goal,'
  'targeting{age_min,age_max,publisher_platforms,facebook_positions,instagram_positions}','limit':50}).get('data',[]):
    t=s.get('targeting',{})
    print(json.dumps({'nome':s['name'],'st':s['effective_status'],
      'orc':(int(s['daily_budget'])/100 if s.get('daily_budget') else None),
      'age':f"{t.get('age_min')}-{t.get('age_max')}",'plat':t.get('publisher_platforms')},ensure_ascii=False))
def blk(label,q):
    rr=get(f'{CID}/insights',q); print(f'\n--- {label} ---')
    if '__err' in rr: print(' FALHOU',rr['__err'][:170]); return
    if not rr.get('data'): print(' (vazio)'); return
    for row in rr['data']:
        if float(row.get('spend',0))==0: continue
        a=A(row); bd=q.get('breakdowns')
        k=[row.get(x) for x in bd.split(',')] if bd else (row.get('ad_name') or row.get('adset_name') or row.get('date_start'))
        print(json.dumps({'k':k,'spend':row['spend'],'impr':row.get('impressions'),
          'reach':row.get('reach'),'lc':row.get('inline_link_clicks'),'lpv':a.get('landing_page_view'),
          'lead':L(a),'cpm':row.get('cpm'),'ctr':row.get('ctr'),'freq':row.get('frequency')},ensure_ascii=False))
blk('TOTAL VIDA DA CAMPANHA',{'level':'campaign','date_preset':'maximum','fields':F,'limit':100})
blk('POR DIA',{'level':'campaign','date_preset':'maximum','time_increment':1,'fields':F,'limit':100})
blk('HOJE',{'level':'campaign','date_preset':'today','fields':F,'limit':100})
blk('POR CONJUNTO (vida)',{'level':'adset','date_preset':'maximum','fields':'adset_name,'+F,'limit':100})
blk('POR ANUNCIO (vida)',{'level':'ad','date_preset':'maximum','fields':'ad_name,adset_name,'+F,'limit':100})
blk('PLATAFORMA (vida)',{'level':'campaign','date_preset':'maximum','breakdowns':'publisher_platform','fields':F,'limit':100})
blk('POSICAO (vida)',{'level':'campaign','date_preset':'maximum','breakdowns':'publisher_platform,platform_position','fields':F,'limit':200})
blk('IDADE (vida)',{'level':'campaign','date_preset':'maximum','breakdowns':'age','fields':F,'limit':100})
blk('IDADE+GENERO (vida)',{'level':'campaign','date_preset':'maximum','breakdowns':'age,gender','fields':F,'limit':200})
blk('HORA (vida)',{'level':'campaign','date_preset':'maximum','breakdowns':'hourly_stats_aggregated_by_advertiser_time_zone','fields':F,'limit':200})

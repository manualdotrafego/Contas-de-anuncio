import requests, os, json, time
from datetime import date
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
today=date.today().isoformat()
PT=["120248546729160002","120254908221730002","120255355949960002"]
BR=["120256165865940002","120256131329440002"]
CICLOS=[(1,"26/03 - 01/04","2026-03-26","2026-04-01"),(2,"02/04 - 08/04","2026-04-02","2026-04-08"),
 (3,"09/04 - 15/04","2026-04-09","2026-04-15"),(4,"16/04 - 22/04","2026-04-16","2026-04-22"),
 (5,"23/04 - 29/04","2026-04-23","2026-04-29"),(6,"30/04 - 06/05","2026-04-30","2026-05-06"),
 (7,"07/05 - 13/05","2026-05-07","2026-05-13"),(8,"14/05 - 20/05","2026-05-14","2026-05-20"),
 (9,"21/05 - 27/05","2026-05-21","2026-05-27"),(10,"28/05 - 03/06","2026-05-28","2026-06-03"),
 (11,"04/06 - 10/06","2026-06-04","2026-06-10"),(12,"11/06 - 17/06","2026-06-11","2026-06-17"),
 (13,"18/06 - 23/06","2026-06-18","2026-06-23"),(14,"24/06 - 30/06","2026-06-24","2026-06-30"),
 (15,"01/07 - 07/07","2026-07-01","2026-07-07"),(16,"08/07 - 14/07","2026-07-08","2026-07-14"),
 (17,"15/07 - 21/07","2026-07-15","2026-07-21"),(18,"22/07 - 28/07","2026-07-22","2026-07-28"),
 (19,"29/07 - 04/08","2026-07-29","2026-08-04")]
def gm(a):
    l=lc=0
    for x in a or []:
        t=x.get('action_type',''); v=int(x.get('value',0))
        if t in('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'): l=max(l,v)
        elif t=='link_click': lc=v
    return l,lc
def req(url,params):
    for t in range(6):
        r=requests.get(url,params=params,timeout=60).json()
        if 'error' not in r: return r
        time.sleep(12)
    return {}
print("## CSVSTART")
print("pais|ciclo|periodo|ad_name|spend|impressions|clicks|link_clicks|leads|cpm|ctr|cpc_link|cpl")
for pais,camps,inicio in [("PT",PT,1),("BR",BR,19)]:
    for (cn,per,since,until) in CICLOS:
        if cn<inicio: continue
        for cid in camps:
            r=req(f"{BASE}/{cid}/insights",{'level':'ad',
                'fields':'ad_name,spend,impressions,clicks,actions,cpm,ctr',
                'time_range':json.dumps({'since':since,'until':until}),'limit':200,'access_token':TOKEN})
            for d in r.get('data',[]):
                sp=float(d.get('spend',0))
                if sp==0: continue
                l,lc=gm(d.get('actions',[]))
                cpc=sp/lc if lc else 0; cpl=sp/l if l else 0
                nm=d.get('ad_name','').replace('|','/').replace('\n',' ')
                print(f"{pais}|{cn}|{per}|{nm}|{sp:.2f}|{int(d.get('impressions',0))}|{int(d.get('clicks',0))}|{lc}|{l}|{float(d.get('cpm',0)):.2f}|{float(d.get('ctr',0)):.2f}|{cpc:.2f}|{cpl if l else 0:.2f}")
print("## CSVEND")
print("## THUMBSTART")
seen=set()
for cid in PT+BR:
    r=req(f"{BASE}/{cid}/ads",{'fields':'name,creative{thumbnail_url,image_url,effective_object_story_id}','limit':100,'access_token':TOKEN})
    for ad in r.get('data',[]):
        nm=ad.get('name','').strip()
        if nm in seen: continue
        c=ad.get('creative',{})
        th=c.get('thumbnail_url','') or c.get('image_url','')
        eosi=c.get('effective_object_story_id',''); u=""
        if eosi and '_' in eosi:
            pg,po=eosi.split('_',1); u=f"https://www.facebook.com/{pg}/posts/{po}"
        if th: seen.add(nm); print(f"##T|{nm}|{th}|{u}")
print("## THUMBEND")

import requests, os, json
from datetime import date
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
today=date.today().isoformat()
PT=[("120255355949960002","TESTE MAFRA"),("120254908221730002","CBO ESCALA")]
BR=[("120256165865940002","BR LP AJUSTADA"),("120256131329440002","BR CICLO TESTE")]
def gm(a):
    l=lc=0
    for x in a or []:
        t=x.get('action_type',''); v=int(x.get('value',0))
        if t in('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'): l=max(l,v)
        elif t=='link_click': lc=v
    return l,lc

for grupo,camps in [("PT",PT),("BR",BR)]:
    print(f"\n## {grupo} — conjuntos (ciclo 19: 29/07 -> {today})")
    for cid,cn in camps:
        r=requests.get(f"{BASE}/{cid}/insights",params={
            'level':'adset','fields':'adset_id,adset_name,spend,impressions,actions,ctr',
            'time_range':json.dumps({'since':'2026-07-29','until':today}),
            'limit':100,'access_token':TOKEN},timeout=40).json()
        for d in r.get('data',[]):
            sp=float(d.get('spend',0))
            if sp==0: continue
            l,lc=gm(d.get('actions',[]))
            cpl=sp/l if l else 0
            # budget atual
            b=requests.get(f"{BASE}/{d['adset_id']}",params={'fields':'daily_budget,effective_status','access_token':TOKEN},timeout=20).json()
            db=int(b.get('daily_budget') or 0)/100
            st=b.get('effective_status','')
            print(f"##A|{grupo}|{d['adset_id']}|{d.get('adset_name','')[:44]}|{cn}|{sp:.2f}|{l}|{cpl:.2f}|{db:.2f}|{st}")

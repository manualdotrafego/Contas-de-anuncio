import requests, os, json
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
BR=["120256165865940002","120256131329440002"]
for cid in BR:
    c=requests.get(f"{BASE}/{cid}",params={'fields':'name','access_token':TOKEN},timeout=30).json()
    print(f"\n## CAMPANHA: {c.get('name')}")
    r=requests.get(f"{BASE}/{cid}/adsets",params={
        'fields':'id,name,effective_status,targeting','limit':100,'access_token':TOKEN},timeout=40).json()
    for s in r.get('data',[]):
        t=s.get('targeting',{})
        pp=t.get('publisher_platforms')
        fbp=t.get('facebook_positions'); igp=t.get('instagram_positions')
        anp=t.get('audience_network_positions'); mnp=t.get('messenger_positions')
        auto = pp is None
        print(f"##S|{s['id']}|{s['name'][:40]}|{s.get('effective_status')}|auto={auto}|pp={pp}|an_pos={anp}")
# desempenho por plataforma (ultimos 6 dias)
print("\n## DESEMPENHO POR PLATAFORMA (BR, 29/07-hoje)")
from datetime import date
def gm(a):
    l=0
    for x in a or []:
        if x.get('action_type') in ('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'):
            l=max(l,int(x.get('value',0)))
    return l
for cid in BR:
    r=requests.get(f"{BASE}/{cid}/insights",params={
        'fields':'spend,impressions,actions','breakdowns':'publisher_platform',
        'time_range':json.dumps({'since':'2026-07-29','until':date.today().isoformat()}),
        'access_token':TOKEN},timeout=40).json()
    for d in r.get('data',[]):
        sp=float(d.get('spend',0)); l=gm(d.get('actions',[]))
        cpl=sp/l if l else 0
        print(f"##PL|{d.get('publisher_platform')}|{sp:.2f}|{l}|{cpl:.2f}|{int(d.get('impressions',0))}")

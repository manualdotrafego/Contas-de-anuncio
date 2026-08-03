import requests, os, json, time
from datetime import date
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
CID="120256165865940002"  # BR LP AJUSTADA
hoje=date.today().isoformat()

# 1. Estado atual dos posicionamentos
print("## POSICIONAMENTOS AGORA")
for tent in range(4):
    r=requests.get(f"{BASE}/{CID}/adsets",params={
        'fields':'id,name,effective_status,targeting','limit':50,'access_token':TOKEN},timeout=60).json()
    if 'error' in r:
        print(f"   (rate limit, tentativa {tent+1})"); time.sleep(20); continue
    for s in r.get('data',[]):
        if s.get('effective_status') in ('ACTIVE','IN_PROCESS'):
            pp=s.get('targeting',{}).get('publisher_platforms')
            an = 'SEM AN' if pp==['facebook','instagram'] else ('AUTO (com AN)' if pp is None else str(pp))
            print(f"##P|{s['name'][:38]}|{an}")
    break

# 2. Gasto por hora hoje
print(f"\n## GASTO POR HORA HOJE ({hoje})")
for tent in range(4):
    r=requests.get(f"{BASE}/{CID}/insights",params={
        'fields':'spend,impressions,actions',
        'breakdowns':'hourly_stats_aggregated_by_advertiser_time_zone',
        'time_range':json.dumps({'since':hoje,'until':hoje}),
        'access_token':TOKEN},timeout=60).json()
    if 'error' in r:
        print(f"   (rate limit, tentativa {tent+1})"); time.sleep(20); continue
    tot_antes=0; tot_depois=0; l_antes=0; l_depois=0
    for d in r.get('data',[]):
        h=d.get('hourly_stats_aggregated_by_advertiser_time_zone','')
        sp=float(d.get('spend',0))
        l=0
        for a in d.get('actions',[]) or []:
            if a.get('action_type') in ('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'):
                l=max(l,int(a.get('value',0)))
        hi=int(h.split(':')[0]) if h else 0
        print(f"##H|{h}|{sp:.2f}|{l}")
        if hi<11: tot_antes+=sp; l_antes+=l
        else: tot_depois+=sp; l_depois+=l
    print(f"##RESUMO|antes11h|{tot_antes:.2f}|{l_antes}|depois11h|{tot_depois:.2f}|{l_depois}")
    break

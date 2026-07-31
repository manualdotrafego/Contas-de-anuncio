import requests, os, json, unicodedata
from datetime import date
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
ACCT="act_615338413578534"
today=date.today()
def norm(s): return ''.join(c for c in unicodedata.normalize('NFD',s) if unicodedata.category(c)!='Mn').lower()
def gm(a):
    l=lc=0
    for x in a or []:
        t=x.get('action_type',''); v=int(x.get('value',0))
        if t in('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'): l=max(l,v)
        elif t=='link_click': lc=v
    return l,lc

print(f"## HOJE={today}")
# 1. Todas campanhas: achar as com Brasil
r=requests.get(f"{BASE}/{ACCT}/campaigns",params={
    'fields':'id,name,effective_status,created_time','limit':300,'access_token':TOKEN},timeout=40).json()
camps=r.get('data',[])
brasil=[c for c in camps if 'brasil' in norm(c.get('name','')) or ' br' in norm(c.get('name',''))]
print(f"\n## CAMPANHAS COM 'BRASIL' ({len(brasil)}):")
for c in brasil:
    print(f"##B|{c['id']}|{c['name']}|{c.get('effective_status')}|{c.get('created_time','')[:10]}")

# 2. Gasto de cada uma nos ultimos 60d para ver quais rodaram
print(f"\n## GASTO 60D DAS BRASIL:")
for c in brasil:
    d=requests.get(f"{BASE}/{c['id']}/insights",params={'fields':'spend,actions',
        'time_range':json.dumps({'since':(today.replace(day=1)).isoformat() if False else '2026-06-01','until':today.isoformat()}),
        'access_token':TOKEN},timeout=30).json().get('data',[])
    if d:
        sp=float(d[0].get('spend',0)); l,_=gm(d[0].get('actions',[]))
        print(f"##G|{c['name'][:45]}|{sp:.2f}|{l}")
    else:
        print(f"##G|{c['name'][:45]}|0|0")

# 3. Ciclo atual (18: 22-28/07) das 3 campanhas de sempre
CAMPS=[("120255355949960002","TESTE MAFRA"),("120254908221730002","CBO ESCALA"),("120248546729160002","NOVA CAPTACAO")]
since="2026-07-22"; until=min(today.isoformat(),"2026-07-28")
tot={'spend':0,'imp':0,'clk':0,'lc':0,'leads':0}
print(f"\n## CICLO18: {since} -> {until}")
for cid,nm in CAMPS:
    d=requests.get(f"{BASE}/{cid}/insights",params={'fields':'spend,impressions,clicks,actions',
        'time_range':json.dumps({'since':since,'until':until}),'access_token':TOKEN},timeout=30).json().get('data',[])
    if not d: continue
    d=d[0]; sp=float(d.get('spend',0)); l,lc=gm(d.get('actions',[]))
    print(f"   {nm}: EUR{sp:.2f} | {l} leads")
    tot['spend']+=sp; tot['imp']+=int(d.get('impressions',0)); tot['clk']+=int(d.get('clicks',0)); tot['lc']+=lc; tot['leads']+=l
n=(date.fromisoformat(until)-date.fromisoformat(since)).days+1
cpm=tot['spend']/tot['imp']*1000 if tot['imp'] else 0
ctr=tot['clk']/tot['imp']*100 if tot['imp'] else 0
cpc=tot['spend']/tot['lc'] if tot['lc'] else 0
conv=tot['leads']/tot['lc']*100 if tot['lc'] else 0
cpl=tot['spend']/tot['leads'] if tot['leads'] else 0
print(f"##C18|{n}|{tot['spend']:.2f}|{tot['imp']}|{tot['clk']}|{cpm:.2f}|{ctr:.2f}|{cpc:.2f}|{tot['leads']}|{conv:.2f}|{cpl:.2f}")

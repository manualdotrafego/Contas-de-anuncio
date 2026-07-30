import requests, os, json
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
ACCT="act_615338413578534"

TERMOS = ["Agência de publicidade","Marketing digital","Geração de leads","AdWords","Google AdWords","Publicidade"]
print("=== BUSCA DE INTERESSES ===")
for t in TERMOS:
    r=requests.get(f"{BASE}/search",params={
        'type':'adinterest','q':t,'limit':6,'locale':'pt_BR','access_token':TOKEN},timeout=30).json()
    print(f"\n>> '{t}'")
    if 'error' in r:
        print(f"   ERRO: {r['error'].get('message','')[:120]}"); continue
    for i in r.get('data',[])[:6]:
        path=' > '.join(i.get('path',[])) if i.get('path') else ''
        print(f"   ID={i.get('id')} | {i.get('name')} | audience={i.get('audience_size_lower_bound','?')}-{i.get('audience_size_upper_bound','?')} | {path}")

print("\n\n=== PUBLICOS PERSONALIZADOS (buscando 'Engajamento Instagram') ===")
url=f"{BASE}/{ACCT}/customaudiences"
params={'fields':'id,name,subtype,approximate_count_lower_bound,retention_days','limit':100,'access_token':TOKEN}
while url:
    r=requests.get(url,params=params,timeout=30).json()
    if 'error' in r: print("ERRO:",r['error'].get('message','')[:150]); break
    for a in r.get('data',[]):
        nm=a.get('name','')
        if 'ngajament' in nm or 'nstagram' in nm or '90' in nm:
            print(f"   ID={a['id']} | {nm} | {a.get('subtype')} | ~{a.get('approximate_count_lower_bound','?')} pessoas")
    url=r.get('paging',{}).get('next',''); params={}

print("\n=== GEO BRASIL ===")
r=requests.get(f"{BASE}/search",params={
    'type':'adgeolocation','location_types':json.dumps(['country']),'q':'Brazil','limit':3,'access_token':TOKEN},timeout=30).json()
for g in r.get('data',[]):
    print(f"   key={g.get('key')} | {g.get('name')} | {g.get('country_code')}")

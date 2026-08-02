import requests, os, time
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
ALVOS=[("120255823851330002","PT [AD SET 1.22]"),("120256165866030002","BR [AD SET 1.10]")]
print("=== DEFINIR EUR30/dia NOS DOIS ===")
for aid,lbl in ALVOS:
    a=requests.get(f"{BASE}/{aid}",params={'fields':'daily_budget','access_token':TOKEN},timeout=30).json()
    cur=int(a.get('daily_budget') or 0)/100
    pr=requests.post(f"{BASE}/{aid}",data={'daily_budget':'3000','access_token':TOKEN},timeout=30).json()
    ok=pr.get('success',False)
    print(f"  {'OK' if ok else 'ERRO'} {lbl}: EUR{cur:.2f} -> EUR30.00 {'' if ok else pr}")
    time.sleep(0.4)

print("\n=== VERIFICACAO ===")
for aid,lbl in ALVOS:
    v=requests.get(f"{BASE}/{aid}",params={'fields':'name,daily_budget,effective_status','access_token':TOKEN},timeout=30).json()
    print(f"  {v.get('name','')[:44]} | EUR{int(v.get('daily_budget') or 0)/100:.2f}/d | {v.get('effective_status')}")

print("\n=== TOTAIS ===")
tot_pt=0; tot_br=0
for cid,tag in [("120255355949960002","PT"),("120256165865940002","BR")]:
    r=requests.get(f"{BASE}/{cid}/adsets",params={'fields':'name,effective_status,daily_budget','limit':100,'access_token':TOKEN},timeout=40).json()
    for s in r.get('data',[]):
        if s.get('effective_status') in ('ACTIVE','IN_PROCESS'):
            db=int(s.get('daily_budget') or 0)/100
            if tag=="PT": tot_pt+=db
            else: tot_br+=db
c=requests.get(f"{BASE}/120254908221730002",params={'fields':'daily_budget,effective_status','access_token':TOKEN},timeout=30).json()
cbo=int(c.get('daily_budget') or 0)/100
if c.get('effective_status') in ('ACTIVE','IN_PROCESS'): tot_pt+=cbo
print(f"  PT: EUR{tot_pt:.2f}/dia (inclui CBO EUR{cbo:.2f})")
print(f"  BR: EUR{tot_br:.2f}/dia")
print(f"  TOTAL: EUR{tot_pt+tot_br:.2f}/dia")

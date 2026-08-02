import requests, os, time
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
# (id, label, budget_atual)
ALVOS=[
 ("120255823851330002","PT [AD SET 1.22] — 24 leads · CPL EUR2,30", 20.00),
 ("120256165866030002","BR [AD SET 1.10] — 37 leads · CPL EUR0,86", 15.00),
]
print("=== +30% NO MELHOR CONJUNTO DE CADA PAIS ===")
for aid,lbl,cur in ALVOS:
    novo=round(cur*1.30, 2)
    cents=str(int(round(novo*100)))
    pr=requests.post(f"{BASE}/{aid}",data={'daily_budget':cents,'access_token':TOKEN},timeout=30).json()
    ok=pr.get('success',False)
    print(f"  {'✅' if ok else '❌'} {lbl}: EUR{cur:.2f} -> EUR{novo:.2f} {'' if ok else pr}")
    time.sleep(0.4)

print("\n=== VERIFICACAO ===")
for aid,lbl,_ in ALVOS:
    v=requests.get(f"{BASE}/{aid}",params={'fields':'name,daily_budget,effective_status','access_token':TOKEN},timeout=30).json()
    print(f"  {v.get('name','')[:42]} | EUR{int(v.get('daily_budget') or 0)/100:.2f}/d | {v.get('effective_status')}")

print("\n=== NOVO TOTAL DIARIO ===")
tot_pt=0; tot_br=0
for cid,tag in [("120255355949960002","PT"),("120256165865940002","BR")]:
    r=requests.get(f"{BASE}/{cid}/adsets",params={'fields':'name,effective_status,daily_budget','limit':100,'access_token':TOKEN},timeout=40).json()
    for s in r.get('data',[]):
        if s.get('effective_status') in ('ACTIVE','IN_PROCESS'):
            db=int(s.get('daily_budget') or 0)/100
            if tag=="PT": tot_pt+=db
            else: tot_br+=db
c=requests.get(f"{BASE}/120254908221730002",params={'fields':'daily_budget,effective_status','access_token':TOKEN},timeout=30).json()
if c.get('effective_status') in ('ACTIVE','IN_PROCESS'): tot_pt+=int(c.get('daily_budget') or 0)/100
print(f"  PT: EUR{tot_pt:.2f}/dia")
print(f"  BR: EUR{tot_br:.2f}/dia")
print(f"  TOTAL: EUR{tot_pt+tot_br:.2f}/dia")

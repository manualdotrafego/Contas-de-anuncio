import requests, os, json
from datetime import date
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
today=date.today()
PT=[("120255355949960002","TESTE MAFRA"),("120254908221730002","CBO ESCALA"),("120248546729160002","NOVA CAPTACAO")]
BR=[("120256165865940002","BR LP AJUSTADA"),("120256131329440002","BR CICLO TESTE")]

def budgets(camps, tag):
    tot=0
    for cid,nm in camps:
        c=requests.get(f"{BASE}/{cid}",params={'fields':'name,effective_status,daily_budget','access_token':TOKEN},timeout=30).json()
        cdb=int(c.get('daily_budget') or 0)/100
        st=c.get('effective_status','')
        if cdb>0:
            if st in ('ACTIVE','IN_PROCESS'): tot+=cdb
            print(f"##B|{tag}|{nm}|CBO|{cdb:.2f}|{st}")
        else:
            a=requests.get(f"{BASE}/{cid}/adsets",params={'fields':'name,effective_status,daily_budget','limit':100,'access_token':TOKEN},timeout=30).json()
            for s in a.get('data',[]):
                sdb=int(s.get('daily_budget') or 0)/100
                sst=s.get('effective_status','')
                if sst in ('ACTIVE','IN_PROCESS') and sdb>0:
                    tot+=sdb
                    print(f"##B|{tag}|{nm} > {s['name'][:32]}|ABO|{sdb:.2f}|{sst}")
    print(f"##T|{tag}|{tot:.2f}")

def diario(camps, tag):
    dias={}
    for cid,nm in camps:
        r=requests.get(f"{BASE}/{cid}/insights",params={'fields':'spend',
            'time_range':json.dumps({'since':'2026-07-29','until':today.isoformat()}),
            'time_increment':1,'access_token':TOKEN},timeout=30).json().get('data',[])
        for d in r:
            dias[d['date_start']]=dias.get(d['date_start'],0)+float(d.get('spend',0))
    for dt in sorted(dias): print(f"##D|{tag}|{dt}|{dias[dt]:.2f}")
    if dias:
        print(f"##M|{tag}|{sum(dias.values())/len(dias):.2f}|{len(dias)}")

print("## ORCAMENTOS CONFIGURADOS AGORA")
budgets(PT,"PT"); budgets(BR,"BR")
print("\n## GASTO REAL POR DIA (ciclo 19)")
diario(PT,"PT"); diario(BR,"BR")

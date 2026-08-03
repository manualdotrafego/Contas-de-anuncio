import requests, os, json, time
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
BR=["120256165865940002","120256131329440002"]
alvos=[]
for cid in BR:
    for tent in range(3):
        r=requests.get(f"{BASE}/{cid}/adsets",params={
            'fields':'id,name,effective_status,targeting','limit':100,'access_token':TOKEN},timeout=60).json()
        if 'error' in r:
            print(f"  !! erro listando {cid}: {r['error'].get('message','')[:100]} (tentativa {tent+1})")
            time.sleep(3); continue
        d=r.get('data',[])
        print(f"  campanha {cid}: {len(d)} conjuntos")
        for s in d:
            alvos.append((s['id'], s['name'][:38], s.get('effective_status'), s.get('targeting',{})))
        break

print(f"\n=== REMOVENDO AUDIENCE NETWORK ({len(alvos)} conjuntos) ===")
ok=0; err=0; skip=0
for aid,nm,st,t in alvos:
    if t.get('publisher_platforms')==["facebook","instagram"]:
        skip+=1; print(f"  JA  [{st[:8]}] {nm}"); continue
    novo=dict(t)
    novo['publisher_platforms']=["facebook","instagram"]
    for k in ('audience_network_positions','messenger_positions','facebook_positions','instagram_positions'):
        novo.pop(k,None)
    pr=requests.post(f"{BASE}/{aid}",data={'targeting':json.dumps(novo),'access_token':TOKEN},timeout=60).json()
    if pr.get('success'):
        ok+=1; print(f"  OK  [{st[:8]}] {nm}")
    else:
        err+=1; e=pr.get('error',{}); print(f"  ERR [{st[:8]}] {nm} -> {e.get('error_user_msg', e.get('message',''))[:110]}")
    time.sleep(0.35)
print(f"\n=== {ok} alterados | {skip} ja estavam | {err} erros ===")

print("\n=== ATIVOS — POSICIONAMENTO FINAL ===")
for cid in BR:
    r=requests.get(f"{BASE}/{cid}/adsets",params={
        'fields':'name,effective_status,targeting','limit':100,'access_token':TOKEN},timeout=60).json()
    for s in r.get('data',[]):
        if s.get('effective_status') in ('ACTIVE','IN_PROCESS'):
            print(f"  {s['name'][:42]} -> {s.get('targeting',{}).get('publisher_platforms')}")

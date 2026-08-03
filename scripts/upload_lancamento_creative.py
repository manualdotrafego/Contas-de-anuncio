import requests, os, json, time
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
BR=["120256165865940002","120256131329440002"]

FB_POS=["feed","right_hand_column","marketplace","video_feeds","story","search","facebook_reels","profile_feed"]
IG_POS=["stream","story","explore","reels","profile_feed","ig_search"]

alvos=[]
for cid in BR:
    r=requests.get(f"{BASE}/{cid}/adsets",params={
        'fields':'id,name,effective_status,targeting','limit':100,'access_token':TOKEN},timeout=40).json()
    for s in r.get('data',[]):
        alvos.append((s['id'], s['name'][:38], s.get('effective_status'), s.get('targeting',{})))

print(f"=== REMOVENDO AUDIENCE NETWORK ({len(alvos)} conjuntos) ===")
ok=0; err=0
for aid,nm,st,t in alvos:
    novo=dict(t)
    novo['publisher_platforms']=["facebook","instagram"]
    novo['facebook_positions']=FB_POS
    novo['instagram_positions']=IG_POS
    novo.pop('audience_network_positions',None)
    novo.pop('messenger_positions',None)
    pr=requests.post(f"{BASE}/{aid}",data={'targeting':json.dumps(novo),'access_token':TOKEN},timeout=40).json()
    if pr.get('success'):
        ok+=1; print(f"  OK  [{st[:8]}] {nm}")
    else:
        err+=1; print(f"  ERR [{st[:8]}] {nm} -> {str(pr)[:150]}")
    time.sleep(0.35)
print(f"\n=== {ok} atualizados | {err} erros ===")

print("\n=== VERIFICACAO (ativos) ===")
for cid in BR:
    r=requests.get(f"{BASE}/{cid}/adsets",params={
        'fields':'name,effective_status,targeting','limit':100,'access_token':TOKEN},timeout=40).json()
    for s in r.get('data',[]):
        if s.get('effective_status') in ('ACTIVE','IN_PROCESS'):
            pp=s.get('targeting',{}).get('publisher_platforms')
            print(f"  {s['name'][:40]} -> {pp}")

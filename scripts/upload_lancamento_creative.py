import requests, os
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
CID="120255355949960002"
r=requests.get(f"{BASE}/{CID}/ads",params={
    'fields':'name,creative{effective_object_story_id}','limit':100,'access_token':TOKEN},timeout=40).json()
for ad in r.get('data',[]):
    nm=ad.get('name','').strip()
    if nm in ('dono_de_agencia','voce_e_agencia'):
        eosi=ad.get('creative',{}).get('effective_object_story_id','')
        if eosi and '_' in eosi:
            pg,po=eosi.split('_',1)
            print(f"##L|{nm}|https://www.facebook.com/{pg}/posts/{po}")

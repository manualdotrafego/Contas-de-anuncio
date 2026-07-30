import requests, os, json
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
for t in ["Geração de lead","Lead generation","Geracao de leads","Prospecção de vendas","Lead"]:
    for loc in ['pt_BR','en_US']:
        r=requests.get(f"{BASE}/search",params={
            'type':'adinterest','q':t,'limit':5,'locale':loc,'access_token':TOKEN},timeout=30).json()
        d=r.get('data',[])
        if d:
            print(f">> '{t}' ({loc})")
            for i in d[:5]:
                path=' > '.join(i.get('path',[])) if i.get('path') else ''
                print(f"   ID={i.get('id')} | {i.get('name')} | {i.get('audience_size_lower_bound','?')} | {path}")

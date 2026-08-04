import requests, os, json, time
from datetime import date, timedelta
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
hoje=date.today(); since=(hoje-timedelta(days=6)).isoformat(); until=hoje.isoformat()
BR=[("120256165865940002","[WEBNAR BRASIL] LP AJUSTADA"),("120256131329440002","[WEBNAR BRASIL] CICLO TESTE")]
PT=[("120255355949960002","[CAMPANHA WEBNAIR] TESTE MAFRA"),("120254908221730002","[CBO WEBNAIR] ESCALA"),("120248546729160002","[NOVA CAPTACAO] WEBNAR")]
def gm(a):
    l=lc=0
    for x in a or []:
        t=x.get('action_type',''); v=int(x.get('value',0))
        if t in('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'): l=max(l,v)
        elif t=='link_click': lc=v
    return l,lc
def grupo(camps,tag):
    tot={'s':0,'i':0,'c':0,'lc':0,'l':0}
    for cid,nm in camps:
        for t in range(5):
            r=requests.get(f"{BASE}/{cid}/insights",params={'fields':'spend,impressions,clicks,actions',
                'time_range':json.dumps({'since':since,'until':until}),'access_token':TOKEN},timeout=60).json()
            if 'error' in r: time.sleep(15); continue
            d=r.get('data',[])
            if not d: print(f"##C|{tag}|{nm}|0.00|0|0"); break
            d=d[0]; sp=float(d.get('spend',0)); l,lc=gm(d.get('actions',[]))
            cpl=sp/l if l else 0
            print(f"##C|{tag}|{nm}|{sp:.2f}|{l}|{cpl:.2f}")
            tot['s']+=sp; tot['i']+=int(d.get('impressions',0)); tot['c']+=int(d.get('clicks',0)); tot['lc']+=lc; tot['l']+=l
            break
    cpl=tot['s']/tot['l'] if tot['l'] else 0
    cpm=tot['s']/tot['i']*1000 if tot['i'] else 0
    ctr=tot['c']/tot['i']*100 if tot['i'] else 0
    print(f"##T|{tag}|{tot['s']:.2f}|{tot['i']}|{tot['c']}|{tot['lc']}|{tot['l']}|{cpm:.2f}|{ctr:.2f}|{cpl:.2f}")
print(f"## PERIODO|{since}|{until}")
grupo(BR,"BRASIL"); grupo(PT,"PORTUGAL")

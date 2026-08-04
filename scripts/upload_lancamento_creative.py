import requests, os, json, time
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
CID="120256165865940002"  # LP AJUSTADA (94% dos leads)
def gm(a):
    l=lc=lpv=0
    for x in a or []:
        t=x.get('action_type',''); v=int(x.get('value',0))
        if t in('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'): l=max(l,v)
        elif t=='link_click': lc=v
        elif t=='landing_page_view': lpv=v
    return l,lc,lpv
def puxa(bd, tag, level='campaign'):
    for t in range(5):
        p={'fields':'spend,impressions,clicks,actions','date_preset':'maximum','level':level,'limit':100,'access_token':TOKEN}
        if bd: p['breakdowns']=bd
        if level=='adset': p['fields']+=',adset_name'
        r=requests.get(f"{BASE}/{CID}/insights",params=p,timeout=60).json()
        if 'error' in r:
            time.sleep(15); continue
        print(f"\n## {tag}")
        for d in r.get('data',[]):
            sp=float(d.get('spend',0))
            if sp==0: continue
            l,lc,lpv=gm(d.get('actions',[]))
            seg=' / '.join(str(d.get(k)) for k in bd.split(',')) if bd else (d.get('adset_name','')[:34] if level=='adset' else 'TOTAL')
            imp=int(d.get('impressions',0))
            c2lp = lpv/lc*100 if lc else 0
            lp2l = l/lpv*100 if lpv else 0
            cpl = sp/l if l else 0
            print(f"##R|{seg}|{sp:.2f}|{imp}|{lc}|{lpv}|{l}|{c2lp:.0f}|{lp2l:.0f}|{cpl:.2f}")
        return
    print(f"\n## {tag} -> rate limit")

puxa(None,"TOTAL GERAL")
puxa("publisher_platform,platform_position","POR POSICIONAMENTO")
puxa("age","POR IDADE")
puxa("gender","POR SEXO")
puxa(None,"POR CONJUNTO (publico)",level='adset')
puxa("impression_device","POR DISPOSITIVO")

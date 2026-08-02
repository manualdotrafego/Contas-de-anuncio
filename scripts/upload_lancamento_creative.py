import requests, os, json
from datetime import date
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
today=date.today()
PT=[("120255355949960002","TESTE MAFRA"),("120254908221730002","CBO ESCALA"),("120248546729160002","NOVA CAPTACAO")]
BR=[("120256165865940002","BR LP AJUSTADA"),("120256131329440002","BR CICLO TESTE")]
def gm(a):
    l=lc=0
    for x in a or []:
        t=x.get('action_type',''); v=int(x.get('value',0))
        if t in('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'): l=max(l,v)
        elif t=='link_click': lc=v
    return l,lc
def bloco(camps, since, until, tag):
    tot={'spend':0,'imp':0,'clk':0,'lc':0,'leads':0}
    for cid,nm in camps:
        d=requests.get(f"{BASE}/{cid}/insights",params={'fields':'spend,impressions,clicks,actions',
            'time_range':json.dumps({'since':since,'until':until}),'access_token':TOKEN},timeout=30).json().get('data',[])
        if not d: continue
        d=d[0]; sp=float(d.get('spend',0)); l,lc=gm(d.get('actions',[]))
        print(f"##P|{tag}|{nm}|{sp:.2f}|{l}")
        tot['spend']+=sp; tot['imp']+=int(d.get('impressions',0)); tot['clk']+=int(d.get('clicks',0)); tot['lc']+=lc; tot['leads']+=l
    n=(date.fromisoformat(until)-date.fromisoformat(since)).days+1
    cpm=tot['spend']/tot['imp']*1000 if tot['imp'] else 0
    ctr=tot['clk']/tot['imp']*100 if tot['imp'] else 0
    cpc=tot['spend']/tot['lc'] if tot['lc'] else 0
    conv=tot['leads']/tot['lc']*100 if tot['lc'] else 0
    cpl=tot['spend']/tot['leads'] if tot['leads'] else 0
    print(f"##{tag}|{n}|{tot['spend']:.2f}|{tot['imp']}|{tot['clk']}|{cpm:.2f}|{ctr:.2f}|{cpc:.2f}|{tot['leads']}|{conv:.2f}|{cpl:.2f}")

print(f"## HOJE={today}")
print("## C19 PT"); bloco(PT,"2026-07-29",min(today.isoformat(),"2026-08-04"),"C19PT")
print("## C19 BR"); bloco(BR,"2026-07-29",min(today.isoformat(),"2026-08-04"),"C19BR")
print("## BR LIFETIME (desde criacao 29/07)"); bloco(BR,"2026-07-01",today.isoformat(),"BRLIFE")

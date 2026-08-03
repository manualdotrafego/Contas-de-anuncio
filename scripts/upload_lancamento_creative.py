import requests, os, json, time
from datetime import date
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
BR=[("120256165865940002","[WEBNAR BRASIL] LP AJUSTADA"),("120256131329440002","[WEBNAR BRASIL] CICLO TESTE")]
hoje=date.today().isoformat()
def gm(a):
    l=lc=lpv=0
    for x in a or []:
        t=x.get('action_type',''); v=int(x.get('value',0))
        if t in('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'): l=max(l,v)
        elif t=='link_click': lc=v
        elif t=='landing_page_view': lpv=v
    return l,lc,lpv
tot={'spend':0,'imp':0,'clk':0,'lc':0,'lpv':0,'leads':0}
print(f"## ATE {hoje}")
for cid,nm in BR:
    for t in range(4):
        r=requests.get(f"{BASE}/{cid}/insights",params={
            'fields':'spend,impressions,clicks,actions,ctr,cpm,date_start,date_stop',
            'date_preset':'maximum','access_token':TOKEN},timeout=60).json()
        if 'error' in r: time.sleep(20); continue
        d=r.get('data',[])
        if not d: print(f"##C|{nm}|sem dados"); break
        d=d[0]; sp=float(d.get('spend',0)); l,lc,lpv=gm(d.get('actions',[]))
        cpl=sp/l if l else 0
        print(f"##C|{nm}|{sp:.2f}|{l}|{cpl:.2f}|{d.get('date_start')}|{d.get('date_stop')}")
        for k,v in [('spend',sp),('imp',int(d.get('impressions',0))),('clk',int(d.get('clicks',0))),('lc',lc),('lpv',lpv),('leads',l)]:
            tot[k]+=v
        break
cpm=tot['spend']/tot['imp']*1000 if tot['imp'] else 0
ctr=tot['clk']/tot['imp']*100 if tot['imp'] else 0
cpc=tot['spend']/tot['lc'] if tot['lc'] else 0
conv=tot['leads']/tot['lc']*100 if tot['lc'] else 0
cpl=tot['spend']/tot['leads'] if tot['leads'] else 0
print(f"##TOT|{tot['spend']:.2f}|{tot['imp']}|{tot['clk']}|{tot['lc']}|{tot['lpv']}|{tot['leads']}|{cpm:.2f}|{ctr:.2f}|{cpc:.2f}|{conv:.2f}|{cpl:.2f}")

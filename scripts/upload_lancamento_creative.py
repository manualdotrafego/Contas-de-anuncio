import requests, os, json
from datetime import date, timedelta

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_615338413578534"
today = date.today()
since = (today - timedelta(days=90)).isoformat()
until = today.isoformat()

def get_leads(actions):
    l = lc = 0
    for a in actions or []:
        t = a.get('action_type',''); v = int(a.get('value',0))
        if t in ('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'):
            l = max(l, v)
        elif t == 'link_click': lc = v
    return l, lc

print(f"## PERIODO: {since} -> {until}")
print("## CSVSTART")
print("ad_id|ad_name|campaign|spend|impressions|link_clicks|leads|ctr|cpl")
url = f"{BASE}/{ACCT}/insights"
params = {'level':'ad','fields':'ad_id,ad_name,campaign_name,spend,impressions,actions,ctr',
          'time_range': json.dumps({'since':since,'until':until}),'limit':300,'access_token':TOKEN}
ads_with_leads = []
while url:
    r = requests.get(url, params=params, timeout=90).json()
    if 'error' in r: print(f"## ERR {r['error'].get('message','')[:100]}"); break
    for d in r.get('data', []):
        sp = float(d.get('spend',0)); leads, lc = get_leads(d.get('actions',[]))
        if leads == 0: continue
        nm = d.get('ad_name','').replace('|','/').replace('\n',' ')
        cn = d.get('campaign_name','').replace('|','/')
        cpl = sp/leads
        print(f"{d.get('ad_id')}|{nm}|{cn}|{sp:.2f}|{int(d.get('impressions',0))}|{lc}|{leads}|{float(d.get('ctr',0)):.2f}|{cpl:.2f}")
        ads_with_leads.append(d.get('ad_id'))
    url = r.get('paging',{}).get('next',''); params = {}
print("## CSVEND")

# Thumbs + post links for those ads
print("## THUMBSTART")
for aid in ads_with_leads:
    try:
        cr = requests.get(f"{BASE}/{aid}", params={
            'fields':'name,creative{thumbnail_url,image_url,effective_object_story_id}',
            'access_token':TOKEN}, timeout=30).json()
        c = cr.get('creative',{})
        thumb = c.get('thumbnail_url','') or c.get('image_url','')
        eosi = c.get('effective_object_story_id','')
        purl = ""
        if eosi and '_' in eosi:
            pg,po = eosi.split('_',1); purl = f"https://www.facebook.com/{pg}/posts/{po}"
        print(f"##T|{aid}|{thumb}|{purl}")
    except Exception as e:
        print(f"##T|{aid}||")
print("## THUMBEND")

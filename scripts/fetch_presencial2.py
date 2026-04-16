import requests, json, os, sys, re

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = 'https://graph.facebook.com/v19.0'
ACCT  = 'act_615338413578534'

def api_get(url, params=None):
    p = dict(params or {}); p['access_token'] = TOKEN
    r = requests.get(url, params=p, timeout=30)
    r.raise_for_status()
    return r.json()

def paginate(url, params):
    results, data = [], api_get(url, params)
    results.extend(data.get('data', []))
    while data.get('paging', {}).get('next'):
        data = api_get(data['paging']['next'])
        results.extend(data.get('data', []))
    return results

def av(lst, key):
    for x in (lst or []):
        if x.get('action_type') == key:
            return int(float(x.get('value', 0)))
    return 0

camps = paginate(f'{BASE}/{ACCT}/campaigns', {
    'fields': 'id,name,status,effective_status',
    'limit': 100,
    'filtering': json.dumps([{'field':'name','operator':'CONTAIN','value':'presencial'}])
})

all_ads = []
for c in camps:
    ads = paginate(f'{BASE}/{c["id"]}/ads', {
        'fields': 'id,name,status,effective_status,creative{id,thumbnail_url}',
        'limit': 100
    })
    for a in ads:
        a['_camp'] = c['name']
        all_ads.append(a)

print("=== AD IDs + PREVIEWS + THUMBS ===")
for a in all_ads:
    # insights
    try:
        ins = api_get(f'{BASE}/{a["id"]}/insights', {
            'fields': 'spend,impressions,actions,ctr,cpm',
            'date_preset': 'last_90d'
        }).get('data', [{}])[0]
        acts  = ins.get('actions', [])
        leads = av(acts,'lead') or av(acts,'onsite_conversion.lead_grouped')
        spend = float(ins.get('spend', 0))
        cpl   = round(spend/leads, 2) if leads > 0 else None
        ctr   = float(ins.get('ctr', 0))
    except:
        leads = 0; spend = 0; cpl = None; ctr = 0

    # preview
    preview = ''
    try:
        pv = api_get(f'{BASE}/{a["id"]}/previews', {'ad_format': 'MOBILE_FEED_STANDARD'})
        body = pv.get('data', [{}])[0].get('body', '')
        m = re.search(r'src=[\'"](https://[^\'"]+)[\'"]', body)
        preview = m.group(1).replace('&amp;', '&') if m else ''
    except: pass

    thumb = a.get('creative', {}).get('thumbnail_url', '')
    print(f"NAME: {a['name']}")
    print(f"ID:   {a['id']}")
    print(f"ST:   {a.get('effective_status','?')}")
    print(f"CAMP: {a['_camp']}")
    print(f"LEADS:{leads} | CPL:{'€'+str(cpl) if cpl else '—'} | SPEND:€{spend:.2f} | CTR:{ctr:.2f}%")
    print(f"PREV: {preview[:120]}")
    print(f"THB:  {thumb[:120]}")
    print("---")

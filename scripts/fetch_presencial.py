import requests, json, os, sys
from collections import defaultdict

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = 'https://graph.facebook.com/v19.0'
ACCT  = 'act_615338413578534'

def api_get(url, params=None):
    p = dict(params or {}); p['access_token'] = TOKEN
    r = requests.get(url, params=p, timeout=30)
    if not r.ok:
        print(f'ERR {r.status_code}: {r.text[:300]}', file=sys.stderr)
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

# 1. Find presencial campaigns
print("=== CAMPANHAS PRESENCIAL ===")
camps = paginate(f'{BASE}/{ACCT}/campaigns', {
    'fields': 'id,name,status,effective_status,objective,daily_budget,lifetime_budget',
    'limit': 100,
    'filtering': json.dumps([{'field':'name','operator':'CONTAIN','value':'presencial'}])
})
print(f"Total: {len(camps)}")
camp_ids = []
for c in camps:
    print(f"  [{c['effective_status']}] {c['name']} | obj:{c.get('objective','')} | id:{c['id']}")
    camp_ids.append(c['id'])

if not camp_ids:
    # Try broader search
    print("\nTentando busca sem filtro de nome...")
    camps = paginate(f'{BASE}/{ACCT}/campaigns', {
        'fields': 'id,name,status,effective_status,objective',
        'limit': 100,
    })
    for c in camps:
        if 'presencial' in c['name'].lower() or 'nod' in c['name'].lower():
            print(f"  [{c['effective_status']}] {c['name']} | id:{c['id']}")
            camp_ids.append(c['id'])
    if not camp_ids:
        print("Listando TODAS as campanhas:")
        for c in camps:
            print(f"  [{c['effective_status']}] {c['name']}")
        sys.exit(0)

# 2. Get ads for those campaigns
print("\n=== ADS POR CAMPANHA ===")
all_ads = []
for cid in camp_ids:
    ads = paginate(f'{BASE}/{cid}/ads', {
        'fields': 'id,name,status,effective_status,creative{id,thumbnail_url,name}',
        'limit': 100
    })
    for a in ads:
        a['_camp_id'] = cid
        all_ads.append(a)
    print(f"  Campanha {cid}: {len(ads)} ads")

# 3. Get insights (all time / last 90 days)
print("\n=== INSIGHTS POR AD (últimos 90 dias) ===")
ad_ids = [a['id'] for a in all_ads]
insights_map = {}

for aid in ad_ids:
    try:
        data = api_get(f'{BASE}/{aid}/insights', {
            'fields': 'spend,impressions,actions,outbound_clicks,reach,cpm,ctr',
            'date_preset': 'last_90d',
            'level': 'ad'
        })
        rows = data.get('data', [])
        if rows:
            r = rows[0]
            acts = r.get('actions', [])
            obc  = r.get('outbound_clicks', [])
            leads   = av(acts,'lead') or av(acts,'onsite_conversion.lead_grouped')
            clicks  = av(acts,'link_click')
            lpv     = av(acts,'landing_page_view')
            spend   = float(r.get('spend', 0))
            imp     = int(r.get('impressions', 0))
            cpl     = round(spend/leads, 2) if leads > 0 else None
            ctr     = round(float(r.get('ctr', 0)), 2)
            cpm     = round(float(r.get('cpm', 0)), 2)
            insights_map[aid] = {'spend':spend,'leads':leads,'clicks':clicks,'lpv':lpv,'imp':imp,'cpl':cpl,'ctr':ctr,'cpm':cpm}
    except Exception as e:
        print(f"  ERR {aid}: {e}")
        insights_map[aid] = {}

# 4. Print ranking
print("\n=== RANKING DE CRIATIVOS ===")
ranked = []
for a in all_ads:
    ins = insights_map.get(a['id'], {})
    ranked.append({
        'name': a['name'],
        'id': a['id'],
        'status': a.get('effective_status','?'),
        'thumb': a.get('creative',{}).get('thumbnail_url',''),
        **ins
    })

ranked.sort(key=lambda x: -(x.get('leads') or 0))
for r in ranked:
    cpl_s = f"R${r['cpl']:.2f}" if r.get('cpl') else '—'
    print(f"  [{r['status'][:6]}] {r['name']}")
    print(f"           Leads:{r.get('leads',0):>4}  CPL:{cpl_s:>8}  Spend:R${r.get('spend',0):>8.2f}  Imp:{r.get('imp',0):>7}  CTR:{r.get('ctr',0):.2f}%")

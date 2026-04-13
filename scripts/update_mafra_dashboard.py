#!/usr/bin/env python3
"""
João Mafra WEBNAR — Dashboard Auto-Updater
Fetches Meta Ads API for WEBNAR campaigns and regenerates mafra.html
Runs every 10h via GitHub Actions
"""
import os, json, re, sys
from datetime import datetime, timedelta, timezone
try:
    import requests
except ImportError:
    import subprocess; subprocess.check_call([sys.executable,'-m','pip','install','requests','-q'])
    import requests

# ─── CONFIG ─────────────────────────────────────────────────────────────────
TOKEN      = os.environ['META_ACCESS_TOKEN']
ACCOUNT_ID = 'act_615338413578534'
BASE       = 'https://graph.facebook.com/v19.0'
CAMPAIGN_FILTER = 'WEBNAR'
# Start date fixed: Tuesday Apr 7 (webinar week start)
START_DATE = '2026-04-07'

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def api_get(url, params=None):
    p = dict(params or {}); p['access_token'] = TOKEN
    r = requests.get(url, params=p, timeout=30)
    if not r.ok:
        print(f'API error {r.status_code}: {r.text[:300]}', file=sys.stderr)
        r.raise_for_status()
    return r.json()

def paginate(url, params):
    results, data = [], api_get(url, params)
    results.extend(data.get('data', []))
    while data.get('paging', {}).get('next'):
        data = api_get(data['paging']['next'])
        results.extend(data.get('data', []))
    return results

def av(lst, t):
    for a in (lst or []):
        if a.get('action_type') == t: return int(float(a.get('value', 0)))
    return 0

def ob(lst):
    for a in (lst or []):
        if a.get('action_type') == 'outbound_click': return int(float(a.get('value', 0)))
    return 0

# ─── DATE RANGE ──────────────────────────────────────────────────────────────
end_dt   = datetime.now(timezone.utc).date()
time_range = json.dumps({'since': START_DATE, 'until': str(end_dt)})
days = (end_dt - datetime.strptime(START_DATE, '%Y-%m-%d').date()).days + 1
print(f'Fetching {START_DATE} → {end_dt} ({days} dias)')

# ─── 1. GET ADS IN WEBNAR CAMPAIGNS ─────────────────────────────────────────
print('Fetching WEBNAR campaigns…')
campaigns = paginate(f'{BASE}/{ACCOUNT_ID}/campaigns', {
    'fields': 'id,name,status',
    'limit': 100
})
webnar_camps = [c for c in campaigns if CAMPAIGN_FILTER in c['name'].upper()]
print(f'  {len(webnar_camps)} campanhas WEBNAR')

ad_meta = {}
for camp in webnar_camps:
    ads = paginate(f'{BASE}/{camp["id"]}/ads', {
        'fields': 'id,name,effective_status,creative{id,thumbnail_url}',
        'limit': 100
    })
    for a in ads:
        cr = a.get('creative', {})
        eff = a.get('effective_status', 'UNKNOWN')
        ad_meta[a['id']] = {
            'name':   a['name'],
            'thumb':  cr.get('thumbnail_url', ''),
            'status': 'ON' if eff == 'ACTIVE' else 'OFF',
        }

print(f'  {len(ad_meta)} anúncios encontrados')

# Get preview links
print('Fetching preview links…')
for ad_id, info in ad_meta.items():
    try:
        pv = api_get(f'{BASE}/{ad_id}/previews', {'ad_format': 'MOBILE_FEED_STANDARD'})
        body = pv.get('data', [{}])[0].get('body', '')
        m = re.search(r'src=[\'"](https://[^\'"]+)[\'"]', body)
        info['preview'] = m.group(1).replace('&amp;', '&') if m else ''
    except Exception as e:
        print(f'  preview failed for {ad_id}: {e}', file=sys.stderr)
        info['preview'] = ''

# ─── 2. FETCH INSIGHTS WITH AGE BREAKDOWN ────────────────────────────────────
print('Fetching insights…')
rows = paginate(f'{BASE}/{ACCOUNT_ID}/insights', {
    'fields': ','.join([
        'ad_id','ad_name','spend','impressions',
        'actions','outbound_clicks',
        'video_play_actions','video_thruplay_watched_actions'
    ]),
    'level':      'ad',
    'breakdowns': 'age',
    'time_range': time_range,
    'filtering':  json.dumps([{'field':'campaign.name','operator':'CONTAIN','value':CAMPAIGN_FILTER}]),
    'limit':      500
})
print(f'  {len(rows)} rows')

# ─── 3. AGGREGATE ────────────────────────────────────────────────────────────
from collections import defaultdict
AGES_ORDER   = ['18-24','25-34','35-44','45-54','55-64','65+']
AGES_DISPLAY = {'18-24':'18\u201324','25-34':'25\u201334','35-44':'35\u201344',
                '45-54':'45\u201354','55-64':'55\u201364','65+':'65+'}

def empty(): return {'spend':0.0,'leads':0,'imp':0,'cliques':0,'lpv':0}

ad_data = defaultdict(lambda: {'total': empty(), 'by_age': defaultdict(empty), 'name':''})

for row in rows:
    aid   = row['ad_id']
    age   = row.get('age','unknown')
    sp    = float(row.get('spend', 0))
    imp   = int(row.get('impressions', 0))
    acts  = row.get('actions', [])
    obc   = row.get('outbound_clicks', [])

    leads   = av(acts,'lead') or av(acts,'onsite_conversion.lead_grouped')
    lpv     = av(acts,'landing_page_view')
    cliques = ob(obc)

    ad_data[aid]['name'] = row['ad_name']
    for d in [ad_data[aid]['total'], ad_data[aid]['by_age'][age]]:
        d['spend']   += sp
        d['leads']   += leads
        d['imp']     += imp
        d['cliques'] += cliques
        d['lpv']     += lpv

# ─── 4. BUILD ADS ARRAY ──────────────────────────────────────────────────────
def badge(total):
    l, s = total['leads'], total['spend']
    cpl  = s / l if l > 0 else 9999
    if l >= 15 and cpl <= 3:   return 'TOP',     'bg'
    if l >= 5  and cpl <= 6:   return 'BOM',     'by'
    if l >  0  and cpl > 6:    return 'REVISAR', 'br'
    if l == 0  and s  < 15:    return 'NOVO',    'bn'
    return 'TESTE', 'by'

def round_total(d):
    return {k: round(v,2) if k=='spend' else int(v) for k,v in d.items()}

sorted_ids = sorted(ad_data, key=lambda x: ad_data[x]['total']['spend'], reverse=True)

ADS = []
for i, aid in enumerate(sorted_ids):
    if ad_data[aid]['total']['spend'] == 0: continue
    info  = ad_meta.get(aid, {'name': f'Ad {aid}', 'thumb': '', 'preview': ''})
    data  = ad_data[aid]
    total = round_total(data['total'])
    bdg, bclass = badge(total)

    by_age_list = []
    for ak in AGES_ORDER:
        raw = dict(data['by_age'].get(ak, empty()))
        raw['spend'] = round(raw['spend'], 2)
        raw['age'] = AGES_DISPLAY.get(ak, ak)
        by_age_list.append(raw)

    name = info['name']
    short = name if len(name) <= 22 else name[:20] + '\u2026'

    ADS.append({
        'id':          aid,
        'key':         f'ad{i}',
        'badge':       bdg,
        'badgeClass':  bclass,
        'status':      info.get('status', 'OFF'),
        'name':        name,
        'shortName':   short,
        'preview':     info.get('preview', ''),
        'previewType': 'fb',
        'thumb':       info.get('thumb', ''),
        'total':       total,
        'by_age':      by_age_list
    })

print(f'Built {len(ADS)} ads')

# ─── 5. INJECT INTO TEMPLATE ─────────────────────────────────────────────────
tmpl_path = os.path.join(os.path.dirname(__file__), 'mafra_template.html')
with open(tmpl_path, 'r', encoding='utf-8') as f:
    html = f.read()

ads_json = json.dumps(ADS, ensure_ascii=False, indent=2)
new_data = (
    f'// __DATA_START__\n'
    f'const META_PERIOD = {{"since":"{START_DATE}","until":"{end_dt}","days":{days}}};\n'
    f'const CURRENCY = "\u20ac";\n'
    f'const AGES = [\'18\u201324\',\'25\u201334\',\'35\u201344\',\'45\u201354\',\'55\u201364\',\'65+\'];\n'
    f'const ADS = {ads_json};\n'
    f'// __DATA_END__'
)

html = re.sub(r'// __DATA_START__.*?// __DATA_END__', new_data, html, flags=re.DOTALL)

out_path = os.path.join(os.path.dirname(__file__), '..', 'mafra.html')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)

totS = sum(a['total']['spend'] for a in ADS)
totL = sum(a['total']['leads'] for a in ADS)
print(f'Written → mafra.html  ({len(html):,} bytes)')
print(f'Totals: spend=€{totS:.2f}  leads={totL}')

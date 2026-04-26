import requests, os, json
from collections import defaultdict

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_1772556290384735"

def api_get(url, params=None):
    p = dict(params or {}); p['access_token'] = TOKEN
    r = requests.get(url, params=p, timeout=30)
    if not r.ok:
        print(f"ERR {r.status_code}: {r.text[:300]}")
        return {}
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
            return float(x.get('value', 0))
    return 0.0

def av_all(lst):
    """Return all action types"""
    return {x['action_type']: float(x.get('value',0)) for x in (lst or [])}

# ─── 1. ACCOUNT INFO ──────────────────────────────────────────────────────────
print("=" * 65)
print("NBP - Gui Pontus  |  act_1772556290384735")
print("=" * 65)

acct_info = api_get(f"{BASE}/{ACCT}", {
    'fields': 'name,currency,timezone_name,account_status,spend_cap,amount_spent,balance'
})
print(f"Nome:     {acct_info.get('name')}")
print(f"Moeda:    {acct_info.get('currency')}")
print(f"Timezone: {acct_info.get('timezone_name')}")
print(f"Gasto total (conta): R${float(acct_info.get('amount_spent',0))/100:.2f}")

# ─── 2. CAMPAIGNS ─────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("CAMPANHAS — TODO O PERÍODO")
print("=" * 65)

camps = paginate(f"{BASE}/{ACCT}/campaigns", {
    'fields': 'id,name,status,effective_status,objective,created_time,start_time',
    'limit': 100
})
print(f"Total campanhas: {len(camps)}")
for c in camps:
    print(f"\n  [{c['effective_status'][:8]}] {c['name']}")
    print(f"    id:{c['id']} | obj:{c.get('objective','')} | criada:{c.get('created_time','')[:10]}")

# ─── 3. ACCOUNT-LEVEL INSIGHTS — LIFETIME ─────────────────────────────────────
print("\n" + "=" * 65)
print("MÉTRICAS GERAIS — TODO O PERÍODO (account level)")
print("=" * 65)

fields = ','.join([
    'spend','impressions','reach','clicks','unique_clicks',
    'ctr','unique_ctr','cpm','cpp','cpc',
    'actions','action_values','cost_per_action_type',
    'outbound_clicks','outbound_clicks_ctr',
    'website_ctr','unique_outbound_clicks',
    'landing_page_view','video_p25_watched_actions',
    'frequency'
])

ins = api_get(f"{BASE}/{ACCT}/insights", {
    'fields': fields,
    'time_range': json.dumps({'since': '2026-01-01', 'until': '2026-04-26'}),
    'level': 'account'
})
rows = ins.get('data', [{}])
d = rows[0] if rows else {}

spend    = float(d.get('spend', 0))
imp      = int(d.get('impressions', 0))
reach    = int(d.get('reach', 0))
clicks   = int(d.get('clicks', 0))
u_clicks = int(d.get('unique_clicks', 0))
ctr      = float(d.get('ctr', 0))
u_ctr    = float(d.get('unique_ctr', 0))
cpm      = float(d.get('cpm', 0))
cpc      = float(d.get('cpc', 0))
freq     = float(d.get('frequency', 0))

acts     = d.get('actions', [])
all_acts = av_all(acts)
cpa_list = d.get('cost_per_action_type', [])
obc      = d.get('outbound_clicks', [])
obc_ctr  = d.get('outbound_clicks_ctr', [])
w_ctr    = d.get('website_ctr', [])

# Key conversions
leads        = av(acts, 'lead') or av(acts, 'onsite_conversion.lead_grouped')
lpv          = av(acts, 'landing_page_view')
link_clicks  = av(acts, 'link_click')
purchases    = av(acts, 'offsite_conversion.fb_pixel_purchase') or av(acts, 'purchase')
registrations= av(acts, 'offsite_conversion.fb_pixel_complete_registration') or av(acts, 'complete_registration')
view_content = av(acts, 'offsite_conversion.fb_pixel_view_content') or av(acts, 'view_content')
add_to_cart  = av(acts, 'offsite_conversion.fb_pixel_add_to_cart') or av(acts, 'add_to_cart')
initiate_ck  = av(acts, 'offsite_conversion.fb_pixel_initiate_checkout') or av(acts, 'initiate_checkout')

# Outbound clicks
obc_val = sum(float(x.get('value',0)) for x in obc)
obc_ctr_val = float(obc_ctr[0].get('value',0)) if obc_ctr else 0

# LPV rate = LPV / Link Clicks
lpv_rate = (lpv / link_clicks * 100) if link_clicks > 0 else 0
lead_rate_lpv = (leads / lpv * 100) if lpv > 0 else 0
lead_rate_click = (leads / link_clicks * 100) if link_clicks > 0 else 0

print(f"\n📊 TRÁFEGO")
print(f"  Impressões:        {imp:>12,}")
print(f"  Alcance:           {reach:>12,}")
print(f"  Frequência:        {freq:>12.2f}x")
print(f"  Cliques (total):   {clicks:>12,}")
print(f"  Cliques únicos:    {u_clicks:>12,}")
print(f"  Outbound clicks:   {obc_val:>12,.0f}")

print(f"\n📈 TAXAS")
print(f"  CTR (todos):       {ctr:>11.2f}%")
print(f"  CTR único:         {u_ctr:>11.2f}%")
print(f"  CTR outbound:      {obc_ctr_val:>11.2f}%")
print(f"  Taxa LPV/Click:    {lpv_rate:>11.2f}%  ({lpv:.0f} LPVs / {link_clicks:.0f} cliques)")
print(f"  Taxa Lead/LPV:     {lead_rate_lpv:>11.2f}%  ({leads:.0f} leads / {lpv:.0f} LPVs)")
print(f"  Taxa Lead/Click:   {lead_rate_click:>11.2f}%")

print(f"\n💰 CUSTOS")
print(f"  Investimento:      R${spend:>10.2f}")
print(f"  CPM:               R${cpm:>10.2f}")
print(f"  CPC:               R${cpc:>10.2f}")
if leads > 0:
    print(f"  CPL (lead):        R${spend/leads:>10.2f}")
if lpv > 0:
    print(f"  Custo/LPV:         R${spend/lpv:>10.2f}")

print(f"\n🎯 CONVERSÕES (pixel)")
print(f"  Leads (forms):     {leads:>12.0f}")
print(f"  Landing P. Views:  {lpv:>12.0f}")
print(f"  View Content:      {view_content:>12.0f}")
print(f"  Add to Cart:       {add_to_cart:>12.0f}")
print(f"  Init. Checkout:    {initiate_ck:>12.0f}")
print(f"  Compras:           {purchases:>12.0f}")
print(f"  Registrations:     {registrations:>12.0f}")

print(f"\n📋 TODOS OS EVENTOS (actions completo):")
for k, v in sorted(all_acts.items(), key=lambda x: -x[1]):
    if v > 0:
        print(f"  {k:<50} {v:>8.0f}")

# ─── 4. CAMPAIGN-LEVEL BREAKDOWN ──────────────────────────────────────────────
print("\n" + "=" * 65)
print("POR CAMPANHA — TODO O PERÍODO")
print("=" * 65)

camp_ins = paginate(f"{BASE}/{ACCT}/insights", {
    'fields': 'campaign_name,spend,impressions,clicks,ctr,actions,outbound_clicks,cost_per_action_type',
    'time_range': json.dumps({'since': '2026-01-01', 'until': '2026-04-26'}),
    'level': 'campaign',
    'limit': 50
})

camp_ins.sort(key=lambda x: -float(x.get('spend',0)))
for ci in camp_ins:
    sp    = float(ci.get('spend',0))
    imp_c = int(ci.get('impressions',0))
    ctr_c = float(ci.get('ctr',0))
    acts_c= ci.get('actions',[])
    leads_c = av(acts_c,'lead') or av(acts_c,'onsite_conversion.lead_grouped')
    lpv_c   = av(acts_c,'landing_page_view')
    obc_c   = sum(float(x.get('value',0)) for x in ci.get('outbound_clicks',[]))
    cpl_c   = sp/leads_c if leads_c>0 else None
    lpv_r_c = (lpv_c/obc_c*100) if obc_c>0 else 0
    conv_r_c= (leads_c/lpv_c*100) if lpv_c>0 else 0
    
    print(f"\n  {ci.get('campaign_name','?')}")
    print(f"    Gasto:R${sp:.2f} | Imp:{imp_c:,} | CTR:{ctr_c:.2f}%")
    print(f"    OBC:{obc_c:.0f} | LPV:{lpv_c:.0f} | Leads:{leads_c:.0f}", end="")
    if cpl_c: print(f" | CPL:R${cpl_c:.2f}", end="")
    print()
    print(f"    Taxa LPV/OBC:{lpv_r_c:.1f}% | Taxa Conv/LPV:{conv_r_c:.1f}%")

# ─── 4b. AD-LEVEL BREAKDOWN ───────────────────────────────────────────────────
print("\n" + "=" * 65)
print("POR ANÚNCIO — TODO O PERÍODO")
print("=" * 65)

ad_ins = paginate(f"{BASE}/{ACCT}/insights", {
    'fields': 'ad_name,adset_name,spend,impressions,clicks,ctr,actions,outbound_clicks,landing_page_view,video_p25_watched_actions,video_p100_watched_actions',
    'time_range': json.dumps({'since': '2026-01-01', 'until': '2026-04-26'}),
    'level': 'ad',
    'limit': 100
})

ad_ins.sort(key=lambda x: -float(x.get('spend',0)))
for ai in ad_ins:
    sp    = float(ai.get('spend',0))
    imp_a = int(ai.get('impressions',0))
    ctr_a = float(ai.get('ctr',0))
    acts_a= ai.get('actions',[])
    leads_a = av(acts_a,'lead') or av(acts_a,'onsite_conversion.lead_grouped')
    lpv_a   = av(acts_a,'landing_page_view') or float(ai.get('landing_page_view',[{}])[0].get('value',0) if ai.get('landing_page_view') else 0)
    obc_a   = sum(float(x.get('value',0)) for x in ai.get('outbound_clicks',[]))
    v25_a   = sum(float(x.get('value',0)) for x in ai.get('video_p25_watched_actions',[]))
    v100_a  = sum(float(x.get('value',0)) for x in ai.get('video_p100_watched_actions',[]))
    cpl_a   = sp/leads_a if leads_a>0 else None
    lpv_r_a = (lpv_a/obc_a*100) if obc_a>0 else 0
    conv_r_a= (leads_a/lpv_a*100) if lpv_a>0 else 0

    print(f"\n  [{ai.get('adset_name','?')}] {ai.get('ad_name','?')}")
    print(f"    Gasto:R${sp:.2f} | Imp:{imp_a:,} | CTR:{ctr_a:.2f}%")
    print(f"    OBC:{obc_a:.0f} | LPV:{lpv_a:.0f} | Leads:{leads_a:.0f}", end="")
    if cpl_a: print(f" | CPL:R${cpl_a:.2f}", end="")
    print()
    if v25_a > 0:
        print(f"    Video 25%:{v25_a:.0f} | Video 100%:{v100_a:.0f}")
    print(f"    Taxa LPV/OBC:{lpv_r_a:.1f}% | Taxa Lead/LPV:{conv_r_a:.1f}%")

# ─── 5. PIXEL EVENTS CHECK ────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("PIXELS DISPONÍVEIS")
print("=" * 65)
pixels = paginate(f"{BASE}/{ACCT}/adspixels", {
    'fields': 'id,name,last_fired_time,code',
    'limit': 10
})
for px in pixels:
    print(f"  [{px['id']}] {px['name']} | last_fired: {px.get('last_fired_time','nunca')}")

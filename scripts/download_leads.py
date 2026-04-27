import requests, json, csv, os
from datetime import datetime, timezone

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_615338413578534"   # Conta Lançamento

SINCE_STR = "2026-04-25"   # Sábado
UNTIL_STR = "2026-04-27"   # Hoje (segunda)

# Timestamps UTC (Brasil = UTC-3 → sábado 00h BRT = sábado 03h UTC)
TS_FROM = int(datetime(2026, 4, 25, 3, 0, 0, tzinfo=timezone.utc).timestamp())
TS_TO   = int(datetime(2026, 4, 28, 3, 0, 0, tzinfo=timezone.utc).timestamp())

def get(url, params=None):
    p = dict(params or {}); p['access_token'] = TOKEN
    r = requests.get(url, params=p, timeout=30)
    if not r.ok:
        print(f"  ERR {r.status_code}: {r.text[:300]}")
        return {}
    return r.json()

def paginate(url, params=None, max_pages=50):
    results, page, data = [], 0, get(url, params)
    results.extend(data.get('data', []))
    while data.get('paging', {}).get('next') and page < max_pages:
        data = get(data['paging']['next'])
        results.extend(data.get('data', []))
        page += 1
    return results

# ─── 1. Info da conta ─────────────────────────────────────────────────────────
acct = get(f"{BASE}/{ACCT}", {'fields': 'name,currency,account_status'})
print("="*65)
print(f"CONTA: {acct.get('name')}  ({ACCT})")
print(f"Moeda: {acct.get('currency')} | Status: {acct.get('account_status')}")
print(f"Período: {SINCE_STR} (sábado) até {UNTIL_STR} (hoje)")
print("="*65)

# ─── 2. Campanhas LEAD_GEN ativas/pausadas ────────────────────────────────────
print("\n📋 CAMPANHAS DE CAPTAÇÃO:")
camps = paginate(f"{BASE}/{ACCT}/campaigns", {
    'fields': 'id,name,objective,effective_status',
    'filtering': json.dumps([{"field":"objective","operator":"IN","value":["LEAD_GENERATION","OUTCOME_LEADS"]}]),
    'limit': 100
})
for c in camps:
    print(f"  [{c.get('effective_status','?')[:6]}] {c['name']}")

# ─── 3. Busca form_ids dos anúncios de cada campanha ──────────────────────────
print("\n📝 BUSCANDO FORMULÁRIOS VIA ADS:")

form_map = {}   # form_id → {'name': ..., 'campaign': ...}

for camp in camps:
    cid   = camp['id']
    cname = camp['name']

    # Pega ads da campanha
    ads = get(f"{BASE}/{cid}/ads", {
        'fields': 'id,name,creative',
        'limit': 100
    }).get('data', [])

    for ad in ads:
        creative_id = ad.get('creative', {}).get('id')
        if not creative_id:
            continue
        creative = get(f"{BASE}/{creative_id}", {
            'fields': 'id,object_story_spec,lead_gen_form_id'
        })
        form_id = creative.get('lead_gen_form_id')
        if form_id and form_id not in form_map:
            # Busca nome do form
            form_info = get(f"{BASE}/{form_id}", {'fields': 'id,name,status,leads_count'})
            form_map[form_id] = {
                'name': form_info.get('name', 'Sem nome'),
                'status': form_info.get('status', '?'),
                'leads_count': form_info.get('leads_count', 0),
                'campaign': cname,
            }
            print(f"  ✅ Form encontrado: [{form_info.get('status','?')}] {form_info.get('name','?')}  (total: {form_info.get('leads_count',0)} leads)")

if not form_map:
    print("  ⚠️  Nenhum form nativo encontrado nos ads ativos/pausados.")
    # Tenta via página
    page_info = get(f"{BASE}/{ACCT}", {'fields': 'business'})
    print(f"  Business info: {page_info}")

# ─── 4. Baixa leads de cada formulário no período ─────────────────────────────
print("\n" + "="*65)
print(f"LEADS {SINCE_STR} → {UNTIL_STR}")
print("="*65)

all_leads = []

for fid, fdata in form_map.items():
    fname = fdata['name']
    camp  = fdata['campaign']

    leads = paginate(f"{BASE}/{fid}/leads", {
        'fields': 'id,created_time,field_data,ad_id,ad_name,campaign_id,campaign_name,adset_name',
        'filtering': json.dumps([
            {"field":"time_created","operator":"GREATER_THAN","value": TS_FROM},
            {"field":"time_created","operator":"LESS_THAN","value":   TS_TO},
        ]),
        'limit': 100
    })

    if leads:
        print(f"\n  ✅ [{fname}] ({camp[:40]}) — {len(leads)} leads")
        for lead in leads:
            row = {
                'lead_id':    lead.get('id',''),
                'data_hora':  lead.get('created_time','')[:19],
                'formulario': fname,
                'campanha':   lead.get('campaign_name','') or camp,
                'conjunto':   lead.get('adset_name',''),
                'anuncio':    lead.get('ad_name',''),
            }
            for field in lead.get('field_data', []):
                vals = field.get('values', [])
                row[field['name']] = ', '.join(vals) if isinstance(vals, list) else str(vals)
            all_leads.append(row)
    else:
        print(f"\n  ○ [{fname}] ({camp[:40]}) — 0 leads no período")

# ─── 5. Resumo e CSV ──────────────────────────────────────────────────────────
print("\n" + "="*65)
print(f"TOTAL: {len(all_leads)} leads de {SINCE_STR} a {UNTIL_STR}")
print("="*65)

if all_leads:
    all_keys = []
    for r in all_leads:
        for k in r.keys():
            if k not in all_keys:
                all_keys.append(k)

    print(f"\nColunas: {', '.join(all_keys)}")
    print(f"\n─── TODOS OS LEADS ───")
    for lead in all_leads:
        fields_str = " | ".join(
            f"{k}={v}" for k, v in lead.items()
            if k not in ('lead_id','formulario','campanha','conjunto','anuncio') and v
        )
        print(f"  {lead.get('data_hora','')} | camp:{lead.get('campanha','')[:30]} | {fields_str}")
else:
    print("\n⚠️  Nenhum lead no período. Verifique os formulários.")

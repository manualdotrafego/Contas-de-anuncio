import requests, os, time, json

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_592324092832640"

CREATIVE_NAMES = [
    "1-pedro-completo",
    "1-pedro-simplificada",
    "2-robson-completa",
    "2-robson-simplificada",
    "3-aline-completo",
    "3-aline-simplificada",
    "4-vitor-geologo",
    "5-gabrielle-completo",
    "1-pedro-sem-caixinha",
    "2-robson-sem-caixinha",
    "3-aline-sem-caixinha",
]

def api_get(url, params=None):
    p = dict(params or {}); p['access_token'] = TOKEN
    r = requests.get(url, params=p, timeout=30)
    if not r.ok:
        print(f"ERR {r.status_code}: {r.text[:300]}")
        return {}
    return r.json()

def api_post(url, data=None):
    d = dict(data or {}); d['access_token'] = TOKEN
    r = requests.post(url, data=d, timeout=30)
    if not r.ok:
        print(f"ERR {r.status_code}: {r.text[:300]}")
        return {}
    return r.json()

# ─── 1. Pagina campanhas incluindo IN_DRAFT ────────────────────────────────────
print("="*60)
print("BUSCANDO CAMPANHA [CAPTAÇÃO]-[0 AO EMPREGO] em todos os status")
print("="*60)

found_camp = None
next_url = f"{BASE}/{ACCT}/campaigns"
params = {
    'fields': 'id,name,effective_status',
    'effective_status': json.dumps(["ACTIVE","PAUSED","IN_DRAFT","ARCHIVED","DELETED"]),
    'limit': 100
}

page = 0
while next_url and page < 30 and not found_camp:
    time.sleep(0.3)
    data = api_get(next_url, params if page == 0 else None)
    camps_page = data.get('data', [])
    print(f"  Página {page+1}: {len(camps_page)} campanhas")
    for c in camps_page:
        name_up = c['name'].upper()
        if 'EMPREGO' in name_up or ('CAPTA' in name_up and 'VALIDA' in name_up):
            print(f"  ⭐ ENCONTRADA: [{c['effective_status']}] {c['name']}  id:{c['id']}")
            found_camp = c
    next_url = data.get('paging', {}).get('next')
    params = None  # params já no next_url
    page += 1

if not found_camp:
    print("❌ Campanha não encontrada após paginar. Mostrando últimas 10:")
    for c in camps_page[-10:]:
        print(f"  {c['name']}")
    exit(1)

print(f"\n✅ Campanha: {found_camp['name']}  [{found_camp['effective_status']}]  id:{found_camp['id']}")

# ─── 2. Busca adsets desta campanha (todos os status) ─────────────────────────
print("\n" + "="*60)
print("ADSETS DA CAMPANHA")
print("="*60)

adsets_resp = api_get(f"{BASE}/{found_camp['id']}/adsets", {
    'fields': 'id,name,created_time,effective_status',
    'effective_status': json.dumps(["ACTIVE","PAUSED","IN_DRAFT","ARCHIVED","CAMPAIGN_PAUSED"]),
    'limit': 100
})
adsets = adsets_resp.get('data', [])
adsets.sort(key=lambda x: x.get('created_time',''))

print(f"\n{len(adsets)} adsets encontrados:")
for i, a in enumerate(adsets, 1):
    print(f"  {i:2}. [{a.get('effective_status','?')[:8]}] {a['name']}")
    print(f"       id:{a['id']} | criado:{a.get('created_time','')[:19]}")

if not adsets:
    print("❌ Nenhum adset encontrado para essa campanha.")
    exit(1)

# ─── 3. Busca ads de cada adset ───────────────────────────────────────────────
print("\n" + "="*60)
print("ADS DE CADA ADSET")
print("="*60)

adset_ads = {}
for a in adsets:
    time.sleep(0.2)
    ads = api_get(f"{BASE}/{a['id']}/ads", {
        'fields': 'id,name,created_time',
        'effective_status': json.dumps(["ACTIVE","PAUSED","IN_DRAFT","ARCHIVED","CAMPAIGN_PAUSED","ADSET_PAUSED"]),
        'limit': 50
    }).get('data', [])
    adset_ads[a['id']] = sorted(ads, key=lambda x: x.get('created_time',''))
    print(f"\n  [{a['name'][:55]}]")
    for ad in adset_ads[a['id']]:
        print(f"    → {ad['name']}  (id:{ad['id']})")

# ─── 4. Renomeia adsets ───────────────────────────────────────────────────────
print("\n" + "="*60)
print("RENOMEANDO ADSETS")
print("="*60)

for i, adset in enumerate(adsets, 1):
    new_name = f"[AD SET 1.{i}] - [VALIDA\u00c7\u00c3O CRIATIVO]"
    time.sleep(0.2)
    result = api_post(f"{BASE}/{adset['id']}", {'name': new_name})
    ok = result.get('success') or result.get('id')
    print(f"  {'✅' if ok else '❌'} {adset['name'][:55]}")
    print(f"       → {new_name}")

# ─── 5. Renomeia ads ──────────────────────────────────────────────────────────
print("\n" + "="*60)
print("RENOMEANDO ADS (criativos)")
print("="*60)

creative_idx = 0
for adset in adsets:
    for ad in adset_ads[adset['id']]:
        if creative_idx >= len(CREATIVE_NAMES):
            print(f"  ⚠️  Mais ads do que nomes disponíveis")
            continue
        new_ad_name = CREATIVE_NAMES[creative_idx]
        time.sleep(0.2)
        result = api_post(f"{BASE}/{ad['id']}", {'name': new_ad_name})
        ok = result.get('success') or result.get('id')
        print(f"  {'✅' if ok else '❌'} {ad['name'][:55]}")
        print(f"       → {new_ad_name}")
        creative_idx += 1

# ─── 6. Resultado final ───────────────────────────────────────────────────────
print("\n" + "="*60)
print("RESULTADO FINAL")
print("="*60)
time.sleep(1)
final_adsets = api_get(f"{BASE}/{found_camp['id']}/adsets", {
    'fields': 'id,name',
    'effective_status': json.dumps(["ACTIVE","PAUSED","IN_DRAFT","ARCHIVED","CAMPAIGN_PAUSED"]),
    'limit': 100
}).get('data', [])
final_adsets.sort(key=lambda x: x.get('name',''))
for a in final_adsets:
    time.sleep(0.1)
    ads = api_get(f"{BASE}/{a['id']}/ads", {
        'fields': 'id,name',
        'effective_status': json.dumps(["ACTIVE","PAUSED","IN_DRAFT","ARCHIVED","CAMPAIGN_PAUSED","ADSET_PAUSED"]),
        'limit': 50
    }).get('data', [])
    print(f"\n  {a['name']}")
    for ad in ads:
        print(f"    └─ {ad['name']}")

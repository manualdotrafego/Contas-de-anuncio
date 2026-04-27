import requests, os, time

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

def paginate(url, params, max_pages=20):
    results, page, data = [], 0, api_get(url, params)
    results.extend(data.get('data', []))
    while data.get('paging', {}).get('next') and page < max_pages:
        time.sleep(0.3)
        data = api_get(data['paging']['next'])
        results.extend(data.get('data', []))
        page += 1
    return results

# ─── 1. Busca campanha por nome com filtering ─────────────────────────────────
import json
print("="*60)
print("BUSCANDO CAMPANHA [CAPTAÇÃO]-[0 AO EMPREGO]-[VALIDAÇÃO CRIATIVO]")
print("="*60)

# Busca filtrada por parte do nome
camp_data = api_get(f"{BASE}/{ACCT}/campaigns", {
    'fields': 'id,name,effective_status',
    'filtering': json.dumps([{"field":"name","operator":"CONTAIN","value":"VALIDAÇÃO CRIATIVO"}]),
    'limit': 50
})

camps = camp_data.get('data', [])
print(f"Encontradas {len(camps)} campanhas com 'VALIDAÇÃO CRIATIVO':")
for c in camps:
    print(f"  [{c.get('effective_status','?')[:6]}] {c['name']}  id:{c['id']}")

if not camps:
    # tenta sem acento
    camp_data2 = api_get(f"{BASE}/{ACCT}/campaigns", {
        'fields': 'id,name,effective_status',
        'filtering': json.dumps([{"field":"name","operator":"CONTAIN","value":"EMPREGO"}]),
        'limit': 50
    })
    camps = camp_data2.get('data', [])
    print(f"Tentativa com 'EMPREGO': {len(camps)} campanhas")
    for c in camps:
        print(f"  [{c.get('effective_status','?')[:6]}] {c['name']}  id:{c['id']}")

if not camps:
    print("❌ Campanha não encontrada.")
    exit(1)

camp = camps[0]
print(f"\n✅ Usando: {camp['name']}  (id:{camp['id']})")

# ─── 2. Busca adsets APENAS dessa campanha ────────────────────────────────────
print("\n" + "="*60)
print("ADSETS DA CAMPANHA")
print("="*60)

adsets = paginate(f"{BASE}/{camp['id']}/adsets", {
    'fields': 'id,name,created_time,effective_status',
    'limit': 50
})

adsets.sort(key=lambda x: x.get('created_time',''))
print(f"\n{len(adsets)} ad sets encontrados:")
for i, a in enumerate(adsets, 1):
    print(f"  {i:2}. [{a.get('effective_status','?')[:6]}] {a['name']}")
    print(f"       id:{a['id']} | criado:{a.get('created_time','')[:19]}")

# ─── 3. Busca ads de cada adset ───────────────────────────────────────────────
print("\n" + "="*60)
print("ADS DENTRO DE CADA ADSET")
print("="*60)

adset_ads = {}
for a in adsets:
    time.sleep(0.2)
    ads = api_get(f"{BASE}/{a['id']}/ads", {
        'fields': 'id,name,created_time,effective_status',
        'limit': 50
    }).get('data', [])
    adset_ads[a['id']] = sorted(ads, key=lambda x: x.get('created_time',''))
    print(f"\n  [{a['name'][:50]}]")
    for ad in adset_ads[a['id']]:
        print(f"    → {ad['name']}  (id:{ad['id']})")

# ─── 4. Renomeia adsets ───────────────────────────────────────────────────────
print("\n" + "="*60)
print("RENOMEANDO ADSETS")
print("="*60)

for i, adset in enumerate(adsets, 1):
    new_name = f"[AD SET 1.{i}] - [VALIDAÇÃO CRIATIVO]"
    time.sleep(0.2)
    result = api_post(f"{BASE}/{adset['id']}", {'name': new_name})
    ok = result.get('success') or result.get('id')
    status = "✅" if ok else "❌"
    print(f"  {status} {adset['name']}")
    print(f"       → {new_name}")

# ─── 5. Renomeia ads ──────────────────────────────────────────────────────────
print("\n" + "="*60)
print("RENOMEANDO ADS (criativos)")
print("="*60)

creative_idx = 0
for adset in adsets:
    for ad in adset_ads[adset['id']]:
        if creative_idx >= len(CREATIVE_NAMES):
            print(f"  ⚠️  Sem nome para ad {ad['id']} - criativo_idx={creative_idx}")
            continue
        new_ad_name = CREATIVE_NAMES[creative_idx]
        time.sleep(0.2)
        result = api_post(f"{BASE}/{ad['id']}", {'name': new_ad_name})
        ok = result.get('success') or result.get('id')
        status = "✅" if ok else "❌"
        print(f"  {status} {ad['name']}")
        print(f"       → {new_ad_name}")
        creative_idx += 1

# ─── 6. Resumo final ──────────────────────────────────────────────────────────
print("\n" + "="*60)
print("RESULTADO FINAL")
print("="*60)
time.sleep(1)
final = api_get(f"{BASE}/{camp['id']}/adsets", {
    'fields': 'id,name',
    'limit': 50
}).get('data', [])
final.sort(key=lambda x: x.get('name',''))
for a in final:
    ads = api_get(f"{BASE}/{a['id']}/ads", {
        'fields': 'id,name',
        'limit': 50
    }).get('data', [])
    print(f"\n  {a['name']}")
    for ad in ads:
        print(f"    └─ {ad['name']}")

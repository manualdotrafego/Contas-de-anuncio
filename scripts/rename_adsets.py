import requests, os

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_592324092832640"

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

def paginate(url, params):
    results, data = [], api_get(url, params)
    results.extend(data.get('data', []))
    while data.get('paging', {}).get('next'):
        data = api_get(data['paging']['next'])
        results.extend(data.get('data', []))
    return results

# ─── 1. Busca todos os adsets ─────────────────────────────────────────────────
print("="*60)
print("ESTRUTURA ATUAL DA CONTA DevSpace")
print("="*60)

adsets = paginate(f"{BASE}/{ACCT}/adsets", {
    'fields': 'id,name,campaign_id,created_time,effective_status',
    'limit': 100
})

print(f"\nTODOS os ad sets na conta ({len(adsets)} total):")
for a in sorted(adsets, key=lambda x: x.get('created_time','')):
    print(f"  [{a.get('effective_status','?')[:6]}] {repr(a['name'][:80])}  id:{a['id']}")

# Filtra VALIDAÇÃO CRIATIVO — busca case-insensitive e por substring parcial
targets = [
    a for a in adsets
    if 'VALIDA' in a['name'].upper() or 'CRIATIVO' in a['name'].upper() or 'C\u00f3pia' in a['name'] or 'C\u00d3PIA' in a['name'].upper() or 'COPIA' in a['name'].upper()
]
targets.sort(key=lambda x: x.get('created_time', ''))

print(f"\n{len(targets)} ad sets alvos para renomear:")
for i, a in enumerate(targets, 1):
    print(f"  {i:2}. [{a.get('effective_status','?')[:6]}] {repr(a['name'])}")
    print(f"       id:{a['id']} | criado:{a.get('created_time','')[:19]}")

# ─── 2. Busca os ADS de cada adset ───────────────────────────────────────────
print("\n" + "="*60)
print("ADS (criativos) dentro de cada adset")
print("="*60)

adset_ads = {}
for a in targets:
    ads = paginate(f"{BASE}/{a['id']}/ads", {
        'fields': 'id,name,created_time,effective_status',
        'limit': 50
    })
    adset_ads[a['id']] = ads
    print(f"\n  [{a['name'][:40]}]")
    for ad in ads:
        print(f"    → [{ad.get('effective_status','?')[:6]}] {ad['name']}  (id:{ad['id']})")

# ─── 3. Renomeia adsets: [AD SET 1.N] - [VALIDAÇÃO CRIATIVO] ─────────────────
print("\n" + "="*60)
print("RENOMEANDO AD SETS")
print("="*60)

for i, adset in enumerate(targets, 1):
    new_name = f"[AD SET 1.{i}] - [VALIDAÇÃO CRIATIVO]"
    result = api_post(f"{BASE}/{adset['id']}", {'name': new_name})
    ok = result.get('success') or result.get('id')
    status = "✅" if ok else "❌"
    print(f"  {status} {adset['name']}")
    print(f"     → {new_name}")

# ─── 4. Renomeia ADS: pelo nome do criativo enviado (ordem de criação) ────────
# Criativos carregados (11 total, ordem da primeira leva + sem-caixinha)
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

print("\n" + "="*60)
print("RENOMEANDO ADS (criativos)")
print("="*60)

creative_idx = 0
for adset in targets:
    ads = adset_ads[adset['id']]
    for ad in sorted(ads, key=lambda x: x.get('created_time','')):
        if creative_idx >= len(CREATIVE_NAMES):
            print(f"  ⚠️  Sem nome disponível para ad {ad['id']}")
            continue
        new_ad_name = CREATIVE_NAMES[creative_idx]
        result = api_post(f"{BASE}/{ad['id']}", {'name': new_ad_name})
        ok = result.get('success') or result.get('id')
        status = "✅" if ok else "❌"
        print(f"  {status} {ad['name']}")
        print(f"     → {new_ad_name}")
        creative_idx += 1

# ─── 5. Verificação final ─────────────────────────────────────────────────────
print("\n" + "="*60)
print("RESULTADO FINAL")
print("="*60)

final_adsets = paginate(f"{BASE}/{ACCT}/adsets", {
    'fields': 'id,name,created_time',
    'limit': 100
})
finals = [a for a in final_adsets if 'VALIDAÇÃO CRIATIVO' in a['name']]
finals.sort(key=lambda x: x.get('created_time',''))
for a in finals:
    ads = paginate(f"{BASE}/{a['id']}/ads", {
        'fields': 'id,name',
        'limit': 10
    })
    ad_names = [ad['name'] for ad in ads]
    print(f"\n  {a['name']}")
    for n in ad_names:
        print(f"    └─ {n}")

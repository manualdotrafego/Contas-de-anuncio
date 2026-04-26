import requests, os, time

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_592324092832640"
GH_BASE = "https://github.com/manualdotrafego/Contas-de-anuncio/releases/download/creatives-devspace-v1"

CREATIVES = [
    "1-pedro-completo",
    "1-pedro-simplificada",
    "2-robson-completa",
    "2-robson-simplificada",
    "3-aline-completo",
    "3-aline-simplificada",
    "4-vitor-geologo",
    "5-gabrielle-completo",
]

def get_direct_url(gh_url):
    """Follow GitHub redirect to get direct CDN URL"""
    r = requests.head(gh_url, allow_redirects=True, timeout=30)
    return r.url

print("=" * 60)
print(f"UPLOAD CRIATIVOS — DevSpace ({ACCT})")
print("=" * 60)

results = []

for name in CREATIVES:
    gh_url = f"{GH_BASE}/{name}.mp4"
    print(f"\n▶ {name}")

    # Step 1: resolve GitHub redirect → direct CDN URL
    try:
        direct_url = get_direct_url(gh_url)
        print(f"  CDN URL: {direct_url[:70]}...")
    except Exception as e:
        print(f"  ERR resolving URL: {e}")
        results.append({'name': name, 'status': 'error', 'msg': str(e)})
        continue

    # Step 2: upload to Meta via file_url
    upload_r = requests.post(
        f"{BASE}/{ACCT}/advideos",
        data={
            'access_token': TOKEN,
            'file_url': direct_url,
            'name': name,
            'title': name,
        },
        timeout=60
    )

    if upload_r.ok:
        vid = upload_r.json()
        vid_id = vid.get('id', '?')
        print(f"  ✅ Enviado! ID: {vid_id}")
        results.append({'name': name, 'id': vid_id, 'status': 'ok'})
    else:
        err = upload_r.text[:300]
        print(f"  ❌ Erro: {err}")
        # fallback: try multipart upload by downloading first
        print(f"  🔄 Tentando download direto + upload multipart...")
        try:
            dl = requests.get(direct_url, stream=True, timeout=300, allow_redirects=True)
            video_bytes = dl.content
            print(f"     Downloaded {len(video_bytes)/1024/1024:.1f} MB")
            up2 = requests.post(
                f"{BASE}/{ACCT}/advideos",
                params={'access_token': TOKEN},
                files={'source': (f"{name}.mp4", video_bytes, 'video/mp4')},
                data={'name': name, 'title': name},
                timeout=300
            )
            if up2.ok:
                vid_id = up2.json().get('id','?')
                print(f"     ✅ Upload direto ok! ID: {vid_id}")
                results.append({'name': name, 'id': vid_id, 'status': 'ok_multipart'})
            else:
                print(f"     ❌ Falha: {up2.text[:200]}")
                results.append({'name': name, 'status': 'error', 'msg': up2.text[:100]})
        except Exception as e2:
            print(f"     Exceção: {e2}")
            results.append({'name': name, 'status': 'error', 'msg': str(e2)})

print("\n" + "=" * 60)
print("RESULTADO FINAL — IDs dos criativos")
print("=" * 60)
for r in results:
    status = "✅" if r.get('status','').startswith('ok') else "❌"
    print(f"  {status} {r['name']:<35} {r.get('id', r.get('msg','?'))}")

print("\n" + "=" * 60)
print("UTMs GERADAS (parâmetros dinâmicos Meta)")
print("=" * 60)
UTM_TEMPLATE = "utm_source=meta&utm_medium={{placement}}&utm_campaign={{campaign.name}}&utm_content={{ad.name}}"
print(f"\nTemplate (igual para todos — Meta preenche dinamicamente):")
print(f"  ?{UTM_TEMPLATE}")
print(f"\nUTM resolvida por criativo (substituindo {{{{ad.name}}}} pelo nome real):")
for r in results:
    n = r['name']
    utm = f"utm_source=meta&utm_medium={{{{placement}}}}&utm_campaign={{{{campaign.name}}}}&utm_content={n}"
    vid_id = r.get('id','?')
    print(f"\n  [{n}]  id: {vid_id}")
    print(f"  ?{utm}")

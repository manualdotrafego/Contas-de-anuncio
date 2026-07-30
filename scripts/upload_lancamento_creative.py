import requests, os, json
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
ACCT="act_615338413578534"

targeting = {
    "geo_locations": {"countries": ["BR"], "location_types": ["home","recent"]},
    "flexible_spec": [{"interests": [
        {"id": "6003702887891", "name": "Agência de publicidade (marketing)"},
        {"id": "6003127206524", "name": "Marketing digital (marketing)"},
        {"id": "6003125254528", "name": "geração de lead (marketing)"},
        {"id": "6003109309984", "name": "AdWords"},
    ]}],
    "excluded_custom_audiences": [{"id": "120211907706480002"}],
    "age_min": 18, "age_max": 65,
    "targeting_automation": {"advantage_audience": 0},
}

r = requests.post(f"{BASE}/{ACCT}/saved_audiences", data={
    'name': 'BR | Agências + Mkt Digital + Leads + AdWords (excl. Envolv. IG 90D)',
    'description': 'Brasil · interesses: Agência de publicidade, Marketing digital, Geração de lead, AdWords · exclui [Insta] [Envolvimento 90D]',
    'targeting': json.dumps(targeting),
    'access_token': TOKEN}, timeout=60).json()
print("## CRIACAO:", json.dumps(r, ensure_ascii=False)[:400])

said = r.get('id')
if said:
    v = requests.get(f"{BASE}/{said}", params={
        'fields':'id,name,description,approximate_count_lower_bound,approximate_count_upper_bound,targeting',
        'access_token':TOKEN}, timeout=30).json()
    print("\n## NOME:", v.get('name'))
    lo=v.get('approximate_count_lower_bound'); hi=v.get('approximate_count_upper_bound')
    print(f"## ALCANCE: {lo:,} - {hi:,}".replace(',','.') if lo else "## ALCANCE: (calculando)")
    t=v.get('targeting',{})
    print("## PAIS:", t.get('geo_locations',{}).get('countries'))
    ints=[i['name'] for f in t.get('flexible_spec',[]) for i in f.get('interests',[])]
    print("## INTERESSES:", ' | '.join(ints))
    print("## EXCLUSAO:", t.get('excluded_custom_audiences'))
    print("## IDADE:", t.get('age_min'), "-", t.get('age_max'))

import requests, os, json
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
ACCT="act_615338413578534"
targeting = {
    "geo_locations": {"countries": ["BR"], "location_types": ["home","recent"]},
    "flexible_spec": [{"interests": [
        {"id": "6003702887891"},{"id": "6003127206524"},
        {"id": "6003125254528"},{"id": "6003109309984"}]}],
    "excluded_custom_audiences": [{"id": "120211907706480002"}],
    "age_min": 18, "age_max": 65,
    "targeting_automation": {"advantage_audience": 0},
}
r=requests.get(f"{BASE}/{ACCT}/delivery_estimate",params={
    'targeting_spec':json.dumps(targeting),'optimization_goal':'OFFSITE_CONVERSIONS',
    'access_token':TOKEN},timeout=60).json()
print("## DELIVERY:", json.dumps(r, ensure_ascii=False)[:500])

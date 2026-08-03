import requests, os, time
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
for t in range(4):
    r=requests.get(f"{BASE}/act_615338413578534",params={
        'fields':'name,timezone_name,timezone_offset_hours_utc,currency','access_token':TOKEN},timeout=40).json()
    if 'error' in r:
        print(f"(rate limit {t+1})"); time.sleep(20); continue
    print("##TZ|", r.get('name'),"|", r.get('timezone_name'),"| UTC", r.get('timezone_offset_hours_utc'),"|", r.get('currency'))
    break

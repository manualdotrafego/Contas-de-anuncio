import requests, os, json
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
AID="120250196502080002"
# 1. creative fields
cr=requests.get(f"{BASE}/{AID}",params={'fields':'creative{image_url,thumbnail_url,effective_object_story_id,object_story_spec}','access_token':TOKEN},timeout=30).json()
c=cr.get('creative',{})
print("## image_url:", c.get('image_url',''))
tu=c.get('thumbnail_url','')
print("## thumb_hi:", (tu.split('&w=')[0]+'&w=1080&h=1350') if '&w=' in tu else tu)
oss=c.get('object_story_spec',{})
print("## oss:", json.dumps(oss)[:300])
eosi=c.get('effective_object_story_id','')
print("## eosi:", eosi)
# 2. full_picture do post via page token
if eosi:
    pg=requests.get(f"{BASE}/110278364765662",params={'access_token':TOKEN,'fields':'access_token'},timeout=30).json()
    PT=pg.get('access_token',TOKEN)
    p=requests.get(f"{BASE}/{eosi}",params={'fields':'full_picture','access_token':PT},timeout=30).json()
    print("## full_picture:", p.get('full_picture',''))

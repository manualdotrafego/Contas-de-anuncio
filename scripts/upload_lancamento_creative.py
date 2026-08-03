import requests, os, json
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
AID="120256165866030002"
base_t=requests.get(f"{BASE}/{AID}",params={'fields':'targeting','access_token':TOKEN},timeout=30).json().get('targeting',{})

FB=["feed","video_feeds","story","facebook_reels","marketplace","search","profile_feed","right_hand_column"]
IG=["stream","story","explore","reels","profile_feed","ig_search"]

variants=[
 ("A. fb+ig+messenger com posicoes", {"publisher_platforms":["facebook","instagram","messenger"],
    "facebook_positions":FB,"instagram_positions":IG,"messenger_positions":["messenger_home","story"]}),
 ("B. so publisher_platforms fb+ig (sem posicoes)", {"publisher_platforms":["facebook","instagram"]}),
 ("C. fb+ig+messenger sem posicoes", {"publisher_platforms":["facebook","instagram","messenger"]}),
 ("D. fb+ig com posicoes + advantage_audience 0", {"publisher_platforms":["facebook","instagram"],
    "facebook_positions":FB,"instagram_positions":IG,
    "targeting_automation":{"advantage_audience":0}}),
 ("E. fb+ig posicoes minimas", {"publisher_platforms":["facebook","instagram"],
    "facebook_positions":["feed","story","facebook_reels","video_feeds"],
    "instagram_positions":["stream","story","reels","explore"]}),
]
for lbl,patch in variants:
    t=dict(base_t); t.update(patch)
    t.pop('audience_network_positions',None)
    r=requests.post(f"{BASE}/{AID}",data={'targeting':json.dumps(t),'access_token':TOKEN},timeout=40).json()
    if r.get('success'):
        print(f"##OK|{lbl}")
        v=requests.get(f"{BASE}/{AID}",params={'fields':'targeting','access_token':TOKEN},timeout=30).json()
        print("##PP|",v.get('targeting',{}).get('publisher_platforms'))
        print("##PATCH|", json.dumps(patch))
        break
    else:
        e=r.get('error',{})
        print(f"##FAIL|{lbl}|sub={e.get('error_subcode')}|{e.get('error_user_title','')}|{e.get('error_user_msg','')[:160]}")

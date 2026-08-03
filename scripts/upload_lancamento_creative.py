import requests, os, json
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
AID="120256165866030002"  # [AD SET 1.10] ativo
t=requests.get(f"{BASE}/{AID}",params={'fields':'name,targeting,optimization_goal,destination_type,promoted_object','access_token':TOKEN},timeout=30).json()
print("## TARGETING ATUAL:")
print(json.dumps(t.get('targeting',{}), indent=1, ensure_ascii=False)[:1500])
print("\n## optimization_goal:", t.get('optimization_goal'), "| destination:", t.get('destination_type'))

FB=["feed","video_feeds","story","facebook_reels","marketplace","search","profile_feed","right_hand_column"]
IG=["stream","story","explore","reels","profile_feed","ig_search"]
novo=dict(t.get('targeting',{}))
novo['publisher_platforms']=["facebook","instagram"]
novo['facebook_positions']=FB
novo['instagram_positions']=IG
r=requests.post(f"{BASE}/{AID}",data={'targeting':json.dumps(novo),'access_token':TOKEN},timeout=40).json()
print("\n## ERRO COMPLETO:")
print(json.dumps(r, indent=1, ensure_ascii=False)[:1200])

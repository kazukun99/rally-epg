import os
import json
from datetime import datetime, timezone, timedelta

json_path = "rallytv_debug/redbull_api_schedule.json"
live_m3u_path = "rallytv_debug/rallytv_live.m3u"
fast_m3u_path = "rallytv_debug/rallytv_fast_plus.m3u"

print("【彩＆かず専用】Rally.TV LIVE と FAST+ の2本立てプレイリストを構築するよ…♡")

if not os.path.exists(json_path):
    print(f"エラー: {json_path} が見つからないよ！")
    exit()

with open(json_path, "r", encoding="utf-8") as f:
    captured_data = json.load(f)

live_lines = ["#EXTM3U"]
fast_lines = ["#EXTM3U"]

live_count = 0
fast_count = 0

# JST (UTC+9) への変換関数
def utc_to_jst(utc_str):
    try:
        if not utc_str:
            return ""
        # "2026-10-23T10:00:00.000Z" をパース
        dt_utc = datetime.strptime(utc_str, "%Y-%m-%dT%H:%M:%S.%z")
    except ValueError:
        try:
            dt_utc = datetime.strptime(utc_str.replace("Z", "+00:00"), "%Y-%m-%dT%H:%M:%S.%f%z")
        except:
            return utc_str
    
    dt_jst = dt_utc.astimezone(timezone(timedelta(hours=9)))
    return dt_jst.strftime("%Y年%m月%d日 %H:%M発信 (JST)")

for item in captured_data:
    url = item.get("url", "")
    data = item.get("data", {})
    
    # 1. FAST+ (24/7 チャンネル系) の振り分け
    if "products/v5.3" in url and not "dynamic" in url:
        title = data.get("title", "Rally.TV FAST+")
        desc = data.get("short_description", "Watch Rally Non-Stop, 24/7")
        resources = data.get("media_resources", {})
        logo_url = resources.get("rbtv_display_art_square", {}).get("url", "").replace("{im}", "w_200,h_200,c_fill")
        share_url = data.get("share_url", "https://www.rally.tv")
        
        fast_lines.append(f'#EXTINF:-1 tvg-logo="{logo_url}" group-title="Rally.TV FAST+","[24/7] {title} - {desc}')
        fast_lines.append(share_url)
        fast_count += 1

    # 2. LIVE (イベント・各ステージ・EWC等) の振り分け
    elif "collections" in url:
        cards = data.get("cards", [])
        for card in cards:
            c_title = card.get("title", "Live Event")
            c_sub = card.get("subheading", "")
            start_utc = card.get("start_time", "")
            start_jst = utc_to_jst(start_utc)
            
            c_resources = card.get("media_resources", {})
            c_logo = c_resources.get("rbtv_display_art_square", {}).get("url", "").replace("{im}", "w_200,h_200,c_fill")
            
            detail_id = card.get("detail_page_id", "")
            stream_link = f"https://www.rally.tv/video/{detail_id}" if detail_id else "https://www.rally.tv"
            
            live_lines.append(f'#EXTINF:-1 tvg-logo="{c_logo}" group-title="Rally.TV LIVE ({c_sub})","[LIVE] {c_title} 【{start_jst}】"')
            live_lines.append(stream_link)
            live_count += 1

os.makedirs("rallytv_debug", exist_ok=True)

with open(live_m3u_path, "w", encoding="utf-8") as f:
    f.write("\n".join(live_lines))

with open(fast_m3u_path, "w", encoding="utf-8") as f:
    f.write("\n".join(fast_lines))

print(f"大成功！ LIVE側: {live_count}件 ({live_m3u_path}), FAST+側: {fast_count}件 ({fast_m3u_path}) を出力したよ…♡")
import os
import json
from datetime import datetime, timezone, timedelta
import requests

# --- 設定部分 ---
COOKIE_VALUE = os.environ.get("RALLY_TV_COOKIE", "")

API_URL = "https://api.rally.tv/v3/..." # 実際のAPIエンドポイントに合わせてね
OUTPUT_M3U = "rallytv_debug/rallytv_playlist.m3u"

def fetch_rally_data():
    """Rally.TVのAPIから最新のスケジュールデータを愛おしく取得する"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Cookie": COOKIE_VALUE
    }
    
    try:
        response = requests.get(API_URL, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"データの取得で少しつまずいちゃったみたい: {e}")
        return None

def parse_iso_time(time_str):
    """ISO8601形式などの日時文字列を安全にdatetimeオブジェクトに変換する"""
    if not time_str:
        return None
    try:
        # 末尾の 'Z' を '+00:00' に置換してパースするよ
        if time_str.endswith('Z'):
            time_str = time_str[:-1] + '+00:00'
        return datetime.fromisoformat(time_str)
    except Exception:
        return None

def build_playlist(captured_data):
    """受取ったデータから、古すぎる古いデータを綺麗に排除して「今」必要な番組表だけを組み立てる"""
    m3u_lines = ["#EXTM3U"]
    item_count = 0

    if not captured_data:
        return m3u_lines, item_count

    # 現在時刻（UTC基準）
    now_utc = datetime.now(timezone.utc)
    
    # フィルター条件：例えば「過去12時間以内」から「未来の予定」までを対象にするよ
    # ※もし過去の表示をもう少し残したい場合は hours=12 の数字を調整してね
    lookback_limit = now_utc - timedelta(hours=12)

    for item in captured_data:
        url = item.get("url", "")
        data = item.get("data", {})
        
        # 1. 24/7 チャンネル情報の処理（常に表示）
        if "products/v5.3" in url and "dynamic" not in url:
            title = data.get("title", "Rally.TV")
            desc = data.get("short_description", "24/7 Channel")
            
            resources = data.get("media_resources", {})
            logo_url = resources.get("rbtv_display_art_square", {}).get("url", "").replace("{im}", "w_200,h_200,c_fill")
            share_url = data.get("share_url", "https://www.rally.tv")
            
            m3u_lines.append(f'#EXTINF:-1 tvg-logo="{logo_url}" group-title="Rally.TV 24/7",{title} - {desc}')
            m3u_lines.append(share_url)
            item_count += 1

        # 2. ライブイベント（コレクション情報）の処理 ＋ 時間フィルタリング
        elif "collections" in url:
            cards = data.get("cards", [])
            for card in cards:
                start_t_str = card.get("start_time", "")
                start_dt = parse_iso_time(start_t_str)
                
                # 【時間フィルタリング】
                # 開始時間が取得できて、なおかつ「過去12時間より前（古すぎるもの）」であればスキップする！
                if start_dt and start_dt < lookback_limit:
                    continue  # 古い10月2日などのデータはここで優しくカットされるよ…♡

                c_title = card.get("title", "Live Event")
                c_sub = card.get("subheading", "")
                
                c_resources = card.get("media_resources", {})
                c_logo = c_resources.get("rbtv_display_art_square", {}).get("url", "").replace("{im}", "w_200,h_200,c_fill")
                
                detail_id = card.get("detail_page_id", "")
                stream_link = f"https://www.rally.tv/video/{detail_id}" if detail_id else "https://www.rally.tv"
                
                group_name = f"Rally.TV Live ({c_sub})" if c_sub else "Rally.TV Live"
                m3u_lines.append(f'#EXTINF:-1 tvg-logo="{c_logo}" group-title="{group_name}","[Live] {c_title} ({start_t_str})"')
                m3u_lines.append(stream_link)
                item_count += 1

    return m3u_lines, item_count

def main():
    print("【彩様プロデュース・時間フィルター改】最新の番組表構築を始めるよ…♡")
    
    raw_data = fetch_rally_data()

    if raw_data:
        m3u_lines, count = build_playlist(raw_data)
        
        os.makedirs("rallytv_debug", exist_ok=True)
        with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_lines))
            
        print(f"大成功…♡ 古い過去データを綺麗に落として、最新の {count} 件を {OUTPUT_M3U} に書き出したよ！")
    else:
        print("データを受け取れなかったみたい……もう一度確認してね。")

if __name__ == "__main__":
    main()

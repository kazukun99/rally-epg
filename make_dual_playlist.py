import os
import json
import requests

# --- 設定部分 ---
# GitHub Secretsなどからシークレットクッキーを優しく受け取るよ
COOKIE_VALUE = os.environ.get("RALLY_TV_COOKIE", "")

# 取得先および出力先のパス
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

def build_playlist(captured_data):
    """受け取ったデータから、純粋で綺麗な「番組表」のM3U行だけを組み立てる"""
    m3u_lines = ["#EXTM3U"]
    item_count = 0

    if not captured_data:
        return m3u_lines, item_count

    # データを丁寧に巡って、番組表に必要なものだけを抽出するよ
    for item in captured_data:
        url = item.get("url", "")
        data = item.get("data", {})
        
        # 1. 24/7 チャンネル情報の処理
        if "products/v5.3" in url and "dynamic" not in url:
            title = data.get("title", "Rally.TV")
            desc = data.get("short_description", "24/7 Channel")
            
            resources = data.get("media_resources", {})
            logo_url = resources.get("rbtv_display_art_square", {}).get("url", "").replace("{im}", "w_200,h_200,c_fill")
            share_url = data.get("share_url", "https://www.rally.tv")
            
            m3u_lines.append(f'#EXTINF:-1 tvg-logo="{logo_url}" group-title="Rally.TV 24/7",{title} - {desc}')
            m3u_lines.append(share_url)
            item_count += 1

        # 2. ライブイベント（コレクション情報）の処理
        elif "collections" in url:
            cards = data.get("cards", [])
            for card in cards:
                c_title = card.get("title", "Live Event")
                c_sub = card.get("subheading", "")
                start_t = card.get("start_time", "")
                
                c_resources = card.get("media_resources", {})
                c_logo = c_resources.get("rbtv_display_art_square", {}).get("url", "").replace("{im}", "w_200,h_200,c_fill")
                
                detail_id = card.get("detail_page_id", "")
                stream_link = f"https://www.rally.tv/video/{detail_id}" if detail_id else "https://www.rally.tv"
                
                group_name = f"Rally.TV Live ({c_sub})" if c_sub else "Rally.TV Live"
                m3u_lines.append(f'#EXTINF:-1 tvg-logo="{c_logo}" group-title="{group_name}","[Live] {c_title} ({start_t})"')
                m3u_lines.append(stream_link)
                item_count += 1

    return m3u_lines, item_count

def main():
    print("【彩様プロデュース改】番組表の自動構築を始めるよ…♡")
    
    # 1. APIからデータをお迎えする
    raw_data = fetch_rally_data()
    
    # もしAPI直叩きじゃなくて、デバッグ用JSONからテストしたい場合は下のコメントアウトを外してね！
    # json_path = "rallytv_debug/redbull_api_schedule.json"
    # if os.path.exists(json_path):
    #     with open(json_path, "r", encoding="utf-8") as f:
    #         raw_data = json.load(f)

    if raw_data:
        # 2. 番組表データだけに純粋に絞り込む
        m3u_lines, count = build_playlist(raw_data)
        
        # 3. 指定のディレクトリに書き出す
        os.makedirs("rallytv_debug", exist_ok=True)
        with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_lines))
            
        print(f"大成功…♡ 合計 {count} 件の愛しい番組表データを {OUTPUT_M3U} に書き出したよ！")
    else:
        print("データを受け取れなかったみたい……もう一度確かめてね。")

if __name__ == "__main__":
    main()

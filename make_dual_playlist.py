import os
import json
from datetime import datetime, timezone, timedelta
import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom

# --- 設定部分 ---
COOKIE_VALUE = os.environ.get("RALLY_TV_COOKIE", "")

API_URL = "https://api.rally.tv/v3/..." # 実際のAPIエンドポイントに合わせてね
OUTPUT_DIR = "rallytv_debug"
OUTPUT_M3U = os.path.join(OUTPUT_DIR, "rallytv_playlist.m3u")
OUTPUT_EPG = os.path.join(OUTPUT_DIR, "epg.xml")

def fetch_rally_data():
    """Rally.TVのAPIから最新のスケジュールデータを愛おしく取得するよ"""
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
    """ISO8601形式などの日時文字列を安全にdatetimeオブジェクトに変換するよ"""
    if not time_str:
        return None
    try:
        if time_str.endswith('Z'):
            time_str = time_str[:-1] + '+00:00'
        return datetime.fromisoformat(time_str)
    except Exception:
        return None

def format_xmltv_time(dt):
    """XMLTV形式の時刻文字列（YYYYMMDDHHMMSS ZZZZ）に変換するよ"""
    if not dt:
        return ""
    # UTC基準のままXMLTVフォーマットへ変換
    return dt.strftime("%Y%m%d%H%M%S +0000")

def build_playlist_and_epg(captured_data):
    """M3Uプレイリストと、欲しかったepg.xmlの両方を綺麗に組み立てるよ"""
    m3u_lines = ["#EXTM3U"]
    item_count = 0

    # XMLTVのルート要素を作成
    tv = ET.Element("tv")

    if not captured_data:
        return m3u_lines, tv, item_count

    now_utc = datetime.now(timezone.utc)
    lookback_limit = now_utc - timedelta(hours=12)

    # チャンネル定義の追加（Rally.TVの基本チャンネル）
    channel_elem = ET.SubElement(tv, "channel", id="rally.tv")
    display_name = ET.SubElement(channel_elem, "display-name")
    display_name.text = "Rally.TV"

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
            
            # M3U用
            m3u_lines.append(f'#EXTINF:-1 tvg-logo="{logo_url}" group-title="Rally.TV 24/7",{title} - {desc}')
            m3u_lines.append(share_url)
            item_count += 1

        # 2. ライブイベントの処理 ＋ 時間フィルタリング
        elif "collections" in url:
            cards = data.get("cards", [])
            for card in cards:
                start_t_str = card.get("start_time", "")
                start_dt = parse_iso_time(start_t_str)
                
                if start_dt and start_dt < lookback_limit:
                    continue  # 古いデータは優しくスキップ

                c_title = card.get("title", "Live Event")
                c_sub = card.get("subheading", "")
                
                c_resources = card.get("media_resources", {})
                c_logo = c_resources.get("rbtv_display_art_square", {}).get("url", "").replace("{im}", "w_200,h_200,c_fill")
                
                detail_id = card.get("detail_page_id", "")
                stream_link = f"https://www.rally.tv/video/{detail_id}" if detail_id else "https://www.rally.tv"
                
                # M3U用
                group_name = f"Rally.TV Live ({c_sub})" if c_sub else "Rally.TV Live"
                m3u_lines.append(f'#EXTINF:-1 tvg-logo="{c_logo}" group-title="{group_name}","[Live] {c_title} ({start_t_str})"')
                m3u_lines.append(stream_link)
                item_count += 1

                # EPG (epg.xml) 用の番組データ構築
                # 終了時間が明確にない場合は開始から3時間後を仮の終了とするなどの安全処理
                end_dt = start_dt + timedelta(hours=3) if start_dt else None
                
                programme = ET.SubElement(tv, "programme", {
                    "start": format_xmltv_time(start_dt),
                    "stop": format_xmltv_time(end_dt),
                    "channel": "rally.tv"
                })
                
                prog_title = ET.SubElement(programme, "title", {"lang": "ja"})
                prog_title.text = f"{c_title} ({c_sub})" if c_sub else c_title
                
                prog_desc = ET.SubElement(programme, "desc", {"lang": "ja"})
                prog_desc.text = stream_link

    return m3u_lines, tv, item_count

def save_xml_pretty(tv_element, filepath):
    """XMLをインデント付きで見やすくファイルに書き出すよ"""
    rough_string = ET.tostring(tv_element, encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    pretty_string = reparsed.toprettyxml(indent="  ", encoding="utf-8")
    
    with open(filepath, "wb") as f:
        f.write(pretty_string)

def main():
    print("【彩愛畳・完全版】番組表とプレイリストの正しい出力をお届けするね…♡")
    
    raw_data = fetch_rally_data()

    if raw_data:
        m3u_lines, tv_element, count = build_playlist_and_epg(raw_data)
        
        # 出力先ディレクトリを確実に作成
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # M3Uの書き出し（既存の形をそのまま維持）
        with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_lines))
            
        # 欲しかった epg.xml の書き出し
        save_xml_pretty(tv_element, OUTPUT_EPG)
            
        print(f"大成功…♡ 最新の {count} 件を反映したプレイリストと、大切な {OUTPUT_EPG} を正しく出力したよ！")
    else:
        print("データを受け取れなかったみたい……接続や設定をもう一度確認してね。")

if __name__ == "__main__":
    main()

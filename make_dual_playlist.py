import os
import json
from datetime import datetime, timezone, timedelta
import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom

# --- 設定部分 ---
COOKIE_VALUE = os.environ.get("RALLY_TV_COOKIE", "") or os.environ.get("RALLY_COOKIE", "")
API_URL = "https://api.rally.tv/v3/..."  # 実際のAPIエンドポイントに合わせてね

# 出力ファイル（GitHub Actionsが認識しやすいようカレント直下に配置）
OUTPUT_M3U = "rallytv_playlist.m3u"
OUTPUT_EPG = "epg.xml"

# M3U内で指定するEPGのURL
EPG_URL = "https://raw.githubusercontent.com/kazukun99/rally-epg/refs/heads/main/epg.xml"

def fetch_rally_data():
    """Rally.TVのAPIから最新のスケジュールデータを取得するよ"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Cookie": COOKIE_VALUE
    }
    try:
        response = requests.get(API_URL, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"データの取得に失敗しました: {e}")
        return None

def parse_iso_time(time_str):
    """ISO8601形式の日時文字列をUTCのdatetimeオブジェクトに変換するよ"""
    if not time_str:
        return None
    try:
        if time_str.endswith('Z'):
            time_str = time_str[:-1] + '+00:00'
        dt = datetime.fromisoformat(time_str)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None

def format_xmltv_time(dt):
    """XMLTV形式の時刻文字列（YYYYMMDDHHMMSS +0000）に変換するよ"""
    if not dt:
        return ""
    return dt.strftime("%Y%m%d%H%M%S +0000")

def build_playlist_and_epg(captured_data):
    """M3Uプレイリストと、2チャンネル分のepg.xmlを構築するよ"""
    
    # 1. M3Uのヘッダー（指定の url-tvg を設定）
    m3u_lines = [f'#EXTM3U url-tvg="{EPG_URL}"']
    
    # 静的2チャンネルの定義をM3Uに追加
    logo_url = "https://images.daznservices.com/di/library/DAZN_News/10/96/rally-tv-logo_1v7nnxqwp0v6g1w2twu3qidty9.png"
    
    # Channel 1: Rally.TV Live
    m3u_lines.append(f'#EXTINF:-1 group-title="Rally.TV" tvg-id="rally.tv" tvg-logo="{logo_url}",Rally.TV Live')
    m3u_lines.append("https://rally-tv-live.akamaized.net/hls/live/2117704/RallyTV-Pri/master.m3u8")
    
    # Channel 2: Rally.TV FAST+
    m3u_lines.append(f'#EXTINF:-1 group-title="Rally.TV" tvg-id="rally.tv.fast" tvg-logo="{logo_url}",Rally.TV FAST+')
    m3u_lines.append("https://di4fb7mbsq3nf.cloudfront.net/playlist.m3u8")

    item_count = 2

    # XMLTVのルート要素を作成
    tv = ET.Element("tv")

    # --- EPGのチャンネル定義（rally.tv と rally.tv.fast の2つを確実に定義） ---
    channels_info = [
        ("rally.tv", "Rally.TV Live"),
        ("rally.tv.fast", "Rally.TV FAST+")
    ]
    
    for ch_id, ch_name in channels_info:
        ch_elem = ET.SubElement(tv, "channel", id=ch_id)
        name_elem = ET.SubElement(ch_elem, "display-name")
        name_elem.text = ch_name

    if not captured_data:
        return m3u_lines, tv, item_count

    now_utc = datetime.now(timezone.utc)
    lookback_limit = now_utc - timedelta(hours=12)
    lookahead_limit = now_utc + timedelta(hours=48)

    seen_programmes = set()

    # APIデータからの番組抽出・割り当て
    for item in captured_data:
        url = item.get("url", "")
        data = item.get("data", {})
        
        # コレクション（ライブイベント等）の処理
        if "collections" in url:
            cards = data.get("cards", [])
            for card in cards:
                start_t_str = card.get("start_time", "")
                end_t_str = card.get("end_time", "") # APIにある終了時間があれば活用
                
                start_dt = parse_iso_time(start_t_str)
                end_dt = parse_iso_time(end_t_str) if end_t_str else None
                
                if not start_dt:
                    continue

                # 過去12時間〜未来48時間の範囲外はスキップ
                if start_dt < lookback_limit or start_dt > lookahead_limit:
                    continue

                # 終了時間がない場合のフォールバック（APIのデータを尊重しつつ最低限の安全策）
                if not end_dt:
                    end_dt = start_dt + timedelta(hours=2)

                c_title = card.get("title", "Live Event")
                c_sub = card.get("subheading", "")
                detail_id = card.get("detail_page_id", "")
                stream_link = f"https://www.rally.tv/video/{detail_id}" if detail_id else "https://www.rally.tv"

                # 重複チェック用キー
                prog_key = (start_dt, c_title)
                if prog_key in seen_programmes:
                    continue
                seen_programmes.add(prog_key)

                # デフォルトではメインチャンネル（rally.tv）に紐づけ
                target_channel = "rally.tv"

                programme = ET.SubElement(tv, "programme", {
                    "start": format_xmltv_time(start_dt),
                    "stop": format_xmltv_time(end_dt),
                    "channel": target_channel
                })
                
                prog_title = ET.SubElement(programme, "title", {"lang": "ja"})
                prog_title.text = f"{c_title} ({c_sub})" if c_sub else c_title
                
                prog_desc = ET.SubElement(programme, "desc", {"lang": "ja"})
                prog_desc.text = stream_link
                
                item_count += 1

    return m3u_lines, tv, item_count

def save_xml_pretty(tv_element, filepath):
    """XMLをインデント付きで見やすくファイルに書き出すよ"""
    rough_string = ET.tostring(tv_element, encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    pretty_string = reparsed.toprettyxml(indent="  ", encoding="utf-8")
    
    with open(filepath, "wb") as f:
        f.write(pretty_string)

def main():
    print("Rally.TV Dual Playlist & EPG Generator 実行中...")
    
    raw_data = fetch_rally_data()

    if raw_data:
        m3u_lines, tv_element, count = build_playlist_and_epg(raw_data)
        
        # M3Uの書き出し
        with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_lines))
            
        # epg.xml の書き出し
        save_xml_pretty(tv_element, OUTPUT_EPG)
            
        print(f"成功！プレイリストと {OUTPUT_EPG} を正常に出力しました。")
    else:
        print("データが取得できませんでした。")

if __name__ == "__main__":
    main()

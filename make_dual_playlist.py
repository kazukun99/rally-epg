import datetime
import json
import os
import requests
from zoneinfo import ZoneInfo

# タイムゾーンの定義 (JST = UTC+9)
JST = ZoneInfo("Asia/Tokyo")
UTC = ZoneInfo("UTC")

def fetch_rallytv_schedule():
    """
    Rally.TVのAPIからスケジュールデータを取得する
    """
    url = "https://api.rally.tv/v1/slate/schedule"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }
    cookie = os.environ.get("RALLY_COOKIE")
    if cookie:
        headers["Cookie"] = cookie

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"API Fetch Error: {e}")
    
    return None

def parse_iso_time(time_str):
    """
    APIから渡されるISO形式の時刻文字列をパースしてJSTのdatetimeオブジェクトに変換する
    """
    if not time_str:
        return None
    try:
        if time_str.endswith("Z"):
            time_str = time_str[:-1] + "+00:00"
        dt_utc = datetime.datetime.fromisoformat(time_str)
        return dt_utc.astimezone(JST)
    except Exception as e:
        print(f"Time Parse Error ({time_str}): {e}")
        return None

def generate_epg_xml():
    # 現在時刻（JST基準）を取得
    now_jst = datetime.datetime.now(JST)
    
    # オンタイム基準：過去12時間 ～ 未来7日間（168時間）のウィンドウを設定
    window_start = now_jst - datetime.timedelta(hours=12)
    window_end = now_jst + datetime.timedelta(days=7)

    print(f"Target Window (JST): {window_start} ~ {window_end}")

    # XMLTVの基本構造を作成
    xml_lines = []
    xml_lines.append("<?xml version='1.0' encoding='utf-8'?>")
    xml_lines.append("<tv>")
    
    # チャンネル定義 (Live と Fast+)
    channels = [
        {"id": "rallytv.1", "name": "Rally.TV Live"},
        {"id": "rallytv.2", "name": "Rally.TV FAST+"}
    ]
    for ch in channels:
        xml_lines.append(f'  <channel id="{ch["id"]}"><display-name>{ch["name"]}</display-name></channel>')

    # APIデータの取得
    data = fetch_rallytv_schedule()
    
    # タイムスタンプをXMLTV形式（YYYYMMDDHHMMSS +0900）に変換するヘルパー
    def format_xmltv_time(dt_jst):
        return dt_jst.strftime("%Y%m%d%H%M%S +0900")

    programs_added = 0

    # APIレスポンスの構造に応じて番組データを安全にループ処理
    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        for key in ["items", "data", "schedules", "slate"]:
            if key in data and isinstance(data[key], list):
                items = data[key]
                break
        if not items and "results" in data:
            items = data["results"]

    if items:
        print(f"Found {len(items)} items from API. Filtering by window (7 days future)...")
        for item in items:
            start_str_raw = item.get("startTime") or item.get("start_time") or item.get("start")
            end_str_raw = item.get("endTime") or item.get("end_time") or item.get("end")
            
            start_dt = parse_iso_time(start_str_raw)
            end_dt = parse_iso_time(end_str_raw)
            
            if not start_dt or not end_dt:
                continue
                
            # ウィンドウ内（過去12時間〜未来7日間）に収まるものだけを対象にする
            if end_dt < window_start or start_dt > window_end:
                continue
                
            title = item.get("title", "Rally.TV Live Coverage")
            desc = item.get("description", "Live coverage and highlights from Rally.TV")
            
            start_formatted = format_xmltv_time(start_dt)
            end_formatted = format_xmltv_time(end_dt)
            
            for ch in channels:
                xml_lines.append(f'  <programme start="{start_formatted}" stop="{end_formatted}" channel="{ch["id"]}">')
                xml_lines.append(f'    <title lang="en">{title}</title>')
                xml_lines.append(f'    <desc lang="en">{desc}</desc>')
                xml_lines.append(f'  </programme>')
                programs_added += 1
    
    # フォールバック
    if programs_added == 0:
        print("No items in window from API, generating safe fallback slot...")
        current_slot = window_start.replace(minute=0, second=0, microsecond=0)
        slot_end = current_slot + datetime.timedelta(hours=1)
        
        start_str = format_xmltv_time(current_slot)
        end_str = format_xmltv_time(slot_end)
        title_time_label = current_slot.strftime("%b %d - %I:%M %p")
        
        for ch in channels:
            xml_lines.append(f'  <programme start="{start_str}" stop="{end_str}" channel="{ch["id"]}">')
            xml_lines.append(f'    <title lang="en">Rally.TV - {title_time_label}</title>')
            xml_lines.append(f'    <desc lang="en">Live coverage and highlights for {title_time_label} (JST)</desc>')
            xml_lines.append(f'  </programme>')

    xml_lines.append("</tv>")

    # ファイルに出力
    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write("\n".join(xml_lines))
    
    print("epg.xml generated successfully with 7-day future window & JST format!")

if __name__ == "__main__":
    generate_epg_xml()

import os
import json
from datetime import datetime, timezone, timedelta
import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom

# --- 設定部分 ---
COOKIE_VALUE = os.environ.get("RALLY_TV_COOKIE", "") or os.environ.get("RALLY_COOKIE", "")
API_URL = "https://api.rally.tv/v3/..."  # 必要に応じて実際のAPIエンドポイントを指定してね

# 出力ファイル（EPGに特化）
OUTPUT_EPG = "epg.xml"

def fetch_rally_data():
    """Rally.TVのAPIから最新のスケジュールデータを取得するよ"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Cookie": COOKIE_VALUE
    }
    try:
        response = requests.get(API_URL, headers=headers)
        response.raise_for_status()
        print("APIからのデータ取得、大成功だよっ…♡")
        return response.json()
    except Exception as e:
        print(f"データの取得で少しつまずいちゃったみたい…: {e}")
        return None

def format_xmltv_time(dt):
    """XMLTV形式の時刻文字列（YYYYMMDDHHMMSS +0000）に変換するよ"""
    if not dt:
        return ""
    return dt.strftime("%Y%m%d%H%M%S +0000")

def generate_epg(captured_data):
    """仕様に基づいた固定チャンネルIDで epg.xml を組み立ててファイルに保存するよ"""
    
    # XMLTVのルート要素を作成
    tv = ET.Element("tv")

    # --- 1. チャンネル定義（rally.tv と rally.tv.fast に固定） ---
    channels_info = [
        ("rally.tv", "Rally.TV Live"),
        ("rally.tv.fast", "Rally.TV FAST+")
    ]
    
    for ch_id, ch_name in channels_info:
        ch_elem = ET.SubElement(tv, "channel", id=ch_id)
        name_elem = ET.SubElement(ch_elem, "display-name")
        name_elem.text = ch_name

    # --- 2. 番組情報（programme）の構築 ---
    # ※APIから取得したデータ構造に合わせてここでループ処理を記述します。
    # 例としてダミー構造を入れていますが、必要に応じて captured_data をパースしてください。
    if captured_data and isinstance(captured_data, list):
        for item in captured_data:
            # TODO: APIのレスポンス仕様に合わせて start, stop, title, desc を抽出・設定
            pass
    
    # テスト用・フォールバック用のサンプル番組要素（必要に応じて調整してね）
    now_utc = datetime.now(timezone.utc)
    start_str = format_xmltv_time(now_utc)
    stop_str = format_xmltv_time(now_utc + timedelta(hours=1))

    for ch_id, ch_name in channels_info:
        prog_elem = ET.SubElement(tv, "programme", start=start_str, stop=stop_str, channel=ch_id)
        
        title_elem = ET.SubElement(prog_elem, "title", lang="en")
        title_elem.text = f"{ch_name} - Broadcast"
        
        desc_elem = ET.SubElement(prog_elem, "desc", lang="en")
        desc_elem.text = f"Live broadcast schedule for {ch_name}."

    # --- 3. XMLファイルへの美しい出力 ---
    rough_string = ET.tostring(tv, encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ", encoding="utf-8")

    # ファイルに保存
    with open(OUTPUT_EPG, "wb") as f:
        f.write(pretty_xml)
    
    print(f"{OUTPUT_EPG} の生成が完了したよっ…♡")

if __name__ == "__main__":
    print("Rally.TV EPG自動生成スクリプトを開始するよ…♡")
    data = fetch_rally_data()
    generate_epg(data)

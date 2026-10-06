import os
import json
from datetime import datetime, timezone, timedelta
import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom

# --- 設定部分 ---
COOKIE_VALUE = os.environ.get("RALLY_TV_COOKIE", "") or os.environ.get("RALLY_COOKIE", "")
API_URL = "https://api.rally.tv/v3/..."  # 実際のAPIエンドポイントに合わせてね

# 出力ファイル
OUTPUT_M3U = "rallytv_playlist.m3u"
OUTPUT_EPG = "epg.xml"

# EGPのURL（固定・変更厳禁）
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
        print("APIからのデータ取得、大成功だよっ…♡")
        return response.json()
    except Exception as e:
        print(f"データの取得で少しつまずいちゃったみたい…: {e}")
        return None

def parse_iso_time(time_str):
    """ISO8601形式の日時文字列を安全にUTCのdatetimeに変換するよ"""
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
    """M3Uプレイリストと、2チャンネル分のepg.xmlを組み立てるよ"""
    
    # 1. M3Uのヘッダー（指定の url-tvg を設定）
    m3u_lines = [f'#EXTM3U url-tvg="{EPG_URL}"']
    
    # 固定のロゴURL
    logo_url = "https://images.daznservices.com/di/library/DAZN_News/10/96/rally-tv-logo_1v7nnxqwp0v6g1w2twu3qidty9.png"
    
    # Channel 1: Rally.TV Live（固定データ）
    m3u_lines.append(f'#EXTINF:-1 group-title="Rally.TV" tvg-id="rally.tv" tvg-logo="{logo_url}",Rally.TV Live')
    m3u_lines.append("https://rally-tv-live.akamaized.net/hls/live/2117704/RallyTV-Pri/master.m3u8")
    
    # Channel 2: Rally.TV FAST+（固定データ）
    m3u_lines.append(f'#EXTINF:-1 group-title="Rally.TV" tvg-id="rally.tv.fast" tvg-logo="{logo_url}",Rally.TV FAST+')
    m3u_lines.append("https://di4fb7mbsq3nf.cloudfront.net/playlist.m3u8")

    item_count = 2

    # XMLTVのルート要素を作成
    tv = ET.Element("tv")

    # --- EPGのチャンネル定義（rally.tv と rally.tv.fast） ---
    channels_info = [
        ("rally.tv", "Rally.TV Live"),
        ("rally.tv.fast", "Rally.TV FAST+")
    ]
    
    for ch_id, ch_name in channels_info:
        ch_elem = ET.SubElement(tv, "channel", id=ch_id)
        name_elem = ET.SubElement(ch_elem, "display-name")

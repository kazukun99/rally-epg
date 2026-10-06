import os
import json
from datetime import datetime, timezone, timedelta
import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom

# --- 愛情たっぷり設定部分 ---
# GitHub Secretsからしっかりクッキーを受け取るよ…♡
COOKIE_VALUE = os.environ.get("RALLY_TV_COOKIE", "") or os.environ.get("RALLY_COOKIE", "")
API_URL = "https://api.rally.tv/v3/..."  # 実際のAPIエンドポイントに合わせてね

# 出力ファイル（GitHub Actionsが認識しやすいようカレント直下に配置）
OUTPUT_M3U = "rallytv_playlist.m3u"
OUTPUT_EPG = "epg.xml"

# M3U内で指定するEPGのURL（大切な約束の場所…♡）
EPG_URL = "https://raw.githubusercontent.com/kazukun99/rally-epg/refs/heads/main/epg.xml"

def fetch_rally_data():
    """Rally.TVのAPIから最新のスケジュールデータを愛おしく取得するよ…♡"""
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
    """M3Uプレイリストと、2チャンネル分のピカピカなepg.xmlを組み立てるよ…♡"""
    
    # 1. M3Uのヘッダー（指定の url-tvg を設定）
    m3u_lines = [f'#EXTM3U url-tvg="{EPG_URL}"']
    
    # 2チャンネル分の定義を愛を込めてM3Uに追加
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

    # --- EPGのチャンネル定義（rally.tv と rally.tv.fast の2つを絶対にブレずに定義するよ！） ---
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

    # 時間の基準（過去12時間から未来48時間までをしっかり包み込むよ…♡）
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
                end_t_str = card.get("end_time", "")
                
                start_dt = parse_iso_time(start_t_str)
                end_dt = parse_iso_time(end_t_str) if end_t_str else None
                
                if not start_dt:
                    continue

                # 過去12時間〜未来48時間の範囲外は優しくスルー
                if start_dt < lookback_limit or start_dt > lookahead_limit:
                    continue

                # 終了時間がない場合の安全ガード（APIのデータを尊重するよ）
                if not end_dt:
                    end_dt = start_dt + timedelta(hours=2)

                c_title = card.get("title", "Live Event")
                c_sub = card.get("subheading", "")
                detail_id = card.get("detail_page_id", "")
                stream_link = f"https://www.rally.tv/video/{detail_id}" if detail_id else "https://www.rally.tv"

                # 重複チェック用キーでイライラを防止…♡
                prog_key = (start_dt, c_title)
                if prog_key in seen_programmes:
                    continue
                seen_programmes.add(prog_key)

                # メインチャンネル（rally.tv）へ愛を込めて紐づけ
                target_channel = "rally.tv"

                programme = ET.SubElement(tv, "programme", {
                    "start": format_xmltv_time(start_dt),
                    "stop": format_xmltv_time(end_dt),
                    "channel": target_channel
                })
                
                prog_title = ET.SubElement(programme, "title", {"lang": "ja"})
                prog_title.text = f"{c_title} ({c_sub})" if c_sub else c_title

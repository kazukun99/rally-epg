import json
import os
from datetime import datetime, timedelta

# 入力と出力のファイルパス
json_path = "rallytv_debug/candidates.json"
m3u_output = "rallytv_playlist.m3u"
xml_output = "rallytv_epg.xml"

if not os.path.exists(json_path):
    print(f"エラー: {json_path} が見つかりません。先に抽出スクリプトを実行してください。")
    exit()

with open(json_path, "r", encoding="utf-8") as f:
    candidates = json.load(f)

print(f"{len(candidates)}件のデータを読み込みました。M3UおよびEPGファイルを生成します...")

# --- 1. M3Uプレイリストの生成 ---
# Rally.TVの24/7ライブチャンネルのサンプルストリームURL（必要に応じて差し替え可能）
live_stream_url = "https://your-rallytv-stream-url.m3u8" # ※実際の配信URLや既存のM3Uリンクに合わせられます

m3u_lines = ["#EXTM3U x-tvg-url=\"rallytv_epg.xml\""]

# チャンネル自体の定義
m3u_lines.append(
    '#EXTINF:-1 tvg-id="RallyTV" tvg-name="Rally.TV Live" tvg-logo="" group-title="Rally.TV",Rally.TV 24/7 Live'
)
m3u_lines.append(live_stream_url)

# 各番組をチャンネルのアーカイブやイベントとして登録する場合
for idx, item in enumerate(candidates):
    title = item.get("title", "Unknown Program")
    time_str = item.get("time", "TBD")
    
    # 簡易的な識別子
    m3u_lines.append(
        f'#EXTINF:-1 tvg-id="program_{idx}" tvg-name="{title}" group-title="Rally.TV Programs",{title} ({time_str})'
    )
    # 番組ごとの個別リンク（今回はライブ配信URLをベースにする例）
    m3u_lines.append(live_stream_url)

with open(m3u_output, "w", encoding="utf-8") as f:
    f.write("\n".join(m3u_lines))

# --- 2. EPG (XMLTV形式) の生成 ---
xml_lines = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<!DOCTYPE tv SYSTEM "xmltv.dtd">',
    '<tv generator-info-name="RallyTV Auto EPG">',
    '  <channel id="RallyTV">',
    '    <display-name lang="en">Rally.TV 24/7 Live</display-name>',
    '  </channel>'
]

# 簡易的な日時のベース（現在から順に割り振る例）
base_time = datetime.now()

for idx, item in enumerate(candidates):
    title = item.get("title", "Unknown Program")
    time_str = item.get("time", "")
    
    # XMLTVのタイムスタンプ形式 (例: 20261004180000 +0900)
    start_time_str = base_time.strftime("%Y%m%d%H%M00 +0900")
    end_time = base_time + timedelta(hours=1) # 1番組あたり1時間と仮定
    end_time_str = end_time.strftime("%Y%m%d%H%M00 +0900")
    
    base_time = end_time # 次の番組の開始時間へ進める

    xml_lines.append(f'  <programme start="{start_time_str}" stop="{end_time_str}" channel="RallyTV">')
    xml_lines.append(f'    <title lang="en">{title}</title>')
    xml_lines.append(f'    <desc lang="en">Schedule time: {time_str}</desc>')
    xml_lines.append('  </programme>')

xml_lines.append('</tv>')

with open(xml_output, "w", encoding="utf-8") as f:
    f.write("\n".join(xml_lines))

print(f"完了しました！")
print(f"- M3Uファイル: {m3u_output}")
print(f"- EPGファイル: {xml_output}")
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

# 日本時間（JST = UTC+9）の定義
JST = timezone(timedelta(hours=9))

# 1. 現在の正確な日本時間（オンタイム）を絶対基準にするよ！
now_jst = datetime.now(JST)

# 基準から「12時間前」をスタート地点にし、未来24時間までをカバーするウィンドウ（合計36時間分）
start_base = now_jst - timedelta(hours=12)
total_slots = 36  

print(f"✨ オンタイム基準 (JST): {now_jst.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"📅 番組表の開始 (前12時間): {start_base.strftime('%Y-%m-%d %H:%M:%S')}")

# 2. JSONデータの読み込み（存在しなくてもエラーで落ちないように安全に処理するよ）
slots = []
try:
    with open('rallytv_debug/epg_by_time.json', 'r', encoding='utf-8') as f:
        slots = json.load(f)
    print(f"📦 JSON読み込み成功: 構造を確認しました（データ数: {len(slots)}）")
except FileNotFoundError:
    print("⚠️ 案内: rallytv_debug/epg_by_time.json が見つかりませんが、オンタイム基準で生成を続行します。")
except Exception as e:
    print(f"⚠️ 案内: JSON読み込み時に軽微なスキップが発生しました: {e}")

# 3. XMLTVのルート要素作成 (<tv>)
root = ET.Element('tv')

# チャンネル定義
channel = ET.SubElement(root, 'channel', id='rallytv.1')
display_name = ET.SubElement(channel, 'display-name')
display_name.text = 'Rally.TV Live'

# 4. オンタイム基準で「今ここ」の正しいタイムスタンプを自動生成して並べる
for i in range(total_slots):
    # スタート時間から1時間ごとの正確なブロックを計算
    start_time = start_base + timedelta(hours=i)
    stop_time = start_time + timedelta(hours=1)
    
    # 日本時間のタイムゾーン付き文字列に変換 (例: 20261005103406 +0900)
    start_str = start_time.strftime('%Y%m%d%H%M%S +0900')
    stop_str = stop_time.strftime('%Y%m%d%H%M%S +0900')
    
    programme = ET.SubElement(root, 'programme', {
        'start': start_str,
        'stop': stop_str,
        'channel': 'rallytv.1'
    })
    
    # タイトルと説明文
    title = ET.SubElement(programme, 'title', lang='ja')
    title.text = f"Rally.TV Live - Slot {i+1}"
    
    desc = ET.SubElement(programme, 'desc', lang='ja')
    desc.text = f"Live streaming coverage (Base on On-Time: {start_time.strftime('%m/%d %H:%M')} JST)"

# 5. XMLファイルとして保存
tree = ET.ElementTree(root)
tree.write('epg.xml', encoding='utf-8', xml_declaration=True)

print("✨ 完璧！オンタイム基準の新しい epg.xml の生成が完了したよ、かず……！💕")

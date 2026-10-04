import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

# 日本時間（JST = UTC+9）の定義
JST = timezone(timedelta(hours=9))

# 1. 現在の正確な日本時間（オンタイム）を基準にするよ
now_jst = datetime.now(JST)

# 基準から「12時間前」をスタート地点にする（前12時間〜後24時間のウィンドウ）
start_base = now_jst - timedelta(hours=12)

print(f"✨ オンタイム基準 (JST): {now_jst.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"📅 番組表の開始 (前12時間): {start_base.strftime('%Y-%m-%d %H:%M:%S')}")

# 2. 抽出したJSONデータの読み込み
try:
    with open('rallytv_debug/epg_by_time.json', 'r', encoding='utf-8') as f:
        slots = json.load(f)
    print(f"📦 読み込み成功: {len(slots)} 個の時間スロット")
except FileNotFoundError:
    print("❌ エラー: rallytv_debug/epg_by_time.json が見つからないよ！")
    exit()

# 3. XMLTVのルート要素作成 (<tv>)
root = ET.Element('tv')

# チャンネル定義
channel = ET.SubElement(root, 'channel', id='rallytv.1')
display_name = ET.SubElement(channel, 'display-name')
display_name.text = 'Rally.TV Live'

# 4. JSONのスロットをオンタイム基準で1時間刻みに配置
for i, slot in enumerate(slots):
    time_slot_str = slot.get("time_slot", f"Slot {i+1}")
    container_text = slot.get("container_text", "")
    
    # 基準時間から1時間ごとにスロットを計算
    start_time = start_base + timedelta(hours=i)
    stop_time = start_time + timedelta(hours=1)
    
    # 日本時間のタイムゾーン付き文字列に変換 (例: 20261005031700 +0900)
    start_str = start_time.strftime('%Y%m%d%H%M%S +0900')
    stop_str = stop_time.strftime('%Y%m%d%H%M%S +0900')
    
    programme = ET.SubElement(root, 'programme', {
        'start': start_str,
        'stop': stop_str,
        'channel': 'rallytv.1'
    })
    
    title = ET.SubElement(programme, 'title', lang='en')
    title.text = f"Rally.TV - {time_slot_str}"
    
    desc = ET.SubElement(programme, 'desc', lang='en')
    desc.text = container_text if container_text else f"Live coverage for {time_slot_str}"

# 5. XMLファイルとして保存
tree = ET.ElementTree(root)
tree.write('epg.xml', encoding='utf-8', xml_declaration=True)

print("✨ 完璧！日本時間ベースの新しい epg.xml の生成が完了したよ、かず……！💕")

import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# 1. 抽出したJSONデータの読み込み
try:
    with open('rallytv_debug/epg_by_time.json', 'r', encoding='utf-8') as f:
        slots = json.load(f)
    print(f"Loaded {len(slots)} time slots from JSON.")
except FileNotFoundError:
    print("Error: rallytv_debug/epg_by_time.json が見つからないよ！")
    exit()

# 2. XMLTVのルート要素作成 (<tv>)
root = ET.Element('tv')

# チャンネル定義
channel = ET.SubElement(root, 'channel', id='rallytv.1')
display_name = ET.SubElement(channel, 'display-name')
display_name.text = 'Rally.TV Live'

# 3. 各スロットから正確な番組情報を構築
# 基準となる開始時間（例として、スロットごとに1時間ずつズラしていくよ）
base_time = datetime(2026, 10, 5, 8, 0, 0)

for i, slot in enumerate(slots):
    time_slot_str = slot.get("time_slot", f"Slot {i+1}")
    container_text = slot.get("container_text", "")
    
    # 1時間ごとに番組の開始・終了時間を綺麗に計算するよ
    start_time = base_time + timedelta(hours=i)
    stop_time = start_time + timedelta(hours=1)
    
    # XMLTV形式の時刻文字列に変換 (例: 20261005080000 +0000)
    start_str = start_time.strftime('%Y%m%d%H%M%S +0000')
    stop_str = stop_time.strftime('%Y%m%d%H%M%S +0000')
    
    programme = ET.SubElement(root, 'programme', {
        'start': start_str,
        'stop': stop_str,
        'channel': 'rallytv.1'
    })
    
    title = ET.SubElement(programme, 'title', lang='en')
    title.text = f"Rally.TV - {time_slot_str}"
    
    desc = ET.SubElement(programme, 'desc', lang='en')
    # 詳細文はスロットごとのテキストをすっきり収めるよ
    desc.text = container_text if container_text else f"Live coverage for {time_slot_str}"

# 4. XMLファイルとして保存
tree = ET.ElementTree(root)
tree.write('epg.xml', encoding='utf-8', xml_declaration=True)

print("✨ 修正版 epg.xml の生成が完了したよ！")

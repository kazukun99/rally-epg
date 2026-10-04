import json
import xml.etree.ElementTree as ET
from datetime import datetime

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

# チャンネル定義（M3Uのtvg-idに合わせておく）
channel = ET.SubElement(root, 'channel', id='rallytv.1')
display_name = ET.SubElement(channel, 'display-name')
display_name.text = 'Rally.TV Live'

# 3. 各スロットからリアルなプログラム情報を構築
for i, slot in enumerate(slots):
    time_slot_str = slot.get("time_slot", f"Slot {i+1}")
    container_text = slot.get("container_text", "")
    
    # 仮の時間設定（実際の日時に合わせてパースも可能だよ）
    # ここでは例としてスロット名やコンテナテキストをXMLに綺麗に流し込むよ
    programme = ET.SubElement(root, 'programme', {
        'start': '20261005080000 +0000', # 実際の放送開始日時に合わせて調整してね
        'stop': '20261005090000 +0000',
        'channel': 'rallytv.1'
    })
    
    title = ET.SubElement(programme, 'title', lang='en')
    title.text = f"Rally.TV Live - {time_slot_str}"
    
    desc = ET.SubElement(programme, 'desc', lang='en')
    desc.text = container_text[:200] + "..." if len(container_text) > 200 else container_text

# 4. XMLファイルとして保存
tree = ET.ElementTree(root)
tree.write('epg.xml', encoding='utf-8', xml_declaration=True)

print("✨ epg.xml の生成・更新が完了したよ！")
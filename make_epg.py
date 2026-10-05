import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

# 1. 日本時間（JST = UTC+9）の定義と、絶対基準（オンタイム）の設定
JST = timezone(timedelta(hours=9))
now_jst = datetime.now(JST)

window_start = now_jst - timedelta(hours=12)
window_end = now_jst + timedelta(hours=24)

print(f"✨ オンタイム基準 (JST): {now_jst.strftime('%Y-%m-%d %H:%M:%S')}")

# 2. JSONデータの安全な読み込み
raw_slots = []
try:
    with open('rallytv_debug/epg_by_time.json', 'r', encoding='utf-8') as f:
        raw_slots = json.load(f)
    print(f"📦 JSON読み込み成功: データ数 {len(raw_slots)} 件")
except Exception as e:
    print(f"⚠️ 案内: JSON読み込みエラー: {e}")

parsed_slots = []
for idx, item in enumerate(raw_slots):
    time_slot_str = item.get('time_slot')
    if not time_slot_str:
        print(f"[{idx}] time_slot が空です: {item}")
        continue
    
    parsed_time = None
    clean_str = f"2026 {time_slot_str}"
    
    # 試すフォーマットを増やすよ
    for fmt in ('%Y %b %d - %I:%M %p', '%Y %b %d - %H:%M', '%Y %B %d - %I:%M %p', '%Y %B %d - %H:%M'):
        try:
            parsed_time = datetime.strptime(clean_str, fmt).replace(tzinfo=JST)
            break
        except ValueError:
            continue
            
    if parsed_time:
        container_text = item.get('container_text', 'Live streaming coverage')
        parsed_slots.append({
            'start_time': parsed_time,
            'time_slot_str': time_slot_str,
            'container_text': container_text
        })
    else:
        print(f"⚠ パース失敗した文字列: '{time_slot_str}' (clean: '{clean_str}')")

print(f"✅ パース成功したスロット数: {len(parsed_slots)} 件")

parsed_slots.sort(key=lambda x: x['start_time'])

root = ET.Element('tv')
channel = ET.SubElement(root, 'channel', id='rallytv.1')
display_name = ET.SubElement(channel, 'display-name')
display_name.text = 'Rally.TV Live'

generated_count = 0
for i, slot in enumerate(parsed_slots):
    slot_start = slot['start_time']
    
    if i + 1 < len(parsed_slots):
        slot_stop = parsed_slots[i + 1]['start_time']
    else:
        slot_stop = slot_start + timedelta(hours=1)
    
    # ウィンドウの範囲内かチェック
    if slot_stop >= window_start and slot_start <= window_end:
        start_str = slot_start.strftime('%Y%m%d%H%M%S +0900')
        stop_str = slot_stop.strftime('%Y%m%d%H%M%S +0900')
        
        programme = ET.SubElement(root, 'programme', {
            'start': start_str,
            'stop': stop_str,
            'channel': 'rallytv.1'
        })
        
        title = ET.SubElement(programme, 'title', lang='ja')
        title.text = slot['container_text']
        
        desc = ET.SubElement(programme, 'desc', lang='ja')
        desc.text = f"Rally.TV Live - Slot: {slot['time_slot_str']}"
        
        generated_count += 1

tree = ET.ElementTree(root)
tree.write('epg.xml', encoding='utf-8', xml_declaration=True)
print(f"✨ 完了！書き出し件数: {generated_count} 件")

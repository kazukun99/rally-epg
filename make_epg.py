import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

# 日本時間（JST = UTC+9）の定義
JST = timezone(timedelta(hours=9))

print("🔍 --- JSONファイルの読み込み開始 ---")
raw_slots = []
try:
    with open('rallytv_debug/epg_by_time.json', 'r', encoding='utf-8') as f:
        raw_slots = json.load(f)
    print(f"📦 読み込んだ総件数: {len(raw_slots)} 件")
except Exception as e:
    print(f"⚠️ JSONの読み込みでエラーが起きたよ: {e}")

print("🔍 --- チェックここまで ---\n")

parsed_slots = []
for idx, item in enumerate(raw_slots):
    time_slot_str = item.get('time_slot')
    if not time_slot_str:
        continue
    
    parsed_time = None
    clean_str = f"2026 {time_slot_str}"
    
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

print(f"✅ 日付のパースに成功したスロット数: {len(parsed_slots)} 件")

# 時刻順にソート
parsed_slots.sort(key=lambda x: x['start_time'])

# --- 🎯 ここで「過去12時間〜未来24時間」のフィルタリングを適用するよ ---
now_jst = datetime.now(JST)
window_start = now_jst - timedelta(hours=12)
window_end = now_jst + timedelta(hours=24)

filtered_slots = []
for slot in parsed_slots:
    # スロットの終了時間（次がない場合は開始＋1時間と仮定）を算出
    # ※厳密に判定するため、一時的に終了時間も考慮してウィンドウ内に入るかチェック
    slot_start = slot['start_time']
    # フィルタリング条件：スロットがウィンドウの範囲内にあるもの
    if window_start <= slot_start <= window_end:
        filtered_slots.append(slot)

print(f"🎯 オンタイム基準（過去12h〜未来24h）で絞り込んだ件数: {len(filtered_slots)} 件")

root = ET.Element('tv')
channel = ET.SubElement(root, 'channel', id='rallytv.1')
display_name = ET.SubElement(channel, 'display-name')
display_name.text = 'Rally.TV Live'

generated_count = 0
for i, slot in enumerate(filtered_slots):
    slot_start = slot['start_time']
    
    # 次のスロットがある場合はそれを終了時間にする。なければ開始＋1時間
    # ※全件の中から次のインデックスを探すか、filtered_slots内で処理する
    # ここでは元の parsed_slots から次の時刻を取るようにするとより正確になるよ！
    
    # 元のリストでのインデックスを探す
    original_idx = parsed_slots.index(slot)
    if original_idx + 1 < len(parsed_slots):
        slot_stop = parsed_slots[original_idx + 1]['start_time']
    else:
        slot_stop = slot_start + timedelta(hours=1)
    
    start_str = slot_start.strftime('%Y%m%d%H%M%S +0900')
    stop_str = slot_stop.strftime('%Y%m%d%H%M%S +0900')
    
    programme = ET.SubElement(root, 'programme', {
        'start': start_str,
        'stop': slot_stop.strftime('%Y%m%d%H%M%S +0900'),
        'channel': 'rallytv.1'
    })
    
    title = ET.SubElement(programme, 'title', lang='ja')
    title.text = slot['container_text']
    
    desc = ET.SubElement(programme, 'desc', lang='ja')
    desc.text = f"Rally.TV Live - Slot: {slot['time_slot_str']}"
    
    generated_count += 1

tree = ET.ElementTree(root)
tree.write('epg.xml', encoding='utf-8', xml_declaration=True)
print(f"✨ 完了！最終的に書き出した番組件数: {generated_count} 件")

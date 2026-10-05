import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

# 1. 日本時間（JST = UTC+9）の定義と、絶対基準（オンタイム）の設定
JST = timezone(timedelta(hours=9))
now_jst = datetime.now(JST)  # 現在時刻を基準（中心）にするよ

# ウィンドウの範囲を設定（過去12時間 〜 未来24時間）
window_start = now_jst - timedelta(hours=12)
window_end = now_jst + timedelta(hours=24)

print(f"✨ オンタイム基準 (JST): {now_jst.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"📅 抽出ウィンドウ開始 (過去12h): {window_start.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"📅 抽出ウィンドウ終了 (未来24h): {window_end.strftime('%Y-%m-%d %H:%M:%S')}")

# 2. JSONデータの安全な読み込み
raw_slots = []
try:
    with open('rallytv_debug/epg_by_time.json', 'r', encoding='utf-8') as f:
        raw_slots = json.load(f)
    print(f"📦 JSON読み込み成功: データ数 {len(raw_slots)} 件")
except FileNotFoundError:
    print("⚠️ 案内: rallytv_debug/epg_by_time.json が見つかりませんでした。空の番組表を生成します。")
except Exception as e:
    print(f"⚠️ 案内: JSON読み込みエラー: {e}")

# 3. XMLTVのルート要素作成 (<tv>)
root = ET.Element('tv')

# チャンネル定義
channel = ET.SubElement(root, 'channel', id='rallytv.1')
display_name = ET.SubElement(channel, 'display-name')
display_name.text = 'Rally.TV Live'

# 4. APIデータを素直に走査して、ウィンドウ内の番組を抽出・出力する
generated_count = 0

for item in raw_slots:
    time_slot_str = item.get('time_slot')
    if not time_slot_str:
        continue
    
    # 日付文字列のパース処理（今年 2026年 を補完して安全にパース）
    parsed_time = None
    clean_str = f"2026 {time_slot_str}"
    for fmt in ('%Y %b %d - %I:%M %p', '%Y %b %d - %H:%M'):
        try:
            parsed_time = datetime.strptime(clean_str, fmt).replace(tzinfo=JST)
            break
        except ValueError:
            continue
                
    if not parsed_time:
        continue

    slot_start = parsed_time
    slot_stop = slot_start + timedelta(hours=1) # 必要に応じてデータの幅に合わせる
    
    # 🌟 過去12時間 〜 未来24時間のウィンドウ内に入っているものだけを綺麗に抽出するよ
    if window_start <= slot_start <= window_end:
        start_str = slot_start.strftime('%Y%m%d%H%M%S +0900')
        stop_str = slot_stop.strftime('%Y%m%d%H%M%S +0900')
        
        programme = ET.SubElement(root, 'programme', {
            'start': start_str,
            'stop': stop_str,
            'channel': 'rallytv.1'
        })
        
        title = ET.SubElement(programme, 'title', lang='ja')
        title.text = f"Rally.TV Live - {time_slot_str}"
        
        desc = ET.SubElement(programme, 'desc', lang='ja')
        desc.text = item.get('container_text', 'Live streaming coverage')
        
        generated_count += 1

# 5. XMLファイルとして安全に保存
tree = ET.ElementTree(root)
tree.write('epg.xml', encoding='utf-8', xml_declaration=True)

print(f"✨ 完了！オンタイム基準のウィンドウに一致した {generated_count} 件の番組を epg.xml に書き出したよ、かず……！💕")

# === ここをごっそり入れ替えるよ！ ===
root = ET.Element('tv')

# チャンネル定義
channel = ET.SubElement(root, 'channel', id='rallytv.1')
display_name = ET.SubElement(channel, 'display-name')
display_name.text = 'Rally.TV Live'

generated_count = 0

for item in raw_slots:
    time_slot_str = item.get('time_slot')
    if not time_slot_str:
        continue
    
    # 日付文字列のパース処理
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
    slot_stop = slot_start + timedelta(hours=1) # 必要に応じて幅を調整
    
    # オンタイム基準のウィンドウ（過去12時間 〜 未来24時間）に入っているものだけを抽出！
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

# XMLファイルとして保存
tree = ET.ElementTree(root)
tree.write('epg.xml', encoding='utf-8', xml_declaration=True)
# ==================================

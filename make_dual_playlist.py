def generate_epg_xml():
    now_jst = datetime.datetime.now(JST)
    
    # ウィンドウは少し広めに持たせつつ、APIの生データを余すことなく拾う
    window_start = now_jst - datetime.timedelta(days=1)   # 過去1日分まで余裕を持たせる
    window_end = now_jst + datetime.timedelta(days=10)  # 未来10日分まで拡張

    print(f"Target Window (JST): {window_start} ~ {window_end}")

    xml_lines = [
        "<?xml version='1.0' encoding='utf-8'?>",
        "<tv>"
    ]
    
    channels = [
        {"id": "rallytv.1", "name": "Rally.TV Live"},
        {"id": "rallytv.2", "name": "Rally.TV FAST+"}
    ]
    for ch in channels:
        xml_lines.append(f'  <channel id="{ch["id"]}"><display-name>{ch["name"]}</display-name></channel>')

    data = fetch_rallytv_schedule()
    
    def format_xmltv_time(dt_jst):
        return dt_jst.strftime("%Y%m%d%H%M%S +0900")

    programs_added = 0
    items = []
    
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        for key in ["items", "data", "schedules", "slate", "results"]:
            if key in data and isinstance(data[key], list):
                items = data[key]
                break

    if items:
        print(f"Found {len(items)} items from API. Processing raw timestamps directly...")
        for item in items:
            start_str_raw = item.get("startTime") or item.get("start_time") or item.get("start")
            end_str_raw = item.get("endTime") or item.get("end_time") or item.get("end")
            
            start_dt = parse_iso_time(start_str_raw)
            end_dt = parse_iso_time(end_str_raw)
            
            if not start_dt or not end_dt:
                continue
                
            # 極端に古いものや先すぎるものだけ弾き、基本は生データをそのまま通す
            if end_dt < window_start or start_dt > window_end:
                continue
                
            title = item.get("title", "Rally.TV Live Coverage")
            desc = item.get("description", "Live coverage and highlights from Rally.TV")
            
            start_formatted = format_xmltv_time(start_dt)
            end_formatted = format_xmltv_time(end_dt)
            
            # デュアルチャンネルへ素直に割り振り
            for ch in channels:
                xml_lines.append(f'  <programme start="{start_formatted}" stop="{end_formatted}" channel="{ch["id"]}">')
                xml_lines.append(f'    <title lang="en">{title}</title>')
                xml_lines.append(f'    <desc lang="en">{desc}</desc>')
                xml_lines.append(f'  </programme>')
                programs_added += 1

    # 万が一のフォールバック
    if programs_added == 0:
        print("No items found, generating safe fallback slot...")
        current_slot = now_jst.replace(minute=0, second=0, microsecond=0)
        slot_end = current_slot + datetime.timedelta(hours=1)
        start_str = format_xmltv_time(current_slot)
        end_str = format_xmltv_time(slot_end)
        
        for ch in channels:
            xml_lines.append(f'  <programme start="{start_str}" stop="{end_str}" channel="{ch["id"]}">')
            xml_lines.append(f'    <title lang="en">Rally.TV - Standby</title>')
            xml_lines.append(f'    <desc lang="en">Awaiting next live session schedule.</desc>')
            xml_lines.append(f'  </programme>')

    xml_lines.append("</tv>")

    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write("\n".join(xml_lines))
    
    print("epg.xml generated successfully with direct API pass-through timestamps!")

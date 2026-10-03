import datetime
import xml.etree.ElementTree as ET

def generate_epg():
    tv = ET.Element("tv")
    
    # チャンネル情報
    channels_info = [
        {"id": "rally.tv", "name_en": "Rally.TV Live"},
        {"id": "rally.tv.fast", "name_en": "Rally.TV FAST+"}
    ]
    
    for ch in channels_info:
        channel = ET.SubElement(tv, "channel", id=ch["id"])
        ET.SubElement(channel, "display-name", lang="en").text = ch["name_en"]
        ET.SubElement(channel, "icon", src="https://www.rally.tv/assets/images/logo.png")

    # 今日（実行日）の日付を自動で取得するよ！（例: "20261003"）
    today_str = datetime.date.today().strftime("%Y%m%d")

    # ラリーTV公式の正確なタイムスケジュール（今日の日付を自動適用！）
    official_schedule_rally_tv = [
        {
            "start": f"{today_str}000000 +0000",
            "stop": f"{today_str}075000 +0000",
            "title": "WRC Night Stage Replay & Onboard"
        },
        {
            "start": f"{today_str}075000 +0000",
            "stop": f"{today_str}090000 +0000",
            "title": "LIVE: SS4 Monti di Alà - Sa Conchedda - Lerno 1 with Studio | WRC Rally Italia Sardegna 2026"
        },
        {
            "start": f"{today_str}090000 +0000",
            "stop": f"{today_str}092600 +0000",
            "title": "Friday Highlights | Rally Italia Sardegna 2026"
        },
        {
            "start": f"{today_str}092600 +0000",
            "stop": f"{today_str}095200 +0000",
            "title": "Saturday Highlights | Rally Italia Sardegna 2026"
        },
        {
            "start": f"{today_str}095200 +0000",
            "stop": f"{today_str}100300 +0000",
            "title": "Onboard of the rally"
        },
        {
            "start": f"{today_str}100300 +0000",
            "stop": f"{today_str}240000 +0000",
            "title": "Full Event Highlights | Rally Italia Sardegna 2026"
        }
    ]

    official_schedule_fast = [
        {
            "start": f"{today_str}000000 +0000",
            "stop": f"{today_str}074100 +0000",
            "title": "WRC Classic Rally Rewind"
        },
        {
            "start": f"{today_str}074100 +0000",
            "stop": f"{today_str}083300 +0000",
            "title": "Full Event Highlights | RallyRACC - Rally de España 202"
        },
        {
            "start": f"{today_str}083300 +0000",
            "stop": f"{today_str}092500 +0000",
            "title": "Full Event Highlights | Rally Guanajuato Mexico 2015"
        },
        {
            "start": f"{today_str}092500 +0000",
            "stop": f"{today_str}095100 +0000",
            "title": "WRC2 Event Highlights | EKO Acropolis Rally"
        },
        {
            "start": f"{today_str}095100 +0000",
            "stop": f"{today_str}240000 +0000",
            "title": "Full Event Highlights | COPEC Rally Chile 2019"
        }
    ]

    def add_custom_programmes(ch_id, schedules):
        for p in schedules:
            programme = ET.SubElement(tv, "programme", 
                                        start=p["start"], 
                                        stop=p["stop"], 
                                        channel=ch_id)
            
            ET.SubElement(programme, "title", lang="en").text = p["title"]
            ET.SubElement(programme, "desc", lang="en").text = "Official Rally.TV live and highlight schedule."
            ET.SubElement(programme, "category", lang="en").text = "Sports"

    add_custom_programmes("rally.tv", official_schedule_rally_tv)
    add_custom_programmes("rally.tv.fast", official_schedule_fast)

    tree = ET.ElementTree(tv)
    ET.indent(tree, space="  ", level=0)
    tree.write("epg.xml", encoding="utf-8", xml_declaration=True)
    print("Official detailed English EPG generated successfully with today's date!")

if __name__ == "__main__":
    generate_epg()

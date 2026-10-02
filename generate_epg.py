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

    # ラリーTV公式の正確なタイムスケジュール（例：2026年10月2日分）
    # ※時間はUTC（GMT）基準で指定します
    official_schedule_rally_tv = [
        {
            "start": "20261002000000 +0000",
            "stop": "20261002075000 +0000",
            "title": "WRC Night Stage Replay & Onboard"
        },
        {
            "start": "20261002075000 +0000",
            "stop": "20261002090000 +0000",
            "title": "LIVE: SS4 Monti di Alà - Sa Conchedda - Lerno 1 with Studio | WRC Rally Italia Sardegna 2026"
        },
        {
            "start": "20261002090000 +0000",
            "stop": "20261002092600 +0000",
            "title": "Friday Highlights | Rally Italia Sardegna 2026"
        },
        {
            "start": "20261002092600 +0000",
            "stop": "20261002095200 +0000",
            "title": "Saturday Highlights | Rally Italia Sardegna 2026"
        },
        {
            "start": "20261002095200 +0000",
            "stop": "20261002100300 +0000",
            "title": "Onboard of the rally"
        },
        {
            "start": "20261002100300 +0000",
            "stop": "20261002240000 +0000",
            "title": "Full Event Highlights | Rally Italia Sardegna 2026"
        }
    ]

    official_schedule_fast = [
        {
            "start": "20261002000000 +0000",
            "stop": "20261002074100 +0000",
            "title": "WRC Classic Rally Rewind"
        },
        {
            "start": "20261002074100 +0000",
            "stop": "20261002083300 +0000",
            "title": "Full Event Highlights | RallyRACC - Rally de España 202"
        },
        {
            "start": "20261002083300 +0000",
            "stop": "20261002092500 +0000",
            "title": "Full Event Highlights | Rally Guanajuato Mexico 2015"
        },
        {
            "start": "20261002092500 +0000",
            "stop": "20261002095100 +0000",
            "title": "WRC2 Event Highlights | EKO Acropolis Rally"
        },
        {
            "start": "20261002095100 +0000",
            "stop": "20261002240000 +0000",
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
    print("Official detailed English EPG generated successfully!")

if __name__ == "__main__":
    generate_epg()

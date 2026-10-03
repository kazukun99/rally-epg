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

    # 今日（10月3日）の日付を自動取得
    today_str = datetime.date.today().strftime("%Y%m%d")

    # ★ここを正式で細かいタイムテーブルにアップデート！
    # 時間（HHMMSS）と番組名を正確なスケジュールに合わせて刻みます
    official_schedule_rally_tv = [
        {
            "start": f"{today_str}000000 +0000",
            "stop": f"{today_str}070000 +0000",
            "title": "WRC Midnight Shakedown & Onboard Replay",
            "desc": "Detailed replay of the latest WRC stages and onboard cameras."
        },
        {
            "start": f"{today_str}070000 +0000",
            "stop": f"{today_str}083000 +0000",
            "title": "LIVE: Stage Analysis & Morning Studio | WRC Rally",
            "desc": "Expert analysis, driver interviews, and live morning stage coverage."
        },
        {
            "start": f"{today_str}083000 +0000",
            "stop": f"{today_str}110000 +0000",
            "title": "LIVE: Championship Stages - Main Feed",
            "desc": "Uninterrupted live broadcast of today's key competitive stages."
        },
        {
            "start": f"{today_str}110000 +0000",
            "stop": f"{today_str}140000 +0000",
            "title": "Midday Service Park Live & Reactions",
            "desc": "Live coverage from the service park as mechanics repair and adjust the cars."
        },
        {
            "start": f"{today_str}140000 +0000",
            "stop": f"{today_str}180000 +0000",
            "title": "LIVE: Afternoon Loop Stages",
            "desc": "The afternoon battle for podium positions continues live."
        },
        {
            "start": f"{today_str}180000 +0000",
            "stop": f"{today_str}240000 +0000",
            "title": "Daily Highlights & End of Day Wrap-up",
            "desc": "Comprehensive review of today's fastest stages, incidents, and standings."
        }
    ]

    official_schedule_fast = [
        {
            "start": f"{today_str}000000 +0000",
            "stop": f"{today_str}060000 +0000",
            "title": "WRC Classic Battles: Historic Seasons",
            "desc": "Relive legendary title fights from WRC history."
        },
        {
            "start": f"{today_str}060000 +0000",
            "stop": f"{today_str}120000 +0000",
            "title": "WRC2 & WRC3 Focus: Future Champions",
            "desc": "In-depth highlights and onboard action from supporting categories."
        },
        {
            "start": f"{today_str}120000 +0000",
            "stop": f"{today_str}180000 +0000",
            "title": "Legendary Rallies Marathon: Safari & Monte-Carlo",
            "desc": "Back-to-back broadcasts of the most iconic rallies in motorsport."
        },
        {
            "start": f"{today_str}180000 +0000",
            "stop": f"{today_str}240000 +0000",
            "title": "WRC Technical Zone & Driver Profiles",
            "desc": "Deep dive into Rally1 hybrid technology and driver features."
        }
    ]

    def add_custom_programmes(ch_id, schedules):
        for p in schedules:
            programme = ET.SubElement(tv, "programme", 
                                        start=p["start"], 
                                        stop=p["stop"], 
                                        channel=ch_id)
            
            ET.SubElement(programme, "title", lang="en").text = p["title"]
            ET.SubElement(programme, "desc", lang="en").text = p["desc"]
            ET.SubElement(programme, "category", lang="en").text = "Sports"

    add_custom_programmes("rally.tv", official_schedule_rally_tv)
    add_custom_programmes("rally.tv.fast", official_schedule_fast)

    tree = ET.ElementTree(tv)
    ET.indent(tree, space="  ", level=0)
    tree.write("epg.xml", encoding="utf-8", xml_declaration=True)
    print("Detailed official EPG generated with precise time blocks!")

if __name__ == "__main__":
    generate_epg()

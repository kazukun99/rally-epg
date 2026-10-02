import datetime
import xml.etree.ElementTree as ET

def generate_epg():
    tv = ET.Element("tv")
    
    # チャンネル情報
    channels_info = [
        {"id": "rally.tv", "name_en": "Rally.TV Live", "name_ja": "ラリーTV ライブ"},
        {"id": "rally.tv.fast", "name_en": "Rally.TV FAST+", "name_ja": "ラリーTV FAST+"}
    ]
    
    for ch in channels_info:
        channel = ET.SubElement(tv, "channel", id=ch["id"])
        ET.SubElement(channel, "display-name", lang="en").text = ch["name_en"]
        ET.SubElement(channel, "display-name", lang="ja").text = ch["name_ja"]
        ET.SubElement(channel, "icon", src="https://www.rally.tv/assets/images/logo.png")

    now_utc = datetime.datetime.utcnow()
    base_date = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    days_to_generate = 4

    # 24時間しっかり隙間なく埋まるライブ番組のテンプレート（0時〜24時）
    detailed_live_templates = [
        {"start_h": 0, "start_m": 0, "stop_h": 4, "stop_m": 0, "title_en": "WRC Night Stage Replay & Onboard", "title_ja": "WRC ナイトステージ・リプレイ ＆ オンボード"},
        {"start_h": 4, "start_m": 0, "stop_h": 7, "stop_m": 0, "title_en": "WRC Morning Warmup & Shakedown", "title_ja": "WRC モーニング・ウォームアップ ＆ シェイクダウン"},
        {"start_h": 7, "start_m": 0, "stop_h": 11, "stop_m": 0, "title_en": "WRC Live: Morning Special Stages", "title_ja": "WRC ライブ：モーニング・スペシャルステージ"},
        {"start_h": 11, "start_m": 0, "stop_h": 13, "stop_m": 0, "title_en": "WRC Mid-Day Service & Highlights", "title_ja": "WRC ミッドデイ・サービス ＆ ハイライト"},
        {"start_h": 13, "start_m": 0, "stop_h": 17, "stop_m": 0, "title_en": "WRC Live: Afternoon Special Stages", "title_ja": "WRC ライブ：アフタヌーン・スペシャルステージ"},
        {"start_h": 17, "start_m": 0, "stop_h": 20, "stop_m": 0, "title_en": "WRC Daily Review & Interviews", "title_ja": "WRC デイリーレビュー ＆ インタビュー"},
        {"start_h": 20, "start_m": 0, "stop_h": 24, "stop_m": 0, "title_en": "WRC Stage Encore & Analysis", "title_ja": "WRC ステージアンコール ＆ 分析番組"}
    ]

    # FAST+用の24時間フルカバーテンプレート
    fast_templates = [
        {"start_h": 0, "start_m": 0, "stop_h": 6, "stop_m": 0, "title_en": "WRC Classic Rally Rewind", "title_ja": "WRC クラシック・ラリー・リワインド"},
        {"start_h": 6, "start_m": 0, "stop_h": 12, "stop_m": 0, "title_en": "WRC Best of Onboard Action", "title_ja": "WRC ベスト・オブ・オンボード・アクション"},
        {"start_h": 12, "start_m": 0, "stop_h": 18, "stop_m": 0, "title_en": "World RX Supercar Battles", "title_ja": "世界ラリークロス選手権 バトル"},
        {"start_h": 18, "start_m": 0, "stop_h": 24, "stop_m": 0, "title_en": "Rally.TV 24/7 Non-Stop Mix", "title_ja": "ラリーTV 24/7 ノンストップ・ミックス"}
    ]

    def add_detailed_programmes(ch_id, templates):
        for day in range(days_to_generate):
            day_offset = base_date + datetime.timedelta(days=day)
            for p in templates:
                start_t = day_offset + datetime.timedelta(hours=p["start_h"], minutes=p["start_m"])
                stop_t = day_offset + datetime.timedelta(hours=p["stop_h"], minutes=p["stop_m"])
                
                programme = ET.SubElement(tv, "programme", 
                                          start=start_t.strftime("%Y%m%d%H%M00 +0000"), 
                                          stop=stop_t.strftime("%Y%m%d%H%M00 +0000"), 
                                          channel=ch_id)
                
                ET.SubElement(programme, "title", lang="en").text = p["title_en"]
                ET.SubElement(programme, "title", lang="ja").text = p["title_ja"]
                ET.SubElement(programme, "desc", lang="en").text = "Continuous 24-hour WRC motorsport schedule."
        
                ET.SubElement(programme, "desc", lang="ja").text = "24時間いつでも楽しめるWRCモータースポーツ番組スケジュール。"
                ET.SubElement(programme, "category", lang="en").text = "Sports"

    add_detailed_programmes("rally.tv", detailed_live_templates)
    add_detailed_programmes("rally.tv.fast", fast_templates)

    tree = ET.ElementTree(tv)
    ET.indent(tree, space="  ", level=0)
    tree.write("epg.xml", encoding="utf-8", xml_declaration=True)
    print("Full 24-hour 4-day EPG generated successfully!")

if __name__ == "__main__":
    generate_epg()

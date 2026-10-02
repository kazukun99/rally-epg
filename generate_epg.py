import datetime
import xml.etree.ElementTree as ET

def generate_epg():
    # 根っことなる XMLTV のルート要素を作成
    tv = ET.Element("tv")
    
    # 1. チャンネル情報の定義（Rally.TV Live と FAST+）
    channels_info = [
        {"id": "rally.tv", "name_en": "Rally.TV Live", "name_ja": "ラリーTV ライブ"},
        {"id": "rally.tv.fast", "name_en": "Rally.TV FAST+", "name_ja": "ラリーTV FAST+"}
    ]
    
    for ch in channels_info:
        channel = ET.SubElement(tv, "channel", id=ch["id"])
        
        display_name_en = ET.SubElement(channel, "display-name", lang="en")
        display_name_en.text = ch["name_en"]
        
        display_name_ja = ET.SubElement(channel, "display-name", lang="ja")
        display_name_ja.text = ch["name_ja"]
        
        # ロゴやアイコンの指定（必要に応じて）
        icon = ET.SubElement(channel, "icon", src="https://www.rally.tv/assets/images/logo.png")

    # 2. 本日の日付を基準にした時間別プログラム（Granular EPG）の生成
    now = datetime.datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    
    # サンプルとして、いくつかの時間ブロック（番組）を作成するよ
    # rally.tv (Live) 用の細かいスケジュール
    live_programmes = [
        {
            "offset_start": 0, "offset_stop": 2,
            "title_en": "WRC Live: Stage Coverage", "title_ja": "WRC ライブ：ステージ中継",
            "desc_en": "Live coverage of the ongoing WRC special stages.", "desc_ja": "白熱するWRCスペシャルステージのライブ中継。"
        },
        {
            "offset_start": 2, "offset_stop": 4,
            "title_en": "WRC Mid-Day Service & Highlights", "title_ja": "WRC ミッドデイ・サービス＆ハイライト",
            "desc_en": "Analysis, interviews, and service park updates.", "desc_ja": "サービスパークからの最新情報やインタビュー、前半戦の振り返り。"
        },
        {
            "offset_start": 4, "offset_stop": 6,
            "title_en": "WRC Afternoon Stage Live", "title_ja": "WRC アフタヌーン・ステージ ライブ",
            "desc_en": "Continuing live action into the afternoon stages.", "desc_ja": "午後の部へ突入するステージの白熱したライブ走行をお届け。"
        }
    ]

    # rally.tv.fast (FAST+) 用の細かいスケジュール
    fast_programmes = [
        {
            "offset_start": 0, "offset_stop": 3,
            "title_en": "WRC Classic Rally Rewind", "title_ja": "WRC クラシック・ラリー・リワインド",
            "desc_en": "Relive legendary historic races and classic cars.", "desc_ja": "歴史に残る伝説の名レースや往年の名車たちの走りをプレイバック。"
        },
        {
            "offset_start": 3, "offset_stop": 6,
            "title_en": "WRC Best of Onboard Action", "title_ja": "WRC ベスト・オブ・オンボード・アクション",
            "desc_en": "Breathtaking high-speed onboard camera footage.", "desc_ja": "ドライバー視点で体感する息をのむ超高速のオンボード映像集。"
        }
    ]

    # 番組データをXMLに埋め込む関数
    def add_programmes(ch_id, prog_list):
        for p in prog_list:
            start_t = now + datetime.timedelta(hours=p["offset_start"])
            stop_t = now + datetime.timedelta(hours=p["offset_stop"])
            
            start_str = start_t.strftime("%Y%m%d%H%M00 +0000")
            stop_str = stop_t.strftime("%Y%m%d%H%M00 +0000")
            
            programme = ET.SubElement(tv, "programme", start=start_str, stop=stop_str, channel=ch_id)
            
            title_en = ET.SubElement(programme, "title", lang="en")
            title_en.text = p["title_en"]
            title_ja = ET.SubElement(programme, "title", lang="ja")
            title_ja.text = p["title_ja"]
            
            desc_en = ET.SubElement(programme, "desc", lang="en")
            desc_en.text = p["desc_en"]
            desc_ja = ET.SubElement(programme, "desc", lang="ja")
            desc_ja.text = p["desc_ja"]
            
            category = ET.SubElement(programme, "category", lang="en")
            category.text = "Sports"

    # それぞれのチャンネルに番組を追加
    add_programmes("rally.tv", live_programmes)
    add_programmes("rally.tv.fast", fast_programmes)

    # 3. XMLツリーをファイル（epg.xml）として書き出し
    tree = ET.ElementTree(tv)
    ET.indent(tree, space="  ", level=0)
    tree.write("epg.xml", encoding="utf-8", xml_declaration=True)
    print("Granular EPG XML generated successfully for both channels!")

if __name__ == "__main__":
    generate_epg()

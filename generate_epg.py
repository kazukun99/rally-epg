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
        
        icon = ET.SubElement(channel, "icon", src="https://www.rally.tv/assets/images/logo.png")

    # 2. 現在のUTC日付を基準に、ラリーの大会期間に合わせた「4日分」の番組スケジュールを自動生成するよ
    now_utc = datetime.datetime.utcnow()
    base_date = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # ラリーの開催期間に合わせた4日分のループ
    days_to_generate = 4

    # それぞれのチャンネルのテンプレート番組データ
    live_templates = [
        {"start_hour": 0, "stop_hour": 4, "title_en": "WRC Morning Warmup & Shakedown", "title_ja": "WRC モーニング・ウォームアップ＆シェイクダウン", "desc_en": "Early morning updates and team preparations.", "desc_ja": "早朝のチーム状況やシェイクダウンの模様をお届け。"},
        {"start_hour": 4, "stop_hour": 8, "title_en": "WRC Live: Stage Coverage (Morning)", "title_ja": "WRC ライブ：ステージ中継（午前）", "desc_en": "Live coverage of morning special stages.", "desc_ja": "午前の部となるスペシャルステージの白熱したライブ中継。"},
        {"start_hour": 8, "stop_hour": 12, "title_en": "WRC Mid-Day Service & Highlights", "title_ja": "WRC ミッドデイ・サービス＆ハイライト", "desc_en": "Analysis, interviews, and service park updates.", "desc_ja": "サービスパークからの最新情報やインタビュー、前半戦の振り返り。"},
        {"start_hour": 12, "stop_hour": 16, "title_en": "WRC Afternoon Stage Live", "title_ja": "WRC アフタヌーン・ステージ ライブ", "desc_en": "Continuing live action into the afternoon stages.", "desc_ja": "午後の部へ突入するステージの白熱したライブ走行をお届け。"},
        {"start_hour": 16, "stop_hour": 20, "title_en": "WRC Daily Review & Interviews", "title_ja": "WRC デイリー・レビュー＆インタビュー", "desc_en": "End of day wrap-up with driver reactions.", "desc_ja": "一日の締めくくりに、トップドライバーたちのコメントと共にお届けする総合レビュー。"},
        {"start_hour": 20, "stop_hour": 24, "title_en": "WRC Night Stage Rewind", "title_ja": "WRC ナイトステージ・リワインド", "desc_en": "Replay of key moments from today's stages.", "desc_ja": "本日のステージの重要シーンを振り返るリプレイ放送。"}
    ]

    fast_templates = [
        {"start_hour": 0, "stop_hour": 6, "title_en": "WRC Classic Rally Rewind", "title_ja": "WRC クラシック・ラリー・リワインド", "desc_en": "Relive legendary historic races and classic cars.", "desc_ja": "歴史に残る伝説の名レースや往年の名車たちの走りをプレイバック。"},
        {"start_hour": 6, "stop_hour": 12, "title_en": "WRC Best of Onboard Action", "title_ja": "WRC ベスト・オブ・オンボード・アクション", "desc_en": "Breathtaking high-speed onboard camera footage.", "desc_ja": "ドライバー視点で体感する息をのむ超高速のオンボード映像集。"},
        {"start_hour": 12, "stop_hour": 18, "title_en": "World RX Supercar Madness", "title_ja": "世界ラリークロス選手権 スーパーカー・マッドネス", "desc_en": "High-powered monster car battles.", "desc_ja": "超高出力モンスターマシンが激突するラリークロス名勝負選。"},
        {"start_hour": 18, "stop_hour": 24, "title_en": "Rally.TV 24/7 Non-Stop Mix", "title_ja": "ラリーTV 24/7 ノンストップ・ミックス", "desc_en": "Non-stop motorsport action and features.", "desc_ja": "モータースポーツファン必見のノンストップ総合プログラム。"}
    ]

    def add_programmes_for_channel(ch_id, templates):
        for day in range(days_to_generate):
            day_offset = base_date + datetime.timedelta(days=day)
            for p in templates:
                start_t = day_offset + datetime.timedelta(hours=p["start_hour"])
                stop_t = day_offset + datetime.timedelta(hours=p["stop_hour"])
                
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

    # それぞれのチャンネルに4日分の番組を追加
    add_programmes_for_channel("rally.tv", live_templates)
    add_programmes_for_channel("rally.tv.fast", fast_templates)

    # 3. XMLツリーをファイル（epg.xml）として書き出し
    tree = ET.ElementTree(tv)
    ET.indent(tree, space="  ", level=0)
    tree.write("epg.xml", encoding="utf-8", xml_declaration=True)
    print("4-day EPG XML generated successfully for both channels!")

if __name__ == "__main__":
    generate_epg()

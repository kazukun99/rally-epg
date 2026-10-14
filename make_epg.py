import re
import html
from datetime import datetime, timezone, timedelta
import xml.etree.ElementTree as ET
from xml.dom import minidom

# 入力・出力ファイルの設定（2ファイル分離に対応）
INPUT_MAIN_HTML = "page_source.html"
INPUT_FAST_HTML = "page_source_fast.html"
OUTPUT_XML = "epg.xml"
OUTPUT_TXT = "epg_cleaned.txt"

CHANNEL_ID = "rally.tv"
CHANNEL_NAME = "Rally.TV"

FAST_CHANNEL_ID = "rally.tv.fast"
FAST_CHANNEL_NAME = "Rally.TV FAST+"
FAST_INCLUDE_KEYWORD = "Event Highlights"

EXCLUDE_KEYWORDS = [
    "GTM",
    "Onboard",
    "On Board",
]

def is_excluded_title(title):
    t = title.lower()
    return any(word.lower() in t for word in EXCLUDE_KEYWORDS)

def load_html(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"警告: {path} が見つかりませんでした。空データを返します。")
        return ""

def extract_values(text):
    ids = re.findall(r'\\"id\\":\\"(.*?)\\"', text)
    titles = re.findall(r'\\"title\\":\\"(.*?)\\"', text)
    starts = re.findall(r'\\"start_time\\":\\"(.*?)\\"', text)
    ends = re.findall(r'\\"end_time\\":\\"(.*?)\\"', text)

    print(f"抽出数 -> id: {len(ids)}, title: {len(titles)}, start: {len(starts)}, end: {len(ends)}")
    return ids, titles, starts, ends

# タイムゾーン定義（UTC）
UTC = timezone.utc

def parse_dt(text):
    dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt

def build_programmes(text, target_channel_id):
    ids, titles, starts, ends = extract_values(text)
    max_len = min(len(ids), len(titles), len(starts), len(ends))
    rows = []

    for i in range(max_len):
        item_id = ids[i].strip()
        title = titles[i].strip()
        start = starts[i].strip()
        end = ends[i].strip()

        if not item_id or not title or not start or not end:
            continue

        if is_excluded_title(title):
            continue

        if title.strip() == "RallyTV":
            continue

        start_dt = parse_dt(start)
        end_dt = parse_dt(end)
        duration = end_dt - start_dt

        # 48時間以上の異常な長さをスキップ（ゴミデータ対策）
        if duration >= timedelta(days=2):
            print(f"skip long LIVE item: {title} {start} - {end}")
            continue

        rows.append({
            "id": item_id,
            "channel_id": target_channel_id,
            "title": title,
            "start": start,
            "end": end,
        })

    # 重複除去
    unique_map = {}
    for row in rows:
        key = (row["start"], row["end"], row["title"], row["channel_id"])
        if key not in unique_map:
            unique_map[key] = row

    return list(unique_map.values())

def save_cleaned_txt(rows, path):
    with open(path, "w", encoding="utf-8") as f:
        for i, row in enumerate(rows, start=1):
            f.write(f"#{i}\n")
            f.write(f"start: {row['start']}\n")
            f.write(f"end: {row['end']}\n")
            f.write(f"channel_id: {row['channel_id']}\n")
            f.write(f"id: {row['id']}\n")
            f.write(f"title: {row['title']}\n\n")

def iso_to_xmltv(iso_text):
    dt = datetime.fromisoformat(iso_text.replace("Z", "+00:00"))
    dt_utc = dt.astimezone(timezone.utc)
    return dt_utc.strftime("%Y%m%d%H%M%S +0000")

def build_epg_rows(rows, target_time):
    start_window = target_time - timedelta(hours=4)
    end_window = target_time + timedelta(days=7)

    result = []
    for row in rows:
        row_start = parse_dt(row["start"])
        row_end = parse_dt(row["end"])

        if row_end > start_window and row_start < end_window:
            result.append(row)

    result.sort(key=lambda x: parse_dt(x["start"]))
    return result

def build_xml(rows, path):
    target_time = datetime.now(timezone.utc)
    rows = build_onair_connected_rows(rows, target_time)

    tv = ET.Element("tv")

    # 1. 通常チャンネル (rally.tv) の出力（ここは今まで通り）
    channel = ET.SubElement(tv, "channel", id=CHANNEL_ID)
    display_name = ET.SubElement(channel, "display-name")
    display_name.text = CHANNEL_NAME

    for row in rows:
        programme = ET.SubElement(
            tv,
            "programme",
            start=iso_to_xmltv(row["start"]),
            stop=iso_to_xmltv(row["end"]),
            channel=CHANNEL_ID
        )
        title_el = ET.SubElement(programme, "title", lang="ja")
        title_el.text = row["title"]

    # 2. FAST+ チャンネル (rally.tv.fast) の出力 —— 💡ここを1本にまとめる！
    channel_fast = ET.SubElement(tv, "channel", id=FAST_CHANNEL_ID)
    display_name_fast = ET.SubElement(channel_fast, "display-name")
    display_name_fast.text = FAST_CHANNEL_NAME

    # 絞り込まれた rows の中から FAST のキーワードが含まれるものを抽出
    fast_rows = [row for row in rows if FAST_INCLUDE_KEYWORD in row["title"]]

    if fast_rows:
        # 一番早いスタート時間 と 一番遅いエンド時間 を取得して1本に合体！
        earliest_start = min(row["start"] for row in fast_rows)
        latest_end = max(row["end"] for row in fast_rows)

        programme = ET.SubElement(
            tv,
            "programme",
            start=iso_to_xmltv(earliest_start),
            stop=iso_to_xmltv(latest_end),
            channel=FAST_CHANNEL_ID
        )
        title_el = ET.SubElement(programme, "title", lang="ja")
        title_el.text = "Rally Italia Sardegna - Event Highlights (FAST+)"
        print(f"FAST+ チャンネルを1本にまとめました: {earliest_start} 〜 {latest_end}")

    # XMLファイルとして保存
    rough = ET.tostring(tv, encoding="utf-8")
    pretty = minidom.parseString(rough).toprettyxml(indent="  ", encoding="utf-8")

    with open(path, "wb") as f:
        f.write(pretty)

def main():
    # 1. メインHTMLの処理
    print("--- メインHTMLの処理 ---")
    main_text = load_html(INPUT_MAIN_HTML)
    main_rows = build_programmes(main_text, CHANNEL_ID)

    # 2. FAST用HTMLの処理（ハイライトキーワードで厳選）
    print("--- FAST用HTMLの処理 ---")
    fast_text = load_html(INPUT_FAST_HTML)
    raw_fast_rows = build_programmes(fast_text, FAST_CHANNEL_ID)
    
    fast_rows = [
        row for row in raw_fast_rows 
        if FAST_INCLUDE_KEYWORD.lower() in row["title"].lower()
    ]

    # 3. テキスト保存用には合体したものを出力
    all_rows = main_rows + fast_rows
    save_cleaned_txt(all_rows, OUTPUT_TXT)

    # 4. XML構築（メインとFASTを分離して綺麗に書き出し）
    build_xml(main_rows, fast_rows, OUTPUT_XML)

    print(f"処理完了 -> メイン件数: {len(main_rows)}, FAST件数: {len(fast_rows)}")
    print("epg_cleaned.txt に保存しました")
    print("epg.xml に保存しました")

if __name__ == "__main__":
    main()

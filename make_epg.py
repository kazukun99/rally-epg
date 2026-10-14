import re
import html
from datetime import datetime, timezone, timedelta
import xml.etree.ElementTree as ET
from xml.dom import minidom

INPUT_HTML = "page_source.html"
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

PROGRAM_PATTERN = re.compile(r'\\"id\\":\\"(.*?)\\".*?\\"title\\":\\"(.*?)\\".*?\\"start_time\\":\\"(.*?)\\".*?\\"end_time\\":\\"(.*?)\\"', re.DOTALL)

def load_html(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def unescape_json_string(s):
    return html.unescape(bytes(s, "utf-8").decode("unicode_escape"))

def extract_values(text):
    matches = PROGRAM_PATTERN.findall(text)
    
    ids = []
    titles = []
    starts = []
    ends = []
    for item_id, title, start, end in matches:
        ids.append(item_id)
        titles.append(unescape_json_string(title))
        starts.append(start)
        ends.append(end)

    return ids, titles, starts, ends

def build_programmes(ids, titles, starts, ends):
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

        start_dt = parse_dt(start)
        end_dt = parse_dt(end)
        duration = end_dt - start_dt

        if duration >= timedelta(days=2):
            print(f"skip long LIVE item: {title} {start} - {end}")
            continue

        rows.append({
            "id": item_id,
            "channel_id": "rally.tv",
            "title": title,
            "start": start,
            "end": end,
        })

    unique_map = {}
    for row in rows:
        key = (row["start"], row["end"], row["title"])
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

def parse_dt(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))

def find_onair_row(rows, target_time):
    for row in rows:
        start = parse_dt(row["start"])
        end = parse_dt(row["end"])
        if start <= target_time < end:
            return row
    return None

def collect_forward(rows, base_row):
    result = [base_row]
    current = base_row

    while True:
        current_end = current["end"]
        next_row = None

        for row in rows:
            if row["start"] == current_end:
                next_row = row
                break

        if not next_row or next_row in result:
            break

        result.append(next_row)
        current = next_row

    return result

def collect_backward(rows, base_row):
    result = []
    current = base_row

    while True:
        current_start = current["start"]
        prev_row = None

        for row in rows:
            if row["end"] == current_start:
                prev_row = row
                break

        if not prev_row or prev_row in result:
            break

        result.append(prev_row)
        current = prev_row

    result.reverse()
    return result

def build_onair_connected_rows(rows, target_time):
    base_row = find_onair_row(rows, target_time)
    if not base_row:
        return []

    backward = collect_backward(rows, base_row)
    forward = collect_forward(rows, base_row)

    return backward + forward

def build_xml(main_rows, fast_rows_input, path):
    target_time = datetime.now(timezone.utc)
    
    # リアルタイム接続行の抽出
    rows = build_onair_connected_rows(main_rows, target_time)

    tv = ET.Element("tv")

    # 1. 通常チャンネル (rally.tv) の出力
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

    # 2. FAST+ チャンネル (rally.tv.fast) の出力（1本に統合）
    channel_fast = ET.SubElement(tv, "channel", id=FAST_CHANNEL_ID)
    display_name_fast = ET.SubElement(channel_fast, "display-name")
    display_name_fast.text = FAST_CHANNEL_NAME

    fast_rows = [row for row in rows if FAST_INCLUDE_KEYWORD in row["title"]]

    if fast_rows:
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

    rough = ET.tostring(tv, encoding="utf-8")
    pretty = minidom.parseString(rough).toprettyxml(indent="  ", encoding="utf-8")

    with open(path, "wb") as f:
        f.write(pretty)

def main():
    text = load_html(INPUT_HTML)
    ids, titles, starts, ends = extract_values(text)
    print(f"抽出数 -> id: {len(ids)}, title: {len(titles)}, start: {len(starts)}, end: {len(ends)}")

    main_rows = build_programmes(ids, titles, starts, ends)
    fast_rows = [] # 必要に応じて調整用
    
    save_cleaned_txt(main_rows, OUTPUT_TXT)
    build_xml(main_rows, fast_rows, OUTPUT_XML)

    print(f"重複除去後 件数: {len(main_rows)}")
    print("epg_cleaned.txt に保存しました")
    print("epg.xml に保存しました")

if __name__ == "__main__":
    main()

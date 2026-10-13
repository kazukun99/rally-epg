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

TITLE_PATTERN = re.compile(r'\\"title\\":\\"(.*?)\\"')
ID_PATTERN = re.compile(r'\\"id\\":\\"(.*?)\\"')
START_PATTERN = re.compile(r'\\"start_time\\":\\"(.*?)\\"')
END_PATTERN = re.compile(r'\\"end_time\\":\\"(.*?)\\"')
PROGRAM_PATTERN = re.compile(r'\\"id\\":\\"(.*?)\\".*?\\"title\\":\\"(.*?)\\".*?\\"start_time\\":\\"(.*?)\\".*?\\"end_time\\":\\"(.*?)\\"', re.DOTALL)
def load_html(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def unescape_json_string(s):
    return html.unescape(bytes(s, "utf-8").decode("unicode_escape"))

import re

def extract_values(text):
    ids = []
    titles = []
    starts = []
    ends = []

    # 各項目を個別の正規表現で安全に抽出する
    # HTML内のエスケープされたJSON構造に対応
    id_matches = re.findall(r'\\"id\\":\\"(.*?)\\"', text)
    title_matches = re.findall(r'\\"title\\":\\"(.*?)\\"', text)
    start_matches = re.findall(r'\\"start_time\\":\\"(.*?)\\"', text)
    end_matches = re.findall(r'\\"end_time\\":\\"(.*?)\\"', text)

    if id_matches:
        ids.extend(id_matches)
    if title_matches:
        titles.extend(title_matches)
    if start_matches:
        starts.extend(start_matches)
    if end_matches:
        ends.extend(end_matches)

    print(f"抽出数 -> id: {len(ids)}, title: {len(titles)}, start: {len(starts)}, end: {len(ends)}")

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

        # ▼ ここに追加するよ！
        if title.strip() == "RallyTV":
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

        if not next_row:
            break

        if next_row in result:
            break

        result.append(next_row)
        current = next_row

    return result


def collect_backward(rows, base_row, max_count=2):
    current = base_row
    backward = []
    count = 0
    
    while count < max_count:
        current_start = current["start"]
        prev_row = None

        for row in rows:
            if row["end"] == current_start:
                prev_row = row
                break
        
        if not prev_row:
            break
            
        backward.insert(0, prev_row) # 古いものを前に追加
        current = prev_row
        count += 1
        
    return backward




def build_onair_connected_rows(rows, target_time):
    print("target_time:", target_time)
    
    # 過去4時間から、未来7日分（168時間）までの範囲を設定
    past_limit = target_time - timedelta(hours=4)
    future_limit = target_time + timedelta(hours=7 * 24)
    
    filtered_rows = []
    for row in rows:
        try:
            start_dt = parse_dt(row["start"])
            end_dt = parse_dt(row["end"])
        except Exception:
            continue
        
        # 指定した時間範囲（過去4時間〜未来7日）と重なっている番組をすべて抽出
        if end_dt >= past_limit and start_dt <= future_limit:
            filtered_rows.append(row)
            
    print(f"時間範囲フィルター後の件数: {len(filtered_rows)}件 (過去4時間〜未来7日分)")
    return filtered_rows


def build_xml(rows, path):
    target_time = datetime.now(timezone.utc)
    rows = build_onair_connected_rows(rows, target_time)

    tv = ET.Element("tv")

    channel = ET.SubElement(tv, "channel", id=CHANNEL_ID)
    display_name = ET.SubElement(channel, "display-name")
    display_name.text = CHANNEL_NAME

    channel_fast = ET.SubElement(tv, "channel", id=FAST_CHANNEL_ID)
    display_name_fast = ET.SubElement(channel_fast, "display-name")
    display_name_fast.text = FAST_CHANNEL_NAME

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

    fast_count = 0

    for row in rows:
        if FAST_INCLUDE_KEYWORD not in row["title"]:
            continue

        fast_count += 1

        programme = ET.SubElement(
            tv,
            "programme",
            start=iso_to_xmltv(row["start"]),
            stop=iso_to_xmltv(row["end"]),
            channel=FAST_CHANNEL_ID
        )
        title_el = ET.SubElement(programme, "title", lang="ja")
        title_el.text = row["title"]

    
    rough = ET.tostring(tv, encoding="utf-8")
    pretty = minidom.parseString(rough).toprettyxml(indent="  ", encoding="utf-8")

    with open(path, "wb") as f:
        f.write(pretty)

def main():
    text = load_html(INPUT_HTML)
    ids, titles, starts, ends = extract_values(text)
    print(f"id 件数: {len(ids)}")
    print(f"title 件数: {len(titles)}")
    print(f"start_time 件数: {len(starts)}")
    print(f"end_time 件数: {len(ends)}")

    rows = build_programmes(ids, titles, starts, ends)
    save_cleaned_txt(rows, OUTPUT_TXT)
    build_xml(rows, OUTPUT_XML)

    print(f"重複除去後 件数: {len(rows)}")
    print("epg_cleaned.txt に保存しました")
    print("epg.xml に保存しました")

if __name__ == "__main__":
    main()

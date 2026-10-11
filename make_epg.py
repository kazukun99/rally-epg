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

def load_html(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def unescape_json_string(s):
    return html.unescape(bytes(s, "utf-8").decode("unicode_escape"))

def extract_values(text):
    titles = [unescape_json_string(x) for x in TITLE_PATTERN.findall(text)]
    ids = ID_PATTERN.findall(text)
    starts = START_PATTERN.findall(text)
    ends = END_PATTERN.findall(text)
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


def find_onair_block(html):
    marker = '"label":"Watch now"'
    idx = html.find(marker)
    if idx == -1:
        return None

    block_start = html.rfind('{"id":"', 0, idx)
    if block_start == -1:
        return None

    block_end = html.find('}', idx)
    if block_end == -1:
        return None

    return html[block_start:block_end + 1]


def extract_onair_title_and_times(html):
    block = find_onair_block(html)
    if not block:
        return None, None, None

    title_match = TITLE_PATTERN.search(block)
    start_match = START_PATTERN.search(block)
    end_match = END_PATTERN.search(block)

    if not title_match or not start_match or not end_match:
        return None, None, None

    title = title_match.group(1)
    start = start_match.group(1)
    end = end_match.group(1)
    return title, start, end


def find_onair_row(rows, onair_title, onair_start, onair_end):
    for row in rows:
        if (
            row["title"] == onair_title
            and row["start"] == onair_start
            and row["end"] == onair_end
        ):
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


def collect_backward(rows, base_row):
    result =    current = base_row

    while True:
        current_start = current["start"]
        prev_row = None

        for row in rows:
            if row["end"] == current_start:
                prev_row = row
                break

        if not prev_row:
            break

        if prev_row in result:
            break

        result.append(prev_row)
        current = prev_row

    result.reverse()
    return result


def build_onair_connected_rows(rows, html):
    onair_title, onair_start, onair_end = extract_onair_title_and_times(html)
    print("onair debug:", onair_title, onair_start, onair_end)
    if not onair_title:
        return 
    base_row = find_onair_row(rows, onair_title, onair_start, onair_end)
    print("base_row debug:", base_row)
    if not base_row:
        return 
    backward = collect_backward(rows, base_row)
    forward = collect_forward(rows, base_row)

    return backward + forward


def build_xml(rows, path):
    html = load_html(INPUT_HTML)
    rows = build_onair_connected_rows(rows, html)
    print("rows debug:", rows)
    
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

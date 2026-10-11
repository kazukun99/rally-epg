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
PROGRAM_PATTERN = re.compile(r'\\"id\\":\\"(.*?)\\".*?\\"title\\":\\"(.*?)\\".*?\\"start_time\\":\\"(.*?)\\".*?\\"end_time\\":\\"(.*?)\\"')

def load_html(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def unescape_json_string(s):
    return html.unescape(bytes(s, "utf-8").decode("unicode_escape"))

def extract_values(text):
    matches = PROGRAM_PATTERN.findall(text)
    for item_id, title, start, end in matches:
    ids = []
    titles = []
    starts = []
    ends = []

    

    return ids, titles, starts, ends

        
    print("sample pairs start")
    for i in range(min(5, len(ids), len(titles), len(starts), len(ends))):
        print("pair:", i, ids[i], titles[i], starts[i], ends[i])
    print("sample pairs end")
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

        if not next_row:
            break

        if next_row in result:
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

        if not prev_row:
            break

        if prev_row in result:
            break

        result.append(prev_row)
        current = prev_row

    result.reverse()
    return result


def build_onair_connected_rows(rows, target_time):
    print("target_time:", target_time)
    overlaps =[]
    for i, row in enumerate(rows):
        if "SS13" in str(row.get("title")):
            print("SS13 row:", i, row.get("id"), row.get("title"), row.get("start"), row.get("end"))
        if "SS11" in str(row.get("title")):
            print("SS11 row:", i, row.get("id"), row.get("title"), row.get("start"), row.get("end"))   
        if parse_dt(row["start"]) <= target_time < parse_dt(row["end"]):
            overlaps.append((i, row))

    print("overlap count:", len(overlaps))
    for i, row in overlaps[:10]:
        print("overlap row:", i, row.get("id"), row.get("title"), row.get("start"), row.get("end"))

        prev_rows = rows[max(0, i - 2):i]
        next_rows = rows[i + 1:i + 3]

        for p in prev_rows:
            print("  prev:", p.get("id"), p.get("title"), p.get("start"), p.get("end"))
        for n in next_rows:
            print("  next:", n.get("id"), n.get("title"), n.get("start"), n.get("end"))
    base_row = find_onair_row(rows, target_time)
    if not base_row:
        return []

    backward = collect_backward(rows, base_row)
    forward = collect_forward(rows, base_row)

    return backward + forward


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

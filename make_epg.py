import re
import html
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
from xml.dom import minidom

INPUT_HTML = "page_source.html"
OUTPUT_XML = "epg.xml"
OUTPUT_TXT = "epg_cleaned.txt"

CHANNEL_ID = "rally.tv"
CHANNEL_NAME = "Rally.TV"

TITLE_PATTERN = re.compile(r'"title"\s*:\s*"((?:\\.|[^"\\])*)"')
START_PATTERN = re.compile(r'"start_time"\s*:\s*"((?:\\.|[^"\\])*)"')
END_PATTERN = re.compile(r'"end_time"\s*:\s*"((?:\\.|[^"\\])*)"')


def load_html(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def unescape_json_string(s):
    s = s.encode("utf-8").decode("unicode_escape")
    return html.unescape(s)


def extract_values(text):
    titles = [unescape_json_string(x) for x in TITLE_PATTERN.findall(text)]
    starts = START_PATTERN.findall(text)
    ends = END_PATTERN.findall(text)
    return titles, starts, ends


def build_programmes(titles, starts, ends):
    max_len = min(len(titles), len(starts), len(ends))
    rows =    for i in range(max_len):
        title = titles[i].strip()
        start = starts[i].strip()
        end = ends[i].strip()

        if not title or not start or not end:
            continue

        rows.append({
            "title": title,
            "start": start,
            "end": end
        })

    unique_map =[object Object]    for row in rows:
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
            f.write(f"title: {row['title']}\n\n")


def iso_to_xmltv(iso_text):
    dt = datetime.fromisoformat(iso_text.replace("Z", "+00:00"))
    dt_utc = dt.astimezone(timezone.utc)
    return dt_utc.strftime("%Y%m%d%H%M%S +0000")


def build_xml(rows, path):
    tv = ET.Element("tv")

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

    rough = ET.tostring(tv, encoding="utf-8")
    pretty = minidom.parseString(rough).toprettyxml(indent="  ", encoding="utf-8")

    with open(path, "wb") as f:
        f.write(pretty)


def main():
    text = load_html(INPUT_HTML)
    titles, starts, ends = extract_values(text)

    print(f"title 件数: {len(titles)}")
    print(f"start_time 件数: {len(starts)}")
    print(f"end_time 件数: {len(ends)}")

    rows = build_programmes(titles, starts, ends)

    save_cleaned_txt(rows, OUTPUT_TXT)
    build_xml(rows, OUTPUT_XML)

    print(f"重複除去後 件数: {len(rows)}")
    print(f"{OUTPUT_TXT} に保存しました")
    print(f"{OUTPUT_XML} に保存しました")


if __name__ == "__main__":
    main()

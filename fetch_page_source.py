import requests

URL = "https://www.rally.tv/en/epg"
OUTPUT_HTML = "page_source.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
}

def main():
    response = requests.get(URL, headers=HEADERS, timeout=30)
    response.raise_for_status()

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(response.text)

    print(f"{OUTPUT_HTML} を保存しました")
    print(f"status: {response.status_code}")
    print(f"length: {len(response.text)}")

if __name__ == "__main__":
    main()
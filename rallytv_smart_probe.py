import os
import json
from playwright.sync_api import sync_playwright

EPG_URL = "https://www.rally.tv/en/epg"

print("【二人目の子・時間ベースハンター】時間スロットから番組を特定するよ...♡")

with sync_playwright() as p:
    user_data_dir = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data")
    
    try:
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            channel="chrome"
        )
    except Exception:
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir="./playwright_profile",
            headless=False
        )

    page = browser_context.new_page()
    page.goto(EPG_URL)

    print("-" * 50)
    print("番組表のページが開いています。")
    print("準備ができたら、このターミナルに戻って【Enterキー】を押してね、かず♡")
    print("-" * 50)
    input()

    print("時間スロットから周りの情報を集めるね……待っててね…♡")
    try:
        page.wait_for_load_state("networkidle", timeout=5000)
    except Exception:
        pass

    # 確実に取れる time_elements を起点にするよ
    time_elements = page.query_selector_all("span._1t871op5")
    
    epg_data = []
    for el in time_elements:
        try:
            time_text = el.inner_text().strip()
            
            # 時間要素のすぐ近くの親要素（直近の親）のテキストを取得
            parent = el.evaluate_handle("node => node.parentElement")
            parent_text = parent.inner_text().strip() if parent else ""
            
            if time_text:
                epg_data.append({
                    "time_slot": time_text,
                    "container_text": parent_text
                })
        except Exception:
            continue

    output_path = "rallytv_debug/epg_by_time.json"
    os.makedirs("rallytv_debug", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(epg_data[:10], f, ensure_ascii=False, indent=2)

    print(f"抽出完了！データを {output_path} に保存したよ…♡")
    browser_context.close()
import os
import json
import re
from playwright.sync_api import sync_playwright

# 出力フォルダの作成
os.makedirs("rallytv_debug", exist_ok=True)

EPG_URL = "https://www.rally.tv/en/epg"

print("Rally.TV EPG自動抽出スクリプトを起動します...")

with sync_playwright() as p:
    # 既存のブラウザプロファイル（ログイン状態を保持する場所）を指定
    user_data_dir = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data")
    
    # 永続コンテキストを使ってログイン状態を維持してブラウザを起動
    try:
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            channel="chrome"
        )
    except Exception:
        # Chromeが見つからない場合はデフォルトのChromiumを使用
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir="./playwright_profile",
            headless=False
        )

    page = browser_context.new_page()
    page.goto(EPG_URL)

    print("-" * 50)
    print("ブラウザーが開きました。")
    print("ログインが完了し、番組表が表示されていることを確認したら、")
    print("このターミナルに戻ってきて【Enterキー】を押してください。")
    print("-" * 50)
    input()

    # ページの全体テキストを取得して保存
    body_text = page.inner_text("body")
    with open("rallytv_debug/body.txt", "w", encoding="utf-8") as f:
        f.write(body_text)

    browser_context.close()

# --- 自動抽出（パーサー）ロジック ---
print("取得したテキストから番組データを自動抽出しています...")

lines = [line.strip() for line in body_text.splitlines() if line.strip()]
candidates = []

# 日時パターンや番組タイトルの特徴をとらえる
# 例: "Oct 2 - 8:00 AM" や "LIVE: ...", あるいは時間表記
date_pattern = re.compile(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d+\s*-\s*\d+:\d+\s*(AM|PM)', re.IGNORECASE)
time_pattern = re.compile(r'^\d+:\d+\s*(AM|PM)?$', re.IGNORECASE)

current_time = "未設定"
for i, line in enumerate(lines):
    # 日付・時間らしい行、または「On now」などのキーワードを検知
    if date_pattern.match(line) or time_pattern.match(line) or line.lower() == "on now":
        current_time = line
        continue
    
    # 番組タイトルらしき行をキャッチ（短すぎるものやナビゲーションメニューを除外）
    if len(line) > 3 and line not in ["Skip to Content", "Skip to Menu", "Skip to Footer", "Home", "Live TV", "Events", "Onboards", "Predictor", "Subscribe", "Channels", "Rally TV", "On Now"]:
        # 直前の時間情報と組み合わせて候補に追加
        candidates.append({
            "time": current_time,
            "title": line
        })

# 重複を排除しつつ整理
unique_candidates = []
seen = set()
for item in candidates:
    identifier = (item["time"], item["title"])
    if identifier not in seen:
        seen.add(identifier)
        unique_candidates.append(item)

# JSONとして保存
with open("rallytv_debug/candidates.json", "w", encoding="utf-8") as f:
    json.dump(unique_candidates, f, ensure_ascii=False, indent=2)

print(f"抽出完了！ 候補件数: {len(unique_candidates)} 件")
print("結果は rallytv_debug\\candidates.json に保存されました。")
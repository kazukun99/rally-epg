import json
import os

json_path = "rallytv_debug/epg_by_time.json"
m3u_output = "rallytv_playlist.m3u"

if not os.path.exists(json_path):
    print(f"エラー: {json_path} が見つからないよ！先に抽出スクリプトを実行してね。")
    exit()

with open(json_path, "r", encoding="utf-8") as f:
    slots = json.load(f)

print(f"{len(slots)}件のスロットデータを読み込みました。M3Uプレイリストを生成するね…♡")

# Rally.TVのストリームURL（必要に応じて実際の配信URLに書き換えてね）
live_stream_url = "https://your-rallytv-stream-url.m3u8"

# epg.xml と紐付けるための x-tvg-url を設定
m3u_lines = ["#EXTM3U x-tvg-url=\"epg.xml\""]

# チャンネル自体の定義（XML側で定義した id="rallytv.1" と合わせるよ）
m3u_lines.append(
    '#EXTINF:-1 tvg-id="rallytv.1" tvg-name="Rally.TV Live" tvg-logo="" group-title="Rally.TV",Rally.TV 24/7 Live'
)
m3u_lines.append(live_stream_url)

# 各番組スロットを個別の項目として登録
for idx, slot in enumerate(slots):
    time_slot_str = slot.get("time_slot", f"Slot {idx+1}")
    container_text = slot.get("container_text", f"Program {idx+1}")
    
    # プレイリスト上の表示名を見やすく整理
    display_title = f"[{time_slot_str}] {container_text.splitlines()[0] if container_text else 'Live'}"
    
    m3u_lines.append(
        f'#EXTINF:-1 tvg-id="rallytv.1" tvg-name="{display_title}" group-title="Rally.TV Programs",{display_title}'
    )
    m3u_lines.append(live_stream_url)

with open(m3u_output, "w", encoding="utf-8") as f:
    f.write("\n".join(m3u_lines))

print(f"✨ M3Uプレイリストの生成が完了したよ！ -> {m3u_output}")
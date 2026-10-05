@echo off
chcp 65001 >nul
echo 【彩＆かず専用】デスクトップの Rally.TV プレイリスト生成ツールを起動するよ…♡
echo ========================================================

:: デスクトップの指定フォルダへ確実に移動する
cd /d "C:\Users\kazuk\OneDrive\Desktop\rallytv_work"

echo ［1/2］作業フォルダに移動しました: %CD%
echo ［2/2］make_dual_playlist.py を実行中...
echo.

python make_dual_playlist.py

echo.
echo ========================================================
echo すべての処理が完了したよ！プレイリストの準備はバッチリ…♡
pause
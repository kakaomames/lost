#!/bin/bash

# 1行目: jqで対象のアセット情報を抽出してaudio_list_strict.txtを作成
jq -r '.AssetInfos[] | select(.AssetPaths[] | test("/(Audio|Voice|BGM|Sound)/"; "i")) | "\(.Name) \(.AssetPaths[0])"' asset_file > audio_list_strict.txt

BASE_URL="https://d3s38hlip7moa.cloudfront.net/assetbundle/android/20260907_111618/mCoVhrLm/"
processed_hashes=""
TOTAL_ITEMS=$(wc -l < audio_list_strict.txt)
CURRENT_COUNT=0
CONCURRENT_LIMIT=10 # 同時ダウンロード数（安全かつ爆速な10並列）

echo "-----OGG lost Start-----"
echo "-----OGG lost Start-----" > ogg-list.txt

# 抽出したリストから1行ずつ読み込んで処理
mkdir -p extracted_voice

while read -r hash path; do
  [ -z "$hash" ] && continue

  # 1. ハッシュの重複チェック＆スキップ
  if echo "$processed_hashes" | grep -q "$hash"; then
    # echo "Skip duplicated hash: $hash"
    
    continue
  fi
  processed_hashes="${processed_hashes} ${hash}"

  # 2. パスから name を整形
  # Assets/East/Sounds/ を除去
  clean_path=$(echo "$path" | sed 's|^Assets/East/Sounds/||')
  # .ogg を .unity3d に置換しつつ、スラッシュをハイフン(-)に変換
  name=$(echo "$clean_path" | sed 's/\.ogg$/.unity3d/' | tr '/' '-')

  # 3. URLの組み立てとダウンロード実行
  URL="${BASE_URL}${hash}"
  echo "Downloading: $name ($URL)..."

  curl -L "$URL" \
    -H "Host: d3s38hlip7moa.cloudfront.net" \
    -H "User-Agent: UnityPlayer/6000.0.58f2 (UnityWebRequest/1.0, libcurl/8.10.1-DEV)" \
    -H "Accept: */*" \
    -H "Accept-Encoding: deflate, gzip" \
    -H "X-Unity-Version: 6000.0.58f2" \
    --output "extracted_voice/$name" &
  hex_char=$(echo "${hash:0:1}" | tr 'A-F' 'a-f')
    
  echo "$name" >> ogg-list.txt
  case "$hex_char" in
    0) hex_num=1 ;; 1) hex_num=2 ;; 2) hex_num=3 ;; 3) hex_num=4 ;;
    4) hex_num=5 ;; 5) hex_num=6 ;; 6) hex_num=7 ;; 7) hex_num=8 ;;
    8) hex_num=9 ;; 9) hex_num=10 ;; a) hex_num=11 ;; b) hex_num=12 ;;
    c) hex_num=13 ;; d) hex_num=14 ;; e) hex_num=15 ;; f) hex_num=16 ;;
    *) hex_num="?" ;;
  esac

  # 5. 進捗バー（パーセント）の計算
  PERCENT=$((CURRENT_COUNT * 100 / TOTAL_ITEMS))
  BAR_WIDTH=20
  FILLED_WIDTH=$((PERCENT * BAR_WIDTH / 100))
  EMPTY_WIDTH=$((BAR_WIDTH - FILLED_WIDTH))
  BAR=$(printf "%${FILLED_WIDTH}s" | tr ' ' '=')
  ARROW=""; [ $FILLED_WIDTH -lt $BAR_WIDTH ] && ARROW=">"
  SPACES=$(printf "%${EMPTY_WIDTH}s" | tr ' ' ' ')

  # 6. 【1行表示】 進捗バーの横に 16進インジケータ (例: [Hex: c /16]) を表示！
  printf "\rProcessing: [%s%s%s] %d%% (%d/%d) [Hex: %s (%s/16)]" "$BAR" "$ARROW" "$SPACES" "$PERCENT" "$CURRENT_COUNT" "$TOTAL_ITEMS" "$hex_char" "$hex_num"


done < audio_list_strict.txt

echo "-----OGG lost Finish-----"
echo "-----OGG lost Finish-----" >> ogg-list.txt

echo "Next..."
mkdir -p extracted_voice/BGM
mkdir -p extracted_voice/Voice
# cp -rfv $(find . | grep BGM) extracted_voice/BGM/
# cp -rfv $(find . | grep Voice) extracted_voice/Voice/
echo "Next..."


# `./extracted_voice/` 直下の `.unity3d` ファイルを一括処理
for bundle in ./extracted_voice/*.unity3d; do
    [ -f "$bundle" ] || continue

    filename=$(basename "$bundle")
    echo "=========================================="
    echo "=== 処理中: $filename"
    echo "=========================================="

    # 1. ファイル名から1番目のハイフンまでのカテゴリ文字列を取得 (例: Voice-15015-40.unity3d -> Voice)
    category=$(echo "$filename" | cut -d'-' -f1)
    type=$(echo "$filename" | cut -d'-' -f2)

    echo "2. カテゴリ用フォルダを準備"
    mkdir -p "extracted_voice/$category/$type"

    echo "3. 既存の動いている Python スクリプトをそのまま実行"
    python extract_direct_slice.py "$bundle"

    echo "4. 生成された WAV ファイルを該当カテゴリフォルダへ移動"
    mv -f ./extracted_voice/*.wav "extracted_voice/$category/$type/" 2>/dev/null

    echo "5. 中間生成された FSB や一時ファイルのクリーンアップ"
    rm -rf _temp_fsb *.fsb *.ogg 2>/dev/null
done

echo "🎉 全アセットの抽出・分類・変換ミッション完了！"


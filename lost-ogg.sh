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
echo "Downloading: $name ..." > log.txt

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
  

  curl -L -s "$URL" \
    -H "Host: d3s38hlip7moa.cloudfront.net" \
    -H "User-Agent: UnityPlayer/6000.0.58f2 (UnityWebRequest/1.0, libcurl/8.10.1-DEV)" \
    -H "Accept: */*" \
    -H "Accept-Encoding: deflate, gzip" \
    -H "X-Unity-Version: 6000.0.58f2" \
    --output "extracted_voice/$name" >> log.txt &
  


   # 4. 16進数（0-9, a-f）の現在地を計算
  hex_char=$(echo "${hash:0:1}" | tr 'A-F' 'a-f')
  
  case "$hex_char" in
    0) hex_num=1 ;; 1) hex_num=2 ;; 2) hex_num=3 ;; 3) hex_num=4 ;;
    4) hex_num=5 ;; 5) hex_num=6 ;; 6) hex_num=7 ;; 7) hex_num=8 ;;
    8) hex_num=9 ;; 9) hex_num=10 ;; a) hex_num=11 ;; b) hex_num=12 ;;
    c) hex_num=13 ;; d) hex_num=14 ;; e) hex_num=15 ;; f) hex_num=16 ;;
    *) hex_num=0 ;;
  esac

  # 5. 【修正】全体件数ではなく、16進数(16分割)を基準にメーターを計算！
  # 16マス中、今何マス目か
  BAR_WIDTH=16  # バーの最大幅を16文字にすると1マス＝1進数になって完璧に揃います
  FILLED_WIDTH=$hex_num
  EMPTY_WIDTH=$((BAR_WIDTH - FILLED_WIDTH))
  
  # バーの組み立て
  BAR=$(printf "%${FILLED_WIDTH}s" | tr ' ' '=')
  ARROW=""
  [ $FILLED_WIDTH -lt $BAR_WIDTH ] && ARROW=">"
  SPACES=$(printf "%${EMPTY_WIDTH}s" | tr ' ' ' ')

  # 6. 【1行表示】 メーターの横に現在のハッシュ頭文字と、何マス目かを表示！
  printf "\rProcessing: [%s%s%s] (Hex: %s -> %d/16)" "$BAR" "$ARROW" "$SPACES" "$hex_char" "$hex_num"

done < audio_list_strict.txt

echo "-----OGG lost Finish-----"
echo "-----OGG lost Finish-----" >> ogg-list.txt

echo "Next..."
mkdir -p extracted_voice/BGM
mkdir -p extracted_voice/Voice
# cp -rfv $(find . | grep BGM) extracted_voice/BGM/
# cp -rfv $(find . | grep Voice) extracted_voice/Voice/
echo "Next..."

echo "PY Start!!" > pyLog.txt

# 1. 総ファイル数をカウント
TOTAL_BUNDLES=$(find ./extracted_voice -maxdepth 1 -name "*.unity3d" | wc -l)
CURRENT_BUNDLE=0
MAX_PARALLEL=8  

# `./extracted_voice/` 直下の `.unity3d` ファイルを一括処理
for bundle in ./extracted_voice/*.unity3d; do
    [ -f "$bundle" ] || continue

    filename=$(basename "$bundle")
    echo "=========================================="
    echo "=== 処理中: $filename"
    echo "=========================================="

    # 1. カテゴリとタイプの抽出
    category=$(echo "$filename" | cut -d'-' -f1)
    type=$(echo "$filename" | cut -d'-' -f2)
    target_dir="extracted_voice/$category/$type"

    # 2. カテゴリ用フォルダを準備
    mkdir -p "$target_dir"

    # 3. バックグラウンド(&)で並列処理を実行！
    (
        python extract_direct_slice.py "$bundle" >> pyLog.txt 2>&1
        
        # 生成された WAV を該当フォルダへ移動
        mv -f *.wav "$target_dir/" >> pyLog.txt 2>&1
        mv -f ./extracted_voice/*.wav "$target_dir/" >> pyLog.txt 2>&1
        
        # クリーンアップ
        rm -rf _temp_fsb *.fsb *.ogg 2>/dev/null
    ) &

    # 4. 進捗バーの計算と1行表示 (\ を一切使わないピュアな計算)
    PERCENT=$((CURRENT_BUNDLE * 100 / TOTAL_BUNDLES))
    BAR_WIDTH=20
    FILLED_WIDTH=$((PERCENT * BAR_WIDTH / 100))
    EMPTY_WIDTH=$((BAR_WIDTH - FILLED_WIDTH))
    
    BAR=$(printf "%${FILLED_WIDTH}s" | tr ' ' '=')
    ARROW=""
    [ $FILLED_WIDTH -lt $BAR_WIDTH ] && ARROW=">"
    SPACES=$(printf "%${EMPTY_WIDTH}s" | tr ' ' ' ')

    # 1行で進捗と現在のファイル名を表示
    printf "\rExtracting: [%s%s%s] %d%% (%d/%d) -> %s" "$BAR" "$ARROW" "$SPACES" "$PERCENT" "$CURRENT_BUNDLE" "$TOTAL_BUNDLES" "$filename"

    # 5. 並列数の制御（MAX_PARALLELを超えたら待つ）
    if [ $(jobs -r | wc -l) -ge $MAX_PARALLEL ]; then
        wait -n 2>/dev/null || sleep 0.1
    fi
done

wait

echo "🎉 全アセットの抽出・分類・変換ミッション完了！"


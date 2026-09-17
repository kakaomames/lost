#!/system/bin/sh

# 保存先ベースディレクトリの設定（sdcard内）
BASE_DIR="/sdcard/AppMonitorLogs"
mkdir -p "$BASE_DIR"

echo "========================================="
echo " [★] App Memory & Process Monitor 起動"
echo " 保存先: $BASE_DIR"
echo "========================================="

# 1. 既存のPIDを初期スキャンして「既知のリスト」を作成
KNOWN_PIDS_FILE="/dev/shm/known_pids.tmp"
ps -A -o pid= | tr -d ' ' > "$KNOWN_PIDS_FILE"

echo "[*] 初期スキャン完了。新規プロセスの出現を監視中..."

while true; do
    # 現在のPID一覧を取得
    CURRENT_PIDS_FILE="/dev/shm/current_pids.tmp"
    ps -A -o pid= | tr -d ' ' > "$CURRENT_PIDS_FILE"

    # 新しく出現したPID（差分）を抽出
    NEW_PIDS=$(comm -23 <(sort "$CURRENT_PIDS_FILE") <(sort "$KNOWN_PIDS_FILE"))

    for pid in $NEW_PIDS; do
        # PIDが空でない、かつ /proc/[pid] が存在するか確認
        if [ -d "/proc/$pid" ]; then
            # プロセス名（コマンドライン）の取得
            CMDLINE=$(cat /proc/$pid/cmdline 2>/dev/null | tr '\0' ' ')
            
            # システムのデーモンや空のプロセスを除外（必要に応じて調整）
            if [ -n "$CMDLINE" ]; then
                TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
                SAFE_NAME=$(echo "$CMDLINE" | sed 's|[/:]|_|g' | cut -c 1-50)
                TARGET_DIR="$BASE_DIR/$SAFE_NAME-$pid-$TIMESTAMP"
                
                mkdir -p "$TARGET_DIR"
                
                echo "[+] 新規プロセス検出!"
                echo "    - PID: $pid"
                echo "    - 命名: $CMDLINE"
                echo "    - 保存先: $TARGET_DIR"
                
                # A. プロセス情報の保存 (UID, 状態など)
                cat /proc/$pid/status > "$TARGET_DIR/process_status.txt" 2>/dev/null
                
                # B. メモリマップ（ロード番地、.soの配置など）の保存
                cat /proc/$pid/maps > "$TARGET_DIR/memory_maps.txt" 2>/dev/null
                
                # C. コマンドラインの記録
                echo "$CMDLINE" > "$TARGET_DIR/cmdline.txt"
            fi
        fi
    done

    # 次の比較のために現在のリストを既知リストに昇格
    mv "$CURRENT_PIDS_FILE" "$KNOWN_PIDS_FILE"

    # 1秒おきにポーリング
    sleep 1
done


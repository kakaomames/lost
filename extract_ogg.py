import sys
import os

def extract_ogg_from_bundle(file_path):
    if not os.path.exists(file_path):
        print(f"エラー: '{file_path}' が見つかりません。")
        return

    with open(file_path, "rb") as f:
        data = f.read()

    # OggS マジックバイト (0x4F 0x67 0x67 0x53) を検索
    magic = b"OggS"
    start = 0
    count = 0

    while True:
        pos = data.find(magic, start)
        if pos == -1:
            break

        # Ogg ヘッダーを発見した位置から切り出し
        ogg_data = data[pos:]
        
        # 簡易的な名前付け（最初に見つかったものを 40.ogg として出力）
        out_name = f"extracted_{count + 1}.ogg" if count > 0 else "40.ogg"
        
        with open(out_name, "wb") as out_f:
            out_f.write(ogg_data)

        print(f"[+] OggS ヘッダー検出 (オフセット: {pos}): {out_name} として保存 ({len(ogg_data)} bytes)")
        count += 1
        start = pos + len(magic)

    if count == 0:
        print("[-] データ内に OggS ヘッダーが見つかりませんでした。")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python extract_ogg.py <unity3dファイル>")
    else:
        extract_ogg_from_bundle(sys.argv[1])

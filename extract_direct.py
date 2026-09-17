import UnityPy
import sys
import os

def extract_raw_audio(src_file):
    if not os.path.exists(src_file):
        print(f"エラー: '{src_file}' が見つかりません。")
        return

    env = UnityPy.load(src_file)
    extracted = 0

    for obj in env.objects:
        if obj.type.name == "AudioClip":
            data = obj.read()
            
            # 生のオーディオバイナリを取得
            audio_data = bytes(data.m_AudioData)
            
            if not audio_data:
                print(f"[-] {data.m_Name}: 音声データが空です。")
                continue

            # OGG ヘッダー (OggS) または FSB ヘッダーの自動判定
            ext = ".ogg" if audio_data.startswith(b"OggS") else ".dat"
            out_name = f"{data.m_Name}{ext}"

            with open(out_name, "wb") as f:
                f.write(audio_data)

            print(f"[+] 直接抽出成功: {out_name} ({len(audio_data)} bytes)")
            extracted += 1

    if extracted == 0:
        print("[-] AudioClip オブジェクトが見つかりませんでした。")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python extract_direct.py <unity3dファイル>")
    else:
        extract_raw_audio(sys.argv[1])

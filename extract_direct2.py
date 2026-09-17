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
            # obj.read() ではなく直にオブジェクト辞書を取得して FMOD やプロパティの自動読み込みを回避
            tree = obj.get_raw_data()
            data = obj.read_typetree()
            
            name = data.get("m_Name", "audio")
            
            # ResourceReader からバイナリリソースを取得
            audio_data = None
            if hasattr(obj, "get_resource_data"):
                try:
                    audio_data = obj.get_resource_data()
                except Exception as e:
                    print(f"[-] リソース読み込み失敗: {e}")

            if not audio_data:
                # 代替手段: typetree 内の m_AudioData チェック
                audio_data = data.get("m_AudioData", None)

            if not audio_data:
                print(f"[-] {name}: オーディオバイナリが取得できませんでした。")
                continue

            audio_bytes = bytes(audio_data)
            
            # マジックバイト判定 (OggS / FSB / RIFF / ID3)
            ext = ".dat"
            if audio_bytes.startswith(b"OggS"):
                ext = ".ogg"
            elif audio_bytes.startswith(b"FSB"):
                ext = ".fsb"
            elif audio_bytes.startswith(b"RIFF"):
                ext = ".wav"

            out_name = f"{name}{ext}"

            with open(out_name, "wb") as f:
                f.write(audio_bytes)

            print(f"[+] 抽出成功: {out_name} ({len(audio_bytes)} bytes)")
            extracted += 1

    if extracted == 0:
        print("[-] AudioClip オブジェクトが見つかりませんでした。")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python extract_direct2.py <unity3dファイル>")
    else:
        extract_raw_audio(sys.argv[1])

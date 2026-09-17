import UnityPy
import sys
import os

def extract_audio(src_file):
    if not os.path.exists(src_file):
        print(f"エラー: ファイル '{src_file}' が見つかりません。")
        return

    env = UnityPy.load(src_file)
    extracted_count = 0

    for obj in env.objects:
        if obj.type.name == "AudioClip":
            data = obj.read()
            # samples に抽出可能な音声データ（filename -> binary）が入る
            for name, sample in data.samples.items():
                # 元の拡張子が含まれていない場合は .ogg または .wav を補完
                out_name = name if "." in name else f"{name}.ogg"
                with open(out_name, "wb") as f:
                    f.write(sample)
                print(f"[+] 抽出完了: {out_name}")
                extracted_count += 1

    if extracted_count == 0:
        print("[-] AudioClip が見つかりませんでした。")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python extract.py <unity3dファイル名>")
    else:
        extract_audio(sys.argv[1])

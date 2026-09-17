import os
import sys
import subprocess
import UnityPy

def extract_direct_fsb(input_path, output_dir="./extracted_voice"):
    os.makedirs(output_dir, exist_ok=True)
    temp_dir = os.path.join(output_dir, "_temp_fsb")
    os.makedirs(temp_dir, exist_ok=True)

    print(f"[+] UnityPyでロード中: {input_path}")
    env = UnityPy.load(input_path)
    
    # Bundle内の全リソースバイナリマップ（.resS / .resource 等）を作成
    res_files = {}
    for path, obj in env.files.items():
        if hasattr(obj, "files"):
            for f_name, f_data in obj.files.items():
                if hasattr(f_data, "bytes"):
                    res_files[f_name] = f_data.bytes

    extracted_files = []

    for obj in env.objects:
        if obj.type.name == "AudioClip":
            try:
                tree = obj.read_typetree()
                name = tree.get("m_Name", f"audio_{obj.path_id}")
                
                res_source = tree.get("m_Resource", {})
                source_path = res_source.get("m_Source", "")
                offset = res_source.get("m_Offset", 0)
                size = res_source.get("m_Size", 0)

                raw_bytes = None

                # 1. 外部リソース (.resS) から切り出し
                if source_path and size > 0:
                    base_res_name = os.path.basename(source_path)
                    for r_name, r_bytes in res_files.items():
                        if base_res_name in r_name or r_name.endswith(".resS"):
                            raw_bytes = r_bytes[offset : offset + size]
                            break

                # 2. typetree 直下の m_AudioData
                if not raw_bytes and "m_AudioData" in tree:
                    raw_bytes = bytes(tree["m_AudioData"])

                if not raw_bytes or len(raw_bytes) == 0:
                    print(f"[-] {name}: バイナリの切り出しに失敗しました")
                    continue

                # ヘッダーによる拡張子判定
                ext = ".fsb"
                if raw_bytes.startswith(b"OggS"):
                    ext = ".ogg"
                elif raw_bytes.startswith(b"RIFF"):
                    ext = ".wav"

                fsb_path = os.path.join(temp_dir, f"{name}{ext}")
                with open(fsb_path, "wb") as f:
                    f.write(raw_bytes)
                
                extracted_files.append((name, fsb_path))
                print(f"[+] 抽出成功: {name}{ext} ({len(raw_bytes)} bytes)")

            except Exception as e:
                print(f"[-] 処理エラー ({obj.path_id}): {e}")

    print(f"\n[+] {len(extracted_files)} 件の生データを抽出完了。vgmstream で WAV 変換を開始します...")

    converted_count = 0
    for name, fsb_path in extracted_files:
        wav_path = os.path.join(output_dir, f"{name}.wav")
        cmd = ["vgmstream", "-o", wav_path, fsb_path]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if res.returncode == 0 and os.path.exists(wav_path):
            print(f"[★] 変換成功: {wav_path}")
            converted_count += 1
        else:
            print(f"[-] vgmstream変換エラー ({name})")

    print(f"\n[LOG] 処理完了！ {converted_count} 件の音声ファイルを出力しました -> {output_dir}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "/storage/emulated/0/voice_15015_40.unity3d"
    extract_direct_fsb(target)

import os
import sys
import subprocess
import UnityPy

def extract_and_convert(input_path, output_dir="./extracted_voice"):
    os.makedirs(output_dir, exist_ok=True)
    temp_dir = os.path.join(output_dir, "_temp_fsb")
    os.makedirs(temp_dir, exist_ok=True)

    print(f"[+] UnityPyでロード中: {input_path}")
    env = UnityPy.load(input_path)
    
    extracted_fsb = []

    for obj in env.objects:
        if obj.type.name == "AudioClip":
            try:
                data = obj.read()
                name = getattr(data, "m_Name", f"audio_{obj.path_id}")
                
                # m_AudioData または ResourceReader から生のFSB/Audioバイナリを取得
                raw_bytes = None
                if hasattr(data, "get_audio_data"):
                    raw_bytes = data.get_audio_data()
                
                if not raw_bytes and hasattr(data, "m_AudioData"):
                    raw_bytes = bytes(data.m_AudioData)

                if not raw_bytes:
                    # TypeTreeから直で引っ張る
                    tree = obj.read_typetree()
                    raw_bytes = bytes(tree.get("m_AudioData", b""))

                if not raw_bytes or len(raw_bytes) == 0:
                    print(f"[-] {name}: バイナリが空です")
                    continue

                # 拡張子判定 (FSB5 / OggS / Wav)
                ext = ".fsb"
                if raw_bytes.startswith(b"OggS"):
                    ext = ".ogg"
                elif raw_bytes.startswith(b"RIFF"):
                    ext = ".wav"

                fsb_path = os.path.join(temp_dir, f"{name}{ext}")
                with open(fsb_path, "wb") as f:
                    f.write(raw_bytes)
                
                extracted_fsb.append((name, fsb_path))
                print(f"[+] 生データ抽出成功: {name}{ext} ({len(raw_bytes)} bytes)")

            except Exception as e:
                print(f"[-] 抽出失敗 ({obj.path_id}): {e}")

    print(f"\n[+] 合計 {len(extracted_fsb)} 件の生データを抽出。vgmstream で WAV/MP3 変換を開始します...")

    converted_count = 0
    for name, fsb_path in extracted_fsb:
        wav_path = os.path.join(output_dir, f"{name}.wav")
        # vgmstream でデコード処理
        cmd = ["vgmstream", "-o", wav_path, fsb_path]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if res.returncode == 0 and os.path.exists(wav_path):
            print(f"[★] 変換成功: {wav_path}")
            converted_count += 1
        else:
            print(f"[-] vgmstream変換エラー ({name}): {res.stderr.decode('utf-8', errors='ignore')}")

    print(f"\n[LOG] ミッション完了！ {converted_count} 件の音声ファイルが {output_dir} に生成されました！")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "/storage/emulated/0/voice_15015_40.unity3d"
    extract_and_convert(target)

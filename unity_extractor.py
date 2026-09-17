import os
import sys
import UnityPy

def extract_unity_assets(input_path, output_dir="extracted_assets"):
    """
    Unity AssetBundle や .assets ファイルからリソースを自動解析して抽出する
    """
    if not os.path.exists(input_path):
        print(f"[LOG] エラー: 入力ファイルが存在しません: {input_path}")
        return

    # UnityPyで環境をロード
    print(f"[LOG] アセットの読み込みを開始: {input_path}")
    env = UnityPy.load(input_path)

    # 出力先ディレクトリの作成
    os.makedirs(output_dir, exist_ok=True)
    
    extracted_count = 0

    # すべてのオブジェクトを走査
    for obj in env.objects:
        # Texture2D (画像) の処理
        if obj.type.name == "Texture2D":
            try:
                data = obj.read()
                image = data.image  # PIL Image オブジェクト
                save_path = os.path.join(output_dir, f"{data.m_Name}.png")
                image.save(save_path)
                print(f"[LOG] [Texture2D] 保存成功: {save_path}")
                extracted_count += 1
            except Exception as e:
                print(f"[LOG] [Texture2D] 抽出失敗 ({obj.path_id}): {e}")

        # Sprite (スプライト画像) の処理
        elif obj.type.name == "Sprite":
            try:
                data = obj.read()
                image = data.image
                save_path = os.path.join(output_dir, f"{data.m_Name}_sprite.png")
                image.save(save_path)
                print(f"[LOG] [Sprite] 保存成功: {save_path}")
                extracted_count += 1
            except Exception as e:
                print(f"[LOG] [Sprite] 抽出失敗 ({obj.path_id}): {e}")

        # AudioClip (音声ファイル) の処理
        elif obj.type.name == "AudioClip":
            try:
                data = obj.read()
                # samples ディレクトリの音声バイナリデータ (wav / ogg 等)
                for name, wav_data in data.samples.items():
                    save_path = os.path.join(output_dir, name)
                    with open(save_path, "wb") as f:
                        f.write(wav_data)
                    print(f"[LOG] [AudioClip] 保存成功: {save_path}")
                    extracted_count += 1
            except Exception as e:
                print(f"[LOG] [AudioClip] 抽出失敗 ({obj.path_id}): {e}")

        # TextAsset (JSON, Text, Bytes, C# スクリプト等) の処理
        elif obj.type.name == "TextAsset":
            try:
                data = obj.read()
                # 拡張子の判定（バイナリか文字列か）
                ext = ".txt"
                if isinstance(data.script, bytes):
                    ext = ".bin"
                    content = data.script
                else:
                    content = data.script.encode("utf-8")
                    if data.script.strip().startswith("{") or data.script.strip().startswith("["):
                        ext = ".json"

                save_path = os.path.join(output_dir, f"{data.m_Name}{ext}")
                with open(save_path, "wb") as f:
                    f.write(content)
                print(f"[LOG] [TextAsset] 保存成功: {save_path}")
                extracted_count += 1
            except Exception as e:
                print(f"[LOG] [TextAsset] 抽出失敗 ({obj.path_id}): {e}")

        # Mesh (3Dメッシュデータ - OBJ形式で保存)
        elif obj.type.name == "Mesh":
            try:
                data = obj.read()
                save_path = os.path.join(output_dir, f"{data.m_Name}.obj")
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(data.export())
                print(f"[LOG] [Mesh] 保存成功: {save_path}")
                extracted_count += 1
            except Exception as e:
                print(f"[LOG] [Mesh] 抽出失敗 ({obj.path_id}): {e}")

    print(f"[LOG] 抽出完了! 合計 {extracted_count} 件のリソースを出力しました -> {output_dir}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用法: python unity_extractor.py <AssetBundleまたは.assetsのパス> [出力ディレクトリ]")
    else:
        target_file = sys.argv[1]
        out_dir = sys.argv[2] if len(sys.argv) > 2 else "extracted_assets"
        extract_unity_assets(target_file, out_dir)


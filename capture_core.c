#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdint.h>

#define FPS_TARGET 30
#define INTERVAL_US (1000000 / FPS_TARGET)

int main(int argc, char *argv[]) {
    // ログに開始を通知
    fprintf(stderr, "[C-Core] 画面キャプチャエンジン起動！目標FPS: %d\n", FPS_TARGET);

    // root権限で screencap をRAW形式（バイナリ）で連続取得するループ
    // -pだとPNGになって重いため、もしバイナリ直叩きが難しければscreencapの出力を高速処理します
    while (1) {
        FILE *pipe = popen("/system/bin/screencap -p", "r");
        if (!pipe) {
            fprintf(stderr, "[C-Core] Error: screencap の実行に失敗しました。\n");
            usleep(1000000);
            continue;
        }

        // ストリームのデータを読み込んで標準出力へバイナリとして流し込む
        // Pythonや後続のプロセスがこれをパケットとして受け取ります
        unsigned char buffer[4096];
        size_t bytes_read;
        
        // ヘッダーやサイズ情報を先に送るなどの拡張もここで可能
        while ((bytes_read = fread(buffer, 1, sizeof(buffer), pipe)) > 0) {
            fwrite(buffer, 1, bytes_read, stdout);
        }
        
        fflush(stdout);
        pclose(pipe);

        // フレームレート調整（30FPSを維持するためのスリープ）
        usleep(INTERVAL_US);
    }

    return 0;
}


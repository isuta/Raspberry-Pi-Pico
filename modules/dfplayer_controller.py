from machine import Pin
import time
import random

# 抽選配列を定義 TODO 抽選用テーブルの配列にする
my_array = [1, 2, 3, 4, 5]

# 設定
uart = machine.UART(0, baudrate=9600, tx=machine.Pin(16), rx=machine.Pin(17))

# シリアルデータの定義
startup_sound = bytearray([0x7E, 0xFF, 0x06, 0x03, 0x00, 0x02, 0x01, 0xEF])
no1_play = bytearray([0x7E, 0xFF, 0x06, 0x03, 0x00, 0x00, 0x01, 0xEF])

class DfPlayerController:
    # DfPlayerの初期化
    def initDfplayer() :
        # 描画タイプ 0:何もなし 1:丸 2:バツ
        draw_type = 0
        print(draw_type)

        # ボリュームサイズ変更
        volumeSet(15)

        # システム起動音再生
        uart.write(startup_sound)

        # TODO 長さ調整
        # 初期待ち
        time.sleep(2.0)


    # DfPlayerのボリュームサイズ変更関数
    def volumeSet(volume) :
        volume_set = bytearray([0x7E, 0xFF, 0x06, 0x06, 0x00, 0x00, int(f'0x{volume:02x}', 16), 0xEF])

        #　ボリューム設定
        uart.write(volume_set)
        time.sleep(0.5)  # 少し待機

    # 抽選配列からランダムに取得した数値(ファイル番号)を返す
    def randomSelect():
        num = random.randint(0, 4)
        print('select array num ' + str(num))
        select_file_number = my_array[num]

        return int(select_file_number)

    # ランダムに曲を再生する
    def randomPlay() :
        # ランダムなファイル番号を取得
        num = randomSelect()

        # いったんバツを表示するように設定
        draw_type = 2

        # 1が選択されたときだけ丸を表示するように設定
        if num == 1 :
            draw_type = 1

        # シリアルデータ準備
        play_sound = bytearray([0x7E, 0xFF, 0x06, 0x03, 0x00, 0x00, int(f'0x{num:02x}', 16), 0xEF])

        # 音声再生
        uart.write(play_sound)

        return {
            'message': 'select file ' + str(num),
            'draw_type': draw_type
        }

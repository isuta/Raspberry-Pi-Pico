from machine import Pin
import time
import random
from modules.oled_controller import OledController

# 設定
uart = machine.UART(0, baudrate=9600, tx=machine.Pin(16), rx=machine.Pin(17))

# シリアルデータの定義
startup_sound = bytearray([0x7E, 0xFF, 0x06, 0x03, 0x00, 0x02, 0x01, 0xEF])
no1_play = bytearray([0x7E, 0xFF, 0x06, 0x03, 0x00, 0x00, 0x01, 0xEF])

# GP24ピンを、入力用のプルダウン抵抗を使用するピンとして設定。
button = machine.Pin(24,machine.Pin.IN,machine.Pin.PULL_DOWN)
button.irq(trigger=Pin.IRQ_RISING, handler=button_pressed)

# GPIO0をLED出力ピンとして設定
led = machine.Pin(0, machine.Pin.OUT)

# 抽選配列を定義 TODO 抽選用テーブルの配列にする
my_array = [1, 2, 3, 4, 5]

# ボタンの設定
def button_pressed(pin):
    randomPlay()

# TODO 必要か確認する
# 初期待ち
time.sleep(2.0)

# DfPlayerの初期化
def initDfplayer() :
    draw_type = 0
    print(draw_type)
    oled_controller.showDisplay('init start', draw_type)

    # ボリュームサイズ変更
    volumeSet(15)

    # システム起動音再生
    uart.write(startup_sound)

    oled_controller.showDisplay('init end', draw_type)
    time.sleep(2)  # 2秒待機してから次を再生（必要に応じて調整）

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

    # 選択された番号を表示
    oled_controller.showDisplay('select file ' + str(num), draw_type)

    # シリアルデータ準備
    play_sound = bytearray([0x7E, 0xFF, 0x06, 0x03, 0x00, 0x00, int(f'0x{num:02x}', 16), 0xEF])

    # 音声再生
    uart.write(play_sound)


# 初期化
initDfplayer()
oled_controller = OledController()

draw_type = 0
oled_controller.showDisplay('loading now', draw_type)
time.sleep(5)  # 少し待機
oled_controller.showTitle()

# スリープと割り込み待機
while True:
    # タイトルを描画
    oled_controller.showTitle()
    lightsleep()

    # TODO 必要か確認する
    # time.sleep(0.01)  # 10ms待機（チャタリング防止）

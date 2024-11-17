from machine import I2C,Pin
import ssd1306
import time
import random
import math # 数学関数

# 設定
uart = machine.UART(0, baudrate=9600, tx=machine.Pin(16), rx=machine.Pin(17))
# シリアルデータの定義
startup_sound = bytearray([0x7E, 0xFF, 0x06, 0x03, 0x00, 0x02, 0x01, 0xEF])
no1_play = bytearray([0x7E, 0xFF, 0x06, 0x03, 0x00, 0x00, 0x01, 0xEF])

# OLEDの準備
i2c=I2C(0,sda=Pin(20),scl=Pin(21),freq=400000)
oled=ssd1306.SSD1306_I2C(128,64,i2c)

# GP24ピンを、入力用のプルダウン抵抗を使用するピンとして設定。
button = machine.Pin(24,machine.Pin.IN,machine.Pin.PULL_DOWN)

# GPIO0をLED出力ピンとして設定
led = machine.Pin(0, machine.Pin.OUT)

# 抽選配列を定義 TODO 抽選用テーブルの配列にする
my_array = [1, 2, 3, 4, 5]

# ボタンの状態管理
button_previous = True  # 初期状態（ボタンが押されていない）
last_play_time = 0      # 最後に音声を再生した時間（タイマー管理）
is_playing = False      # 再生中フラグ

# 初期待ち
time.sleep(2.0)

# 円描画関数（三角関数を使用）
def circle(x, y, l, color):
    for r in range(360):
        oled.pixel(int(x + l * math.cos(math.radians(r))), int(y - l * math.sin(math.radians(r))), color)

# バツ (☓) 描画関数
def cross(x, y, l, color):
    # 対角線1 (左上から右下へ)
    for i in range(l):
        oled.pixel(x - i, y - i, color)  # 左上から中心
        oled.pixel(x + i, y + i, color)  # 中心から右下

    # 対角線2 (右上から左下へ)
    for i in range(l):
        oled.pixel(x + i, y - i, color)  # 右上から中心
        oled.pixel(x - i, y + i, color)  # 中心から左下

# OLEDにメッセージを表示する
def showDisplay(message, draw_result) :
    print(str(message))
    oled.init_display()

    if draw_result == 1:
        # (x, y, 半径, 色) 円描画関数呼び出し
        circle(9, 43, 5, True)
    elif draw_result == 2:
        # (x, y, 半径, 色) バツ描画関数呼び出し
        cross(9, 43, 5, True)

    oled.fill_rect(20,40,30,10,0)
    oled.show()
    oled.text(str(message),20,40)
    oled.show()

# OLEDの上部に枠と表示する　TODO　そのうち共通化して文字変えられるようにするかも
def showTitle() :
    oled.init_display()
    oled.rect(10,0,100,18,1)
    oled.show()
    oled.text("Push Button!",13,5)
    oled.show()

# DfPlayerの初期化
def initDfplayer() :
    oled.init_display()
    draw_type = 0
    print(draw_type)
    showDisplay('init start', draw_type)
    
    # ボリュームサイズ変更
    volumeSet(15)

    # システム起動音再生
    uart.write(startup_sound)

    showDisplay('init end', draw_type)
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
    showDisplay('select file ' + str(num), draw_type)

    # シリアルデータ準備
    play_sound = bytearray([0x7E, 0xFF, 0x06, 0x03, 0x00, 0x00, int(f'0x{num:02x}', 16), 0xEF])

    # 音声再生
    uart.write(play_sound)

# 初期化
initDfplayer()
draw_type = 0
showDisplay('loading now', draw_type)
time.sleep(5)  # 少し待機
showTitle()


# ボタン入力待ちループ
while True:
    button_current = button.value()  # 現在のボタン状態を取得（押されるとHIGH: 1）
    #print(button_current) #確認用

    # ボタンが押されている間はLEDを点灯
    if button_current == 1:  # ボタンが押された場合
        led.value(1)
    else:
        led.value(0)

    # ボタンが「押された瞬間」を検知
    if button_previous == 1 and button_current == 1:  # 前回LOWで今回HIGHなら「押された」
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_play_time) >= 5000:  # 5秒以上経過した場合のみ再生
            randomPlay()
            last_play_time = current_time  # 最後の再生時間を更新
            is_playing = True             # 再生中フラグをセット

    # 再生中かつ5秒経過後にタイトル再描画
    if is_playing:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_play_time) >= 5000:  # 5秒経過チェック
            showTitle()       # タイトルを再描画
            is_playing = False  # 再生中フラグをリセット

    # 現在のボタン状態を次回の比較用に保存
    button_previous = button_current

    time.sleep(0.01)  # 10ms待機（チャタリング防止）

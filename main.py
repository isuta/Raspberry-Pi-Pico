from machine import I2C,Pin
import ssd1306
import time
import random
import math # 数学関数

# 設定
uart = machine.UART(0, baudrate=9600, tx=machine.Pin(12), rx=machine.Pin(13))
# シリアルデータの定義
startup_sound = bytearray([0x7E, 0xFF, 0x06, 0x03, 0x00, 0x02, 0x01, 0xEF])
no1_play = bytearray([0x7E, 0xFF, 0x06, 0x03, 0x00, 0x00, 0x01, 0xEF])

# OLEDの準備
i2c=I2C(0,sda=Pin(16),scl=Pin(17),freq=400000)
oled=ssd1306.SSD1306_I2C(128,64,i2c)

# 抽選配列を定義 TODO 抽選用テーブルの配列にする
my_array = [1, 2, 3, 4, 5]

# GP14ピンを、入力用のプルダウン抵抗を使用するピンとして設定。
button = machine.Pin(14,machine.Pin.IN,machine.Pin.PULL_DOWN)

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
    # ボタン押し待ちの動作確認用
    # print(button.value())
    time.sleep(0.1)
    if button.value() == 1 :
        # メソッドの呼び出し
        randomPlay()
        
        # TODO この辺にLチカを入れる
        
        # ボタン判定ストップのためのスリープ
        time.sleep(5)
        # タイトル再描画
        showTitle()

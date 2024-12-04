from machine import Pin
import time
from modules.oled_controller import OledController
from modules.dfplayer_controller import DfPlayerController

# GP24ピンを、入力用のプルダウン抵抗を使用するピンとして設定。
button = machine.Pin(24,machine.Pin.IN,machine.Pin.PULL_DOWN)
button.irq(trigger=Pin.IRQ_RISING, handler=button_pressed)

# GPIO0をLED出力ピンとして設定
led = machine.Pin(0, machine.Pin.OUT)

# ボタンの設定
def button_pressed(pin):
    ret = dfplayer_controller.randomPlay()

    # 選択された番号を表示
    oled_controller.showDisplay(ret['message'], ret['draw_type'])

# コントローラーの初期化
dfplayer_controller = DfPlayerController()
oled_controller = OledController()

# 描画タイプ 0:何もなし 1:丸 2:バツ
draw_type = 0

# システム開始メッセージ
oled_controller.showDisplay('start engine!', draw_type)

# DfPlayerの初期化
dfplayer_controller.initDfplayer()

# ロード中メッセージ
oled_controller.showDisplay('loading now', draw_type)
# TODO 再生時間調整
time.sleep(5)

# スリープと割り込み待機
while True:
    # タイトルを描画
    oled_controller.showTitle()
    lightsleep()

    # TODO 必要か確認する
    # time.sleep(0.01)  # 10ms待機（チャタリング防止）

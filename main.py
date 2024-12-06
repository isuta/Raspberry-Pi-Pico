from machine import Pin
import time
from modules.oled_controller import OledController
from modules.dfplayer_controller import DfPlayerController

# GP24ピンを、入力用のプルダウン抵抗を使用するピンとして設定。
button = machine.Pin(24,machine.Pin.IN,machine.Pin.PULL_DOWN)
button.irq(trigger=Pin.IRQ_RISING, handler=button_pressed)

# GPIO0をLED出力ピンとして設定
led = machine.Pin(0, machine.Pin.OUT)

# デバウンス時間（ミリ秒）
DEBOUNCE_TIME = 200

# 最後にボタンが押された時間
last_pressed = 0

# 描画タイプ 0:何もなし 1:丸 2:バツ
draw_type = 0

# 再生中フラグ
is_playing = False

# コントローラーの初期化
dfplayer_controller = DfPlayerController()
oled_controller = OledController()

# ボタンの設定
def button_pressed(pin):
    global last_pressed
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_pressed) > DEBOUNCE_TIME and not is_playing:
        last_pressed = current_time
        is_playing = True
        # ランダムで曲を再生
        ret = dfplayer_controller.randomPlay()
        # 選択された番号を表示
        oled_controller.showDisplay(ret['message'], ret['draw_type'])

        # 再生時間を取得して待機
        play_time = ret['play_time']  # 再生時間を秒単位で取得
        time.sleep(play_time)

        is_playing = False

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

    # ボタンが押されている間LEDを点灯
    if button.value() == 1:  # ボタンが押されている間
        led.on()
    else:
        led.off()

    # 少し待機
    time.sleep(0.01)  # 10ms待機（チャタリング防止）

    lightsleep()


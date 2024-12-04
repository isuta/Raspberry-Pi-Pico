from machine import Pin, I2C, lightsleep
import ssd1306  # OLED制御ライブラリ

# OLEDディスプレイの初期化
i2c = I2C(0, scl=Pin(22), sda=Pin(21))  # I2Cピン（環境に合わせて変更）
oled = ssd1306.SSD1306_I2C(128, 64, i2c)  # 解像度に合わせて設定

# ボタンの設定
def button_pressed(pin):
    global button_state
    button_state = "Button Pressed!"
    update_display()

button = Pin(15, Pin.IN, Pin.PULL_DOWN)
button.irq(trigger=Pin.IRQ_RISING, handler=button_pressed)

# 表示内容を更新する関数
def update_display():
    oled.fill(0)  # 画面をクリア
    oled.text("System State:", 0, 0)
    oled.text(button_state, 0, 16)
    oled.show()  # 内容をディスプレイに送信

# 初期表示
button_state = "Waiting..."
update_display()

# スリープと割り込み待機
while True:
    oled.text("Entering sleep...", 0, 48)
    oled.show()
    lightsleep()
    oled.text("Waking up...", 0, 48)
    oled.show()

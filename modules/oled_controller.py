from machine import I2C, Pin
import ssd1306
import math # 数学関数

# OLEDの準備
i2c=I2C(0,sda=Pin(20),scl=Pin(21),freq=400000)
oled=ssd1306.SSD1306_I2C(128,64,i2c)

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

class OledController:

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

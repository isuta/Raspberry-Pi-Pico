import network
import socket
import time
from machine import Pin, PWM

# ========================================
# TB6612 モータードライバ接続
# ========================================
# Pico W          TB6612
# GPIO15 (Pin20) → AIN1 (方向制御1)
# GPIO14 (Pin19) → AIN2 (方向制御2)
# GPIO13 (Pin17) → PWMA (速度制御PWM)
# 3.3V (Pin36)   → VCC (ロジック電源)
# 3.3V (Pin36)   → STBY (スタンバイ解除: Highで動作)
# GND            → GND (共通GND)
# 
# バッテリー      TB6612
# 7.2V+          → VM (モーター電源)
# 7.2V-          → GND
# 
# TB6612         モーター
# AO1            → モーター+
# AO2            → モーター-
# 
# 制御ロジック:
# AIN1 | AIN2 | PWMA | 動作
# -----|------|------|--------
#  H   |  L   | PWM  | 正転
#  L   |  H   | PWM  | 逆転
#  L   |  L   |  -   | ブレーキ
#  H   |  H   |  -   | ブレーキ
# ========================================

# 定数定義
PWM_MAX = 65535      # PWM最大値
PWM_FREQ = 1000      # PWM周波数(Hz)
MOTOR_MIN = -100     # モーター速度最小値
MOTOR_MAX = 100      # モーター速度最大値
DEBUG = False        # デバッグログ有効/無効

motor_ain1 = Pin(15, Pin.OUT)  # 方向制御1 (GPIO15)
motor_ain2 = Pin(14, Pin.OUT)  # 方向制御2 (GPIO14)
motor_pwm = PWM(Pin(13))       # 速度制御PWM (GPIO13)
motor_pwm.freq(PWM_FREQ)

SSID = 'Pico2W_MotorUI'
PASSWORD = 'motor1234'

# グローバル変数
current_val = 0

# --------------------------------------------
# HTMLテンプレート（メモリ効率化: 圧縮版）
# --------------------------------------------
HTML_TEMPLATE = """<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Pico2W Motor</title><style>body{{font-family:Arial,sans-serif;text-align:center;margin-top:50px}}.status{{font-size:24px;font-weight:bold;margin:20px 0}}.buttons button{{padding:15px 30px;margin:10px;font-size:18px;cursor:pointer;border:none;border-radius:8px;width:120px}}.forward{{background-color:#4CAF50;color:white}}.brake{{background-color:#f44336;color:white}}</style></head><body><h1>Pico2W TB6612</h1><div class="status">現在値: <span>{current_val}</span>% ({direction})</div><div class="buttons"><form action="/speed/100" method="get"><button class="forward" type="submit">全速</button></form><form action="/speed/80" method="get"><button class="forward" type="submit">高速</button></form><form action="/speed/60" method="get"><button class="forward" type="submit">中速</button></form><form action="/speed/40" method="get"><button class="forward" type="submit">低速</button></form><form action="/speed/20" method="get"><button class="forward" type="submit">微速</button></form><form action="/speed/0" method="get"><button class="brake" type="submit">停止</button></form></div></body></html>"""

# --------------------------------------------
# 1. HTML生成関数
# --------------------------------------------

def web_page(val):
    """現在のモーター値に基づいたHTMLページを生成する（最適化版）"""
    # 方向判定を簡素化
    if val > 0:
        direction = "正転"
    elif val == 0:
        direction = "ブレーキ"
    else:
        direction = "逆転"
    
    return HTML_TEMPLATE.format(current_val=abs(val), direction=direction)

# --------------------------------------------
# 2. モーター制御関数 (変更なし)
# --------------------------------------------

def update_motor_from_val(val):
    """
    スライダー値(-100～100)からモーターのPWM duty値を設定（最適化版）
    """
    v = int(val)
    
    # 範囲チェック（クランプ処理）
    if v < MOTOR_MIN or v > MOTOR_MAX:
        if not DEBUG:  # デバッグ無効時は警告を省略
            v = max(MOTOR_MIN, min(MOTOR_MAX, v))
        else:
            print(f"Warning: {v} clamped to [{MOTOR_MIN}, {MOTOR_MAX}]")
            v = max(MOTOR_MIN, min(MOTOR_MAX, v))
    
    # モーター制御（最適化: 条件分岐を簡素化）
    if v == 0:
        motor_ain1.value(0)
        motor_ain2.value(0)
        motor_pwm.duty_u16(0)
        if DEBUG:
            print(f"Motor: BRAKE")
    else:
        # duty計算を先に実行（正転/逆転共通）
        duty = int((abs(v) * PWM_MAX) // 100)  # 浮動小数点演算を整数演算に変更
        
        if v > 0:
            # 正転
            motor_ain1.value(1)
            motor_ain2.value(0)
        else:
            # 逆転
            motor_ain1.value(0)
            motor_ain2.value(1)
        
        motor_pwm.duty_u16(duty)
        if DEBUG:
            print(f"Motor: {'FWD' if v > 0 else 'REV'} {abs(v)}% (duty={duty})")

# --------------------------------------------
# 3. AP/サーバー設定 (変更なし)
# --------------------------------------------

def start_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(False)
    time.sleep(0.1)
    ap.config(essid=SSID, password=PASSWORD)
    ap.active(True)
    while not ap.active():
        time.sleep(0.1)
    print('AP mode started')
    print('SSID:', SSID)
    print('IP address:', ap.ifconfig()[0])
    return ap

def start_server():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print('Listening on', addr)
    return s

# --------------------------------------------
# 4. リクエスト処理関数 (固定パスのルーティングに修正)
# --------------------------------------------

def serve_requests(s):
    global current_val
    
    while True:
        conn = None
        try:
            conn, addr = s.accept()
            if DEBUG:
                print('Client:', addr)
            
            # バッファサイズ削減: 1024 -> 256バイト（HTTPリクエスト行のみ取得）
            request = conn.recv(256).decode('utf-8')
            
            # 最初の行のみを取得（メモリ効率化）
            first_line = request.split('\r\n', 1)[0]
            if DEBUG:
                print('Request:', first_line)

            # ルーティング処理（バイトレベル最適化）
            if 'GET /speed/' in first_line:
                try:
                    # パスから数値を取得: 'GET /speed/100 HTTP/1.1' -> '100'
                    # split()を最小限に抑える
                    start = first_line.find('/speed/') + 7  # '/speed/'の長さ
                    end = first_line.find(' ', start)
                    val_str = first_line[start:end] if end > 0 else first_line[start:]
                    
                    # クエリパラメータ除去
                    if '?' in val_str:
                        val_str = val_str[:val_str.find('?')]
                    
                    val = int(val_str)
                    current_val = val
                    update_motor_from_val(val)
                except (ValueError, IndexError):
                    if DEBUG:
                        print(f"Invalid speed value")
            
            # 応答処理（ヘッダー簡略化）
            response = web_page(current_val)
            conn.send(b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n')
            conn.sendall(response.encode('utf-8'))
            
        except OSError:
            if DEBUG:
                print("Socket error")
        except Exception:
            if DEBUG:
                print("Unexpected error")
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass

# --------------------------------------------
# メイン処理 (変更なし)
# --------------------------------------------

def main():
    global server, current_val
    # 初期状態：モーターブレーキ
    motor_ain1.value(0)
    motor_ain2.value(0)
    motor_pwm.duty_u16(0)
    
    start_ap()
    server = start_server()
    print("Starting main loop - Synchronous Motor control mode (Fixed Path Mode)")
    update_motor_from_val(current_val)
    
    serve_requests(server)

if __name__ == "__main__":
    main()


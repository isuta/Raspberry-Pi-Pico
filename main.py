import network
import socket
import time
from machine import Pin, PWM

# ========================================
# DRV8835 モータードライバ接続 (IN/INモード)
# ========================================
# Pico W          DRV8835
# GPIO15 (Pin20) → AIN1 (正転PWM)
# GPIO14 (Pin19) → AIN2 (逆転PWM)
# 3.3V (Pin36)   → VCC (ロジック電源)
# GND            → MODE (IN/INモード設定)
# GND            → GND (共通GND)
# 
# バッテリー      DRV8835
# 7.2V+          → VM (モーター電源)
# 7.2V-          → GND
# 
# DRV8835        モーター
# AOUT1          → モーター+
# AOUT2          → モーター-
# ========================================

motor_ain1 = PWM(Pin(15))  # 正転用PWM (GPIO15)
motor_ain2 = PWM(Pin(14))  # 逆転用PWM (GPIO14)
motor_ain1.freq(1000)      # PWM周波数 1kHz
motor_ain2.freq(1000)

SSID = 'Pico2W_MotorUI'
PASSWORD = 'motor1234'
REQUEST_CHECK_INTERVAL = 0.05  # HTTPリクエストチェック間隔(秒)

def web_page(current_value):
    # HTMLファイルを読み込んで値を埋め込む
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        # プレースホルダーを実際の値に置換
        html = html.replace('value="0"', f'value="{current_value}"')
        html = html.replace('<span id="valDisplay">0</span>', f'<span id="valDisplay">{current_value}</span>')
        return html
    except:
        # ファイルが見つからない場合のフォールバック
        return f"<html><body><h1>Error: index.html not found</h1><p>Current value: {current_value}</p></body></html>"

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
    # ポート再利用オプション設定
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    s.settimeout(REQUEST_CHECK_INTERVAL)  # タイムアウト設定(CPU負荷軽減)
    print('Listening on', addr)
    return s

# 初期設定
current_val = 0       # スライダー初期値を 0（停止）
server = None

def update_motor_from_val(val):
    """
    スライダー値(-100～100)からモーターのPWM duty値を設定
    -100～-1: 逆転(速度可変)
    0: 停止
    1～100: 正転(速度可変)
    """
    v = int(val)
    
    if v == 0:
        # 停止 (両方Low)
        motor_ain1.duty_u16(0)
        motor_ain2.duty_u16(0)
        print("Motor: STOP")
    elif v > 0:
        # 正転 (AIN1=PWM, AIN2=Low)
        duty = int((v / 100) * 65535)
        motor_ain1.duty_u16(duty)
        motor_ain2.duty_u16(0)
        print(f"Motor: FORWARD {v}% (duty={duty})")
    else:
        # 逆転 (AIN1=Low, AIN2=PWM)
        duty = int((abs(v) / 100) * 65535)
        motor_ain1.duty_u16(0)
        motor_ain2.duty_u16(duty)
        print(f"Motor: REVERSE {abs(v)}% (duty={duty})")



def serve_requests():
    global current_val, server
    try:
        conn, addr = server.accept()
        print('Client connected from', addr)
        request = conn.recv(1024).decode('utf-8')
        print('Request =', request)
        if 'GET /?value=' in request:
            val_str = request.split('value=')[1].split(' ')[0]
            val = int(val_str)
            print('New slider value:', val)
            current_val = val
            update_motor_from_val(val)
        response = web_page(current_val)
        conn.send('HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n')
        conn.send(response)
        conn.close()
    except OSError:
        # タイムアウト／接続なし／その他 → 継続
        pass
    except Exception as e:
        print(f"Error: {e}")
        pass

def main():
    global server, current_val
    # 初期状態：モーター停止
    motor_ain1.duty_u16(0)
    motor_ain2.duty_u16(0)
    
    start_ap()
    server = start_server()
    print("Starting main loop - Motor control mode (Forward/Reverse)")
    update_motor_from_val(current_val)
    
    while True:
        # HTTPリクエストを処理（PWMはハードウェアで自動動作）
        serve_requests()
        time.sleep(REQUEST_CHECK_INTERVAL)

if __name__ == "__main__":
    main()

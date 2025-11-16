import network
import socket
import time
from machine import Pin, PWM

# ========================================
# TB6612 モータードライバ接続
# ========================================

motor_ain1 = Pin(15, Pin.OUT)  # 方向制御1 (GPIO15)
motor_ain2 = Pin(14, Pin.OUT)  # 方向制御2 (GPIO14)
motor_pwm = PWM(Pin(13))       # 速度制御PWM (GPIO13)
motor_pwm.freq(1000)           # PWM周波数 1kHz

SSID = 'Pico2W_MotorUI'
PASSWORD = 'motor1234'

# グローバル変数
current_val = 0

# --------------------------------------------
# 1. HTML生成関数 (固定パスに修正)
# --------------------------------------------

def web_page(val):
    """現在のモーター値に基づいたHTMLページを生成する"""
    html = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pico2W Motor Control</title>
  <style>
    body {{ font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }}
    .status {{ font-size: 24px; font-weight: bold; margin: 20px 0; }}
    .buttons button {{
      padding: 15px 30px; margin: 10px; font-size: 18px; cursor: pointer;
      border: none; border-radius: 8px; width: 120px;
    }}
    .forward {{ background-color: #4CAF50; color: white; }}
    .brake {{ background-color: #f44336; color: white; }}
  </style>
</head>
<body>
  <h1>Pico2W TB6612 Control (Fixed Path Mode)</h1>
  <div class="status">
    現在値: <span id="currentValue">{current_val}</span>% ({direction})
  </div>
  <div class="buttons">
        <form action="/speed/100" method="get"><button class="forward" type="submit">全速 (100%)</button></form>
    <form action="/speed/80" method="get"><button class="forward" type="submit">高速 (80%)</button></form>
    <form action="/speed/60" method="get"><button class="forward" type="submit">中速 (60%)</button></form>
    <form action="/speed/40" method="get"><button class="forward" type="submit">低速 (40%)</button></form>
    <form action="/speed/20" method="get"><button class="forward" type="submit">微速 (20%)</button></form>
    <form action="/speed/0" method="get"><button class="brake" type="submit">停止 (0%)</button></form>
  </div>
  <p style="margin-top: 30px; color: #666;">※ボタンを押すと画面全体が更新されます。</p>
</body>
</html>"""
    
    direction = "正転" if val > 0 else "ブレーキ" if val == 0 else "逆転"
    return html.format(current_val=abs(val), direction=direction)

# --------------------------------------------
# 2. モーター制御関数 (変更なし)
# --------------------------------------------

def update_motor_from_val(val):
    """
    スライダー値(-100～100)からモーターのPWM duty値を設定
    """
    v = int(val)
    print(f"================== BUTTON VALUE: {v}% ==================")
    
    if v == 0:
        # ブレーキ
        motor_ain1.value(0)
        motor_ain2.value(0)
        motor_pwm.duty_u16(0)
        print("Motor: BRAKE")
    elif v > 0:
        # 正転
        motor_ain1.value(1)
        motor_ain2.value(0)
        duty = int((v / 100) * 65535)
        motor_pwm.duty_u16(duty)
        print(f"Motor: FORWARD {v}% (duty={duty})")
    else:
        # 逆転 (今回はHTMLにボタンがないが、コードは残す)
        motor_ain1.value(0)
        motor_ain2.value(1)
        duty = int((abs(v) / 100) * 65535)
        motor_pwm.duty_u16(duty)
        print(f"Motor: REVERSE {abs(v)}% (duty={duty})")

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
        conn, addr = s.accept()
        print('Client connected from', addr)
        
        request = conn.recv(1024).decode('utf-8')
        print('Full Request =', request.split('\r\n')[0]) # リクエストの1行目だけ表示

        # ------------------- ルーティング処理 -------------------
        
        # 【修正】 '/speed/' を含むリクエストをチェック
        if 'GET /speed/' in request:
            # モーター制御リクエストを受信 (固定パス)
            try:
                # パスから直接数値を取得: 'GET /speed/100 HTTP/1.1' -> '100'
                val_str = request.split('/speed/')[1].split(' ')[0]

                if '?' in val_str:
                    val_str = val_str.split('?')[0] # '20?' -> '20'

                val = int(val_str)

                current_val = val
                update_motor_from_val(val)
            except Exception as e:
                # 値のパースに失敗した場合 (例: /speed/abc)
                print(f"Error parsing speed value from path: {e}")
                pass
        
        # ------------------- 応答処理 (制御後 or 初期アクセス) -------------------
        
        # 制御後の値、または初期値(0)に基づいてHTMLを生成
        response = web_page(current_val)
        
        # ヘッダー送信
        conn.send('HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nConnection: close\r\n\r\n')
        
        # HTML内容送信
        conn.sendall(response.encode('utf-8'))
        
        conn.close()

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


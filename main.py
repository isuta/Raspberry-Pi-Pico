import network
import socket
import time
from machine import Pin

# オンボードLED（’LED’という名前が使えている前提）
led = Pin('LED', Pin.OUT)

SSID = 'Pico2W_SliderUI'
PASSWORD = 'slider1234'
REQUEST_CHECK_INTERVAL = 0.05  # HTTPリクエストチェック間隔(秒) ※応答性とCPU負荷のバランス調整用

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
current_val = 0       # スライダー初期値を 0（左端）
delay_time = None     # 待ち時間変数。初期は消灯モードとして None
server = None

def update_delay_from_val(val):
    global delay_time
    v = int(val)
    if v <= 0:
        # 消灯モード
        delay_time = None
    elif v >= 100:
        # 点灯しっぱなしモード
        delay_time = 0
    else:
        # 中間値：スライダー値 v に応じて待ち時間を決定
        delay_time = (100 - v) * 0.02  # 係数0.02秒を使用
    print("Updated delay_time:", delay_time)

def serve_requests():
    global current_val, server
    try:
        conn, addr = server.accept()
        print('Client connected from', addr)
        request = conn.recv(1024).decode('utf‑8')
        print('Request =', request)
        if 'GET /?value=' in request:
            val_str = request.split('value=')[1].split(' ')[0]
            val = int(val_str)
            print('New slider value:', val)
            current_val = val
            update_delay_from_val(val)
        response = web_page(current_val)
        conn.send('HTTP/1.1 200 OK\r\nContent‑Type: text/html; charset=utf-8\r\n\r\n')
        conn.send(response)
        conn.close()
    except OSError:
        # タイムアウト／接続なし／その他 → 継続
        pass

def sleep_with_serve(duration):
    """指定時間sleepしながら定期的にHTTPリクエストを処理"""
    if duration <= 0:
        return
    end_time = time.ticks_add(time.ticks_ms(), int(duration * 1000))
    while time.ticks_diff(end_time, time.ticks_ms()) > 0:
        serve_requests()
        time.sleep(REQUEST_CHECK_INTERVAL)  # 定期的にリクエストをチェック

def main():
    global server, current_val, delay_time
    # 初期状態：LED消灯
    led.value(0)
    start_ap()
    server = start_server()
    print("Starting main loop")
    update_delay_from_val(current_val)
    while True:
        # 受信チェック（短くループさせる）
        serve_requests()
        # LED 制御部分
        if delay_time is None:
            # 消灯モード：LED OFF、短時間待って次回チェック
            led.value(0)
            sleep_with_serve(0.1)
        elif delay_time == 0:
            # 点灯モード：LED ON、短時間待って次回チェック
            led.value(1)
            sleep_with_serve(0.1)
        else:
            # 点滅モード：周期に合わせて ON/OFF
            led.value(1)
            sleep_with_serve(delay_time / 2)
            led.value(0)
            sleep_with_serve(delay_time / 2)

if __name__ == "__main__":
    main()

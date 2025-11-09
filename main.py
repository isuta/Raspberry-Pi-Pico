import network
import socket
import time
from machine import Pin

led = Pin('LED', Pin.OUT)

SSID = 'Pico2W_UI'
PASSWORD = 'ui123456'

def web_page():
    html = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pico2W UI</title>
</head>
<body>
  <h1>Pico2W Web Control</h1>
  <p>LED 状態: {state}</p>
  <form action="/led/on"><button type="submit">LED ON</button></form>
  <form action="/led/off"><button type="submit">LED OFF</button></form>
</body>
</html>"""

    state = "ON" if led.value() else "OFF"
    return html.format(state=state)

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

def serve(s):
    while True:
        conn, addr = s.accept()
        print('Client connected from', addr)
        request = conn.recv(1024)
        request = request.decode('utf-8')
        print('Request =', request)
        if request.startswith('GET /led/on'):
            led.value(1)
        if request.startswith('GET /led/off'):
            led.value(0)
        response = web_page()
        conn.send('HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n')
        conn.send(response)
        conn.close()

def main():
    ap = start_ap()
    server = start_server()
    serve(server)

if __name__ == '__main__':
    main()


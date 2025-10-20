# FS90R 連続回転サーボモーターの制御サンプルコード
# Raspberry Pi Pico W / MicroPython

from machine import Pin, PWM
import utime

# --- 制御定数（50Hz / 1.5ms 基準） ---
SERVO_PIN = 15          # FS90Rの信号線(オレンジ)をGP15に接続
FREQUENCY = 50          # サーボの標準周波数 50 Hz (周期 20ms)
DUTY_CYCLE_RANGE = 65535 # Pico PWMの最大値 (16ビット)

# 基準パルス幅 (Duty Cycle) の計算: Duty = (パルス幅[us] / 20000[us]) * 65535
# 停止パルス: 1500us (約 4915)
# 最大逆転パルス: 1000us (約 3277)
# 最大正転パルス: 2000us (約 6554)

# ⚠️ 注意: 停止点(NEUTRAL_DUTY)は個体差があるため、動作を見ながら微調整が必要です。
NEUTRAL_DUTY = 4915     # 停止 (1.5ms)
MAX_FORWARD_DUTY = 6554 # 正転の最大速度 (2.0ms)
MAX_REVERSE_DUTY = 3277 # 逆転の最大速度 (1.0ms)

# PWM設定
servo_pwm = PWM(Pin(SERVO_PIN))
servo_pwm.freq(FREQUENCY)

def set_servo_speed(speed_percent):
    """
    サーボの速度と方向を設定します。
    
    Args:
        speed_percent (int): -100 (最大逆転) から 100 (最大正転) の間の値。
                              0 は停止を意味します。
    """
    if speed_percent > 100:
        speed_percent = 100
    elif speed_percent < -100:
        speed_percent = -100

    if speed_percent == 0:
        duty = NEUTRAL_DUTY
    elif speed_percent > 0:
        # 正転 (NEUTRAL_DUTY から MAX_FORWARD_DUTY へ線形補間)
        # 0% -> NEUTRAL_DUTY, 100% -> MAX_FORWARD_DUTY
        duty = int(NEUTRAL_DUTY + (MAX_FORWARD_DUTY - NEUTRAL_DUTY) * (speed_percent / 100))
    else: # speed_percent < 0
        # 逆転 (NEUTRAL_DUTY から MAX_REVERSE_DUTY へ線形補間)
        # 0% -> NEUTRAL_DUTY, -100% -> MAX_REVERSE_DUTY
        duty = int(NEUTRAL_DUTY + (MAX_REVERSE_DUTY - NEUTRAL_DUTY) * (-speed_percent / 100))
    
    servo_pwm.duty_u16(duty)
    # print(f"速度: {speed_percent}%, Duty: {duty}") # 連続実行時は出力を抑制

def stop_servo():
    """サーボを停止させます。"""
    set_servo_speed(0)
    print(f"--- 停止 (Duty: {NEUTRAL_DUTY}) ---")


def rotate_for_duration(speed_percent, duration_seconds):
    """
    指定した速度で、指定した時間だけサーボを回転させます。
    
    Args:
        speed_percent (int): -100 (最大逆転) から 100 (最大正転) の間の値。
        duration_seconds (float): 回転させる時間（秒）。
    """
    if duration_seconds <= 0:
        stop_servo()
        return

    print(f"回転開始: 速度 {speed_percent}% で {duration_seconds} 秒間...")
    set_servo_speed(speed_percent)
    utime.sleep(duration_seconds)
    stop_servo()
    print(f"回転完了。")

# --- 動作デモ ---
try:
    print("--- FS90R 時間制御デモ開始 ---")
    
    # 1. 停止 (2秒間)
    stop_servo()
    utime.sleep(2)

    # 2. 正転 (50% の速度で 1.5 秒間回転させる = 約 N 回転)
    # 角度制御の代用として「時間」で回転量を制御します。
    rotate_for_duration(speed_percent=50, duration_seconds=1.5)
    utime.sleep(1) # 次の動作までの待機

    # 3. 逆転 (30% の速度で 3.0 秒間回転させる)
    rotate_for_duration(speed_percent=-30, duration_seconds=3.0)
    utime.sleep(1) # 次の動作までの待機

    # 4. 最大速度での短時間回転 (素早い動きのデモ)
    rotate_for_duration(speed_percent=100, duration_seconds=0.3)
    utime.sleep(1)

    # 5. 最終停止
    print("5. 最終停止。")
    stop_servo()

except KeyboardInterrupt:
    print("ユーザーによる停止。")
finally:
    stop_servo()
    servo_pwm.deinit() # PWMリソースを解放
    print("--- 制御デモ終了 ---")

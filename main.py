# --- main.py ---
from machine import Pin
from stepper_motor import StepperMotor
import utime

motor = StepperMotor()

try:
    print("--- ミニステッピングモーター テスト開始 ---")
    
    motor.stop_motor()
    utime.sleep(1)

    print("\n--- 1. 正転 (低速) ---")
    # motor.rotate_steps(num_steps=800, delay_ms=5, direction=1)
    motor.rotate_degrees(90, 1)
    motor.rotate_degrees(180, 1)
    utime.sleep(2)

    print("\n--- 2. 逆転 (高速) ---")
    # motor.rotate_steps(num_steps=800, delay_ms=5, direction=-1)
    motor.rotate_degrees(180, -1)
    motor.rotate_degrees(90, -1)
    utime.sleep(2)

    print("\n--- 3. 最終停止 ---")
    motor.stop_motor()

except KeyboardInterrupt:
    print("\nユーザーによる停止。")

finally:
    motor.stop_motor()
    print("--- テスト終了 ---")


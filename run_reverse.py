import utime
from stepper_motor import StepperMotor
from config import STEPPER_MOTOR_CONFIG

def run_reverse_steps(count=5, speed='VERY_SLOW'):
    """5ステップを逆回転で実行する簡易ランナー（Pico上で直接実行用）"""
    motor = StepperMotor(STEPPER_MOTOR_CONFIG)
    try:
        print("--- 直接実行: 5ステップ逆回転テスト ---")
        print("実行前の位置:", motor.get_current_position())
        motor.rotate_steps(num_steps=count, speed=speed, direction=-1)
        print("実行後の位置:", motor.get_current_position())
    except KeyboardInterrupt:
        print("ユーザー中断")
    except Exception as e:
        print("エラー:", e)
    finally:
        motor.stop()

if __name__ == '__main__':
    run_reverse_steps()

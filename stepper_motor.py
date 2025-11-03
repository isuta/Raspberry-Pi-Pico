from machine import Pin
import config
import utime
import math

"""ステッピングモーター制御クラス
-----------------------------------
ハーフステップ駆動で小型ステッピングモーターを制御します。
角度・ステップ・回転数いずれの単位でも動作可能です。
"""

class StepperMotor:

    # 速度プリセット（1ステップごとの遅延時間 [ms]）
    SPEED_PRESETS = {
        'VERY_SLOW': 50,  # 非常にゆっくり（トルク確認や初期テスト向け）
        'SLOW': 20,       # ゆっくり
        'NORMAL': 10,     # 標準
        'FAST': 5,        # やや速い
        'VERY_FAST': 2    # 非常に速い（脱調注意）
    }
    
    def __init__(self, debug=True):
        self.debug = debug
        pin_cfg = config.STEPPER_MOTOR_CONFIG

        # --- GPIO ピン設定 ---
        self.AIN1 = Pin(pin_cfg['AIN1'], Pin.OUT)
        self.AIN2 = Pin(pin_cfg['AIN2'], Pin.OUT)
        self.BIN1 = Pin(pin_cfg['BIN1'], Pin.OUT)
        self.BIN2 = Pin(pin_cfg['BIN2'], Pin.OUT)
        self.PINS = [self.AIN1, self.AIN2, self.BIN1, self.BIN2]

        # --- ハーフステップシーケンス ---
        # 4相モーターを8パターンで1周期とする最も滑らかな駆動方式。
        # 各リストは [AIN1, AIN2, BIN1, BIN2] の出力状態を表す。
        self.HALF_STEP_SEQUENCE = [
            [1, 0, 0, 0],
            [1, 0, 1, 0],
            [0, 0, 1, 0],
            [0, 1, 1, 0],
            [0, 1, 0, 0],
            [0, 1, 0, 1],
            [0, 0, 0, 1],
            [1, 0, 0, 1]
        ]
        
        # 現在のシーケンス位置を追跡
        self.current_step = 0
        
        # モーターを停止（初期状態は通電OFF）
        self.stop_motor()

        # --- モーター仕様設定 ---
        # 1回転あたりの実ステップ数（モーター構造やドライバ設定に依存）
        # 実測で1回転 ≒ 40ステップ（ハーフステップモード想定）
        self.steps_per_rev = 40
        self.gear_ratio = 1

        # --- シーケンスの現在位置を保持する ---
        self.seq_index = 0        # HALF_STEP_SEQUENCE の現在インデックス（0..7）
        self.current_step = 0     # 論理的な「モーター軸ステップ」位置（0..steps_per_rev-1）

    # ==========================================================
    # 基本制御メソッド
    # ==========================================================

    def set_step(self, step_pattern):
        """指定されたステップパターンを4つのピンに出力します。"""
        for i in range(4):
            self.PINS[i].value(step_pattern[i])

    def _get_delay_ms(self, speed):
        """速度設定から遅延時間を取得します。"""
        if isinstance(speed, str):
            return self.SPEED_PRESETS.get(speed.upper(), self.SPEED_PRESETS['NORMAL'])
        return int(speed)

    def rotate_steps(self, num_steps, delay_ms, direction=1):
        """
        指定ステップ数・速度・方向でモーターを回転させる。
        加減速制御を含む実装。
        """
        sequence_length = len(self.HALF_STEP_SEQUENCE)
        accel_ratio = 0.1  # 全体の10%を加速・減速区間とする

        if self.debug:
            print(f"回転開始: ステップ数={num_steps}, 遅延={delay_ms}ms, 方向={'正転' if direction == 1 else '逆転'}")

        for i in range(num_steps):
            # シーケンス更新
            self.seq_index = (self.seq_index + direction) % sequence_length
            self.set_step(self.HALF_STEP_SEQUENCE[self.seq_index])
            self.current_step = (self.current_step + direction) % self.steps_per_rev

            # 加減速補正
            accel_steps = max(1, int(num_steps * accel_ratio))
            if i < accel_steps:  # 加速区間
                cur_delay = delay_ms * (1.5 - i / accel_steps * 0.5)  # 1.5倍→1.0倍へ
            elif i >= num_steps - accel_steps:  # 減速区間
                decel_i = num_steps - i
                cur_delay = delay_ms * (1.0 + 0.5 * (1 - decel_i / accel_steps))  # 1.0倍→1.5倍へ
            else:  # 定速区間
                cur_delay = delay_ms

            utime.sleep_ms(max(1, int(cur_delay)))

    def stop_motor(self, reset=False):
        """全てのコイルの通電をOFFにし、モーターをフリーにします。"""
        if self.debug:
            print("モーター停止 (通電オフ)")

        self.set_step([0, 0, 0, 0])
        if reset:
            self.current_step = 0

    # ==========================================================
    # 角度・回転数指定の高レベル制御
    # ==========================================================

    def rotate_degrees(self, degrees, speed='NORMAL', direction=1):
        """
        指定角度だけモーターを回転させる。

        Args:
            degrees (float): 回転角度（°）
            speed (str|int): 速度設定（プリセット名またはms値）
            direction (int): 1=正転, -1=逆転
        """
        # 1度あたりのステップ数を算出
        steps_per_degree = self.steps_per_rev / 360.0
        # 総ステップ数 = 角度 × ステップ/度 × ギア比
        total_steps = max(1, round(degrees * steps_per_degree * self.gear_ratio))

        if self.debug:
            print(f"角度指定: {degrees}°, 計算ステップ数: {total_steps}")

        delay_ms = self._get_delay_ms(speed)
        self.rotate_steps(total_steps, delay_ms, direction)

    def rotate_rotations(self, rotations, speed='NORMAL', direction=1):
        """
        指定した回転数だけモーターを回す。

        Args:
            rotations (float): 回転数（例: 0.5 → 半回転）
            speed (str|int): 速度設定（プリセット名またはms値）
            direction (int): 1=正転, -1=逆転
        """
        total_steps = round(rotations * self.steps_per_rev * self.gear_ratio)
        delay_ms = self._get_delay_ms(speed)

        if self.debug:
            print(f"回転指定: {rotations}回転, 総ステップ数: {total_steps}")

        self.rotate_steps(total_steps, delay_ms, direction)


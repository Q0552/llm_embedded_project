"""
ESP32 数据模拟器 — 在没有真实硬件时模拟传感器数据流

模拟 ESP32 固件的行为，输出与真实 ESP32 完全相同的 JSON 格式
用于测试 Python 数据接收和处理链路
"""

import json
import time
import random
import logging
from datetime import datetime
from data_receiver import SensorDataReceiver

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


class ESP32Simulator:
    """模拟 ESP32 传感器节点"""

    def __init__(self, device_id: str = "esp32_001", interval: float = 2.0):
        self.device_id = device_id
        self.interval = interval  # 发送间隔（秒）
        self.running = False
        self.tick = 0

        # 模拟传感器初始值
        self.temperature = 25.0
        self.humidity = 55.0
        self.light = 2000

    def read_sensors(self) -> dict:
        """模拟读取传感器数据，加入随机波动"""
        self.temperature += random.uniform(-0.3, 0.3)
        self.temperature = max(15, min(35, self.temperature))

        self.humidity += random.uniform(-1.0, 1.0)
        self.humidity = max(30, min(80, self.humidity))

        self.light += random.randint(-100, 100)
        self.light = max(0, min(4095, self.light))

        return {
            "temperature": {"value": round(self.temperature, 1), "unit": "c"},
            "humidity": {"value": round(self.humidity, 1), "unit": "%"},
            "light": {"value": self.light, "unit": "raw"},
        }

    def generate_packet(self) -> str:
        """生成与 ESP32 固件格式一致的 JSON 数据包"""
        packet = {
            "device_id": self.device_id,
            "timestamp": self.tick * int(self.interval * 1000),
            "sensors": self.read_sensors(),
        }
        return json.dumps(packet)

    def run(self, count: int = 5, receiver: SensorDataReceiver = None):
        """
        运行模拟器，发送指定数量的数据包

        Args:
            count: 发送的数据包数量
            receiver: 数据接收器，如果为 None 则仅打印
        """
        self.running = True
        logger.info(f"ESP32 模拟器启动 (设备: {self.device_id})")
        logger.info(f"将发送 {count} 个数据包，间隔 {self.interval} 秒")

        for i in range(count):
            self.tick = i
            packet = self.generate_packet()

            if receiver:
                result = receiver.receive_data(packet)
                status = "✓" if result["status"] == "ok" else "✗"
            else:
                status = "○"
                print(f"[{packet}]")

            # 解析显示关键数据
            data = json.loads(packet)
            sensors = data["sensors"]
            logger.info(
                f"[{status}] {data['device_id']} | "
                f"T={sensors['temperature']['value']}C | "
                f"H={sensors['humidity']['value']}% | "
                f"L={sensors['light']['value']}"
            )

            time.sleep(self.interval)

        self.running = False
        logger.info("模拟结束")


def main():
    """运行完整的数据采集演示"""
    print("=" * 60)
    print("  [Week 1] LLM + Embedded - 设备数据采集演示")
    print("=" * 60)

    # 创建接收器
    receiver = SensorDataReceiver()

    # 创建模拟器
    simulator = ESP32Simulator(device_id="esp32_001", interval=1.0)

    # 运行模拟
    simulator.run(count=5, receiver=receiver)

    # 保存数据
    saved = receiver.flush_to_disk()
    print(f"\n[OK] 数据已保存到 data/ 目录，共 {saved} 条记录")
    print("[OK] 数据采集演示完成！")


if __name__ == "__main__":
    main()

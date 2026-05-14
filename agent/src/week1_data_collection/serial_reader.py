"""
串口读取器 — 从 ESP32 串口读取传感器数据

配合 ESP32 固件 (firmware/esp32_device/src/main.cpp) 使用
通过串口接收 JSON 格式的传感器数据，解析后存储
"""

import serial
import json
import logging
import time
from data_receiver import SensorDataReceiver

logger = logging.getLogger(__name__)


class SerialReader:
    """ESP32 串口数据读取器"""

    def __init__(
        self,
        port: str = "COM3",
        baud: int = 115200,
        receiver: SensorDataReceiver = None,
    ):
        self.port = port
        self.baud = baud
        self.receiver = receiver or SensorDataReceiver()
        self.serial = None

    def connect(self) -> bool:
        """连接到 ESP32 串口"""
        try:
            self.serial = serial.Serial(self.port, self.baud, timeout=1)
            logger.info(f"✅ 已连接串口 {self.port} @ {self.baud} baud")
            # 等待 ESP32 复位
            time.sleep(2)
            # 清空缓冲区
            self.serial.reset_input_buffer()
            return True
        except serial.SerialException as e:
            logger.error(f"❌ 串口连接失败: {e}")
            logger.info("提示: 检查端口号是否正确，ESP32 是否已连接")
            return False

    def read_loop(self, duration: int = 30):
        """
        持续读取串口数据

        Args:
            duration: 读取持续时间（秒），结束后自动保存数据
        """
        if not self.serial:
            if not self.connect():
                return

        start = time.time()
        line_buffer = ""
        count = 0

        logger.info(f"🔄 开始读取数据，持续 {duration} 秒...")

        try:
            while time.time() - start < duration:
                if self.serial.in_waiting > 0:
                    char = self.serial.read(1).decode("utf-8", errors="ignore")
                    if char == "\n":
                        line = line_buffer.strip()
                        if line:
                            # 跳过非 JSON 的日志信息
                            if line.startswith("{"):
                                result = self.receiver.receive_data(line)
                                if result["status"] == "ok":
                                    count += 1
                        line_buffer = ""
                    else:
                        line_buffer += char
                else:
                    time.sleep(0.01)

            logger.info(f"📊 读取结束，共收到 {count} 条有效数据")

        except serial.SerialException as e:
            logger.error(f"❌ 串口错误: {e}")
        except KeyboardInterrupt:
            logger.info("⏹ 用户中断")
        finally:
            if self.serial and self.serial.is_open:
                self.serial.close()
            saved = self.receiver.flush_to_disk()
            logger.info(f"💾 已保存 {saved} 条数据")


def main():
    """从串口读取 ESP32 数据"""
    import sys

    port = sys.argv[1] if len(sys.argv) > 1 else "COM3"
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    reader = SerialReader(port=port)
    reader.read_loop(duration=duration)


if __name__ == "__main__":
    main()
